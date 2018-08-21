# -*- coding: utf-8 -*-
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Parser modules.

Parser modules are equipped with :code:`parse` method and it processes the
input text into a list of chunks and an organized HTML snippet.

Examples:

  .. code-block:: python

     import budou
     parser = budou.get_parser('nlapi')
     results = parser.parse('Google Home を使った。', classname='w')
     print(results['html_code'])
     # <span>Google <span class="w">Home を</span>
     # <span class="w">使った。</span></span>

     chunks = results['chunks']
     print(chunks[1].word)  # Home を

"""

from abc import ABCMeta
import re
from xml.etree import ElementTree as ET
import six
import html5lib
from .nlapisegmenter import NLAPISegmenter
from .mecabsegmenter import MecabSegmenter

DEFAULT_CLASS_NAME = 'chunk'

@six.add_metaclass(ABCMeta)
class Parser:
  """Abstract parser class:

  Args:
    segmenter(:obj:`budou.segmenter.Segmenter`): Segmenter module.
  """

  def __init__(self):
    self.segmenter = None

  def parse(self, source, attributes=None, language=None, max_length=None,
            classname=None):
    """Parses the source sentence to output organized HTML code.

    Args:
      source (str): Source sentence to process.
      attributes (:obj:`dict`, optional): Attributes for output SPAN tags.
      language (:obj:`str`, optional): Language code.
      max_length (:obj:`int`, optional): Maximum length of a chunk.

    Returns:
      A dictionary containing :code:`chunks` (:obj:`budou.chunk.ChunkList`)
      and :code:`html_code` (:obj:`str`).
    """
    attributes = parse_attributes(attributes, classname)
    source = preprocess(source)
    chunks = self.segmenter.segment(source, language)
    html_code = chunks.html_serialize(attributes, max_length=max_length)
    return {
        'chunks': chunks,
        'html_code': html_code,
    }


class NLAPIParser(Parser):
  """Parser built on Cloud Language API Segmenter
  (:obj:`budou.nlapisegmenter.NLAPISegmenter`).

  Args:
    options (dict, optional): Optional settings. :code:`cache_filename` is for
      the file path to the cache file. :code:`credentials_path` is for the file
      path to the service account's credentials file.

  Attributes:
    segmenter(:obj:`budou.nlapisegmenter.NLAPISegmenter`): Segmenter module.
  """

  def __init__(self, options=None):
    if options is None:
      options = {}
    self.segmenter = NLAPISegmenter(
        cache_filename=options.get('cache_filename', None),
        credentials_path=options.get('credentials_path', None))


class MecabParser(Parser):
  """Parser built on Mecab Segmenter
  (:obj:`budou.mecabsegmenter.MecabSegmenter`).

  Attributes:
    segmenter(:obj:`budou.mecabsegmenter.MecabSegmenter`): Segmenter module.
  """

  def __init__(self):
    self.segmenter = MecabSegmenter()


def get_parser(segmenter, options=None):
  """Gets a parser.

  Args:
    segmenter (str): Segmenter to use.
    language (:obj:`str`, optional): Language code.
    classname (:obj:`str`, optional): Class name of output SPAN tags.
    options (:obj:`dict`, optional): Optional settings to pass to the segmenter.

  Returns:
    Results in a dict. :code:`chunks` holds a list of chunks
    (:obj:`budou.chunk.ChunkList`) and :code:`html_code` holds the output HTML
    code.

  Raises:
    ValueError: If unsupported segmenter is specified.
  """
  if segmenter == 'nlapi':
    return NLAPIParser(options=options)
  elif segmenter == 'mecab':
    return MecabParser()
  else:
    raise ValueError('Segmenter {} is not supported.'.format(segmenter))

def parse_attributes(attributes=None, classname=None):
  """Parses attributes,

  Args:
    attributes (dict): Input attributes.
    classname (:obj:`str`, optional): Class name of output SPAN tags.

  Returns:
    Parsed attributes. (dict)
  """
  if not attributes:
    attributes = {}
  attributes.setdefault('class', DEFAULT_CLASS_NAME)
  # If `classname` is specified, it overwrites `class` property in `attributes`.
  if classname:
    attributes['class'] = classname
  return attributes

def preprocess(source):
  """Removes unnecessary break lines and white spaces.

  Args:
    source (str): Input sentence.

  Returns:
    Preprocessed sentence. (str)
  """
  doc = html5lib.parseFragment(source)
  source = ET.tostring(doc, encoding='utf-8', method='text').decode('utf-8')
  source = source.replace(u'\n', u'').strip()
  source = re.sub(r'\s\s+', u' ', source)
  return source
