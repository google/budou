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
from abc import ABCMeta, abstractmethod
import hashlib
import six
import shelve

CACHE_SALT = '2016-10-11'
SHELVE_CACHE_FILE_NAME = 'budou-cache.shelve'

def load_cache():
  try:
    from google.appengine.api import memcache
  except:
    return ShelveCache()
  else:
    return AppEngineCache(memcache)


@six.add_metaclass(ABCMeta)
class BudouCache(object):

  def __repr__(self):
    return '<%s>' % (self.__class__.__name__)

  @abstractmethod
  def get(self, source, language):
    pass

  @abstractmethod
  def set(self, source, language, value):
    pass

  def _get_cache_key(self, source, language):
    """Returns a cache key for the given source and class name."""
    key_source = u'%s:%s:%s' % (CACHE_SALT, source, language)
    return hashlib.md5(key_source.encode('utf8')).hexdigest()


class ShelveCache(BudouCache):

  def get(self, source, language):
    cache_shelve = shelve.open(SHELVE_CACHE_FILE_NAME)
    cache_key = self._get_cache_key(source, language)
    result_value = cache_shelve.get(cache_key, None)
    cache_shelve.close()
    return result_value

  def set(self, source, language, value):
    cache_shelve = shelve.open(SHELVE_CACHE_FILE_NAME)
    cache_key = self._get_cache_key(source, language)
    cache_shelve[cache_key] = value
    cache_shelve.close()


class AppEngineCache(BudouCache):

  def __init__(self, memcache):
    self.memcache = memcache

  def get(self, source, language):
    cache_key = self._get_cache_key(source, language)
    result_value = self.memcache.get(cache_key, None)
    return result_value

  def set(self, source, language, value):
    cache_key = self._get_cache_key(source, language)
    self.memcache.set(cache_key, value)
