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

"""Budou cache factory class."""
from abc import ABCMeta, abstractmethod
import hashlib
import six
import pickle
import os


def load_cache():
  try:
    from google.appengine.api import memcache
  except:
    return PickleCache()
  else:
    return AppEngineCache(memcache)


@six.add_metaclass(ABCMeta)
class BudouCache(object):

  CACHE_SALT = '2017-04-13'
  DEFAULT_FILE_PATH = './budou-cache.pickle'

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
    key_source = u'%s:%s:%s' % (self.CACHE_SALT, source, language)
    return hashlib.md5(key_source.encode('utf8')).hexdigest()


class PickleCache(BudouCache):

  def __init__(self, filepath = None):
    self.filepath = filepath if filepath else self.DEFAULT_FILE_PATH

  def get(self, source, language):
    self._create_file_if_none_exists()
    with open(self.filepath, 'rb') as file_object:
      cache_pickle = pickle.load(file_object)
      cache_key = self._get_cache_key(source, language)
      result_value = cache_pickle[cache_key]
      return result_value

  def set(self, source, language, value):
    self._create_file_if_none_exists()
    with open(self.filepath, 'r+b') as file_object:
      cache_pickle = pickle.load(file_object)
      cache_key = self._get_cache_key(source, language)
      cache_pickle[cache_key] = value
      file_object.seek(0)
      pickle.dump(cache_pickle, file_object)

  def _create_file_if_none_exists(self):
    if os.path.exists(self.filepath):
      return
    with open(self.filepath, 'wb') as file_object:
      pickle.dump({}, file_object)


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
