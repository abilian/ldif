from io import BytesIO

import pytest

import ldif
from tests.common import BYTES_OUT, DNS, RECORDS


class TestLDIFWriter:
    def setup_method(self):
        self.stream = BytesIO()
        self.writer = ldif.LDIFWriter(self.stream)

    def test_fold_line_10_n(self):
        self.writer._cols = 10
        self.writer._line_sep = b"\n"
        self.writer._fold_line(b"abcdefghijklmnopqrstuvwxyz")
        folded = b"abcdefghij\n klmnopqrs\n tuvwxyz\n"
        assert self.stream.getvalue() == folded

    def test_fold_line_12_underscore(self):
        self.writer._cols = 12
        self.writer._line_sep = b"__"
        self.writer._fold_line(b"abcdefghijklmnopqrstuvwxyz")
        folded = b"abcdefghijkl__ mnopqrstuvw__ xyz__"
        assert self.stream.getvalue() == folded

    def test_fold_line_oneline(self):
        self.writer._cols = 100
        self.writer._line_sep = b"\n"
        self.writer._fold_line(b"abcdefghijklmnopqrstuvwxyz")
        folded = b"abcdefghijklmnopqrstuvwxyz\n"
        assert self.stream.getvalue() == folded

    def test_needs_base64_encoding_forced(self):
        self.writer._base64_attrs = ["attr_type"]
        result = self.writer._needs_base64_encoding("attr_type", "attr_value")
        assert result

    def test_needs_base64_encoding_not_safe(self):
        result = self.writer._needs_base64_encoding("attr_type", "\r")
        assert result

    def test_needs_base64_encoding_safe(self):
        result = self.writer._needs_base64_encoding("attr_type", "abcABC123_+")
        assert not result

    def test_unparse_attr_base64(self):
        self.writer._unparse_attr("foo", "a\nb\nc")
        value = self.stream.getvalue()
        assert value == b"foo:: YQpiCmM=\n"

    def test_unparse_entry_record(self):
        self.writer._unparse_entry_record(RECORDS[0])
        value = self.stream.getvalue()
        assert value == (
            b"cn: Alison Alison\n"
            b"mail: alicealison@example.com\n"
            b"modifytimestamp: 4a463e9a\n"
            b"objectclass: top\n"
            b"objectclass: person\n"
            b"objectclass: organizationalPerson\n"
        )

    def test_unparse_changetype_add(self):
        self.writer._unparse_changetype(2)
        value = self.stream.getvalue()
        assert value == b"changetype: add\n"

    def test_unparse_changetype_modify(self):
        self.writer._unparse_changetype(3)
        value = self.stream.getvalue()
        assert value == b"changetype: modify\n"

    def test_unparse_changetype_other(self):
        with pytest.raises(ValueError):
            self.writer._unparse_changetype(4)
        with pytest.raises(ValueError):
            self.writer._unparse_changetype(1)

    def test_unparse(self):
        for i, record in enumerate(RECORDS):
            self.writer.unparse(DNS[i], record)
        value = self.stream.getvalue()
        assert value == BYTES_OUT

    def test_unparse_fail(self):
        with pytest.raises(TypeError):
            self.writer.unparse(DNS[0], "foo")

    def test_unparse_binary(self):
        self.writer.unparse("cn=Bjorn J Jensen", {"jpegPhoto": [b"\xf0\xf2\xf3"]})
        value = self.stream.getvalue()
        assert value == b"dn: cn=Bjorn J Jensen\njpegPhoto:: 8PLz\n\n"

    def test_unparse_unicode_dn(self):
        self.writer.unparse("cn=Björn J Jensen", {"foo": ["bar"]})
        value = self.stream.getvalue()
        assert value == b"dn:: Y249QmrDtnJuIEogSmVuc2Vu\nfoo: bar\n\n"

    def test_unparse_uniqode(self):
        self.writer.unparse("o=x", {"test": ["日本語"]})
        value = self.stream.getvalue()
        assert value == b"dn: o=x\ntest:: 5pel5pys6Kqe\n\n"
