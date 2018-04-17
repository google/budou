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

from .cachefactory import load_cache
import collections
from xml.etree import ElementTree as ET
import html5lib
import re
import six
import unicodedata

cache = load_cache()


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
  BREAK_POS = 'BREAK'
  DEPENDENT_LABEL = (
      'P', 'SNUM', 'PRT', 'AUX', 'SUFF', 'AUXPASS', 'RDROP', 'NUMBER', 'NUM',
      'PREF')

  def __init__(self, word, pos=None, label=None, dependency=None):
    self.word = word
    self.pos = pos
    self.label = label
    self.dependency = dependency
    self._add_dependency_if_punct()

  def __repr__(self):
    return 'Chunk(%s, %s, %s, %s)' % (
        repr(self.word), self.pos, self.label, self.dependency)

  @classmethod
  def space(cls):
    """Creates space Chunk."""
    chunk = cls(u' ', cls.SPACE_POS)
    return chunk

  @classmethod
  def breakline(cls):
    """Creates breakline Chunk."""
    chunk = cls(u'\n', cls.BREAK_POS)
    return chunk

  def is_space(self):
    """Checks if this is space Chunk."""
    return self.pos == self.SPACE_POS

  def has_cjk(self):
    """Checks if the word of the chunk contains CJK characters

    Using range from
    https://github.com/nltk/nltk/blob/develop/nltk/tokenize/util.py#L149
    """
    for char in self.word:
      if any([start <= ord(char) <= end for start, end in
          [(4352, 4607), (11904, 42191), (43072, 43135), (44032, 55215),
           (63744, 64255), (65072, 65103), (65381, 65500),
           (131072, 196607)]
          ]):
        return True
    return False

  def update_word(self, word):
    """Updates the word of the chunk."""
    self.word = word

  def serialize(self):
    """Returns serialized chunk data in dictionary."""
    return {
        'word': self.word,
        'pos': self.pos,
        'label': self.label,
        'dependency': self.dependency,
        'has_cjk': self.has_cjk(),
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


class ChunkList(list):
  """Chunk list. """

  def get_overlaps(self, offset, length):
    """Returns chunks overlapped with the given range.

    Args:
      offset: Begin offset of the range. (int)
      length: Length of the range. (int)

    Returns:
      Overlapped chunks. (list of Chunk)
    """
    # In case entity's offset points to a space just before the entity.
    if ''.join([chunk.word for chunk in self])[offset] == ' ':
      offset += 1
    index = 0
    result = []
    for chunk in self:
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
    indexes = [self.index(chunk) for chunk in old_chunks]
    del self[indexes[0]:indexes[-1] + 1]
    self.insert(indexes[0], new_chunk)


class Budou(object):
  """A parser for CJK line break organizer.

  Attributes:
    service: A Resource object with methods for interacting with the service.
        (googleapiclient.discovery.Resource)
  """
  DEFAULT_CLASS_NAME = 'ww'

  def __init__(self, service):
    self.service = service

  @classmethod
  def authenticate(cls, json_path=None):
    """Authenticates for Cloud Natural Language API and returns a parser.

    If a service account private key file is not given, it tries to authenticate
    with default credentials.

    Args:
      json_path: A file path to a service account's JSON private keyfile.
          (str, optional)

    Returns:
      Budou parser. (Budou)
    """
    import google_auth_httplib2
    from googleapiclient import discovery
    scope = ['https://www.googleapis.com/auth/cloud-platform']
    if json_path:
      try:
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_file(
            json_path)
        scoped_credentials = credentials.with_scopes(scope)
      except ImportError:
        print('''Failed to load google.oauth2.service_account module.
              If you are running this script in Google App Engine environment,
              please call `authenticate` method with empty argument to
              authenticate with default credentials.''')
    else:
      import google.auth
      scoped_credentials, project = google.auth.default(scope)
    authed_http = google_auth_httplib2.AuthorizedHttp(scoped_credentials)
    service = discovery.build('language', 'v1beta2', http=authed_http)
    return cls(service)

  def parse(self, source, attributes=None, use_cache=True, language=None,
            max_length=None, use_entity=False, classname=None):
    """Parses input HTML code into word chunks and organized code.

    Args:
      source: Text to be processed. (str)
      attributes: A key-value mapping for attributes of output elements.
          (dictionary, optional)
          **This argument used to accept a string or a list of strings to
          specify class names of the output chunks, but this designation method
          is now deprecated. Please use a dictionary to designate attributes.**
      use_cache: Whether to use caching. (bool, optional)
      language: A language used to parse text. (str, optional)
      max_length: Maximum length of span enclosed chunk. (int, optional)
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
    input_text = self._preprocess(source)

    if language == 'ko':
      # Korean has spaces between words, so this simply parses words by space
      # and wrap them as chunks.
      chunks = self._get_chunks_per_space(input_text)
    else:
      chunks, tokens, language = self._get_chunks_with_api(
          input_text, language, use_entity)
    attributes = self._get_attribute_dict(attributes, classname)
    html_code = self._html_serialize(chunks, attributes, max_length)
    result_value = {
        'chunks': [chunk.serialize() for chunk in chunks],
        'html_code': html_code,
        'language': language,
        'tokens': tokens,
    }
    if use_cache:
      cache.set(source, language, result_value)
    return result_value

  def _get_chunks_per_space(self, input_text):
    """Returns a chunk list by separating words by spaces.

    Args:
      input_text: String to parse. (str)

    Returns:
      A chunk list. (ChunkList)
    """
    chunks = ChunkList()
    words = input_text.split()
    for i, word in enumerate(words):
      chunks.append(Chunk(word))
      if i < len(words) - 1:  # Add no space after the last word.
        chunks.append(Chunk.space())
    return chunks

  def _get_chunks_with_api(self, input_text, language=None, use_entity=False):
    """Returns a chunk list by using Google Cloud Natural Language API.

    Args:
      input_text: String to parse. (str)
      language: A language code. 'ja' and 'ko' are supported. (str, optional)
      use_entity: Whether to use entities in Natural Language API response.
      (bool, optional)

    Returns:
      A chunk list. (ChunkList)
    """
    chunks, tokens, language = self._get_source_chunks(input_text, language)
    if use_entity:
      entities = self._get_entities(input_text, language)
      chunks = self._group_chunks_by_entities(chunks, entities)
    chunks = self._resolve_dependency(chunks)
    chunks = self._insert_breakline(chunks)
    return chunks, tokens, language

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
    doc = html5lib.parseFragment(source)
    source = ET.tostring(doc, encoding='utf-8', method='text').decode('utf-8')
    source = source.replace(u'\n', u'').strip()
    source = re.sub(r'\s\s+', u' ', source)
    return source

  def _get_source_chunks(self, input_text, language=None):
    """Returns a chunk list retrieved from Syntax Analysis results.

    Args:
      input_text: Text to annotate. (str)
      language: Language of the text. 'ja' and 'ko' are supported.
          (str, optional)

    Returns:
      A chunk list. (ChunkList)
    """
    chunks = ChunkList()
    sentence_length = 0
    tokens, language = self._get_annotations(input_text, language)
    for i, token in enumerate(tokens):
      word = token['text']['content']
      begin_offset = token['text']['beginOffset']
      label = token['dependencyEdge']['label']
      pos = token['partOfSpeech']['tag']
      if begin_offset > sentence_length:
        chunks.append(Chunk.space())
        sentence_length = begin_offset
      chunk = Chunk(word, pos, label)
      # Determining default concatenating direction based on syntax dependency.
      chunk.maybe_add_dependency(
          i < token['dependencyEdge']['headTokenIndex'])
      chunks.append(chunk)
      sentence_length += len(word)
    return chunks, tokens, language

  def _group_chunks_by_entities(self, chunks, entities):
    """Groups chunks by entities retrieved from NL API Entity Analysis.

    Args:
      chunks: The list of chunks to be processed. (ChunkList)
      entities: List of entities. (list of dict)

    Returns:
      A chunk list. (ChunkList)
    """
    for entity in entities:
      chunks_to_concat = chunks.get_overlaps(
          entity['beginOffset'], len(entity['content']))
      if not chunks_to_concat: continue
      new_chunk_word = u''.join([chunk.word for chunk in chunks_to_concat])
      new_chunk = Chunk(new_chunk_word)
      chunks.swap(chunks_to_concat, new_chunk)
    return chunks

  def _html_serialize(self, chunks, attributes, max_length):
    """Returns concatenated HTML code with SPAN tag.

    Args:
      chunks: The list of chunks to be processed. (ChunkList)
      attributes: If a dictionary, it should be a map of name-value pairs for
          attributes of output SPAN tags. If a string, it should be a class name
          of output SPAN tags. If an array, it should be a list of class names
          of output SPAN tags. (str or dict or list of str)
      max_length: Maximum length of span enclosed chunk. (int, optional)      

    Returns:
      The organized HTML code. (str)
    """
    doc = ET.Element('span')
    for chunk in chunks:
      if chunk.is_space():
        if doc.getchildren():
          if doc.getchildren()[-1].tail is None:
            doc.getchildren()[-1].tail = ' '
          else:
            doc.getchildren()[-1].tail += ' '
        else:
          if doc.text is not None:
            # We want to preserve space in cases like "Hello 你好"
            # But the space in " 你好" can be discarded.
            doc.text += ' '
      else:
        if chunk.has_cjk() and not (max_length and len(chunk.word) > max_length):
          ele = ET.Element('span')
          ele.text = chunk.word
          for k, v in attributes.items():
            ele.attrib[k] = v
          doc.append(ele)
        else:
          # add word without span tag for non-CJK text (e.g. English)
          # by appending it after the last element
          if doc.getchildren():
            if doc.getchildren()[-1].tail is None:
              doc.getchildren()[-1].tail = chunk.word
            else:
              doc.getchildren()[-1].tail += chunk.word
          else:
            if doc.text is None:
              doc.text = chunk.word
            else:
              doc.text += chunk.word
    result = ET.tostring(doc, encoding='utf-8').decode('utf-8')
    result = html5lib.serialize(
        html5lib.parseFragment(result), sanitize=True,
        quote_attr_values="always")
    return result

  def _resolve_dependency(self, chunks):
    """Resolves chunk dependency by concatenating them.

    Args:
      chunks: a chink list. (ChunkList)

    Returns:
      A chunk list. (ChunkList)
    """
    chunks = self._concatenate_inner(chunks, True)
    chunks = self._concatenate_inner(chunks, False)
    return chunks

  def _concatenate_inner(self, chunks, direction):
    """Concatenates chunks based on each chunk's dependency.

    Args:
      direction: Direction of concatenation process. True for forward. (bool)

    Returns:
      A chunk list. (ChunkList)
    """
    tmp_bucket = []
    source_chunks = chunks if direction else chunks[::-1]
    target_chunks = ChunkList()
    for chunk in source_chunks:
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
      target_chunks.append(chunk)
      tmp_bucket = []
    if tmp_bucket: target_chunks += tmp_bucket
    return target_chunks if direction else target_chunks[::-1]

  def _insert_breakline(self, chunks):
    """Inserts a breakline instead of a trailing space if the chunk is in CJK.

    Args:
      chunks: a chunk list. (ChunkList)

    Returns:
      A chunk list. (ChunkList)
    """
    target_chunks = ChunkList()
    for chunk in chunks:
      if chunk.word[-1] == ' ' and chunk.has_cjk():
        chunk_to_add = Chunk(
            chunk.word[:-1], chunk.pos, chunk.label, chunk.dependency)
        target_chunks.append(chunk_to_add)
        target_chunks.append(chunk.breakline())
      else:
        target_chunks.append(chunk)
    return target_chunks

  def _get_annotations(self, text, language='', encoding='UTF32'):
    """Returns the list of annotations from the given text."""
    body = {
        'document': {
            'type': 'PLAIN_TEXT',
            'content': text,
        },
        'features': {
            'extract_syntax': True,
        },
        'encodingType': encoding,
    }

    if language:
      body['document']['language'] = language

    request = self.service.documents().annotateText(body=body)
    response = request.execute()
    tokens = response.get('tokens', [])
    language = response.get('language')
    return tokens, language

  def _get_entities(self, text, language='', encoding='UTF32'):
    """Returns the list of annotations from the given text."""
    body = {
        'document': {
            'type': 'PLAIN_TEXT',
            'content': text,
        },
        'encodingType': encoding,
    }

    if language:
      body['document']['language'] = language

    request = self.service.documents().analyzeEntities(body=body)
    response = request.execute()
    result = []
    for entity in response.get('entities', []):
      mentions = entity.get('mentions', [])
      if not mentions: continue
      entity_text = mentions[0]['text']
      offset = entity_text['beginOffset']
      for word in entity_text['content'].split():
        result.append({'content': word, 'beginOffset': offset})
        offset += len(word)
    return result
