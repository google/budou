# -*- coding: utf-8 -*-
#
# Copyright 2016 Google Inc. All rights reserved
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
import logging
import unittest

DEFAULT_SENTENCE = u'今日は晴れ。'

DEFAULT_TOKENS = [{
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
    self.parser._GetAnnotations = MagicMock(
        return_value=DEFAULT_TOKENS)

  def tearDown(self):
    pass

  def test_process(self):
    expected_chunks = [
      budou.Chunk(u'今日は', u'NOUN', u'NN', True),
      budou.Chunk(u'晴れ。', u'NOUN', u'ROOT', False)
    ]

    expected_html_code = (u'<span class="ww">今日は</span>'
                        u'<span class="ww">晴れ。</span>')

    result = self.parser.Process(DEFAULT_SENTENCE)

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

  def test_preprocess(self):
    source = u' a\nb<br> c   d'
    expected = u'ab c d'
    result = self.parser._Preprocess(source)
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
    result = self.parser._GetSourceChunks(DEFAULT_SENTENCE)
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
    result = self.parser._MigrateHTML(chunks, dom)
    self.assertEqual(
        expected, result,
        'The HTML source code should be migrated into the chunk list.')

  def test_get_elements_list(self):
    source = u'<a>こちら</a>をクリック'
    dom = html.fragment_fromstring(source, create_parent='body')
    expected = [
      budou.Element(u'こちら', 'a', u'<a>こちら</a>', 0)
    ]
    result = self.parser._GetElementsList(dom)
    self.assertEqual(
        result, expected,
        'The input DOM should be processed to an element list.')

  def test_spanize(self):
    chunks = [
      budou.Chunk(u'a', None, None, None),
      budou.Chunk(u'b', None, None, None),
      budou.Chunk(u'c', None, None, None),
    ]
    classname = 'foo'
    expected = (
        u'<span class="foo">a</span>'
        '<span class="foo">b</span>'
        '<span class="foo">c</span>')
    result = self.parser._Spanize(chunks, classname)
    self.assertEqual(
        result, expected,
        'The chunks should be compiled to a HTML code.')

  def test_concatenate_chunks(self):
    chunks = [
      budou.Chunk(u'a', None, budou.TARGET_LABEL[0], True),
      budou.Chunk(u'b', None, budou.TARGET_LABEL[1], False),
      budou.Chunk(u'c', None, budou.TARGET_LABEL[2], True),
    ]
    expected_forward_concat = [
      budou.Chunk(u'ab', None, budou.TARGET_LABEL[1], False),
      budou.Chunk(u'c', None, budou.TARGET_LABEL[2], True),
    ]
    result = self.parser._ConcatenateChunks(chunks, True)
    self.assertEqual(
        result, expected_forward_concat,
        'Forward directional chunks should be concatenated to following '
        'chunks.')
    expected_backward_concat = [
      budou.Chunk(u'ab', None, budou.TARGET_LABEL[0], True),
      budou.Chunk(u'c', None, budou.TARGET_LABEL[2], True),
    ]
    result = self.parser._ConcatenateChunks(chunks, False)
    self.assertEqual(
        result, expected_backward_concat,
        'Backward directional chunks should be concatenated to preceding '
        'chunks.')

if __name__ == '__main__':
  unittest.main()
