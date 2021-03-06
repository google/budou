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

"""Budou: an automatic organizer tool for beautiful line breaking in CJK

Usage:
  budou [--segmenter=<seg>] [--language=<lang>] [--separator=<separator>] [--classname=<class>] [--inlinestyle] [--wbr] [<source>]
  budou -h | --help
  budou -v | --version


Options:
  -h --help                   Show this screen.

  -v --version                Show version.

  --segmenter=<segmenter>     Segmenter to use [default: nlapi].

  --language=<language>       Language the source in.

  --separator=<separator>     Custom separator instead of SPAN tags, when used
                              classname and inlinestyle are ignored

  --classname=<classname>     Class name for output SPAN tags. Use
                              comma-separated value to specify multiple classes.

  --inlinestyle               Add :code:`display:inline-block` as inline style
                              attribute.

  --wbr                       User WBR tag for serialization instead of
                              inline-block SPAN tags.
"""

from __future__ import print_function

import sys
import warnings
from docopt import docopt
from .parser import get_parser
from .__version__ import __version__


def main():
  """Budou main method for the command line tool.
  """
  args = docopt(__doc__)
  if args['--version']:
    print(__version__)
    sys.exit()

  if args['<source>']:
    source = args['<source>']
  elif not sys.stdin.isatty():
    source = sys.stdin.read()
  else:
    print(__doc__.split("\n\n")[1])
    sys.exit()

  result = parse(
      source,
      segmenter=args['--segmenter'],
      language=args['--language'],
      classname=args['--classname'],
      inlinestyle=args['--inlinestyle'],
      wbr=args['--wbr'],
      )

  if args['--separator']:
    output = result['chunks'].separator_serialize(args['--separator'])
  else:
    output = result['html_code']
    
  if not isinstance(output, str):
    output = output.encode('utf-8')
  print(output)

  sys.exit()

def parse(source, segmenter='nlapi', language=None, max_length=None,
          classname=None, attributes=None, inlinestyle=False, wbr=False,
          **kwargs):
  """Parses input source.

  Args:
    source (str): Input source to process.
    segmenter (str, optional): Segmenter to use [default: nlapi].
    language (str, optional): Language code.
    max_length (int, optional): Maximum length of a chunk.
    classname (str, optional): Class name of output SPAN tags.
    attributes (dict, optional): Attributes for output SPAN tags.
    inlinestyle (bool, optional): Add :code:`display:inline-block` as inline
                                  style attribute.
    wbr (bool, optional): User WBR tag for serialization.

  Returns:
    Results in a dict. :code:`chunks` holds a list of chunks
    (:obj:`budou.chunk.ChunkList`) and :code:`html_code` holds the output HTML
    code.
  """
  parser = get_parser(segmenter, **kwargs)
  return parser.parse(
      source, language=language, max_length=max_length, classname=classname,
      attributes=attributes, inlinestyle=inlinestyle, wbr=wbr)

def authenticate(json_path=None):
  """Gets a Natural Language API parser by authenticating the API.

  **This method is deprecated.** Please use :obj:`budou.parser.get_parser` to
  obtain a parser instead.

  Args:
    json_path (str, optional): The file path to the service account's
        credentials.

  Returns:
    Parser. (:obj:`budou.parser.NLAPIParser`)

  """
  msg = ('budou.authentication() is deprecated. '
         'Please use budou.parser.get_parser() to obtain a parser instead.')
  warnings.warn(msg, DeprecationWarning)
  parser = get_parser('nlapi', credentials_path=json_path)
  return parser

if __name__ == '__main__':
  main()
