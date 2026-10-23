import pytest

import xmldictify as x


def test_multiple_root_keys_raises():
    with pytest.raises(x.MultipleRootsError):
        x.unparse({"a": 1, "b": 2})


def test_empty_dict_raises():
    with pytest.raises(x.MultipleRootsError):
        x.unparse({})


def test_root_value_list_raises():
    with pytest.raises(x.InvalidRootValueError):
        x.unparse({"a": [1, 2]})


def test_invalid_element_name_raises():
    with pytest.raises(x.InvalidXMLNameError):
        x.unparse({"1bad": "x"})


def test_invalid_attribute_name_raises():
    with pytest.raises(x.InvalidXMLNameError):
        x.unparse({"a": {"@1bad": "x"}})


def test_non_dict_input_raises():
    with pytest.raises(x.MultipleRootsError):
        x.unparse("not a dict")
