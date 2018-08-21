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

from .context import budou
import unittest
from budou.chunk import Chunk, ChunkList

class TestChunk(unittest.TestCase):

  def test_has_cjk(self):
    result = Chunk('Hello').has_cjk()
    self.assertFalse(result,
        'should be false when no CJK character is included.')

    result = Chunk(u'AとB').has_cjk()
    self.assertTrue(result,
        'should be true when any CJK character is included.')

  def test_is_punt(self):
    puncts = [
        u'。', u'、', u'「', u'」', u'（', u'）', u'[', u']', u'(', u')']
    expected = [True for _ in puncts]
    results = [Chunk(c).is_punct() for c in puncts]
    self.assertListEqual(expected, results,
        'Punctuation marks should be detected.')

  def test_is_open_punct(self):
    puncts = [
        u'。', u'、', u'「', u'」', u'（', u'）', u'[', u']', u'(', u')']
    expected = [
        False, False, True, False, True, False, True, False, True, False]
    results = [Chunk(c).is_open_punct() for c in puncts]
    self.assertListEqual(expected, results,
        'Open punctuation marks should be detected.')


class TestChunkList(unittest.TestCase):

  def setUp(self):
    self.chunks = ChunkList(Chunk('ab', dependency=None),
        Chunk('cde', dependency=True), Chunk('fgh', dependency=False))

  def test_get_overlaps(self):
    # chunks: ab cde fgh
    # range : __ _*_ ___
    chunks = self.chunks.get_overlaps(3, 1)
    expected = ['cde']
    self.assertEqual(expected, [chunk.word for chunk in chunks])

    # chunks: ab cde fgh
    # range : __ **_ ___
    chunks = self.chunks.get_overlaps(2, 2)
    expected = ['cde']
    self.assertEqual(expected, [chunk.word for chunk in chunks])

    # chunks: ab cde fgh
    # range : _* **_ ___
    chunks = self.chunks.get_overlaps(1, 3)
    expected = ['ab', 'cde']
    self.assertEqual(expected, [chunk.word for chunk in chunks])

    # chunks: ab cde fgh
    # range : _* *** ___
    chunks = self.chunks.get_overlaps(1, 4)
    expected = ['ab', 'cde']
    self.assertEqual(expected, [chunk.word for chunk in chunks])

    # chunks: ab cde fgh
    # range : _* *** *__
    chunks = self.chunks.get_overlaps(1, 5)
    expected = ['ab', 'cde', 'fgh']
    self.assertEqual(expected, [chunk.word for chunk in chunks])

  def test_swap(self):
    old_chunks = self.chunks[0:2]
    new_chunk = Chunk('ijk')
    self.chunks.swap(old_chunks, new_chunk)
    expected = ['ijk', 'fgh']
    self.assertEqual(
        expected, [chunk.word for chunk in self.chunks],
        'Old chunks should be replaced with the new chunk.')

  def test_concatenate_inner(self):
    self.chunks._concatenate_inner(True)
    self.assertEqual(
        ['ab', 'cdefgh'], [chunk.word for chunk in self.chunks],
        'Chunks should be concatenated if they depends on the following word.')
    self.assertEqual(
        [None, False], [chunk.dependency for chunk in self.chunks],
        'Dependency should persist even if it\'s concatenated by others.')

    self.chunks._concatenate_inner(False)
    self.assertEqual(
        ['abcdefgh'], [chunk.word for chunk in self.chunks],
        'Chunks should be concatenated if they depends on the previous word.')

  def test_insert_breaklines(self):
    chunks = ChunkList(Chunk(u'これが '), Chunk('Android'))
    chunks._insert_breaklines()
    self.assertEqual(
        [u'これが', '\n', 'Android'], [chunk.word for chunk in chunks],
        'Trailing spaces in CJK chunk should be converted to breaklines.')

  def test_html_serialize(self):
    chunks = ChunkList(Chunk('Hello'), Chunk.space(), Chunk(u'今天'),
        Chunk(u'天气'), Chunk(u'很好'))
    attributes = {
        'class': 'foo'
        }
    expected = (
        '<span>'
        'Hello '
        u'<span class="foo">今天</span>'
        u'<span class="foo">天气</span>'
        u'<span class="foo">很好</span>'
        '</span>')
    result = chunks.html_serialize(attributes, None)
    self.assertEqual(
        result, expected,
        'The chunks should be compiled to a HTML code.')

    chunks = ChunkList(Chunk('Hey<'), Chunk('<script>alert(1)</script>'),
      Chunk('>guys'))
    attributes = {
        'class': 'foo'
        }
    expected = ('<span>'
        'Hey&lt;&lt;script&gt;alert(1)&lt;/script&gt;&gt;guys'
        '</span>')
    result = chunks.html_serialize(attributes, None)
    self.assertEqual(
        result, expected, 'HTML tags included in a chunk should be encoded.')

    chunks = ChunkList(Chunk(u'去年'), Chunk(u'インフルエンザに'),
      Chunk(u'かかった。'))
    attributes = {
        'class': 'foo'
        }
    expected = (
        '<span>'
        u'<span class="foo">去年</span>'
        u'インフルエンザに'
        u'<span class="foo">かかった。</span>'
        '</span>')
    result = chunks.html_serialize(attributes, 6)
    self.assertEqual(
        result, expected,
        'Chunks that exceed the max length should not be enclosed by a span.')

  # TODO (tushuhei) Check if TypeError is raised when any instance but Chunk
  # is given to the list.

if __name__ == '__main__':
  unittest.main()
