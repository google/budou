# -*- coding: utf-8 -*-
#
# Copyright 2017 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Budou, an automatic CJK line break organizer."""

from __future__ import print_function
from . import cachefactory
import collections
import httplib2
from lxml import etree
from lxml import html
import re
import six
import unicodedata
from google.cloud import language as nlp

cache = cachefactory.load_cache()

Element = collections.namedtuple('Element', ['text', 'tag', 'source', 'index'])
"""HTML element.

Attributes:
  text: Text of the element. (str)
  tag: Tag name of the element. (str)
  source: HTML source of the element. (str)
  index: Character-wise offset from the top of the sentence. (int)
"""


class Chunk(object):
  """Chunk object. This represents a unit for word segmentation.

  Attributes:
    word: Surface word of the chunk. (str)
    pos: Part of speech. (str)
    label: Label information. (str)
    dependency: Dependency to neighbor words. None for no dependency, True for
        dependency to the following word, and False for the dependency to the
        previous word. (bool or None)
  """
  SPACE_POS = 'SPACE'
  HTML_POS = 'HTML'
  DEPENDENT_LABEL = (
      'P', 'SNUM', 'PRT', 'AUX', 'SUFF', 'MWV', 'AUXPASS', 'AUXVV', 'RDROP',
      'NUMBER', 'NUM')

  def __init__(self, word, pos=None, label=None, dependency=None):
    self.word = word
    self.pos = pos
    self.label = label
    self.dependency = dependency
    self._add_dependency_if_punct()

  def __repr__(self):
    return '<Chunk %s pos: %s, label: %s, dependency: %s>' % (
        self.word, self.pos, self.label, self.dependency)

  @classmethod
  def space(cls):
    """Creates space Chunk."""
    chunk = cls(u' ', cls.SPACE_POS)
    return chunk

  @classmethod
  def html(cls, html_code):
    """Creates HTML Chunk."""
    chunk = cls(html_code, cls.HTML_POS)
    return chunk

  def is_space(self):
    """Checks if this is space Chunk."""
    return self.pos == self.SPACE_POS

  def update_as_html(self, word):
    """Updates the chunk as HTML chunk with the given word."""
    self.word = word
    self.pos = self.HTML_POS

  def update_word(self, word):
    """Updates the word of the chunk."""
    self.word = word

  def serialize(self):
    """Returns serialized chunk data in dictionary."""
    return {
        'word': self.word,
        'pos': self.pos,
        'label': self.label,
        'dependency': self.dependency
    }

  def maybe_add_dependency(self, default_dependency_direction):
    """Adds dependency if any dependency is not assigned yet."""
    if self.dependency is None and self.label in self.DEPENDENT_LABEL:
      self.dependency = default_dependency_direction

  def _add_dependency_if_punct(self):
    """Adds dependency if the chunk is punctuation."""
    if self.pos == 'PUNCT':
      try:
        # Getting unicode category to determine the direction.
        # Concatenates to the following if it belongs to Ps or Pi category.
        # Ps: Punctuation, open (e.g. opening bracket characters)
        # Pi: Punctuation, initial quote (e.g. opening quotation mark)
        # Otherwise, concatenates to the previous word.
        # See also https://en.wikipedia.org/wiki/Unicode_character_property
        category = unicodedata.category(self.word)
        self.dependency = category in ('Ps', 'Pi')
      except:
        pass


