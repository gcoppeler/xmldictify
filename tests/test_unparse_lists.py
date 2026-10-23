import xmldictify as x


def test_list_becomes_repeated_siblings():
    result = x.unparse({"a": {"b": ["1", "2"]}}, full_document=False)
    assert result == "<a><b>1</b><b>2</b></a>"


def test_empty_list_emits_nothing():
    result = x.unparse({"a": {"b": []}}, full_document=False)
    assert result == "<a></a>"


def test_single_empty_string_in_list_forces_empty_element():
    result = x.unparse({"a": {"b": [""]}}, full_document=False)
    assert result == "<a><b></b></a>"


def test_nested_list_without_expand_iter_stringifies():
    result = x.unparse({"line": {"points": [[1, 5], [2, 6]]}}, full_document=False)
    assert result == "<line><points>[1, 5]</points><points>[2, 6]</points></line>"


def test_nested_list_with_expand_iter():
    result = x.unparse(
        {"line": {"points": [[1, 5], [2, 6]]}}, full_document=False, expand_iter="coord"
    )
    assert result == (
        "<line>"
        "<points><coord>1</coord><coord>5</coord></points>"
        "<points><coord>2</coord><coord>6</coord></points>"
        "</line>"
    )
