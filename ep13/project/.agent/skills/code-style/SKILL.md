---
name: code-style
description: The project's code style. Use when writing or reviewing Python code in this repository.
---
Style rules for this repository.

1. Python 3, standard library only. No new dependencies without a decision in the team channel.
2. Names: snake_case for functions and variables, CapWords for classes, UPPER_CASE for constants.
3. Lines up to 100 characters. One blank line between functions, two between classes.
4. Every public function has a one-line docstring that says what it returns.
5. Functions longer than 40 lines are split.
6. No bare except. Catch the error you expect.
7. Tests live in tests/, one file per module, named test_<module>.py.
8. Comments say why, not what.
9. Imports at the top: standard library first, then local modules, one per line.
