"""Checks for the eval harness. No API key, no model: hand-made workspaces play the agent's result.
Run: python3 test_eval.py"""
import json, os, re, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import eval as E

n = 0
def check(name, cond):
    global n
    n += 1
    print(("ok   " if cond else "FAIL ") + name)
    assert cond, name

def sub(work, name, old, new):
    p = os.path.join(work, name)
    text = open(p).read()
    assert old in text, (name, old)
    open(p, "w").write(text.replace(old, new))

# 1 isolation: every trial starts from the same clean copy
a, b = E.new_workdir(), E.new_workdir()
open(a + "/config.py", "a").write("# leftover\n")
check("two trials get different folders", a != b)
check("a change in one trial does not leak into the next", "leftover" not in open(b + "/config.py").read())

# 2 the baseline project fails every task that changes something, and passes the read-only one only without an answer
for t in ("version", "tax", "discount"):
    w = E.new_workdir()
    check("untouched project fails %s" % t, not E.grade(t, w, "", E.snapshot(w))["pass"])

# 3 version: a correct fix passes; the classic miss (cli.py banner left at 1.0.0) fails and the grader names it
w = E.new_workdir()
for f, old, new in (("config.py", "1.0.0", "1.1.0"), ("cli.py", "v1.0.0", "v1.1.0"), ("README.md", "1.0.0", "1.1.0")):
    sub(w, f, old, new)
check("version: every place updated passes", E.grade("version", w, "", {})["pass"])
w = E.new_workdir()
sub(w, "config.py", "1.0.0", "1.1.0"); sub(w, "README.md", "1.0.0", "1.1.0")
g = E.grade("version", w, "done", {})
check("version: banner left behind fails, and says which check", not g["pass"] and [k for k, v in g["checks"].items() if not v] == ["banner", "no old version"])
w = E.new_workdir()
for f, old, new in (("config.py", "1.0.0", "1.1.0"), ("cli.py", "v1.0.0", "v1.1.0"), ("README.md", "1.0.0", "1.1.0"), ("CHANGELOG.md", "## 1.0.0", "## 1.1.0")):
    sub(w, f, old, new)
check("version: rewriting the changelog history fails", not E.grade("version", w, "", {})["pass"])

# 3b the pilot found a rigid grader: an agent that made the banner read config.VERSION is also right (behaviour, not wording)
w = E.new_workdir()
sub(w, "config.py", "1.0.0", "1.1.0"); sub(w, "README.md", "1.0.0", "1.1.0")
sub(w, "cli.py", 'BANNER = "shop v1.0.0"', 'from config import VERSION\nBANNER = "shop v%s" % VERSION')
check("version: a banner that reads config.VERSION passes", E.grade("version", w, "", {})["pass"])

# 4 tax: changing only the constant breaks the test, so it fails; the full change passes
w = E.new_workdir()
sub(w, "config.py", "0.07", "0.08")
check("tax: only the constant changed fails", not E.grade("tax", w, "", {})["pass"])
sub(w, "README.md", "7%", "8%"); sub(w, "tests/test_pricing.py", "107.0", "108.0")
check("tax: constant, README and tests changed passes", E.grade("tax", w, "", {})["pass"])

# 5 discount: right behaviour plus a test passes; a function that forgets the tax fails
w = E.new_workdir()
open(w + "/pricing.py", "a").write("\n\ndef apply_discount(prices, percent):\n    return calc_total([p * (1 - percent / 100) for p in prices])\n")
check("discount: right function but no test fails", not E.grade("discount", w, "", {})["pass"])
open(w + "/tests/test_pricing.py", "a").write("\n\nclass TestDiscount(unittest.TestCase):\n    def test_discount(self):\n        from pricing import apply_discount\n        self.assertEqual(apply_discount([100], 10), 96.3)\n")
sub(w, "tests/test_pricing.py", 'if __name__ == "__main__":\n    unittest.main()\n', "")
check("discount: right function and a test passes", E.grade("discount", w, "", {})["pass"])
sub(w, "pricing.py", "return calc_total([p * (1 - percent / 100) for p in prices])", "return round(sum(p * (1 - percent / 100) for p in prices), 2)")
check("discount: a function without tax fails", not E.grade("discount", w, "", {})["pass"])

# 6 readonly: the answer is the outcome, and a changed file fails even with the right answer
w = E.new_workdir(); snap = E.snapshot(w)
check("readonly: right answer, nothing changed passes", E.grade("readonly", w, "Order 1042 is shipped on 18 Nov.", snap)["pass"])
check("readonly: wrong answer fails", not E.grade("readonly", w, "It is packing.", snap)["pass"])
open(w + "/orders.csv", "a").write("1044,C,new\n")
check("readonly: right answer but a file changed fails", not E.grade("readonly", w, "shipped on 18 Nov", snap)["pass"])

# 7 the table maths
recs = [{"pass": p, "turns": t, "tokens_read": k} for p, t, k in ((True, 4, 100), (False, 6, 300), (True, 5, 200))]
s = E.summarize(recs)
check("table: 2 of 3 passed, mean turns 5.0, mean tokens 200, spread 100 to 300", (s["passed"], s["all_pass"], s["any_pass"], s["turns"], s["tokens"], s["tokens_min"], s["tokens_max"]) == (2, False, True, 5.0, 200, 100, 300))

# 8 only the one sentence differs between the setups
check("the change is one sentence", CHANGE if (CHANGE := E.CHANGE) and CHANGE.count(". ") == 0 and CHANGE.endswith(".") else False)

# 9 the trace can be saved as JSON
class B:     # stands in for an SDK block
    def model_dump(self, exclude_none=True): return {"type": "text", "text": "hi", "signature": "x"}
check("messages become plain JSON", json.dumps(E.jsonable([{"role": "user", "content": "q"}, {"role": "assistant", "content": [B()]}])) and
      E.jsonable([{"role": "assistant", "content": [B()]}])[0]["content"][0] == {"type": "text", "text": "hi"})
print("%d checks passed" % n)
