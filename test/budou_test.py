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

from lxml import html
from mock import MagicMock
import budou
import os
import unittest

DEFAULT_SENTENCE_JA = u'今日は晴れ。'
DEFAULT_SENTENCE_KO = u'오늘은 맑음.'

DEFAULT_TOKENS = [
    {
        u'text': {u'content': u'今日', u'beginOffset': 0},
        u'dependencyEdge': {u'headTokenIndex': 2, u'label': u'NN'},
        u'partOfSpeech': {u'tag': u'NOUN'},
        u'lemma': u'今日'
    },
    {
        u'text': {u'content': u'は', u'beginOffset': 2},
        u'dependencyEdge': {u'headTokenIndex': 0, u'label': u'PRT'},
        u'partOfSpeech': {u'tag': u'PRT'},
        u'lemma': u'は'
    },
    {
        u'text': {u'content': u'晴れ', u'beginOffset': 3},
        u'dependencyEdge': {u'headTokenIndex': 2, u'label': u'ROOT'},
        u'partOfSpeech': {u'tag': u'NOUN'},
        u'lemma': u'晴れ'
    },
    {
        u'text': {u'content': u'。', u'beginOffset': 5},
        u'dependencyEdge': {u'headTokenIndex': 2, u'label': u'P'},
        u'partOfSpeech': {u'tag': u'PUNCT'},
        u'lemma': u'。'
    }]


