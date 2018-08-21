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
import os
import json
import unittest
from mock import MagicMock

CASES_PATH = 'cases.ndjson'

class TestNLAPISegmenter(unittest.TestCase):

  def setUp(self):
    self.segmenter = budou.nlapisegmenter.NLAPISegmenter(debug=True)
    cases_path = os.path.join(os.path.dirname(__file__), CASES_PATH)
    with open(cases_path) as f:
      self.cases = [json.loads(row) for row in f.readlines() if row.strip()]

  def test_segment(self):
    for case in self.cases:
      # Mocks external API request.
      self.segmenter._get_annotations = MagicMock(return_value={
        'tokens': case['tokens'], 'language': case['language']})
      self.segmenter._get_entities = MagicMock(return_value=case['entities'])
      chunks = self.segmenter.segment(
          case['sentence'], language=case['language'], use_entity=False)
      self.assertEqual(
          case['expected'], [chunk.word for chunk in chunks],
          u'Chunks do not match in a test case (entity off): {source}'.format(
            source=case['sentence']))
      chunks = self.segmenter.segment(
          case['sentence'], language=case['language'], use_entity=True)
      self.assertEqual(
          case['expected_with_entity'], [chunk.word for chunk in chunks],
          u'Chunks do not match in a test case (entity on): {source}'.format(
            source=case['sentence']))


if __name__ == '__main__':
  unittest.main()

