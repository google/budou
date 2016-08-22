# Budou - CJK Line Break Organizer
Budou provides beautiful CJK typography for websites with meaningful line breaks.

East Asian Language text, aka CJK (Chinese Japanese and Korean), has some line breaking rules to provide beautiful typography.
However, this is non-trivial process which requires a large dictionary and consideration of syntactic and semantic constraints.
Budou automatically translates sentences into organized HTML code, with meaningful chunks wrapped in non-breaking markup
so as to semantically control line breaks.
Budou uses [Cloud Natural Language API](https://cloud.google.com/natural-language/) to parse the input sentence and concatenate
words to produce meaningful chunks utilizing PoS (part-of-speech) tagging and syntactic information.

## Setup
Install the library by running `python setup.py install`.
Also, a credential json file is needed for authorization to Cloud Natural Language API.

## How to use
```python
import budou
# Login to Cloud Natural Language API with credentials
parser = budou.login('/path/to/credentials.json')
result = parser.Process(u'今日も元気です', 'wordwrap')
print result['html_code']     # => "<span class="wordwrap">今日も</span><span class="wordwrap">元気です</span>"
print result['chunks'][0]     # => "Chunk(word='今日も', pos='NOUN', label='NN', forward=True)"
print result['chunks'][1]     # => "Chunk(word='元気です', pos='NOUN', label='ROOT', forward=False)]"

```


## Author
Shuhei Iitsuka

- Website: https://tushuhei.com
- Twitter: https://twitter.com/tushuhei


Disclaimer
----------

This library is authored by a Googler and copyrighted by Google, but
is not an official Google product.


License
-------

Copyright 2016 Google Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
