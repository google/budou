# Budou - Automatic CJK line breaking tool
[![Build Status](https://travis-ci.org/google/budou.svg?branch=master)](https://travis-ci.org/google/budou)

English uses spacing and hyphenation as cues to allow for beautiful line breaks.
Some of CJK languages, which has none of these, are notoriously more difficult.
Breaks occur randomly, usually in the middle of a word.
This is a long standing issue in typography on web, and results in degradation of readability.

Budou automatically translates CJK sentences into organized HTML code with meaningful chunks wrapped in non-breaking markup
so as to semantically control line breaks.
Budou uses [Cloud Natural Language API](https://cloud.google.com/natural-language/) (NL API) to analyze the input sentence,
and it concatenates proper words in order to produce meaningful chunks utilizing part-of-speech (pos) tagging and syntactic information.

Budou outputs HTML code by wrapping the chunks with `SPAN` tag.
By specifying their `display` property as `inline-block` in CSS, semantic units will no longer be split at the end of a line.

Budou supports only Japanese and Korean currently, but support for other Asian languages with line break issues, such as Chinese and Thai,
will be added as Cloud Natural Language API adds support.


## Setup
Install the library by running ` pip install budou`.

Also, a credential json file is needed for authorization to Cloud Natural Language API.

## How to use
### Japanse
Japanese needs a request to NL API, so a credential file is needed for authentication.

```python
import budou
# Login to Cloud Natural Language API with credentials
parser = budou.authenticate('/path/to/credentials.json')
result = parser.parse(u'今日も元気です', {'class': 'wordwrap'}, language='ja')

print result['html_code']  # => "<span class="wordwrap">今日も</span><span class="wordwrap">元気です</span>"

print result['chunks'][0]  # => "Chunk(word='今日も', pos='NOUN', label='NN', forward=True)"
print result['chunks'][1]  # => "Chunk(word='元気です', pos='NOUN', label='ROOT', forward=False)]"
```

### Korean
Korean is processed by separating words by spaces, so no credential file is needed.

```python
import budou
parser = budou.authenticate()
result = parser.parse(u'오늘은 날씨가 좋습니다.', {'class': 'wordwrap'}, language='ko')

print result['html_code']  # => "<span class="wordwrap">오늘은</span> <span class="wordwrap">날씨가</span> <span class="wordwrap">좋습니다.</span>"
```

Semantic units in the output HTML will not be split at the end of line by conditioning each `SPAN` tag with `display: inline-block` in CSS.

```html
<span class="wordwrap">今日も</span><span class="wordwrap">元気です</span>
<span class="wordwrap">오늘은</span> <span class="wordwrap">날씨가</span> <span class="wordwrap">좋습니다.</span>
```

```css
.wordwrap {
  display: inline-block;
}
```


## How it works
![Nexus Example Image](https://raw.githubusercontent.com/wiki/google/budou/images/nexus_example.jpeg)


## Supported Language
- Japanese
- Korean

Support for other Asian languages with line break issues, such as Chinese and Thai, will be added as Cloud Natural Language API adds support.


## Author
Shuhei Iitsuka

- Website: https://tushuhei.com
- Twitter: https://twitter.com/tushuhei


## Disclaimer
This library is authored by a Googler and copyrighted by Google, but
is not an official Google product.


## License
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
