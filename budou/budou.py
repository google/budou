# -*- coding: utf-8 -*-
#
# Copyright 2016 Google Inc. All rights reserved.
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

import collections
from googleapiclient import discovery
import hashlib
import httplib2
from lxml import etree
from lxml import html
from oauth2client.client import GoogleCredentials
import oauth2client.service_account
import re
import shelve
import six

Chunk = collections.namedtuple('Chunk', ['word', 'pos', 'label', 'forward'])
"""Word chunk object.

Args:
  word: Surface word of the chunk. (unicode)
  pos: Part of speech. (string)
  label: Label information. (string)
  forward: Whether the word depends on the following words. (boolean)
"""

Element = collections.namedtuple('Element', ['text', 'tag', 'source', 'index'])
"""HTML element object.

Args:
  text: Text of the element (unicode).
  tag: Tag name of the element (string).
  source: HTML source of the element (string).
  index: Character-wise offset from the top of the sentence (number).
"""

SPACE_POS = 'SPACE'
HTML_POS = 'HTML'
DEFAULT_CLASS_NAME = 'ww'
TARGET_LABEL = ('P', 'SNUM', 'PRT', 'AUX', 'SUFF', 'MWV', 'AUXPASS', 'AUXVV')
CACHE_SALT = '2016-09-13'
CACHE_FILE_NAME = 'budou-cache'


