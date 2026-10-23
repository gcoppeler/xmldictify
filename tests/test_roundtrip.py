"""Round-trip tests: parse(unparse(x)) == x, for cases documented as
round-trip-safe. expand_iter and attribute/mixed-content ordering are
explicitly excluded, matching upstream xmltodict's own caveats.
"""

import xmldictify as x


def _roundtrip(doc, **kwargs):
    return x.parse(x.unparse(doc, **kwargs))


def test_simple_text_roundtrip():
    doc = {"a": "hello"}
    assert _roundtrip(doc) == doc


def test_nested_roundtrip():
    doc = {"a": {"b": "1", "c": "2"}}
    assert _roundtrip(doc) == doc


def test_attributes_roundtrip():
    doc = {"a": {"@x": "1", "#text": "hi"}}
    assert _roundtrip(doc) == doc


def test_list_roundtrip():
    doc = {"a": {"b": ["1", "2", "3"]}}
    assert _roundtrip(doc) == doc


def test_empty_element_roundtrip():
    doc = {"a": {"b": None}}
    assert _roundtrip(doc) == doc


def test_deeply_nested_roundtrip():
    doc = {"a": {"b": {"c": {"d": "deep"}}}}
    assert _roundtrip(doc) == doc


def test_mixed_list_and_scalar_roundtrip():
    doc = {"root": {"item": [{"@id": "1", "#text": "x"}, {"@id": "2", "#text": "y"}]}}
    assert _roundtrip(doc) == doc
