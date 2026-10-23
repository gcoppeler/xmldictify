import xmldictify as x

# root=depth1, list=depth2, artist=depth3, name=depth4
XML = (
    "<root><list>"
    "<artist><name>A</name></artist>"
    "<artist><name>B</name></artist>"
    "<artist><name>C</name></artist>"
    "</list></root>"
)


def test_item_depth_zero_is_full_document_mode():
    calls = []

    def cb(path, item):
        calls.append((path, item))
        return True

    result = x.parse("<a><b>1</b></a>", item_callback=cb)
    assert result == {"a": {"b": "1"}}
    assert calls == []  # item_callback is not invoked outside streaming mode


def test_item_depth_streams_subtrees_and_returns_none():
    seen = []

    def cb(path, item):
        seen.append(item)
        return True

    result = x.parse(XML, item_depth=3, item_callback=cb)
    assert result is None
    assert seen == [{"name": "A"}, {"name": "B"}, {"name": "C"}]


def test_item_callback_receives_ancestor_path():
    paths = []

    def cb(path, item):
        paths.append(path)
        return True

    x.parse(XML, item_depth=3, item_callback=cb)
    assert paths == [[("root", None), ("list", None), ("artist", None)]] * 3


def test_item_callback_false_stops_parsing_early():
    import pytest

    seen = []

    def cb(path, item):
        seen.append(item)
        return len(seen) < 2

    with pytest.raises(x.ParsingInterrupted):
        x.parse(XML, item_depth=3, item_callback=cb)
    assert seen == [{"name": "A"}, {"name": "B"}]


def test_item_callback_false_raises_parsing_interrupted():
    import pytest

    def cb(path, item):
        return False

    with pytest.raises(x.ParsingInterrupted):
        x.parse(XML, item_depth=3, item_callback=cb)


def test_item_depth_four_streams_leaf_text():
    seen = []
    x.parse(XML, item_depth=4, item_callback=lambda path, item: seen.append(item) or True)
    assert seen == ["A", "B", "C"]


def test_item_depth_one_streams_root_itself():
    seen = []
    x.parse(
        "<a x=\"1\"><b>hi</b></a>",
        item_depth=1,
        item_callback=lambda path, item: seen.append((path, item)) or True,
    )
    assert seen == [([("a", {"x": "1"})], {"@x": "1", "b": "hi"})]
