from hypothesis import given, strategies as st

from parcoblatta.scanner.validators import ensure_list

@given(...)
def test_ensure_list_given_value_returns_wrapped_in_list(value: str | int):
    value_list = ensure_list(value)
    assert isinstance(value_list, list)
    assert len(value_list) == 1

@given(...)
def test_ensure_list_given_list_returns_self(value: list[str | int]):
    value_list = ensure_list(value)
    assert value_list == value
