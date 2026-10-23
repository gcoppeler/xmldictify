import xmldictify as x

XML = "<a><b>data1</b><b>data2</b><c>data3</c></a>"


def test_force_list_by_tag_name():
    result = x.parse(XML, force_list=("b",))
    assert result == {"a": {"b": ["data1", "data2"], "c": "data3"}}


def test_force_list_true_forces_everything():
    result = x.parse(XML, force_list=True)
    assert result == {"a": {"b": ["data1", "data2"], "c": ["data3"]}}


def test_force_list_callable():
    result = x.parse(XML, force_list=lambda path, key, value: key == "c")
    assert result == {"a": {"b": ["data1", "data2"], "c": ["data3"]}}


def test_force_cdata_true_wraps_every_leaf():
    xml = "<a><b>data1</b><c>data2</c></a>"
    result = x.parse(xml, force_cdata=True)
    assert result == {"a": {"b": {"#text": "data1"}, "c": {"#text": "data2"}}}


def test_force_cdata_by_tag_name():
    xml = "<a><b>data1</b><c>data2</c></a>"
    result = x.parse(xml, force_cdata=("b",))
    assert result == {"a": {"b": {"#text": "data1"}, "c": "data2"}}


def test_force_cdata_callable():
    xml = "<a><b>data1</b><c>data2</c></a>"
    result = x.parse(xml, force_cdata=lambda path, key, value: key == "c")
    assert result == {"a": {"b": "data1", "c": {"#text": "data2"}}}
