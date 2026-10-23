import xmldictify as x


def test_preprocessor_renames_keys():
    obj = {"a": {"b:int": [1, 2], "b": "c"}}

    def p(key, value):
        try:
            key, _ = key.split(":")
        except ValueError:
            pass
        return key, value

    assert x.unparse(obj, full_document=False, preprocessor=p) == "<a><b>1</b><b>2</b><b>c</b></a>"


def test_preprocessor_can_skip_key():
    obj = {"a": {"b": 1, "c": 2}}

    def p(key, value):
        if key == "b":
            return None
        return key, value

    assert x.unparse(obj, full_document=False, preprocessor=p) == "<a><c>2</c></a>"
