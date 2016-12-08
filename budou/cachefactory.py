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

"""Budou cache factory class."""

try:
  from google.appengine.api import memcache
except:
  from .budoucache.shelvecache import ShelveCache as BudouCache
else:
  from .budoucache.appenginecache import AppEngineCache as BudouCache

class CacheFactory(object):
  @classmethod
  def load(self):
    return BudouCache()