class ChunkQueue(object):
  """Chunk queue object.

  Attributes:
    chunks: List of included Chunk objects. (list of Chunk)
  """

  def __init__(self):
    self.chunks = []

  def add(self, chunk):
    """Adds a chunk to the chunk list."""
    self.chunks.append(chunk)

  def resolve_dependency(self):
    """Resolves chunk dependency by concatenating them."""
    self._concatenate_inner(True)
    self._concatenate_inner(False)

  def _concatenate_inner(self, direction):
    """Concatenates chunks based on each chunk's dependency.

    Args:
      direction: Direction of concatenation process. True for forward. (bool)
    """
    result = []
    tmp_bucket = []
    chunks = self.chunks if direction else self.chunks[::-1]
    for chunk in chunks:
      if (
            # if the chunk has matched dependency, do concatenation.
            chunk.dependency == direction or
            # if the chunk is SPACE, concatenate to the previous chunk.
            (direction == False and chunk.is_space())
        ):
        tmp_bucket.append(chunk)
        continue
      tmp_bucket.append(chunk)
      if not direction: tmp_bucket = tmp_bucket[::-1]
      new_word = ''.join([tmp_chunk.word for tmp_chunk in tmp_bucket])
      chunk.update_word(new_word)
      result.append(chunk)
      tmp_bucket = []
    if tmp_bucket: result += tmp_bucket
    self.chunks = result if direction else result[::-1]

  def get_overlaps(self, offset, length):
    """Returns chunks overlapped with the given range.

    Args:
      offset: Begin offset of the range. (int)
      length: Length of the range. (int)

    Returns:
      Overlapped chunks. (list of Chunk)
    """
    # In case entity's offset points to a space just before the entity.
    if ''.join([chunk.word for chunk in self.chunks])[offset] == ' ':
      offset += 1
    index = 0
    result = []
    for chunk in self.chunks:
      if offset < index + len(chunk.word) and index < offset + length:
        result.append(chunk)
      index += len(chunk.word)
    return result

  def swap(self, old_chunks, new_chunk):
    """Swaps old consecutive chunks with new chunk.

    Args:
      old_chunks: List of consecutive Chunks to be removed. (list of Chunk)
      new_chunk: A Chunk to be inserted. (Chunk)
    """
    indexes = [self.chunks.index(chunk) for chunk in old_chunks]
    del self.chunks[indexes[0]:indexes[-1] + 1]
    self.chunks.insert(indexes[0], new_chunk)


