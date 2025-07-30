import pytest

from edpop_explorer.external_data.deutsche_isil_agentur import get_isil_name_by_code


@pytest.mark.requests
def test_isil_agentur_normal():
    assert get_isil_name_by_code("DE-139") == "Frankfurt/O StuRegB"


@pytest.mark.requests
def test_isil_agentur_empty():
    assert get_isil_name_by_code("") is None


@pytest.mark.requests
def test_isil_agentur_nonexisting():
    assert get_isil_name_by_code("random") is None