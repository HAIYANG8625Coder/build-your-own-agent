---
name: pricing-rules
description: Change prices, discounts or tax in the shop. Use when a task touches pricing.py, coupons, shipping fees or tax.
---
Money rules the code must keep.

1. Amounts are integers in cents, never floats. Only the display layer divides by 100.
2. Rounding is half up, once, at the end of the calculation, never per line.
3. A discount never makes a total negative. The lowest total is 0.
4. Tax is added after discounts. Shipping is added after tax and is not taxed.
5. Coupons do not stack. If two apply, the larger one wins.
6. Every pricing change needs a test with at least one edge case: zero, exactly at a threshold, and a very large order.
7. Changes to the tax table need a line in CHANGELOG.md under "Tax".
8. Ask the finance team before changing the free-shipping threshold.
