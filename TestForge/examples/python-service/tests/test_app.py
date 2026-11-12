import pytest

from app import add, is_adult


def test_add_positive_numbers() -> None:
    assert add(2, 3) == 5


@pytest.mark.parametrize("age,expected", [(17, False), (18, True), (19, True)])
def test_is_adult_boundary(age: int, expected: bool) -> None:
    assert is_adult(age) is expected


def test_is_adult_rejects_negative() -> None:
    with pytest.raises(ValueError):
        is_adult(-1)
