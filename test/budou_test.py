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

from mock import MagicMock
import budou
import json
import os
import unittest


class TestChunkMethods(unittest.TestCase):

  def test_maybe_add_dependency(self):
    chunk = budou.Chunk('foo', label=None)
    chunk.maybe_add_dependency(True)
    self.assertEqual(
        None, chunk.dependency,
        'Dependency should not be added if the chunk does not belong to'
        'dependent labels.')

    chunk = budou.Chunk('foo', label=budou.Chunk.DEPENDENT_LABEL[0])
    chunk.maybe_add_dependency(True)
    self.assertEqual(
        True, chunk.dependency,
        'Dependency should be added if the chunk belongs to dependent labels.')

    chunk = budou.Chunk('foo', label=budou.Chunk.DEPENDENT_LABEL[0])
    chunk.dependency = False
    chunk.maybe_add_dependency(True)
    self.assertEqual(
        False, chunk.dependency,
        'Dependency should not be added if the chunk has dependency already.')

  def test_add_dependency_if_punct(self):
    test_characters = [
        u'。', u'、', u'「', u'」', u'（', u'）', u'[', u']', u'(', u')']
    expected_dependency = [
        False, False, True, False, True, False, True, False, True, False]
    for i, character in enumerate(test_characters):
      # _add_dependency_if_punct is called in __init__ implicitly.
      chunk = budou.Chunk(character, pos='PUNCT')
      self.assertEqual(
          expected_dependency[i], chunk.dependency,
          'Punctuation marks should be assigned with proper dependencies.')


class TestChunkListMethods(unittest.TestCase):
  def setUp(self):
    chunks = budou.ChunkList()
    chunks.append(budou.Chunk('ab', dependency=None))
    chunks.append(budou.Chunk('cde', dependency=True))
    chunks.append(budou.Chunk('fgh', dependency=False))
    self.chunks = chunks

  def tearDown(self):
    self.chunks = None

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
    new_chunk = budou.Chunk('ijk')
    self.chunks.swap(old_chunks, new_chunk)
    expected = ['ijk', 'fgh']
    self.assertEqual(
        expected, [chunk.word for chunk in self.chunks],
        'Old chunks should be replaced with the new chunk.')


