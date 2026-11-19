import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pricing import calc_total
from cart import Cart


class TestPricing(unittest.TestCase):
    def test_total(self):
        self.assertEqual(calc_total([100]), 107.0)

    def test_cart(self):
        c = Cart()
        c.add(50)
        c.add(50)
        self.assertEqual(c.summary(), "2 items, total 107.00")


if __name__ == "__main__":
    unittest.main()
