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

"""MeCab based Segmenter.

Word segmenter module powered by `MeCab <https://github.com/taku910/mecab>`_.
You need to install MeCab to use this segmenter.
The easiest way to install MeCab is to run :code:`make install-mecab`. The
script will download source codes from GitHub and build the tool. It also setup
`IPAdic <https://ja.osdn.net/projects/ipadic/>`_, a standard dictionary for
Japanese.
"""

import logging
import sys
import six
from .segmenter import Segmenter
from .chunk import Chunk, ChunkList

_DEPENDENT_POS_FORWARD = set()
_DEPENDENT_POS_BACKWARD = {u'助詞', u'助動詞'}
_DEPENDENT_LABEL_FORWARD = set()
_DEPENDENT_LABEL_BACKWARD = {u'非自立'}

class MecabSegmenter(Segmenter):
  """Mecab Segmenter.

  Attributes:
    tagger (MeCab.Tagger): MeCab Tagger to parse the input sentence.
    supported_languages (list of str): List of supported languages' codes.
  """

  supported_languages = {'ja'}

  def __init__(self):
    try:
      import MeCab
      self.tagger = MeCab.Tagger('-Ochasen')
    except ImportError:
      logging.error(
          ('mecab-python3 is not installed. Install the module by running '
           '`$ pip install mecab-python3`. If MeCab is not installed in your '
           'system yet, run `$ make install-mecab` instead.'))
      sys.exit(1)

  def segment(self, source, language=None):
    """Returns a chunk list from the given sentence.

    Args:
      input_text (str): Source string to segment.
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

    chunks = ChunkList()
    seek = 0
    source_str = source.encode('utf-8') if six.PY2 else source
    results = self.tagger.parse(source_str).split('\n')[:-2]
    for row in results:
      if six.PY2:
        row = row.decode('utf-8')
      token = row.split('\t')
      word = token[0]
      labels = token[3].split('-')
      pos = labels[0]
      label = labels[1] if len(labels) > 1 else None
      if source[seek: seek + len(word)] != word:
        assert source[seek] == ' '
        assert source[seek + 1: seek + len(word) + 1] == word
        chunks.append(Chunk.space())
        seek += 1

      dependency = None
      if pos in _DEPENDENT_POS_FORWARD:
        dependency = True
      elif pos in _DEPENDENT_POS_BACKWARD:
        dependency = False
      elif label in _DEPENDENT_LABEL_FORWARD:
        dependency = True
      elif label in _DEPENDENT_LABEL_BACKWARD:
        dependency = False

      chunk = Chunk(word, pos=pos, label=label, dependency=dependency)
      if chunk.is_punct():
        chunk.dependency = chunk.is_open_punct()
      chunks.append(chunk)
      seek += len(word)
    chunks.resolve_dependencies()
    return chunks
