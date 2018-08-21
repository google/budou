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

import codecs
import os
from setuptools import setup

def read_file(name):
  with codecs.open(
      os.path.join(os.path.dirname(__file__), name), 'r', 'utf-8') as f:
    return f.read().strip()

about = {}
with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
  'budou', '__version__.py')) as f:
  exec(f.read(), about)

setup(
    name='budou',
    version=about['__version__'],
    author='Shuhei Iitsuka',
    author_email='tushuhei@google.com',
    description='CJK Line Break Organizer',
    license='Apache',
    url='https://github.com/google/budou/',
    packages=['budou'],
    install_requires=read_file('requirements.txt').splitlines(),
    tests_require=['mock'],
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    test_suite='tests',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    entry_points = {
        'console_scripts': ['budou=budou.budou:main'],
    }
)
