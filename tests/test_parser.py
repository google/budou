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

class TestParser(unittest.TestCase):

  def test_parse_attributes(self):
    results = budou.parser.parse_attributes()
    self.assertIn('class', results,
        '`class` property should be included even if no attribute is given.')
    self.assertEqual(results['class'], budou.parser.DEFAULT_CLASS_NAME,
        'default class name should be used when no attribute is given.')

    results = budou.parser.parse_attributes(classname='baz')
    self.assertEqual(results['class'], 'baz',
        'classname should be added to attributes as class property.')

    results = budou.parser.parse_attributes(
        attributes={'foo': 'bar', 'class': 'erase-me'}, classname='baz')
    self.assertEqual(results['foo'], 'bar',
        'all properties but `class` should be preserved')
    self.assertEqual(results['class'], 'baz',
        '`classname` should precede to `class` property in `attributes`.')

  def test_preprocess(self):
    source = u' a\nb<br> c   d'
    expected = u'ab c d'
    result = budou.parser.preprocess(source)
    self.assertEqual(
        expected, result,
        'BR tags, line breaks, and unnecessary spaces should be removed.')

    source = u'a <script>alert(1)</script> b<div>c</div>'
    expected = u'a alert(1) bc'
    result = budou.parser.preprocess(source)
    self.assertEqual(
        expected, result,
        'XML tags should be removed.')

if __name__ == '__main__':
  unittest.main()
