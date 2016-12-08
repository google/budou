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

"""Abstract cache module."""

import six
from abc import ABCMeta, abstractmethod
import hashlib
from .. import config

@six.add_metaclass(ABCMeta)
class BudouCache(object):
  @abstractmethod
  def get(self, source, language):
    pass

  @abstractmethod
  def set(self, source, language, value):
    pass

  def _get_cache_key(self, source, language):
    """Returns a cache key for the given source and class name."""
    key_source = u'%s:%s:%s' % (config.CACHE_SALT, source, language)
    return hashlib.md5(key_source.encode('utf8')).hexdigest()
