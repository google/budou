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
import os
import pickle
import six


def load_cache(filename=None):
  """Loads cache system.

  If Google App Engine Standard Environment's memcache is available, this uses
  memcache as the backend. Otherwise, this uses :obj:`pickle` to cache
  the outputs in the local file system.

  Args:
    filename (:obj:`str`, optional): The file path to the cache file. This is
        used only when :obj:`pickle` is used as the backend.
  """
  try:
    return AppEngineMemcache()
  except ImportError:
    return PickleCache(filename)


@six.add_metaclass(ABCMeta)
class BudouCache:
  """Base class for cache system.
  """

  @abstractmethod
  def get(self, key):
    """Abstract method: Gets a value by a key.

    Args:
      key (str): Key to retrieve the value.

    Returns:
      Retrieved value.

    Raises:
      NotImplementedError: If it's not implemented.
    """
    raise NotImplementedError()

  @abstractmethod
  def set(self, key, val):
    """Abstract method: Sets a value in a key.

    Args:
      key (str): Key for the value.
      val: Value to set.

    Returns:
      Retrieved value.

    Raises:
      NotImplementedError: If it's not implemented.
    """
    raise NotImplementedError()


class PickleCache(BudouCache):
  """Cache system with :obj:`pickle` backend.

  Args:
    filename (str): The file path to the cache file.

  Attributes:
    filename (str): The file path to the cache file.
  """

  DEFAULT_FILE_NAME = '/tmp/budou-cache.pickle'
  """ The default path to the cache file.
  """

  def __init__(self, filename):
    self.filename = filename if filename else self.DEFAULT_FILE_NAME

  def get(self, key):
    """Gets a value by a key.

    Args:
      key (str): Key to retrieve the value.

    Returns: Retrieved value.
    """
    self._create_file_if_none_exists()
    with open(self.filename, 'rb') as file_object:
      cache_pickle = pickle.load(file_object)
      val = cache_pickle.get(key, None)
      return val

  def set(self, key, val):
    """Sets a value in a key.

    Args:
      key (str): Key for the value.
      val: Value to set.

    Returns:
      Retrieved value.
    """
    self._create_file_if_none_exists()
    with open(self.filename, 'r+b') as file_object:
      cache_pickle = pickle.load(file_object)
      cache_pickle[key] = val
      file_object.seek(0)
      pickle.dump(cache_pickle, file_object)

  def _create_file_if_none_exists(self):
    if os.path.exists(self.filename):
      return
    with open(self.filename, 'wb') as file_object:
      pickle.dump({}, file_object)


class AppEngineMemcache(BudouCache):
  """Cache system with :obj:`google.appengine.api.memcache` backend.

  Attributes:
    memcache (:obj:`google.appengine.api.memcache`): Memcache service.
  """

  def __init__(self):
    from google.appengine.api import memcache
    self.memcache = memcache

  def get(self, key):
    """Gets a value by a key.

    Args:
      key (str): Key to retrieve the value.

    Returns:
      Retrieved value.
    """
    return self.memcache.get(key, None)

  def set(self, key, val):
    """Sets a value in a key.

    Args:
      key (str): Key for the value.
      val: Value to set.

    Returns:
      Retrieved value.
    """
    self.memcache.set(key, val)
