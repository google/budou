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
"""Segmenter module.
"""

from abc import ABCMeta, abstractmethod
import six

@six.add_metaclass(ABCMeta)
class Segmenter:
  """Base class for Segmenter modules.
  """

  @abstractmethod
  def segment(self, source, language=None):
    """Returns a chunk list from the given sentence.

    Args:
      source (str): Source string to segment.
      language (:obj:`str`, optional): A language code.

    Returns:
      A chunk list. (:obj:`budou.chunk.ChunkList`)

    Raises:
      NotImplementedError: If not implemented.
    """
    raise NotImplementedError()
