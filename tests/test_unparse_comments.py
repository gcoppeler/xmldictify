import xmldictify as x


def test_element_comment():
    obj = {"a": {"#comment": "note", "b": "1"}}
    assert x.unparse(obj, full_document=False) == "<a><!--note--><b>1</b></a>"


def test_multiple_element_comments():
    obj = {"a": {"#comment": ["n1", "n2"], "b": "1"}}
    assert x.unparse(obj, full_document=False) == "<a><!--n1--><!--n2--><b>1</b></a>"


def test_top_level_comment():
    obj = {"#comment": "top", "a": "1"}
    assert x.unparse(obj, full_document=False) == "<!--top--><a>1</a>"


def test_none_and_empty_comments_are_skipped():
    assert x.unparse({"a": {"#comment": None, "b": "1"}}, full_document=False) == "<a><b>1</b></a>"
    assert x.unparse({"a": {"#comment": "", "b": "1"}}, full_document=False) == "<a><b>1</b></a>"


def test_comment_with_double_hyphen_rejected():
    import pytest

    with pytest.raises(ValueError, match="cannot contain '--'"):
        x.unparse({"a": {"#comment": "bad--comment", "b": "1"}}, full_document=False)


def test_comment_ending_with_hyphen_rejected():
    import pytest

    with pytest.raises(ValueError, match="cannot end with '-'"):
        x.unparse({"a": {"#comment": "trailing-", "b": "1"}}, full_document=False)


def test_parse_unparse_comment_roundtrip():
    xml = "<a><b>1</b><!--e1--></a>"
    parsed = x.parse(xml, process_comments=True)
    assert parsed == {"a": {"b": "1", "#comment": "e1"}}
    reparsed = x.parse(x.unparse(parsed), process_comments=True)
    assert reparsed == parsed


def test_toplevel_comments_captured_on_parse():
    xml = "<!--top1--><a><b>1</b></a><!--top2-->"
    result = x.parse(xml, process_comments=True)
    assert set(result["#comment"]) == {"top1", "top2"}
    assert result["a"] == {"b": "1"}
