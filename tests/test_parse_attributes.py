import xmldictify as x


def test_attribute_only_element():
    assert x.parse('<a has="an attribute"/>') == {"a": {"@has": "an attribute"}}


def test_attribute_and_text():
    result = x.parse('<plus a="complex">element as well</plus>')
    assert result == {"plus": {"@a": "complex", "#text": "element as well"}}


def test_xml_attribs_false_drops_attributes():
    result = x.parse('<a x="1">text</a>', xml_attribs=False)
    assert result == {"a": "text"}


def test_custom_attr_prefix():
    result = x.parse('<a x="1">text</a>', attr_prefix="$")
    assert result == {"a": {"$x": "1", "#text": "text"}}


def test_custom_cdata_key():
    result = x.parse('<a x="1">text</a>', cdata_key="_value")
    assert result == {"a": {"@x": "1", "_value": "text"}}


def test_multiple_attributes():
    result = x.parse('<a x="1" y="2"/>')
    assert result == {"a": {"@x": "1", "@y": "2"}}
