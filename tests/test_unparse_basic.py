import xmldictify as x


def test_simple_root():
    # The declaration is always followed by a literal newline.
    assert x.unparse({"a": "text"}) == '<?xml version="1.0" encoding="utf-8"?>\n<a>text</a>'


def test_full_document_false_omits_declaration():
    assert x.unparse({"a": "text"}, full_document=False) == "<a>text</a>"


def test_attributes_and_text():
    result = x.unparse(
        {"text": {"@color": "red", "@stroke": "2", "#text": "This is a test"}},
        full_document=False,
    )
    assert result.startswith("<text ")
    assert 'color="red"' in result
    assert 'stroke="2"' in result
    assert result.endswith(">This is a test</text>")


def test_nested_elements():
    result = x.unparse({"a": {"b": "1", "c": "2"}}, full_document=False)
    assert result == "<a><b>1</b><c>2</c></a>"


def test_none_value_is_empty_element():
    result = x.unparse({"a": {"b": None}}, full_document=False)
    assert result == "<a><b></b></a>"


def test_short_empty_elements():
    result = x.unparse({"a": {"b": None}}, full_document=False, short_empty_elements=True)
    assert result == "<a><b/></a>"


def test_attribute_only_no_text():
    result = x.unparse({"a": {"@x": "1"}}, full_document=False)
    assert result == '<a x="1"></a>'


def test_text_escaping():
    result = x.unparse({"a": "<hi> & 'bye'"}, full_document=False)
    assert result == "<a>&lt;hi&gt; &amp; 'bye'</a>"


def test_attr_escaping_includes_whitespace_chars():
    result = x.unparse({"a": {"@x": "line1\nline2"}}, full_document=False)
    assert "&#10;" in result


def test_scalar_coercion():
    assert x.unparse({"a": 42}, full_document=False) == "<a>42</a>"
    # Booleans coerce to lowercase "true"/"false", not Python's str(bool).
    assert x.unparse({"a": True}, full_document=False) == "<a>true</a>"
    assert x.unparse({"a": False}, full_document=False) == "<a>false</a>"


def test_custom_attr_prefix_and_cdata_key():
    result = x.unparse(
        {"a": {"$x": "1", "_value": "text"}},
        full_document=False,
        attr_prefix="$",
        cdata_key="_value",
    )
    assert result == '<a x="1">text</a>'
