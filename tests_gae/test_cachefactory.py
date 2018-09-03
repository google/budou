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
vendor.add('lib')
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
    self.assertIsInstance(self.cache, budou.AppEngineMemcache,
        'Under GAE environment, AppEngineMemcache should be used.')

  def test_set_and_get(self):
    key = 'apple'
    val = 'banana'
    self.cache.set(key,  val)
    self.assertEqual(val, self.cache.get(key), 'The target should be cached.')
    val = 'cinnamon'
    self.cache.set(key, val)
    self.assertEqual(
        val, self.cache.get(key), 'The cached value should be updated.')

if __name__ == '__main__':
  unittest.main()

