Budou
========

.. image:: https://badge.fury.io/py/budou.svg
   :target: https://badge.fury.io/py/budou

.. image:: https://travis-ci.org/google/budou.svg?branch=master
   :target: https://travis-ci.org/google/budou

English uses spacing and hyphenation as cues to allow for beautiful and legible
line breaks. Certain CJK languages have none of these, and are notoriously more
difficult.  Breaks occur randomly, usually in the middle of a word.  This is a
long standing issue in typography on web, and results in degradation of
readability.

Budou automatically translates CJK sentences into organized HTML code with
lexical chunks wrapped in non-breaking markup so as to semantically control line
breaks. Budou uses word segmenter to analyze the input sentence, and it
concatenates proper words in order to produce meaningful chunks utilizing
part-of-speech (pos) tagging and syntactic information. Processed chunks are
wrapped with :code:`SPAN` tag, so semantic units will no longer be split at
the end of a line by specifying their :code:`display` property as
:code:`inline-block` in CSS.


Installation
--------------

The package is listed in the Python Package Index (PyPI), so you can install it
with pip:

.. code-block:: sh

   $ pip install budou


How to use
--------------

Budou outputs a HTML snippet wrapping chunks with :code:`span` tags. Semantic
chunks in the output HTML will not be split at the end of line by conditioning
each :code:`span` tag with :code:`display: inline-block` in CSS.

.. code-block:: css

   .chunk {
     display: inline-block;
   }


Using as a command-line app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can process your texts by running :code:`budou` command like below.

.. code-block:: sh

   $ budou 渋谷のカレーを食べに行く。

The output is:

.. code-block:: html

   <span><span class="ww">渋谷の</span><span class="ww">カレーを</span>
   <span class="ww">食べに</span><span class="ww">行く。</span></span>

You can also configure the command  passing parameters (e.g. backend segmenter,
class name etc.). If not specified,
`Google Cloud Natural Language API <https://cloud.google.com/natural-language/>`_
is used as the backend segmenter.

.. code-block:: sh

   $ budou 渋谷のカレーを食べに行く。 --segmenter=mecab --classname=wordwrap

The output is:

.. code-block:: html

   <span><span class="wordwrap">渋谷の</span><span class="wordwrap">カレーを</span>
   <span class="wordwrap">食べに</span><span class="wordwrap">行く。</span></span>

Run help command :code:`budou -h` to see available options.


Using programmatically
~~~~~~~~~~~~~~~~~~~~~~~~~

You can use :code:`budou.parse` method for handy processing.

.. code-block:: python

   import budou
   results = budou.parse('渋谷のカレーを食べに行く。')
   print(results['html_code'])
   # <span><span class="ww">渋谷の</span><span class="ww">カレーを</span>
   # <span class="ww">食べに</span><span class="ww">行く。</span></span>


You can also make a parser instance to reuse the segmenter backend with the same
configuration. If you want to integrate Budou into your web framework in a form
of a custom filter or a build process, this would be the way to go.

.. code-block:: python

   import budou
   parser = budou.get_parser(segmenter='mecab')
   results = parser.parse('渋谷のカレーを食べに行く。')
   print(results['html_code'])
   # <span><span class="ww">渋谷の</span><span class="ww">カレーを</span>
   # <span class="ww">食べに</span><span class="ww">行く。</span></span>

   for chunk in results['chunks']:
     print(chunk.word)
   # 渋谷の 名詞
   # カレーを 名詞
   # 食べに 動詞
   # 行く。 動詞


How it works
--------------

.. image:: https://raw.githubusercontent.com/wiki/google/budou/images/nexus_example.jpeg


Available backend segmenters
------------------------------

You can choose the backend segmenter to use considering your environmental
needs.

Google Cloud Natural Language API Segmenter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Natural Language API (NL API) analyzes the input sentence using machine learning
technology. The API can extract not only syntax but also entities included in
the sentence, which can be used for better quality segmentation. Since this is
a simple REST API, you don't need to maintain the dictionary and can support
multiple languages with one single resource.

Supported languages
++++++++++++++++++++++

- Japanese (ja)
- Simplified Chinese (zh)
- Traditional Chinese (zh-Hant)

Authentication
+++++++++++++++

