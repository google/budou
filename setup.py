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

from setuptools import setup

setup(
    name='budou',
    version='0.1.2',
    author='Shuhei Iitsuka',
    author_email='tushuhei@google.com',
    description='CJK Line Break Organizer',
    license='Apache',
    url='https://github.com/google/budou/',
    packages=['budou'],
    install_requires=[
        'google-api-python-client',
        'oauth2client',
        'lxml==3.6.1',
        'six',
    ],
    scripts=[
        'budou/budou.py',
    ],
    tests_require=[
        'mock>=2.0.0',
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
