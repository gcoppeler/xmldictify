import xmldictify as x


def test_leaf_text():
    assert x.parse("<a>hello</a>") == {"a": "hello"}


def test_nested_elements():
    assert x.parse("<a><b>1</b><c>2</c></a>") == {"a": {"b": "1", "c": "2"}}


def test_repeated_siblings_become_list():
    assert x.parse("<a><b>1</b><b>2</b></a>") == {"a": {"b": ["1", "2"]}}


def test_three_repeated_siblings_stay_a_list():
    assert x.parse("<a><b>1</b><b>2</b><b>3</b></a>") == {"a": {"b": ["1", "2", "3"]}}


def test_empty_element_is_none():
    assert x.parse("<a><b/></a>") == {"a": {"b": None}}
    assert x.parse("<a><b></b></a>") == {"a": {"b": None}}


def test_whitespace_only_text_collapses_with_default_strip():
    assert x.parse("<a>\n  <b>1</b>\n</a>") == {"a": {"b": "1"}}


def test_strip_whitespace_false_preserves_text():
    result = x.parse("<a>  padded  </a>", strip_whitespace=False)
    assert result == {"a": "  padded  "}


def test_cdata_separator_joins_fragments():
    # A comment forces expat to flush its text buffer, so "one" and "two"
    # arrive as two separate CharacterDataHandler calls to join.
    xml = "<a>one<!-- c -->two</a>"
    result = x.parse(xml, cdata_separator="-", process_comments=True, comment_key="_c")
    assert result == {"a": {"_c": "c", "#text": "one-two"}}


def test_bytes_input():
    assert x.parse(b"<a>hi</a>") == {"a": "hi"}


def test_file_like_input():
    import io

    f = io.StringIO("<a><b>1</b></a>")
    assert x.parse(f) == {"a": {"b": "1"}}


def test_generator_of_chunks_input():
    def gen():
        yield "<a>"
        yield "<b>1</b>"
        yield "</a>"

    assert x.parse(gen()) == {"a": {"b": "1"}}


def test_malformed_xml_raises():
    import pytest
    from xml.parsers.expat import ExpatError

    with pytest.raises(ExpatError):
        x.parse("<a><b></a>")
