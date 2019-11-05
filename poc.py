import html5lib
from html5lib import getTreeWalker
from html5lib.filters import sanitizer
from html5lib.constants import namespaces, prefixes
content = '<span>This is <wbr> not a cat</span>'
dom = html5lib.parseFragment(content)
treewalker = getTreeWalker('etree')
serializer = html5lib.serializer.HTMLSerializer()
stream = treewalker(dom)
output = serializer.render(sanitizer.Filter(stream, allowed_elements=set([(namespaces['html'], 'span')])))
print(output)
