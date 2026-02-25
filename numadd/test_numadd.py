import pytest
from addition_service import AdditionService
from input_validator import InputValidator
from cache_service import CacheService


# --- AdditionService tests ---

def test_add_two_positive_numbers():
    assert AdditionService().add(3, 4) == 7

def test_add_positive_and_negative():
    assert AdditionService().add(10, -3) == 7

def test_add_floats():
    assert AdditionService().add(1.5, 2.5) == 4.0

def test_add_zeros():
    assert AdditionService().add(0, 0) == 0


# --- InputValidator tests ---

def test_valid_numbers():
    assert InputValidator().validate("3", "4") is True

def test_invalid_string():
    assert InputValidator().validate("abc", "4") is False

def test_none_input():
    assert InputValidator().validate(None, "4") is False

def test_out_of_range():
    assert InputValidator().validate(2e15, 1) is False


# --- CacheService tests ---

def test_cache_miss():
    assert CacheService().get(1, 2) is None

def test_cache_hit():
    cs = CacheService()
    cs.set(1, 2, 3)
    assert cs.get(1, 2) == 3
