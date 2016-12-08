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

"""Cache module for AppEngine usage based on memcache."""

from .budoucache import BudouCache
from google.appengine.api import memcache


class AppEngineCache(BudouCache):
  def get(self, source, language):
    cache_key = self._get_cache_key(source, language)
    result_value = memcache.get(cache_key, None)
    return result_value

  def set(self, source, language, value):
    cache_key = self._get_cache_key(source, language)
    memcache.set(cache_key, value)
