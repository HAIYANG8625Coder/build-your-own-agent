"""Command line for the shop."""
import sys
from cart import Cart

BANNER = "shop v1.0.0"


def main(argv):
    print(BANNER)
    cart = Cart()
    for arg in argv:
        cart.add(float(arg))
    print(cart.summary())


if __name__ == "__main__":
    main(sys.argv[1:])
