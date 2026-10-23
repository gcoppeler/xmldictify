from collections import OrderedDict

import xmldictify as x


def test_default_dict_constructor_is_plain_dict():
    result = x.parse("<a><b>1</b></a>")
    assert type(result) is dict
    assert type(result["a"]) is dict


def test_custom_dict_constructor():
    result = x.parse("<a><b>1</b></a>", dict_constructor=OrderedDict)
    assert isinstance(result, OrderedDict)
    assert isinstance(result["a"], OrderedDict)


def test_process_comments_default_off():
    result = x.parse("<a><!-- hi --><b>1</b></a>")
    assert result == {"a": {"b": "1"}}


def test_process_comments_enabled():
    result = x.parse("<a><!-- hi --><b>1</b></a>", process_comments=True)
    assert result == {"a": {"#comment": "hi", "b": "1"}}


def test_process_comments_custom_key():
    result = x.parse(
        "<a><!-- hi --><b>1</b></a>", process_comments=True, comment_key="_note"
    )
    assert result == {"a": {"_note": "hi", "b": "1"}}
