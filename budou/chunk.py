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

"""Chunk module as a unit of word segment with helpers.
"""

import collections
from xml.etree import ElementTree as ET
import unicodedata
import html5lib

class Chunk:
  """A unit for word segmentation.

  Attributes:
    word (str): Surface word of the chunk.
    pos (:obj:`str`, optional): Part of speech.
    label (:obj:`str`, optional): Label information.
    dependency (:obj:`bool`, optional): Dependency to neighbor words.
        :code:`None` for no dependency, :code:`True` for dependency to the
        following word, and :code:`False` for the dependency to the previous
        word.

  Args:
    word (str): Surface word of the chunk.
    pos (:obj:`str`, optional): Part of speech.
    label (:obj:`str`, optional): Label information.
    dependency (:obj:`bool`, optional): Dependency to neighbor words.
        :code:`None` for no dependency, :code:`True` for dependency to the
        following word, and :code:`False` for the dependency to the previous
        word.
  """
  _SPACE_POS = 'SPACE'
  _BREAK_POS = 'BREAK'

  def __init__(self, word, pos=None, label=None, dependency=None):
    self.word = word
    self.pos = pos
    self.label = label
    self.dependency = dependency

  def __repr__(self):
    return 'Chunk(%s, %s, %s, %s)' % (
        repr(self.word), self.pos, self.label, self.dependency)

  @classmethod
  def space(cls):
    """Creates space Chunk.

    Returns:
      A chunk (:obj:`budou.chunk.Chunk`)
    """
    chunk = cls(u' ', cls._SPACE_POS)
    return chunk

  @classmethod
  def breakline(cls):
    """Creates breakline Chunk.

    Returns:
      A chunk (:obj:`budou.chunk.Chunk`)
    """
    chunk = cls(u'\n', cls._BREAK_POS)
    return chunk

  def serialize(self):
    """Returns serialized chunk data in dictionary."""
    return {
        'word': self.word,
        'pos': self.pos,
        'label': self.label,
        'dependency': self.dependency,
        'has_cjk': self.has_cjk(),
    }

  def is_space(self):
    """Whether the chunk is a space.

    Returns:
      bool: True if it is a space.
    """
    return self.pos == self._SPACE_POS

  def is_punct(self):
    """Whether the chunk is a punctuation mark.

    See also https://en.wikipedia.org/wiki/Unicode_character_property

    Returns:
      bool: True if it is a punctuation mark.
    """
    return len(self.word) == 1 and unicodedata.category(self.word)[0] == 'P'

  def is_open_punct(self):
    """Whether the chunk is an open punctuation mark.

    Ps: Punctuation, open (e.g. opening bracket characters)
    Pi: Punctuation, initial quote (e.g. opening quotation mark)
    See also https://en.wikipedia.org/wiki/Unicode_character_property

    Returns:
      bool: True if it is an open punctuation mark.
    """
    return self.is_punct() and unicodedata.category(self.word) in {'Ps', 'Pi'}

  def has_cjk(self):
    """Checks if the word of the chunk contains CJK characters.

    This is using unicode codepoint ranges from
    https://github.com/nltk/nltk/blob/develop/nltk/tokenize/util.py#L149

    Returns:
      bool: True if the chunk has any CJK character.
    """
    cjk_codepoint_ranges = [
        (4352, 4607), (11904, 42191), (43072, 43135), (44032, 55215),
        (63744, 64255), (65072, 65103), (65381, 65500), (131072, 196607)]
    for char in self.word:
      if any([start <= ord(char) <= end
              for start, end in cjk_codepoint_ranges]):
        return True
    return False