class Budou(object):
  """A parser for CJK line break organizer.

  Attributes:
    service: A Resource object with methods for interacting with the service.
        (googleapiclient.discovery.Resource)
  """
  DEFAULT_CLASS_NAME = 'ww'

  def __init__(self):
    self.client = None

  @classmethod
  def authenticate(cls, json_path=None):
    """Authenticates user for Cloud Natural Language API and returns the parser.

    If the credential file path is not given, this tries to generate credentials
    from default settings.

    Args:
      json_path: A file path to a credential JSON file for a Google Cloud
          Project which Cloud Natural Language API is enabled. (str, optional)

    Returns:
      Budou parser. (Budou)
    """
    parser = cls()
    if json_path:
      try:
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_file(
            json_path)
        parser.client = nlp.LanguageServiceClient(credentials=credentials)
      except ImportError:
        print('Failed to load google.oauth2.service_account module.',
              'If you are running this script in Google App Engine',
              'environemnt, please call `authenticate` method with empty',
              'argument, which will result in caching results with memcache.')
    else:
      parser.client = nlp.LanguageServiceClient()
    return parser

  def parse(self, source, attributes=None, use_cache=True, language=None,
            use_entity=False, classname=None):
    """Parses input HTML code into word chunks and organized code.

    Args:
      source: HTML code to be processed. (str)
      attributes: A key-value mapping for attributes of output elements.
          (dictionary, optional)
          **This argument used to accept a string or a list of strings to
          specify class names of the output chunks, but this designation method
          is now deprecated. Please use a dictionary to designate attributes.**
      use_cache: Whether to use caching. (bool, optional)
      language: A language used to parse text. (str, optional)
      use_entity: Whether to use entities Entity Analysis results. Note that it
          makes additional request to API, which may incur additional cost.
          (bool, optional)
      classname: A class name of output elements. (str, optional)
          **This argument is deprecated. Please use attributes argument
          instead.**

    Returns:
      A dictionary with the list of word chunks and organized HTML code.
      For example:

      {
        'chunks': [
          {'dependency': None, 'label': 'NSUBJ', 'pos': 'NOUN', 'word': '今日も'},
          {'dependency': None, 'label': 'ROOT', 'pos': 'VERB', 'word': '食べる'}
        ],
        'html_code': '<span class="ww">今日も</span><span class="ww">食べる</span>'
      }
    """
    if use_cache:
      result_value = cache.get(source, language)
      if result_value: return result_value
    source = self._preprocess(source)
    dom = html.fragment_fromstring(source, create_parent='body')
    input_text = dom.text_content()

    if language == 'ko':
      # Korean has spaces between words, so this simply parses words by space
      # and wrap them as chunks.
      queue = self._get_chunks_per_space(input_text)
    else:
      queue = self._get_chunks_with_api(input_text, language, use_entity)
    elements = self._get_elements_list(dom)
    queue = self._migrate_html(queue, elements)
    attributes = self._get_attribute_dict(attributes, classname)
    html_code = self._spanize(queue, attributes)
    result_value = {
        'chunks': [chunk.serialize() for chunk in queue.chunks],
        'html_code': html_code
    }
    cache.set(source, language, result_value)
    return result_value

  def _get_chunks_per_space(self, input_text):
    """Returns a chunk queue by separating words by spaces.

    Args:
      input_text: String to parse. (str)

    Returns:
      A queue of chunks. (ChunkQueue)
    """
    queue = ChunkQueue()
    words = input_text.split()
    for i, word in enumerate(words):
      queue.add(Chunk(word))
      if i < len(words) - 1:  # Add no space after the last word.
        queue.add(Chunk.space())
    return queue

  def _get_chunks_with_api(self, input_text, language=None, use_entity=False):
    """Returns a chunk queue by using Google Cloud Natural Language API.

    Args:
      input_text: String to parse. (str)
      language: A language code. 'ja' and 'ko' are supported. (str, optional)
      use_entity: Whether to use entities in Natural Language API response.
      (bool, optional)

    Returns:
      A queue of chunks. (ChunkQueue)
    """
    queue = self._get_source_chunks(input_text, language)
    if use_entity:
      entities = self.get_entities(input_text, language)
      queue = self._group_chunks_by_entities(queue, entities)
    queue.resolve_dependency()
    return queue

  def _get_attribute_dict(self, attributes, classname=None):
    """Returns a dictionary of HTML element attributes.

    Args:
      attributes: If a dictionary, it should be a map of name-value pairs for
      attributes of output elements. If a string, it should be a class name of
      output elements. (dict or str)
      classname: Optional class name. (str, optional)

    Returns:
      An attribute dictionary. (dict of (str, str))
    """
    if attributes and isinstance(attributes, six.string_types):
      return {
          'class': attributes
      }
    if not attributes:
      attributes = {}
    if not classname:
      classname = self.DEFAULT_CLASS_NAME
    attributes.setdefault('class', classname)
    return attributes

  def _preprocess(self, source):
    """Removes unnecessary break lines and white spaces.

    Args:
      source: HTML code to be processed. (str)

    Returns:
      Preprocessed HTML code. (str)
    """
    source = source.replace(u'\n', u'').strip()
    source = re.sub(r'<br\s*\/?\s*>', u' ', source, re.I)
    source = re.sub(r'\s\s+', u' ', source)
    return source

  def _get_source_chunks(self, input_text, language=None):
    """Returns a chunk queue retrieved from Syntax Analysis results.

    Args:
      input_text: Text to annotate. (str)
      language: Language of the text. 'ja' and 'ko' are supported.
          (str, optional)

    Returns:
      A queue of chunks. (ChunkQueue)
    """
    queue = ChunkQueue()
    sentence_length = 0
    tokens = self.get_annotations(input_text, language)
    for i, token in enumerate(tokens):
      word = token['text']['content']
      begin_offset = token['text']['beginOffset']
      label = token['dependencyEdge']['label']
      pos = token['partOfSpeech']['tag']
      if begin_offset > sentence_length:
        queue.add(Chunk.space())
        sentence_length = begin_offset
      chunk = Chunk(word, pos, label)
      # Determining default concatenating direction based on syntax dependency.
      chunk.maybe_add_dependency(
          i < token['dependencyEdge']['headTokenIndex'])
      queue.add(chunk)
      sentence_length += len(word)
    return queue

  def _migrate_html(self, queue, elements):
    """Migrates HTML elements to the word chunks by bracketing each element.

    Args:
      queue: The queue of chunks to be processed. (ChunkQueue)
      elements: List of Element. (list of Element)

    Returns:
      A queue of chunks. (ChunkQueue)
    """
    for element in elements:
      concat_chunks = queue.get_overlaps(element.index, len(element.text))
      if not concat_chunks: continue
      new_chunk_word = u''.join([chunk.word for chunk in concat_chunks])
      new_chunk_word = new_chunk_word.replace(element.text, element.source)
      new_chunk = Chunk.html(new_chunk_word)
      queue.swap(concat_chunks, new_chunk)
    return queue

  def _group_chunks_by_entities(self, queue, entities):
    """Groups chunks by entities retrieved from NL API Entity Analysis.

    Args:
      queue: The queue of chunks to be processed. (ChunkQueue)
      entities: List of entities. (list of dict)

    Returns:
      A queue of chunks. (ChunkQueue)
    """
    for entity in entities:
      concat_chunks = queue.get_overlaps(
          entity['beginOffset'], len(entity['content']))
      if not concat_chunks: continue
      new_chunk_word = u''.join([chunk.word for chunk in concat_chunks])
      new_chunk = Chunk(new_chunk_word)
      queue.swap(concat_chunks, new_chunk)
    return queue

  def _get_elements_list(self, dom):
    """Digs DOM to the first depth and returns the list of elements.

    Args:
      dom: DOM to access the given HTML source. (lxml.html.HtmlElement)

    Returns:
      A list of elements. (list of Element)
    """
    elements = []
    index = 0
    if dom.text:
      index += len(dom.text)
    for element in dom:
      text = etree.tostring(
          element, with_tail=False, method='text',
          encoding='utf8').decode('utf8')
      source = etree.tostring(
          element, with_tail=False, encoding='utf8').decode('utf8')
      elements.append(Element(text, element.tag, source, index))
      index += len(text)
      if element.tail: index += len(element.tail)
    return elements

  def _spanize(self, queue, attributes):
    """Returns concatenated HTML code with SPAN tag.

    Args:
      queue: The queue of chunks to be processed. (ChunkQueue)
      attributes: If a dictionary, it should be a map of name-value pairs for
          attributes of output SPAN tags. If a string, it should be a class name
          of output SPAN tags. If an array, it should be a list of class names
          of output SPAN tags. (str or dict or list of str)

    Returns:
      The organized HTML code. (str)
    """
    result = []
    for chunk in queue.chunks:
      if chunk.is_space():
        result.append(chunk.word)
      else:
        attribute_str = ' '.join(
            '%s="%s"' % (k, v) for k, v in sorted(attributes.items()))
        result.append('<span %s>%s</span>' % (attribute_str, chunk.word))
    return ''.join(result)

  def get_annotations(self, text, language=None, encoding='UTF32'):
    """Returns the list of annotations from the given text."""
    document = nlp.types.Document(
        content=text,
        language=language,
        type='PLAIN_TEXT'
    )
    response = self.client.annotate_text(
        document=document,
        features={'extract_syntax': True},
        encoding_type=encoding,
    )

    result = []
    for token in response.tokens:
      result.append({
          "dependencyEdge": {
              "headTokenIndex": token.dependency_edge.head_token_index,
              "label": token.dependency_edge.Label.Name(
                  token.dependency_edge.label)
          },
          "partOfSpeech": {
              "tag": token.part_of_speech.Tag.Name(token.part_of_speech.tag)
          },
          "text": {
              "beginOffset": token.text.begin_offset,
              "content": token.text.content
          }
      })
    return result

  def get_entities(self, text, language='', encoding='UTF32'):
    """Returns the list of annotations from the given text."""
    document = nlp.types.Document(
        content=text,
        language=language,
        type='PLAIN_TEXT'
    )
    response = self.client.analyze_entities(
        document=document,
        encoding_type=encoding,
    )

    result = []
    for entity in response.entities:
      mentions = entity.mentions
      if not mentions: continue
      entity_text = mentions[0].text
      offset = entity_text.begin_offset
      for word in entity_text.content.split():
        result.append({
            'content': word,
            'beginOffset': offset
        })
        offset += len(word)
    return result
