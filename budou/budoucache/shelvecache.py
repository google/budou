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

"""Cache module for standalone usage based on shelve module."""

import shelve
from .. import config
from .budoucache import BudouCache


class ShelveCache(BudouCache):
  def get(self, source, language):
    cache_shelve = shelve.open(config.SHELVE_CACHE_FILE_NAME)
    cache_key = self._get_cache_key(source, language)
    result_value = cache_shelve.get(cache_key, None)
    cache_shelve.close()
    return result_value

  def set(self, source, language, value):
    cache_shelve = shelve.open(config.SHELVE_CACHE_FILE_NAME)
    cache_key = self._get_cache_key(source, language)
    cache_shelve[cache_key] = value
    cache_shelve.close()

