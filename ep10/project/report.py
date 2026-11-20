"""A plain-text sales report."""
from pricing import calc_total
from config import CURRENCY


def report(orders):
    lines = []
    for name, prices in orders.items():
        lines.append("%s: %.2f %s" % (name, calc_total(prices), CURRENCY))
    return "\n".join(lines)
