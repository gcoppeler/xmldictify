import xmldictify as x

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
    assert calls == [((), {"a": {"b": "1"}})]


def test_item_depth_streams_subtrees_and_returns_none():
    seen = []

    def cb(path, item):
        seen.append(item)
        return True

    result = x.parse(XML, item_depth=2, item_callback=cb)
    assert result is None
    assert seen == [{"name": "A"}, {"name": "B"}, {"name": "C"}]


def test_item_callback_receives_ancestor_path():
    paths = []

    def cb(path, item):
        paths.append(path)
        return True

    x.parse(XML, item_depth=2, item_callback=cb)
    assert paths == [("root", "list")] * 3


def test_item_callback_false_stops_parsing_early():
    seen = []

    def cb(path, item):
        seen.append(item)
        return len(seen) < 2

    x.parse(XML, item_depth=2, item_callback=cb)
    assert seen == [{"name": "A"}, {"name": "B"}]


def test_item_depth_three_streams_leaf_text():
    seen = []
    x.parse(XML, item_depth=3, item_callback=lambda path, item: seen.append(item) or True)
    assert seen == ["A", "B", "C"]