class ChunkList(collections.MutableSequence):
  """List of :obj:`budou.chunk.Chunk` with some helpers.

  This list accepts only instances of :obj:`budou.chunk.Chunk`.

  Example:
    .. code-block:: python

       from budou.chunk import Chunk, ChunkList
       chunks = ChunkList(Chunk('abc'), Chunk('def'))
       chunks.append(Chunk('ghi'))  # OK
       chunks.append('jkl')         # NG

  Args:
    args (list of :obj:`budou.chunk.Chunk`): Initial values included in the
        list.
  """

  def __init__(self, *args):
    self.list = list()
    self.extend(list(args))

  def _check(self, val):
    """Checks if the value is an instance of :obj:`budou.chunk.Chunk`.

    Args:
      val (:obj:`budou.chunk.Chunk`): input to check

    Raises:
      TypeError: If :code:`val` is not an instance of :obj:`budou.chunk.Chunk`.
    """
    if not isinstance(val, Chunk):
      raise TypeError

  def __len__(self):
    return len(self.list)

  def __getitem__(self, i):
    return self.list[i]

  def __delitem__(self, i):
    del self.list[i]

  def __setitem__(self, i, v):
    self._check(v)
    self.list[i] = v

  def insert(self, index, value):
    self._check(value)
    self.list.insert(index, value)

  def get_overlaps(self, offset, length):
    """Returns chunks overlapped with the given range.

    Args:
      offset (int): Begin offset of the range.
      length (int): Length of the range.

    Returns:
      Overlapped chunks. (:obj:`budou.chunk.ChunkList`)
    """
    # In case entity's offset points to a space just before the entity.
    if ''.join([chunk.word for chunk in self])[offset] == ' ':
      offset += 1
    index = 0
    result = ChunkList()
    for chunk in self:
      if offset < index + len(chunk.word) and index < offset + length:
        result.append(chunk)
      index += len(chunk.word)
    return result

  def swap(self, old_chunks, new_chunk):
    """Swaps old consecutive chunks with new chunk.

    Args:
      old_chunks (:obj:`budou.chunk.ChunkList`): List of consecutive Chunks to
          be removed.
      new_chunk (:obj:`budou.chunk.Chunk`): A Chunk to be inserted.
    """
    indexes = [self.index(chunk) for chunk in old_chunks]
    del self[indexes[0]:indexes[-1] + 1]
    self.insert(indexes[0], new_chunk)

  def resolve_dependencies(self):
    """Resolves chunk dependency by concatenating them.
    """
    self._concatenate_inner(True)
    self._concatenate_inner(False)
    self._insert_breaklines()

  def _concatenate_inner(self, direction):
    """Concatenates chunks based on each chunk's dependency.

    Args:
      direction (bool): Direction of concatenation process. True for forward.
    """
    tmp_bucket = []
    source_chunks = self if direction else self[::-1]
    target_chunks = ChunkList()
    for chunk in source_chunks:
      if (
          # if the chunk has matched dependency, do concatenation.
          chunk.dependency == direction or
          # if the chunk is SPACE, concatenate to the previous chunk.
          (direction is False and chunk.is_space())
          ):
        tmp_bucket.append(chunk)
        continue
      tmp_bucket.append(chunk)
      if not direction:
        tmp_bucket = tmp_bucket[::-1]
      new_word = ''.join([tmp_chunk.word for tmp_chunk in tmp_bucket])
      new_chunk = Chunk(new_word, pos=chunk.pos, label=chunk.label,
                        dependency=chunk.dependency)
      target_chunks.append(new_chunk)
      tmp_bucket = ChunkList()
    if tmp_bucket:
      target_chunks += tmp_bucket
    if not direction:
      target_chunks = target_chunks[::-1]
    self.list = target_chunks

  def _insert_breaklines(self):
    """Inserts a breakline instead of a trailing space if the chunk is in CJK.
    """
    target_chunks = ChunkList()
    for chunk in self:
      if chunk.word[-1] == ' ' and chunk.has_cjk():
        chunk.word = chunk.word[:-1]
        target_chunks.append(chunk)
        target_chunks.append(chunk.breakline())
      else:
        target_chunks.append(chunk)
    self.list = target_chunks

  def html_serialize(self, attributes, max_length=None):
    """Returns concatenated HTML code with SPAN tag.

    Args:
      attributes (dict): A map of name-value pairs for attributes of output
          SPAN tags.
      max_length (:obj:`int`, optional): Maximum length of span enclosed chunk.

    Returns:
      The organized HTML code. (str)
    """
    doc = ET.Element('span')
    for chunk in self:
      if (chunk.has_cjk() and
          not (max_length and len(chunk.word) > max_length)):
        ele = ET.Element('span')
        ele.text = chunk.word
        for key, val in attributes.items():
          ele.attrib[key] = val
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
        quote_attr_values='always')
    return result
