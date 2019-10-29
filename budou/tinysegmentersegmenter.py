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

"""TinySegmenter based Segmenter.

Word segmenter module powered by TinySegmenter, a compact Japanese tokenizer
originally developed by Taku Kudo. This is built on its Python port
(https://pypi.org/project/tinysegmenter3/) developed by Tatsuro Yasukawa.
"""

import logging
import sys
import six
import tinysegmenter
from .segmenter import Segmenter
from .chunk import Chunk, ChunkList

_PARTICLES = {u'か', u'かしら', u'から', u'が', u'くらい', u'けれども', u'こそ',
    u'さ', u'さえ', u'しか', u'だけ', u'だに', u'だの', u'て', u'で', u'でも',
    u'と', u'ところが', u'とも', u'な', u'など', u'なり', u'に', u'ね', u'の',
    u'ので', u'のに', u'は', u'ば', u'ばかり', u'へ', u'ほど', u'まで', u'も',
    u'や', u'やら', u'よ', u'より', u'わ', u'を'}
"""set of str: Common particles in Japanese.
Refer to https://en.wikipedia.org/wiki/Japanese_particles
"""

_AUX_VERBS = {u'です', u'でしょ', u'でし', u'ます', u'ませ', u'まし'}
""" set of str: Popylar auxiliary verbs in Japanese.
"""

def is_hiragana(word):
  """Checks is the word is a Japanese hiragana.

  This is using the unicode codepoint range for hiragana.
  https://en.wikipedia.org/wiki/Hiragana_(Unicode_block)

  Args:
    word (str): A word.

  Returns:
    bool: True if the word is a hiragana.
  """
  return len(word) == 1 and 12353 <= ord(word) <= 12447


class TinysegmenterSegmenter(Segmenter):
  """TinySegmenter based Segmenter.

  Attributes:
    supported_languages (list of str): List of supported languages' codes.
  """

  supported_languages = {'ja'}

  def segment(self, source, language=None):
    """Returns a chunk list from the given sentence.

    Args:
      source (str): Source string to segment.
      language (str, optional): A language code.

    Returns:
      A chunk list. (:obj:`budou.chunk.ChunkList`)

    Raises:
      ValueError: If :code:`language` is given and it is not included in
                  :code:`supported_languages`.
    """
    if language and not language in self.supported_languages:
      raise ValueError(
          'Language {} is not supported by NLAPI segmenter'.format(language))

    chunks = ChunkList()
    results = tinysegmenter.tokenize(source)
    seek = 0
    for word in results:
      word = word.strip()
      if not word:
        continue
      if source[seek: seek + len(word)] != word:
        assert source[seek] == ' '
        assert source[seek + 1: seek + len(word) + 1] == word
        chunks.append(Chunk.space())
        seek += 1

      dependency = None
      if word in _PARTICLES or word in _AUX_VERBS or is_hiragana(word):
        dependency = False

      chunk = Chunk(word, dependency=dependency)
      if chunk.is_punct():
        chunk.dependency = chunk.is_open_punct()
      chunks.append(chunk)
      seek += len(word)
    chunks.resolve_dependencies()
    return chunks
