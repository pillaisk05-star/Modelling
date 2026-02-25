import pytest
from add_numbers import add_numbers

def test_add_two_positive_numbers():
    assert add_numbers(2, 3) == 5

def test_add_positive_and_negative():
    assert add_numbers(10, -4) == 6

def test_add_two_negative_numbers():
    assert add_numbers(-3, -7) == -10

def test_add_floats():
    assert add_numbers(1.5, 2.5) == 4.0

def test_add_zero():
    assert add_numbers(0, 5) == 5
