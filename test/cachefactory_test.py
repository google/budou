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

from budou.cachefactory import CacheFactory
from budou.budoucache.shelvecache import ShelveCache
import unittest
import os
from budou import config

class TestStandardCacheFactory(unittest.TestCase):

  def setUp(self):
    self.cache = CacheFactory.load()

  def tearDown(self):
    if os.path.isfile(config.SHELVE_CACHE_FILE_NAME):
      os.remove(config.SHELVE_CACHE_FILE_NAME)
    del self.cache

  def test_load(self):
    self.assertIsInstance(self.cache, ShelveCache,
        'Under non GAE environment, ShelveCache should be loaded.')

  def test_set_and_get(self):
    source = 'apple'
    language = 'a'
    target = 'banana'
    self.cache.set(source, language, target)
    self.assertTrue(os.path.isfile(config.SHELVE_CACHE_FILE_NAME),
        'Cache file should be generated.')
    self.assertEqual(self.cache.get(source, language), target,
        'The target should be cached.')

  def test_cache_key(self):
    self.cache.set('a', 'en', 1)
    self.cache.set('a', 'ja', 2)
    self.cache.set('b', 'en', 3)
    self.assertNotEqual(
        self.cache.get('a', 'en'), self.cache.get('b', 'en'),
        'The cached key should be unique per source text.')
    self.assertNotEqual(
        self.cache.get('a', 'en'), self.cache.get('a', 'ja'),
        'The cached key should be unique per language.')

if __name__ == '__main__':
  unittest.main()

