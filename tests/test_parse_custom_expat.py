from xml.parsers.expat import ExpatError, ParserCreate

import pytest

import xmldictify as x


class _CustomExpat:
    """A pluggable expat-module stand-in, mirroring the shape (ParserCreate +
    ExpatError) that parse(expat=...) expects."""

    def __init__(self, external_entity_result):
        self.external_entity_result = external_entity_result

    def ParserCreate(self, *args, **kwargs):
        parser = ParserCreate(*args, **kwargs)
        parser.ExternalEntityRefHandler = lambda *a, **kw: self.external_entity_result
        return parser

    ExpatError = ExpatError


XML = """
<!DOCTYPE external [
    <!ENTITY ee SYSTEM "http://example.invalid/">
]>
<root>&ee;</root>
"""


def test_custom_expat_module_is_used():
    with pytest.raises(ExpatError):
        x.parse(XML, disable_entities=False, expat=_CustomExpat(0))
    assert x.parse(XML, disable_entities=False, expat=_CustomExpat(1)) == {"root": None}


def test_disable_entities_overrides_custom_expat_handler():
    # disable_entities=True must win even when a custom expat module
    # already wired up its own (permissive) ExternalEntityRefHandler.
    with pytest.raises(ValueError):
        x.parse(XML, disable_entities=True, expat=_CustomExpat(1))