class TestBudouMethods(unittest.TestCase):

  def setUp(self):
    self.parser = budou.Budou(None)
    cases_path = os.path.join(os.path.dirname(__file__), 'cases.ndjson')
    with open(cases_path) as f:
      self.cases = [json.loads(row) for row in f.readlines() if row]

  def tearDown(self):
    self.parser = None

  def test_parse(self):
    for case in self.cases:
      # Mocks external API request.
      budou.api.get_annotations = MagicMock(return_value=case['tokens'])
      budou.api.get_entities = MagicMock(return_value=case['entities'])
      source = case['sentence']
      result = self.parser.parse(
          source, language=case['language'], use_cache=False, use_entity=False)
      expected = case['expected']
      self.assertEqual(expected, [chunk['word'] for chunk in result['chunks']])

      result = self.parser.parse(
          source, language=case['language'], use_cache=False, use_entity=True)
      expected = case['expected_with_entity']
      self.assertEqual(expected, [chunk['word'] for chunk in result['chunks']])

  def test_get_chunks_per_space(self):
    source = 'a b'
    expected = ['a', ' ', 'b']
    chunks = self.parser._get_chunks_per_space(source)
    self.assertEqual(
        expected, [chunk.word for chunk in chunks],
        'Input text should be parsed into chunks separated by spaces.')

  def test_get_attribute_dict(self):
    result = self.parser._get_attribute_dict({})
    self.assertEqual(
        result, {'class': self.parser.DEFAULT_CLASS_NAME},
        'When attributes is none and classname is not provided, the output '
        'should have the default class name in it.')

    result = self.parser._get_attribute_dict('foo')
    self.assertEqual(
        result, {'class': 'foo'},
        'When attributes is a string and classname is not provided, the output '
        'should have the specified class name in it.')

    result = self.parser._get_attribute_dict({'bizz': 'buzz'})
    self.assertEqual(
        result, {
            'bizz': 'buzz',
            'class': self.parser.DEFAULT_CLASS_NAME,
        }, 'When attributes is a dictionary but class property is not '
        'included, the output should have the default class name in it.')

    result = self.parser._get_attribute_dict({'bizz': 'buzz', 'class': 'foo'})
    self.assertEqual(
        result, {
            'bizz': 'buzz',
            'class': 'foo',
        }, 'When attribute is a dictionary and class property is included, '
        'the output should have the specified class name in it.')

    result = self.parser._get_attribute_dict({}, 'foo')
    self.assertEqual(
        result, {'class': 'foo'},
        'When attributes is none and classname is provided, the output should '
        'have classname as the class name.')

    result = self.parser._get_attribute_dict('bar', 'foo')
    self.assertEqual(
        result, {'class': 'bar'},
        'When attributes is a string and classname is provided, the output '
        'should use the class property in attributes over classname.')

    result = self.parser._get_attribute_dict({'bizz': 'buzz'}, 'foo')
    self.assertEqual(
        result, {
            'bizz': 'buzz',
            'class': 'foo',
        }, 'When attributes is a dictionary without class property and '
        'classname is provided, the output should have classname as the class '
        'name.')

    result = self.parser._get_attribute_dict(
        {'bizz': 'buzz', 'class': 'bar'}, 'foo')
    self.assertEqual(
        result, {
            'bizz': 'buzz',
            'class': 'bar',
        }, 'When attributes is a dictionary with class property and classname '
        'is provided, the output should use the class property in attributes '
        'over classname.')

  def test_preprocess(self):
    source = u' a\nb<br> c   d'
    expected = u'ab c d'
    result = self.parser._preprocess(source)
    self.assertEqual(
        expected, result,
        'BR tags, line breaks, and unnecessary spaces should be removed.')

  def test_get_source_chunks(self):
    budou.api.get_annotations = MagicMock(return_value=[{
        'dependencyEdge': {'headTokenIndex': 1, 'label': 'NN'},
        'partOfSpeech': {'tag': 'NOUN'},
        'text': {'beginOffset': 0, 'content': u'六本木'}
      }, {
        'dependencyEdge': {'headTokenIndex': 8, 'label': 'ADVPHMOD'},
        'partOfSpeech': {'tag': 'NOUN'},
        'text': {'beginOffset': 3, 'content': u'ヒルズ'}
      }, {
        'dependencyEdge': {'headTokenIndex': 1, 'label': 'PRT'},
        'partOfSpeech': {'tag': 'PRT'},
        'text': {'beginOffset': 6, 'content': u'で'}
      }, {
        'dependencyEdge': {'headTokenIndex': 8, 'label': 'P'},
        'partOfSpeech': {'tag': 'PUNCT'},
        'text': {'beginOffset': 7, 'content': u'、'}
      }, {
        'dependencyEdge': {'headTokenIndex': 5, 'label': 'P'},
        'partOfSpeech': {'tag': 'PUNCT'},
        'text': {'beginOffset': 8, 'content': u'「'}
      }, {
        'dependencyEdge': {'headTokenIndex': 8, 'label': 'DOBJ'},
        'partOfSpeech': {'tag': 'NOUN'},
        'text': {'beginOffset': 9, 'content': u'ご飯'}
      }, {
        'dependencyEdge': {'headTokenIndex': 5, 'label': 'P'},
        'partOfSpeech': {'tag': 'PUNCT'},
        'text': {'beginOffset': 11, 'content': u'」'}
      }, {
        'dependencyEdge': {'headTokenIndex': 5, 'label': 'PRT'},
        'partOfSpeech': {'tag': 'PRT'},
        'text': {'beginOffset': 12, 'content': u'を'}
      }, {
        'dependencyEdge': {'headTokenIndex': 8, 'label': 'ROOT'},
        'partOfSpeech': {'tag': 'VERB'},
        'text': {'beginOffset': 13, 'content': u'食べ'}
      }, {
        'dependencyEdge': {'headTokenIndex': 8, 'label': 'AUX'},
        'partOfSpeech': {'tag': 'VERB'},
        'text': {'beginOffset': 15, 'content': u'ます'}
      }, {
        'dependencyEdge': {'headTokenIndex': 8, 'label': 'P'},
        'partOfSpeech': {'tag': 'PUNCT'},
        'text': {'beginOffset': 17, 'content': u'。'}
    }])
    chunks = self.parser._get_source_chunks(
        u'六本木ヒルズで、「ご飯」を食べます。')
    expected = [
        budou.Chunk(u'六本木', label='NN', pos='NOUN', dependency=None),
        budou.Chunk(u'ヒルズ', label='ADVPHMOD', pos='NOUN', dependency=None),
        budou.Chunk(u'で', label='PRT', pos='PRT', dependency=False),
        budou.Chunk(u'、', label='P', pos='PUNCT', dependency=False),
        budou.Chunk(u'「', label='P', pos='PUNCT', dependency=True),
        budou.Chunk(u'ご飯', label='DOBJ', pos='NOUN', dependency=None),
        budou.Chunk(u'」', label='P', pos='PUNCT', dependency=False),
        budou.Chunk(u'を', label='PRT', pos='PRT', dependency=False),
        budou.Chunk(u'食べ', label='ROOT', pos='VERB', dependency=None),
        budou.Chunk(u'ます', label='AUX', pos='VERB', dependency=False),
        budou.Chunk(u'。', label='P', pos='PUNCT', dependency=False)
    ]
    self.assertEqual(
        [chunk.word for chunk in expected],
        [chunk.word for chunk in chunks],
        'Words should be match between input text and retrieved chunks.')
    self.assertEqual(
        [chunk.dependency for chunk in expected],
        [chunk.dependency for chunk in chunks],
        'Dependency should be match between input text and retrieved chunks.')

  def test_group_chunks_by_entities(self):
    # chunks: foo bar baz
    # entity: ___ bar ___
    chunks = budou.ChunkList([
        budou.Chunk('foo'), budou.Chunk('bar'), budou.Chunk('baz')])
    entities = [{'beginOffset': 3, 'content': 'bar'}]
    expected = ['foo', 'bar', 'baz']
    result = self.parser._group_chunks_by_entities(chunks, entities)
    self.assertEqual(expected, [chunk.word for chunk in result])

    # chunks: foo bar baz
    # entity: foo ba_ ___
    chunks = budou.ChunkList([
        budou.Chunk('foo'), budou.Chunk('bar'), budou.Chunk('baz')])
    entities = [{'beginOffset': 0, 'content': 'fooba'}]
    expected = ['foobar', 'baz']
    result = self.parser._group_chunks_by_entities(chunks, entities)
    self.assertEqual(expected, [chunk.word for chunk in result])

  def test_html_serialize(self):
    chunks = budou.ChunkList([
        budou.Chunk('a'), budou.Chunk('b'), budou.Chunk.space(),
        budou.Chunk('c')])
    attributes = {
        'class': 'foo'
    }
    expected = (
        '<span>'
        '<span class="foo">a</span>'
        '<span class="foo">b</span> '
        '<span class="foo">c</span>'
        '</span>')
    result = self.parser._html_serialize(chunks, attributes)
    self.assertEqual(
        result, expected,
        'The chunks should be compiled to a HTML code.')

  def test_concatenate_inner(self):
    chunks = budou.ChunkList()
    chunks.append(budou.Chunk('ab', dependency=None))
    chunks.append(budou.Chunk('cde', dependency=True))
    chunks.append(budou.Chunk('fgh', dependency=False))

    chunks = self.parser._concatenate_inner(chunks, True)
    self.assertEqual(
        ['ab', 'cdefgh'], [chunk.word for chunk in chunks],
        'Chunks should be concatenated if they depends on the following word.')
    self.assertEqual(
        [None, False], [chunk.dependency for chunk in chunks],
        'Dependency should persist even if it\'s concatenated by others.')

    chunks = self.parser._concatenate_inner(chunks, False)
    self.assertEqual(
        ['abcdefgh'], [chunk.word for chunk in chunks],
        'Chunks should be concatenated if they depends on the previous word.')


if __name__ == '__main__':
  unittest.main()
