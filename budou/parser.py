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

Parser modules have :code:`parse` method which processes the input text into a
list of chunks and a HTML snippet.

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
from .tinysegmentersegmenter import TinysegmenterSegmenter

DEFAULT_CLASS_NAME = 'ww'

@six.add_metaclass(ABCMeta)
class Parser:
  """Abstract parser class:

  Attributes:
    segmenter(:obj:`budou.segmenter.Segmenter`): Segmenter module.
  """

  def __init__(self):
    self.segmenter = None

  def parse(self, source, language=None, classname=None, max_length=None,
            attributes=None, inlinestyle=False):
    """Parses the source sentence to output organized HTML code.

    Args:
      source (str): Source sentence to process.
      language (str, optional): Language code.
      max_length (int, optional): Maximum length of a chunk.
      attributes (dict, optional): Attributes for output SPAN tags.
      inlinestyle (bool, optional): Add :code:`display:inline-block` as inline
                                    style attribute.

    Returns:
      A dictionary containing :code:`chunks` (:obj:`budou.chunk.ChunkList`)
      and :code:`html_code` (str).
    """
    attributes = parse_attributes(attributes, classname, inlinestyle)
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
    cache_filename (string, optional): the path to the cache file.
    credentials_path (string, optional): the path to the service
        account's credentials file.
    use_entity (bool, optional): Whether to use entity analysis
      results to wrap entity names in the output.
    use_cache (bool, optional): Whether to use a cache system.
    service (:obj:`googleapiclient.discovery.Resource`, optional): A Resource
      object for interacting with Cloud Natural Language API. If this is
      given, the constructor skips the authentication process and use this
      service instead.

  Attributes:
    segmenter(:obj:`budou.nlapisegmenter.NLAPISegmenter`): Segmenter module.
  """

  def __init__(self, **options):
    self.segmenter = NLAPISegmenter(
        cache_filename=options.get('cache_filename', None),
        credentials_path=options.get('credentials_path', None),
        use_entity=options.get('use_entity', False),
        use_cache=options.get('use_cache', True),
        service=options.get('service', None),
        )


class MecabParser(Parser):
  """Parser built on Mecab Segmenter
  (:obj:`budou.mecabsegmenter.MecabSegmenter`).

  Attributes:
    segmenter(:obj:`budou.mecabsegmenter.MecabSegmenter`): Segmenter module.
  """

  def __init__(self):
    self.segmenter = MecabSegmenter()


class TinysegmenterParser(Parser):
  """Parser built on TinySegmenter Segmenter
  (:obj:`budou.tinysegmentersegmenter.TinysegmenterSegmenter`).

  Attributes:
    segmenter(:obj:`budou.tinysegmentersegmenter.TinysegmenterSegmenter`):
        Segmenter module.
  """

  def __init__(self):
    self.segmenter = TinysegmenterSegmenter()


def get_parser(segmenter, **options):
  """Gets a parser.

  Args:
    segmenter (str): Segmenter to use.
    options (dict, optional): Optional settings.

  Returns:
    Parser (:obj:`budou.parser.Parser`)

  Raises:
    ValueError: If unsupported segmenter is specified.
  """
  if segmenter == 'nlapi':
    return NLAPIParser(**options)
  elif segmenter == 'mecab':
    return MecabParser()
  elif segmenter == 'tinysegmenter':
    return TinysegmenterParser()
  else:
    raise ValueError('Segmenter {} is not supported.'.format(segmenter))

def parse_attributes(attributes=None, classname=None, inlinestyle=False):
  """Parses attributes,

  Args:
    attributes (dict): Input attributes.
    classname (str, optional): Class name of output SPAN tags.
    inlinestyle (bool, optional): Add :code:`display:inline-block` as inline
                                  style attribute.

  Returns:
    Parsed attributes. (dict)
  """
  if not attributes:
    attributes = {}
  attributes.setdefault('class', DEFAULT_CLASS_NAME)
  # If `classname` is specified, it overwrites `class` property in `attributes`.
  if classname:
    attributes['class'] = ' '.join(classname.split(','))
  if inlinestyle:
    styles = attributes['style'].split(';') if 'style' in attributes else []
    styles.append('display:inline-block')
    attributes['style'] = ';'.join(styles)
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
