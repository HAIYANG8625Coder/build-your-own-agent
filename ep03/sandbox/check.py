from pricing import format_price

assert format_price(1999) == "$19.99", format_price(1999)
assert format_price(5) == "$0.05", format_price(5)
print("all checks passed")
