import xmldictify as x


def test_pretty_default_tab_indent():
    # Exactly one trailing newline is stripped from the very end of output.
    result = x.unparse({"a": {"b": "1"}}, pretty=True, full_document=False)
    assert result == "<a>\n\t<b>1</b>\n</a>"


def test_pretty_custom_indent_and_newl():
    result = x.unparse(
        {"a": {"b": "1"}}, pretty=True, full_document=False, indent="  ", newl="|"
    )
    assert result == "<a>|  <b>1</b>|</a>"


def test_pretty_int_indent_means_spaces():
    result = x.unparse({"a": {"b": "1"}}, pretty=True, full_document=False, indent=4)
    assert result == "<a>\n    <b>1</b>\n</a>"


def test_pretty_leaf_text_stays_inline():
    result = x.unparse({"a": "hello"}, pretty=True, full_document=False)
    assert result == "<a>hello</a>"
