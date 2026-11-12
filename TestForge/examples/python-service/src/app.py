def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b


def is_adult(age: int) -> bool:
    """Return True when age is at least 18."""
    if age < 0:
        raise ValueError("age must be >= 0")
    return age >= 18
