import unittest
from pprint import pprint
from unittest import mock

from io import BytesIO

from pytest import fixture

import ldif


BYTES = b"""version: 1
dn: cn=Alice Alison,
 mail=alicealison@example.com
objectclass: top
objectclass: person
objectclass: organizationalPerson
cn: Alison Alison
mail: alicealison@example.com
modifytimestamp: 4a463e9a

# another person
dn: mail=foobar@example.org
objectclass: top
objectclass:  person
mail: foobar@example.org
modifytimestamp: 4a463e9a
"""

BYTES_SPACE = b"\n\n".join([block + b"\n" for block in BYTES.split(b"\n\n")])

BYTES_OUT = b"""dn: cn=Alice Alison,mail=alicealison@example.com
cn: Alison Alison
mail: alicealison@example.com
modifytimestamp: 4a463e9a
objectclass: top
objectclass: person
objectclass: organizationalPerson

dn: mail=foobar@example.org
mail: foobar@example.org
modifytimestamp: 4a463e9a
objectclass: top
objectclass: person

"""

BYTES_EMPTY_ATTR_VALUE = b"""dn: uid=foo123,dc=ws1,dc=webhosting,o=eim
uid: foo123
domainname: foo.bar
homeDirectory: /foo/bar.local
aliases:
aliases: foo.bar
"""

LINES = [
    b"version: 1",
    b"dn: cn=Alice Alison,mail=alicealison@example.com",
    b"objectclass: top",
    b"objectclass: person",
    b"objectclass: organizationalPerson",
    b"cn: Alison Alison",
    b"mail: alicealison@example.com",
    b"modifytimestamp: 4a463e9a",
    b"",
    b"dn: mail=foobar@example.org",
    b"objectclass: top",
    b"objectclass:  person",
    b"mail: foobar@example.org",
    b"modifytimestamp: 4a463e9a",
]

BLOCKS = [
    [
        b"version: 1",
        b"dn: cn=Alice Alison,mail=alicealison@example.com",
        b"objectclass: top",
        b"objectclass: person",
        b"objectclass: organizationalPerson",
        b"cn: Alison Alison",
        b"mail: alicealison@example.com",
        b"modifytimestamp: 4a463e9a",
    ],
    [
        b"dn: mail=foobar@example.org",
        b"objectclass: top",
        b"objectclass:  person",
        b"mail: foobar@example.org",
        b"modifytimestamp: 4a463e9a",
    ],
]

DNS = ["cn=Alice Alison,mail=alicealison@example.com", "mail=foobar@example.org"]

CHANGETYPES = [None, None]

RECORDS = [
    {
        "cn": ["Alison Alison"],
        "mail": ["alicealison@example.com"],
        "modifytimestamp": ["4a463e9a"],
        "objectclass": ["top", "person", "organizationalPerson"],
    },
    {
        "mail": ["foobar@example.org"],
        "modifytimestamp": ["4a463e9a"],
        "objectclass": ["top", "person"],
    },
]

URL = b"https://tools.ietf.org/rfc/rfc2849.txt"
URL_CONTENT = "The LDAP Data Interchange Format (LDIF)"
