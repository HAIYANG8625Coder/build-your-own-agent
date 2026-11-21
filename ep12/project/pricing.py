"""Prices for the shop."""
from config import TAX_RATE


def calc_total(prices):
    """Return the total of the prices with tax added, rounded to cents."""
    return round(sum(prices) * (1 + TAX_RATE), 2)