class TestBudouMethods(unittest.TestCase):

  def setUp(self):
    self.parser = budou.Budou(None)
    # Mocks external API request.
    self.parser._get_annotations = MagicMock(
        return_value=DEFAULT_TOKENS)

  def tearDown(self):
    if os.path.exists(budou.SHELVE_CACHE_FILE_NAME):
      os.remove(budou.SHELVE_CACHE_FILE_NAME)

  def test_parse_ja(self):
    """Demonstrates standard usage in Japanese."""
    expected_chunks = [
        budou.Chunk(u'今日は', u'NOUN', u'NN', True),
        budou.Chunk(u'晴れ。', u'NOUN', u'ROOT', False)
    ]

    expected_html_code = (u'<span class="ww">今日は</span>'
                          u'<span class="ww">晴れ。</span>')

    result = self.parser.parse(
        DEFAULT_SENTENCE_JA, language='ja', use_cache=False)

    self.assertEqual(
        expected_chunks, result['chunks'],
        'Processed result should include expected chunks in Japanese.')
    self.assertEqual(
        expected_html_code, result['html_code'],
        'Processed result should include expected html code in Japanese.')

  def test_parse_ko(self):
    """Demonstrates standard usage in Japanese."""
    expected_chunks = [
        budou.Chunk(u'오늘은', None, None, True),
        budou.Chunk(' ', budou.SPACE_POS, budou.SPACE_POS, True),
        budou.Chunk(u'맑음.', None, None, True)
    ]

    expected_html_code = (u'<span class="ww">오늘은</span> '
                          u'<span class="ww">맑음.</span>')

    result = self.parser.parse(
        DEFAULT_SENTENCE_KO, language='ko', use_cache=False)

    self.assertEqual(
        expected_chunks, result['chunks'],
        'Processed result should include expected chunks in Korean.')
    self.assertEqual(
        expected_html_code, result['html_code'],
        'Processed result should include expected html code in Korean.')

  def test_process_with_aria(self):
    """Demonstrates advanced usage considering accessibility."""
    expected_chunks = [
        budou.Chunk(u'今日は', u'NOUN', u'NN', True),
        budou.Chunk(u'晴れ。', u'NOUN', u'ROOT', False)
    ]

    expected_html_code = (
        u'<span aria-describedby="parent" class="text-chunk">今日は</span>'
        u'<span aria-describedby="parent" class="text-chunk">晴れ。</span>')

    result = self.parser.parse(DEFAULT_SENTENCE_JA, {
        'aria-describedby': 'parent',
        'class': 'text-chunk'
        }, use_cache=False)

    self.assertEqual(
        expected_chunks, result['chunks'],
        'Processed result should include expected chunks.')
    self.assertEqual(
        expected_html_code, result['html_code'],
        'Processed result should include expected html code.')

  def test_preprocess(self):
    source = u' a\nb<br> c   d'
    expected = u'ab c d'
    result = self.parser._preprocess(source)
    self.assertEqual(
        expected, result,
        'BR tags, line breaks, and unnecessary spaces should be removed.')

  def test_get_source_chunks(self):
    expected = [
        budou.Chunk(u'今日', u'NOUN', u'NN', True),
        budou.Chunk(u'は', u'PRT', u'PRT', False),
        budou.Chunk(u'晴れ', u'NOUN', u'ROOT', False),
        budou.Chunk(u'。', u'PUNCT', u'P', False),
    ]
    result = self.parser._get_source_chunks(DEFAULT_SENTENCE_JA)
    self.assertEqual(
        expected, result,
        'Input sentence should be processed into source chunks.')

  def test_migrate_html(self):
    source = u'こ<a>ちらを</a>クリック'
    dom = html.fragment_fromstring(source, create_parent='body')
    chunks = [
        budou.Chunk(u'こちら', u'PRON', u'NSUBJ', True),
        budou.Chunk(u'を', u'PRT', u'PRT', False),
        budou.Chunk(u'クリック', u'NOUN', u'ROOT', False),
    ]
    expected = [
        budou.Chunk(
            u'こ<a>ちらを</a>', budou.HTML_POS,
            budou.HTML_POS, True),
        budou.Chunk(u'クリック', u'NOUN', u'ROOT', False),
    ]
    result = self.parser._migrate_html(chunks, dom)
    self.assertEqual(
        expected, result,
        'The HTML source code should be migrated into the chunk list.')

  def test_get_elements_list(self):
    source = u'<a>こちら</a>をクリック'
    dom = html.fragment_fromstring(source, create_parent='body')
    expected = [
        budou.Element(u'こちら', 'a', u'<a>こちら</a>', 0)
    ]
    result = self.parser._get_elements_list(dom)
    self.assertEqual(
        result, expected,
        'The input DOM should be processed to an element list.')

  def test_spanize(self):
    chunks = [
        budou.Chunk(u'a', None, None, None),
        budou.Chunk(u'b', None, None, None),
        budou.Chunk(u'c', None, None, None),
    ]
    attributes = {
        'class': 'foo'
    }
    expected = (
        u'<span class="foo">a</span>'
        '<span class="foo">b</span>'
        '<span class="foo">c</span>')
    result = self.parser._spanize(chunks, attributes)
    self.assertEqual(
        result, expected,
        'The chunks should be compiled to a HTML code.')

  def test_cache(self):
    expected_chunks = [
        budou.Chunk(u'今日は', u'NOUN', u'NN', True),
        budou.Chunk(u'晴れ。', u'NOUN', u'ROOT', False)
    ]

    expected_html_code = (u'<span class="ww">今日は</span>'
                          u'<span class="ww">晴れ。</span>')

    result = self.parser.parse(DEFAULT_SENTENCE_JA, use_cache=True)

    self.assertIn(
        'chunks', result,
        'Processed result should include chunks.')
    self.assertIn(
        'html_code', result,
        'Processed result should include organized html code.')
    self.assertEqual(
        expected_chunks, result['chunks'],
        'Processed result should include expected chunks.')
    self.assertEqual(
        expected_html_code, result['html_code'],
        'Processed result should include expected html code.')

  def test_get_attribute_dict(self):
    result = self.parser._get_attribute_dict({})
    self.assertEqual(
        result, {'class': budou.DEFAULT_CLASS_NAME},
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
            'class': budou.DEFAULT_CLASS_NAME,
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

  def test_get_chunks_per_space(self):
    source = 'a b'
    expected = [
        budou.Chunk('a', None, None, True),
        budou.Chunk(' ', budou.SPACE_POS, budou.SPACE_POS, True),
        budou.Chunk('b', None, None, True)]
    result = self.parser._get_chunks_per_space(source)
    self.assertEqual(
        result, expected,
        'Input text should be parsed into chunks separated by spaces.')

  def test_update_punct_direction(self):
    chunks = [
        budou.Chunk(u'。', u'PUNCT', None, None),
        budou.Chunk(u'、', u'PUNCT', None, None),
        budou.Chunk(u'「', u'PUNCT', None, None),
        budou.Chunk(u'」', u'PUNCT', None, None),
        budou.Chunk(u'（', u'PUNCT', None, None),
        budou.Chunk(u'）', u'PUNCT', None, None),
        budou.Chunk(u'[', u'PUNCT', None, None),
        budou.Chunk(u']', u'PUNCT', None, None),
        budou.Chunk(u'(', u'PUNCT', None, None),
        budou.Chunk(u')', u'PUNCT', None, None),
    ]
    expected = [
        budou.Chunk(u'。', u'PUNCT', None, False),
        budou.Chunk(u'、', u'PUNCT', None, False),
        budou.Chunk(u'「', u'PUNCT', None, True),
        budou.Chunk(u'」', u'PUNCT', None, False),
        budou.Chunk(u'（', u'PUNCT', None, True),
        budou.Chunk(u'）', u'PUNCT', None, False),
        budou.Chunk(u'[', u'PUNCT', None, True),
        budou.Chunk(u']', u'PUNCT', None, False),
        budou.Chunk(u'(', u'PUNCT', None, True),
        budou.Chunk(u')', u'PUNCT', None, False),
    ]
    result = self.parser._update_punct_direction(chunks)
    self.assertEqual(
        result, expected,
        'Punctuation mark\'s concatenating direction should be determined.')


if __name__ == '__main__':
  unittest.main()