class Budou(object):
  """A parser for CJK line break organizer.

  Attributes:
    service: A Resource object with methods for interacting with the service.
  """

  def __init__(self, service):
    self.service = service

  @classmethod
  def authenticate(cls, json_path=None):
    """Authenticates user for Cloud Natural Language API and returns the parser.

    If the credential file path is not given, this tries to generate credentials
    from default settings.

    Args:
      json_path: A file path to a credential JSON file for a Google Cloud
      Project which Cloud Natural Language API is enabled (string, optional).

    Returns:
      Budou module.
    """
    if json_path:
      credentials = (
          oauth2client.service_account.ServiceAccountCredentials
          .from_json_keyfile_name(json_path))
    else:
      credentials = GoogleCredentials.get_application_default()
    scoped_credentials = credentials.create_scoped(
        ['https://www.googleapis.com/auth/cloud-platform'])
    http = httplib2.Http()
    scoped_credentials.authorize(http)
    service = discovery.build('language', 'v1beta1', http=http)
    return cls(service)

  def parse(self, source, attributes=None, use_cache=True, language='',
            classname=DEFAULT_CLASS_NAME):
    """Parses input HTML code into word chunks and organized code.

    Args:
      source: HTML code to be processed (unicode).
      attributes: If a dictionary, then a map of name-value pairs for attributes
      of output SPAN tags. If a string, then this is the class name of output
      SPAN tags. If an array, the elements will be joined together as the class
      name of SPAN tags (dictionary|string, optional).
      use_cache: Whether to use cache (boolean, optional).
      language: A language used to parse text (string, optional).
      classname: A class name of output SPAN tags (string, optional).
      **This argument is deprecated. Please use attributes arg instead.
      When specified with the attributes arg, the class name in the attributes
      arg will be used.**

    Returns:
      A dictionary with the list of word chunks and organized HTML code.
    """
    if use_cache:
      cache_shelve = shelve.open(CACHE_FILE_NAME)
      cache_key = self._get_cache_key(source, language)
      result_value = cache_shelve.get(cache_key, None)
      cache_shelve.close()
      if result_value: return result_value
    source = self._preprocess(source)
    dom = html.fragment_fromstring(source, create_parent='body')
    input_text = dom.text_content()
    chunks = self._get_source_chunks(input_text, language)
    chunks = self._concatenate_punctuations(chunks)
    chunks = self._concatenate_by_label(chunks, True)
    chunks = self._concatenate_by_label(chunks, False)
    chunks = self._migrate_html(chunks, dom)
    attributes = self._get_attribute_dict(attributes, classname)
    html_code = self._spanize(chunks, attributes)
    result_value = {
        'chunks': chunks,
        'html_code': html_code
    }
    if use_cache:
      cache_shelve = shelve.open(CACHE_FILE_NAME)
      cache_shelve[cache_key] = result_value
      cache_shelve.close()
    return result_value

  def _get_attribute_dict(self, attributes, classname=None):
    """Returns a dictionary of attribute name-value pairs.

    Args:
      attributes: If a dictionary, then a map of name-value pairs for attributes
      of output SPAN tags. If a string, then this is the class name of output
      SPAN tags (dictionary|string).
      classname: Optional class name (string, optional).

    Returns:
      A dictionary.
    """
    if attributes and isinstance(attributes, six.string_types):
      return {
          'class': attributes
      }
    if not attributes:
      attributes = {}
    if not classname:
      classname = DEFAULT_CLASS_NAME
    attributes.setdefault('class', classname)
    return attributes

  def _get_cache_key(self, source, classname):
    """Returns a cache key for the given source and class name."""
    key_source = u'%s:%s:%s' % (CACHE_SALT, source, classname)
    return hashlib.md5(key_source.encode('utf8')).hexdigest()

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
    return response.get('tokens', [])

  def _preprocess(self, source):
    """Removes unnecessary break lines and whitespaces.

    Args:
      source: HTML code to be processed (unicode).

    Returns:
      Preprocessed HTML code (unicode).
    """
    source = source.replace(u'\n', u'').strip()
    source = re.sub(r'<br\s*\/?\s*>', u' ', source, re.I)
    source = re.sub(r'\s\s+', u' ', source)
    return source

  def _get_source_chunks(self, input_text, language=''):
    """Returns the words chunks.

    Args:
      input_text: An input text to annotate (unicode).
      language: A language used to parse text (string).

    Returns:
      A list of word chunk objects (list).
    """
    chunks = []
    sentence_length = 0
    tokens = self._get_annotations(input_text, language)
    for token in tokens:
      word = token['text']['content']
      begin_offset = token['text']['beginOffset']
      label = token['dependencyEdge']['label']
      pos = token['partOfSpeech']['tag']
      if begin_offset > sentence_length:
        chunks.append(Chunk(u' ', SPACE_POS, SPACE_POS, True))
        sentence_length = begin_offset
      chunks.append(Chunk(
          word, pos, label,
          tokens.index(token) < token['dependencyEdge']['headTokenIndex']))
      sentence_length += len(word)
    return chunks

  def _migrate_html(self, chunks, dom):
    """Migrates HTML elements to the word chunks by bracketing each element.

    Args:
      chunks: The list of word chunks to be processed.
      dom: DOM to access the given HTML source.

    Returns:
      A list of processed word chunks.
    """
    elements = self._get_elements_list(dom)
    for element in elements:
      result = []
      index = 0
      concat_chunks = []
      for chunk in chunks:
        if (index + len(chunk.word) <= element.index or
            element.index + len(element.text) <= index):
          result.append(chunk)
        elif (index <= element.index and
              element.index + len(element.text) <= index + len(chunk.word)):
          result.append(Chunk(
              chunk.word.replace(element.text, element.source),
              HTML_POS, HTML_POS, True))
        elif (index < element.index + len(element.text) and
              element.index + len(element.text) <= index + len(chunk.word)):
          concat_chunks.append(chunk)
          new_word = u''.join([c_chunk.word for c_chunk in concat_chunks])
          new_word = new_word.replace(element.text, element.source)
          result.append(Chunk(new_word, HTML_POS, HTML_POS, True))
          concat_chunks = []
        else:
          concat_chunks.append(chunk)
        index += len(chunk.word)
      chunks = result
    return chunks

  def _get_elements_list(self, dom):
    """Digs DOM to the first depth and returns the list of elements.

    Args:
      dom: DOM to access the given HTML source.

    Returns:
      A list of elements.
    """
    result = []
    index = 0
    if dom.text:
      index += len(dom.text)
    for element in dom:
      text = etree.tostring(
          element, with_tail=False, method='text',
          encoding='utf8').decode('utf8')
      source = etree.tostring(
          element, with_tail=False, encoding='utf8').decode('utf8')
      result.append(Element(text, element.tag, source, index))
      index += len(text)
      if element.tail: index += len(element.tail)
    return result

  def _spanize(self, chunks, attributes):
    """Returns concatenated HTML code with SPAN tag.

    Args:
      chunks: The list of word chunks.
      attributes: If a dictionary, then a map of name-value pairs for attributes
      of output SPAN tags. If a string, then this is the class name of output
      SPAN tags. If an array, the elements will be joined together as the
      class name of SPAN tags.

    Returns:
      The organized HTML code.
    """
    result = []
    for chunk in chunks:
      if chunk.pos == SPACE_POS:
        result.append(chunk.word)
      else:
        attribute_str = ' '.join(
            '%s="%s"' % (k, v) for k, v in sorted(attributes.items()))
        result.append('<span %s>%s</span>' % (attribute_str, chunk.word))
    return ''.join(result)

  def _concatenate_punctuations(self, chunks):
    """Concatenates chunks backword if they are punctuation marks.

    Args:
      chunks: The list of word chunks.

    Returns:
      The processed word chunks.
    """
    result = []
    tmp_bucket = []
    chunks = chunks[::-1]
    for chunk in chunks:
      if chunk.pos == u'PUNCT':
        tmp_bucket.append(chunk)
        continue
      if tmp_bucket:
        tmp_bucket.append(chunk)
        new_word = ''.join([tmp_chunk.word for tmp_chunk in tmp_bucket[::-1]])
        result.append(Chunk(new_word, chunk.pos, chunk.label, chunk.forward))
        tmp_bucket = []
      else:
        result.append(chunk)
    if tmp_bucket: result += tmp_bucket
    result = result[::-1]
    return result

  def _concatenate_by_label(self, chunks, forward=True):
    """Concatenates chunks based on the label and direction.

    Args:
      chunks: The list of word chunks.
      forward: Concatenation direction.

    Returns:
      The processed word chunks.
    """
    result = []
    tmp_bucket = []
    if not forward: chunks = chunks[::-1]
    for chunk in chunks:
      if ((chunk.label in TARGET_LABEL and chunk.forward == forward) or
          (tmp_bucket and chunk.label == SPACE_POS)):
        tmp_bucket.append(chunk)
        continue
      tmp_bucket.append(chunk)
      if not forward: tmp_bucket = tmp_bucket[::-1]
      new_word = ''.join([tmp_chunk.word for tmp_chunk in tmp_bucket])
      result.append(Chunk(new_word, chunk.pos, chunk.label, chunk.forward))
      tmp_bucket = []
    if tmp_bucket: result += tmp_bucket
    if not forward: result = result[::-1]
    return result
