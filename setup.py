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

import os
from setuptools import setup

def read_file(name):
  with open(os.path.join(os.path.dirname(__file__), name), 'r') as f:
    return f.read().strip()

setup(
    name='budou',
    version='0.6.0',
    author='Shuhei Iitsuka',
    author_email='tushuhei@google.com',
    description='CJK Line Break Organizer',
    license='Apache',
    url='https://github.com/google/budou/',
    packages=['budou'],
    install_requires=read_file('requirements.txt').splitlines(),
    tests_require=read_file('requirements_dev.txt').splitlines(),
    scripts=[
        'budou/budou.py',
    ],
    test_suite='test',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
