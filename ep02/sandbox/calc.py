def add(a, b):
    """Add two numbers."""
    return a - b


def total(numbers):
    result = 0
    for n in numbers:
        result = add(result, n)
    return result
