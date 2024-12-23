import pytest

from edpop_explorer.readers.stcn import safeget


def test_safeget_empty_attribute_chain():
    with pytest.raises(ValueError):
        safeget(None, ())

def test_safeget_empty_dict():
    assert safeget({}, ("attribute",)) is None

def test_safeget_none():
    assert safeget(None, ("attribute",)) is None

def test_safeget_simple():
    assert safeget({"attribute": "value"}, ("attribute",)) == "value"

def test_safeget_nested():
    assert safeget(
        {
            "attribute": {"attribute2": "value"}
        }, ("attribute", "attribute2")
    ) == "value"

def test_safeget_nested_first_attribute_none():
    assert safeget({
        "attribute": None
    }, ("attribute", "attribute2")) is None

def test_safeget_nested_first_attribute_nonexistent():
    assert safeget({
        "other_attribute": None
    }, ("attribute", "attribute2")) is None

def test_safeget_nested_second_attribute_nonexistent():
    assert safeget({
        "attribute": {
            "other_attribute": "value"
        }
    }, ("attribute", "attribute2")) is None

def test_safeget_first():
    assert safeget({
        "attribute": ["value1", "value2"]
    }, ("attribute",), True) == "value1"