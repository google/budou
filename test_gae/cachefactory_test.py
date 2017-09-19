# -*- coding: utf-8 -*-
#
# Copyright 2017 Google Inc. All rights reserved.
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

from google.appengine.api import memcache
from google.appengine.ext import testbed
from google.appengine.ext import vendor
vendor.add("lib")
import budou
import unittest

class TestGAECacheFactory(unittest.TestCase):

  def setUp(self):
    # First, create an instance of the Testbed class.
    self.testbed = testbed.Testbed()
    # Then activate the testbed, which prepares the service stubs for use.
    self.testbed.activate()
    # Next, declare which service stubs you want to use.
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_memcache_stub()
    self.cache = budou.load_cache()

  def tearDown(self):
    del self.cache

  def test_load(self):
    self.assertEqual('<AppEngineCache>', repr(self.cache),
        'Under GAE environment, AppEngineCache should be loaded.')

  def test_set_and_get(self):
    source = 'apple'
    language = 'a'
    target = 'banana'
    self.cache.set(source, language, target)
    self.assertEqual(target, self.cache.get(source, language),
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

