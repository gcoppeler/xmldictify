import xmldictify as x


def test_postprocessor_can_drop_items():
    def pp(path, key, value):
        if key == "c":
            return None
        return key, value

    result = x.parse("<a><b>1</b><c>2</c></a>", postprocessor=pp)
    assert result == {"a": {"b": "1"}}


def test_postprocessor_can_transform_value():
    def pp(path, key, value):
        if key == "b":
            return key, int(value)
        return key, value

    result = x.parse("<a><b>1</b></a>", postprocessor=pp)
    assert result == {"a": {"b": 1}}


def test_postprocessor_can_rename_key():
    def pp(path, key, value):
        if key == "b":
            return "renamed", value
        return key, value

    result = x.parse("<a><b>1</b></a>", postprocessor=pp)
    assert result == {"a": {"renamed": "1"}}


def test_postprocessor_receives_path():
    seen_paths = []

    def pp(path, key, value):
        seen_paths.append(path)
        return key, value

    x.parse("<a><b><c>1</c></b></a>", postprocessor=pp)
    assert ("a", "b") in seen_paths
