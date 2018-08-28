# -*- coding: utf-8 -*-
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Natural Language API based Segmenter.

Word segmenter module powered by
`Cloud Natural Language API <https://cloud.google.com/natural-language/>`_.
You need to enable the API in your Google Cloud Platform project before you
use this module.

Example:
  Once you enabled the API, download a service account's credentials and set
  as `GOOGLE_APPLICATION_CREDENTIALS` environment variable.

  .. code-block:: bash

     $ export GOOGLE_APPLICATION_CREDENTIALS='/path/to/credentials.json'

  Alternatively, you can also pass the path to your credentials file to the
  module.

  .. code-block:: python

     segmenter = budou.segmenter.NLAPISegmenter(
         credentials_path='/path/to/credentials.json')

This module is equipped with caching system not to make multiple requests for
the same source sentence because making request to the API may incur costs.
The caching system is provided by `budou.cachefactory`, and a proper caching
system is chosen to be used based on the environment.

"""

from __future__ import unicode_literals
from builtins import str
import logging
import hashlib
from .segmenter import Segmenter
from .cachefactory import load_cache
from .chunk import Chunk, ChunkList

_DEPENDENT_LABEL = (
    'P', 'SNUM', 'PRT', 'AUX', 'SUFF', 'AUXPASS', 'RDROP', 'NUMBER', 'NUM',
    'PREF')
""" list of str: Labels dependent to other parts.
"""


def _memorize(func):
  """Decorator to cache the given function's output.
  """

  def _wrapper(self, *args, **kwargs):
    """Wrapper to cache the function's output.
    """
    if self.use_cache:
      cache = load_cache(self.cache_filename)
      original_key = ':'.join([
          self.__class__.__name__,
          func.__name__,
          '_'.join([str(a) for a in args]),
          '_'.join([str(w) for w in kwargs.values()])])
      cache_key = hashlib.md5(original_key.encode('utf-8')).hexdigest()
      cached_val = cache.get(cache_key)
      if cached_val:
        return cached_val
    val = func(self, *args, **kwargs)
    if self.use_cache:
      cache.set(cache_key, val)
    return val
  return _wrapper


class NLAPISegmenter(Segmenter):
  """Natural Language API Segmenter.

  Attributes:
    service: A resource object for interacting with Cloud Natural Language API.
    cache_filename (str): File path to the cache file.
    supported_languages (list of str): List of supported languages' codes.

  Args:
      cache_filename (:obj:`str`, optional): File path to the pickle file for
          caching. The file is created automatically if not exist. If the
          environment is Google App Engine Standard Environment and memcache
          service is available, it is used for caching and the pickle file
          won't be generated.
      credentials_path (:obj:`str`, optional): File path to the service
          account's credentials file. If no file path is specified, it tries
          to authenticate with default credentials.
      use_entity (:obj:`bool`, optional): Whether to use entity analysis
          results to wrap entity names in the output.
      use_cache (:obj:`bool`, optional): Whether to use a cache system.
  """

  supported_languages = {'ja', 'ko', 'zh', 'zh-TW', 'zh-CN', 'zh-HK'}

  def __init__(self, cache_filename, credentials_path, use_entity, use_cache):

    self.cache_filename = cache_filename
    self.credentials_path = credentials_path
    self.use_entity = use_entity
    self.use_cache = use_cache
    self._authenticate()

  def _authenticate(self):

    import google_auth_httplib2
    import googleapiclient.discovery

    scope = ['https://www.googleapis.com/auth/cloud-platform']
    if self.credentials_path:
      try:
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path)
        scoped_credentials = credentials.with_scopes(scope)
      except ImportError:
        logging.error('Failed to load google.oauth2.service_account module. '
                      'If you are running this script in Google App Engine '
                      'environment, you can initialize the segmenter with '
                      'default credentials.')

    else:
      import google.auth
      scoped_credentials, _ = google.auth.default(scope)
    authed_http = google_auth_httplib2.AuthorizedHttp(scoped_credentials)
    service = googleapiclient.discovery.build(
        'language', 'v1beta2', http=authed_http)
    self.service = service

  def segment(self, source, language=None):
    """Returns a chunk list from the given sentence.

    Args:
      source (str): Source string to segment.
      language (:obj:`str`, optional): A language code.

    Returns:
      A chunk list. (:obj:`budou.chunk.ChunkList`)

    Raises:
      ValueError: If :obj:`language` is given and it is not included in
                  :obj:`supported_languages`.
    """
    if language and not language in self.supported_languages:
      raise ValueError(
          'Language {} is not supported by NLAPI segmenter'.format(language))

    chunks, language = self._get_source_chunks(source, language=language)
    if self.use_entity:
      entities = self._get_entities(source, language=language)
      chunks = self._group_chunks_by_entities(chunks, entities)
    chunks.resolve_dependencies()
    return chunks

  def _get_source_chunks(self, input_text, language=None):
    """Returns a chunk list retrieved from Syntax Analysis results.

    Args:
      input_text (str): Text to annotate.
      language (:obj:`str`, optional): Language of the text.

    Returns:
      A chunk list. (:obj:`budou.chunk.ChunkList`)
    """
    chunks = ChunkList()
    seek = 0
    result = self._get_annotations(input_text, language=language)
    tokens = result['tokens']
    language = result['language']
    for i, token in enumerate(tokens):
      word = token['text']['content']
      begin_offset = token['text']['beginOffset']
      label = token['dependencyEdge']['label']
      pos = token['partOfSpeech']['tag']
      if begin_offset > seek:
        chunks.append(Chunk.space())
        seek = begin_offset
      chunk = Chunk(word, pos, label)
      if chunk.label in _DEPENDENT_LABEL:
        # Determining concatenating direction based on syntax dependency.
        chunk.dependency = i < token['dependencyEdge']['headTokenIndex']
      if chunk.is_punct():
        chunk.dependency = chunk.is_open_punct()
      chunks.append(chunk)
      seek += len(word)
    return chunks, language

  def _group_chunks_by_entities(self, chunks, entities):
    """Groups chunks by entities retrieved from NL API Entity Analysis.

    Args:
      chunks (:obj:`budou.chunk.ChunkList`): List of chunks to be processed.
      entities (:obj:`list` of :obj:`dict`): List of entities.

    Returns:
      A chunk list. (:obj:`budou.chunk.ChunkList`)
    """
    for entity in entities:
      chunks_to_concat = chunks.get_overlaps(
          entity['beginOffset'], len(entity['content']))
      if not chunks_to_concat:
        continue
      new_chunk_word = u''.join([chunk.word for chunk in chunks_to_concat])
      new_chunk = Chunk(new_chunk_word)
      chunks.swap(chunks_to_concat, new_chunk)
    return chunks

  @_memorize
  def _get_annotations(self, text, language=''):
    """Returns the list of annotations retrieved from the given text.

    Args:
      text (str): Input text.
      language (:obj:`str`, optional): Language code.

    Returns:
      Results in a dictionary. :code:`tokens` contains the list of annotations
      and :code:`language` contains the inferred language from the input.
    """
    body = {
        'document': {
            'type': 'PLAIN_TEXT',
            'content': text,
        },
        'features': {
            'extract_syntax': True,
        },
        'encodingType': 'UTF32',
    }
    if language:
      body['document']['language'] = language

    request = self.service.documents().annotateText(body=body)
    response = request.execute()
    tokens = response.get('tokens', [])
    language = response.get('language')

    return {'tokens': tokens, 'language': language}

  @_memorize
  def _get_entities(self, text, language=''):
    """Returns the list of entities retrieved from the given text.

    Args:
      text (str): Input text.
      language (:obj:`str`, optional): Language code.

    Returns:
      List of entities.
    """
    body = {
        'document': {
            'type': 'PLAIN_TEXT',
            'content': text,
        },
        'encodingType': 'UTF32',
    }
    if language:
      body['document']['language'] = language

    request = self.service.documents().analyzeEntities(body=body)
    response = request.execute()
    result = []
    for entity in response.get('entities', []):
      mentions = entity.get('mentions', [])
      if not mentions:
        continue
      entity_text = mentions[0]['text']
      offset = entity_text['beginOffset']
      for word in entity_text['content'].split():
        result.append({'content': word, 'beginOffset': offset})
        offset += len(word)
    return result
