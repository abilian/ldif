# ldif - parse and generate LDIF data (see [RFC 2849](https://tools.ietf.org/html/rfc2849)).

![Commit activity](https://img.shields.io/github/commit-activity/m/abilian/ldif)
![Code size in bytes](https://img.shields.io/github/languages/code-size/abilian/ldif)
![License](https://img.shields.io/github/license/abilian/ldif)
![Latest version](https://img.shields.io/pypi/v/ldif)
![PyPI Downloads](https://img.shields.io/pypi/dm/ldif)

This is a fork of the `ldif` module from
[python-ldap](http://www.python-ldap.org/) with python3/unicode support.

One of its benefits is that it's a pure-python package (you don't
depend on the `libldap2-dev` (or similar) package that needs to be
installed on your laptop / test machine / production server).

See the last entry in [changelog](https://github.com/abilian/ldif/blob/main/CHANGES.rst) for a more complete list of
differences.

This package only support Python 3 (\>= 3.7, actually).


## Usage

Parse LDIF from a file (or `BytesIO`):

```python
from ldif import LDIFParser
from pprint import pprint

parser = LDIFParser(open("data.ldif", "rb"))
for dn, record in parser.parse():
    print('got entry record: %s' % dn)
    pprint(record)
```

Write LDIF to a file (or `BytesIO`):

```python
from ldif import LDIFWriter

writer = LDIFWriter(open("data.ldif", "wb"))
writer.unparse("mail=alice@example.com", {
    "cn": ["Alice Alison"],
    "mail": ["alice@example.com"],
    "objectclass": ["top", "person"],
})
```


## Unicode support

The stream object that is passed to parser or writer must be an ascii
byte stream.

The spec allows to include arbitrary data in base64 encoding or via URL.
There is no way of knowing the encoding of this data. To handle this,
there are two modes:

By default, the `LDIFParser` will try to interpret all values as UTF-8
and leave only the ones that fail to decode as bytes. But you can also
pass an `encoding` of `None` to the constructor, in which case the
parser will not try to do any conversion and return bytes directly.
