from io import BytesIO
from unittest import mock, skip

import pytest

import ldif
from tests.common import (
    BLOCKS,
    BYTES,
    BYTES_EMPTY_ATTR_VALUE,
    BYTES_SPACE,
    DNS,
    LINES,
    RECORDS,
    URL,
    URL_CONTENT,
)


class TestUnsafeString:
    unsafe_chars = ["\0", "\n", "\r"]
    unsafe_chars_init = unsafe_chars + [" ", ":", "<"]

    def _test_all(self, unsafes, fn):
        for i in range(128):  # TODO: test range(255)
            try:
                match = ldif.UNSAFE_STRING_RE.search(fn(i))
                if i <= 127 and chr(i) not in unsafes:
                    assert match is None
                else:
                    assert match is not None
            except AssertionError:
                print(i)
                raise

    def test_unsafe_chars(self):
        self._test_all(self.unsafe_chars, lambda i: f"a{chr(i)}")

    def test_unsafe_chars_init(self):
        self._test_all(self.unsafe_chars_init, lambda i: f"{chr(i)}")

    def test_example(self):
        s = "cn=Alice, Alison,mail=Alice.Alison@example.com"
        assert ldif.UNSAFE_STRING_RE.search(s) is None

    def test_trailing_newline(self):
        assert ldif.UNSAFE_STRING_RE.search("asd\n") is not None


class TestLower:
    def test_happy(self):
        assert ldif.lower(["ASD", "HuHu"]) == ["asd", "huhu"]

    def test_falsy(self):
        assert ldif.lower(None) == []

    def test_dict(self):
        assert ldif.lower({"Foo": "bar"}) == ["foo"]

    def test_set(self):
        assert ldif.lower({"FOo"}) == ["foo"]


class TestIsDn:
    def test_happy(self):
        pass  # TODO


class TestLDIFParser:
    def setup_method(self):
        self.stream = BytesIO(BYTES)
        self.parser = ldif.LDIFParser(self.stream)

    def test_strip_line_sep(self):
        assert self.parser._strip_line_sep(b"asd \n") == b"asd "
        assert self.parser._strip_line_sep(b"asd\t\n") == b"asd\t"
        assert self.parser._strip_line_sep(b"asd\r\n") == b"asd"
        assert self.parser._strip_line_sep(b"asd\r\t\n") == b"asd\r\t"
        assert self.parser._strip_line_sep(b"asd\n\r") == b"asd\n\r"
        assert self.parser._strip_line_sep(b"asd") == b"asd"
        assert self.parser._strip_line_sep(b"  asd  ") == b"  asd  "

    def test_iter_unfolded_lines(self):
        assert list(self.parser._iter_unfolded_lines()) == LINES

    def test_iter_blocks(self):
        assert list(self.parser._iter_blocks()) == BLOCKS

    def test_iter_blocks_with_additional_spaces(self):
        self.stream = BytesIO(BYTES_SPACE)
        self.parser = ldif.LDIFParser(self.stream)
        assert list(self.parser._iter_blocks()) == BLOCKS

    def _test_error(self, fn):
        self.parser._strict = True
        with pytest.raises(ValueError):
            fn()

        with mock.patch("ldif.log.warning") as warning:
            self.parser._strict = False
            fn()
            assert warning.called

    def test_check_dn_not_none(self):
        self._test_error(
            lambda: self.parser._check_dn("some dn", "mail=alicealison@example.com")
        )

    def test_check_dn_invalid(self):
        self._test_error(lambda: self.parser._check_dn(None, "invalid"))

    def test_check_dn_happy(self):
        self.parser._check_dn(None, "mail=alicealison@example.com")

    def test_check_changetype_dn_none(self):
        self._test_error(lambda: self.parser._check_changetype(None, None, "add"))

    def test_check_changetype_not_none(self):
        self._test_error(
            lambda: self.parser._check_changetype("some dn", "some changetype", "add")
        )

    def test_check_changetype_invalid(self):
        self._test_error(
            lambda: self.parser._check_changetype("some dn", None, "invalid")
        )

    def test_check_changetype_happy(self):
        self.parser._check_changetype("some dn", None, "add")

    def test_parse_attr_base64(self):
        attr_type, attr_value = self.parser._parse_attr(b"foo:: YQpiCmM=\n")
        assert attr_type == "foo"
        assert attr_value == "a\nb\nc"

    @skip("Don't call external URLs in tests")
    def test_parse_attr_url(self):
        self.parser._process_url_schemes = [b"https"]
        line = b"foo:< " + URL + b"\n"
        attr_type, attr_value = self.parser._parse_attr(line)
        assert URL_CONTENT in attr_value

    def test_parse_attr_url_all_ignored(self):
        attr_type, attr_value = self.parser._parse_attr(b"foo:< " + URL + b"\n")
        assert attr_value == ""

    def test_parse_attr_url_this_ignored(self):
        self.parser._process_url_schemes = [b"file"]
        attr_type, attr_value = self.parser._parse_attr(b"foo:< " + URL + b"\n")
        assert attr_value == ""

    def test_parse_attr_dn_non_utf8(self):
        def run():
            attr = (
                b"dn: \x75\x69\x64\x3d\x6b\x6f\xb3\x6f\x62"
                b"\x69\x7a\x6e\x65\x73\x75\x40\x77\n"
            )
            attr_type, attr_value = self.parser._parse_attr(attr)
            assert attr_type == "dn"
            assert attr_value == "uid=koobiznesu@w"

        self._test_error(run)

    def test_parse(self):
        items = list(self.parser.parse())
        for i, item in enumerate(items):
            dn, record = item

            assert dn == DNS[i]
            assert record == RECORDS[i]

    def test_parse_binary(self):
        self.stream = BytesIO(b"dn: cn=Bjorn J Jensen\njpegPhoto:: 8PLz\nfoo: bar")
        self.parser = ldif.LDIFParser(self.stream)
        items = list(self.parser.parse())
        assert items == [
            (
                "cn=Bjorn J Jensen",
                {
                    "jpegPhoto": [b"\xf0\xf2\xf3"],
                    "foo": ["bar"],
                },
            )
        ]

    def test_parse_binary_raw(self):
        self.stream = BytesIO(b"dn: cn=Bjorn J Jensen\njpegPhoto:: 8PLz\nfoo: bar")
        self.parser = ldif.LDIFParser(self.stream, encoding=None)
        items = list(self.parser.parse())
        assert items == [
            (
                "cn=Bjorn J Jensen",
                {
                    "jpegPhoto": [b"\xf0\xf2\xf3"],
                    "foo": [b"bar"],
                },
            )
        ]


class TestLDIFParserEmptyAttrValue:
    def setup_method(self):
        self.stream = BytesIO(BYTES_EMPTY_ATTR_VALUE)
        self.parser = ldif.LDIFParser(self.stream)

    def test_parse(self):
        list(self.parser.parse())

    def test_parse_value(self):
        dn, record = list(self.parser.parse())[0]

        assert record["aliases"] == ["", "foo.bar"]