NL API requires authentication to use. Firstly, create a Google Cloud Platform
project and enable Cloud Natural Language API. Billing also need to be enabled
for the project. Then, download a credentials file for a service account by
accessing `Google Cloud Console <https://console.cloud.google.com/>`_
and navigating through "API & Services" > "Credentials" > "Create credentials" >
"Service account key" > "JSON".

Budou will handle authentication once the path to the credentials file is set
as :code:`GOOGLE_APPLICATION_CREDENTIALS` environment variable.

.. code-block:: sh

   $ export GOOGLE_APPLICATION_CREDENTIALS='/path/to/credentials.json'

You can also pass the path to the credentials file when you initialize the
parser.

.. code-block:: python

   parser = budou.get_parser(
       'nlapi', credentials_path='/path/to/credentials.json')

Natural Language API segmenter uses *Syntax Analysis* and incurs cost according
to monthly usage. Google Cloud Natural Language API has free quota to start
testing the feature at free of cost. Please refer to
https://cloud.google.com/natural-language/pricing for more detailed pricing
information.

Caching system
++++++++++++++++

When on Cloud Natural Language API backend, Budou caches responses from the API
in order to save unnecessary requests to NL API and make the processing faster.
If you want to force refresh the cache, set :code:`use_cache` as :code:`False`.

.. code-block:: python

   parser = budou.parse('明日は晴れるかな', segmenter='nlapi', use_cache=False)

In `Google App Engine Python 2.7 Standard Environment <https://cloud.google.com/appengine/docs/standard/python/>`_,
Budou tries to use
`memcache <https://cloud.google.com/appengine/docs/standard/python/memcache/>`_
service cache the output efficiently across instances.
If not, Budou creates a cache file in
`python pickle <https://docs.python.org/3/library/pickle.html>`_ format.

Entity mode
++++++++++++++++++

Default parser only uses results from Syntactic Analysis for parsing, but you
can also utilize *Entity Analysis* by specifying `use_entity=True`.
Entity Analysis will improve the accuracy of parsing for some phrases,
especially proper nouns, so it is recommended to use if your target sentences
include a name of an individual person, place, organization etc.

Please note that Entity Analysis will results in additional pricing because it
requires additional requests to NL API. For more detail about API pricing, please
refer to https://cloud.google.com/natural-language/pricing for more detail.

.. code-block:: python

  import budou
  # Without Entity mode (default)
  result = budou.parse('六本木ヒルズでご飯を食べます。', use_entity=False)
  print(result['html_code'])
  # <span class="ww">六本木</span><span class="ww">ヒルズに</span><span class="ww">います。</span>

  # With Entity mode
  result = budou.parse('六本木ヒルズでご飯を食べます。', use_entity=True)
  print(result['html_code'])
  # <span class="ww">六本木ヒルズに</span><span class="ww">います。</span>


Mecab Segmenter
~~~~~~~~~~~~~~~~~~~~~~~

TODO

Is Korean supported?
-----------------------

Korean has spaces between chunks, so you can organize line breaking simply by
putting `word-break: keep-all` in your CSS. We recommend you to use that
technique instead of using Budou.


Where to use
---------------

Budou is designed to be used mostly in eye-catching sentences such as titles
and headings assuming split chunks would be more stood out negatively in larger
typography.


Maximum chunk length
-----------------------

Some words (マルチスクリーン, インフルエンザ, etc) may stand out in certain
formats due to their length. For example:

    これが
    マルチスクリーン
    です。

By using :code:`max_length=6` in conjunction with code:`display: inline-block`
styling on the output :code:`span` tags this can be avoided:

    これがマルチス
    クリーンです。

The output would instead look like this.

.. code-block:: html

   <span class="ww">これが</span>マルチスクリーン<span class="ww">です。</span>


Accessibility
-------------------

Some screen reader software read wrapped chunks one by one when Budou is
applied, which may degrades user experience for those who need audio support.
You can attach any attribute to the output chunks to enhance accessibility.
For example, you can make screen readers to read undivided sentences by
combining `aria-describedby` and `aria-label` attribute in the output.

TODO


Author
----------

Shuhei Iitsuka

- Website: https://tushuhei.com
- Twitter: https://twitter.com/tushuhei


Disclaimer
-----------------

This library is authored by a Googler and copyrighted by Google, but is not an
official Google product.


License
-----------

Copyright 2017 Google Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
