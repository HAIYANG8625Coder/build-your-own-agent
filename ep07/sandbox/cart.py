"""A shopping cart."""
from pricing import calc_total


class Cart:
    def __init__(self):
        self.prices = []

    def add(self, price):
        self.prices.append(price)

    def summary(self):
        # uses calc_total so the tax is always included
        return "%d items, total %.2f" % (len(self.prices), calc_total(self.prices))
