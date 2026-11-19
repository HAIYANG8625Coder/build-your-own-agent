"""Score a finished sandbox against the 9 requirements. Usage: python3 check.py <folder>
Each check is a plain yes or no that a person could verify by hand."""
import os, re, subprocess, sys


def read(root, name):
    p = os.path.join(root, name)
    return open(p).read() if os.path.exists(p) else ""


def score(root, level="easy"):
    # the changelog may name the old function when it says what was renamed
    files = [os.path.join(d, f) for d, _, fs in os.walk(root) for f in fs
             if f.endswith((".py", ".md")) and "__pycache__" not in d and f != "CHANGELOG.md"]
    alltext = "\n".join(open(f).read() for f in files)
    cfg, pri = read(root, "config.py"), read(root, "pricing.py")
    tdir = os.path.join(root, "tests")      # a test may live in any file under tests/
    tests = "\n".join(open(os.path.join(tdir, f)).read() for f in sorted(os.listdir(tdir)) if f.endswith(".py")) if os.path.isdir(tdir) else ""
    ran = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                         cwd=root, capture_output=True, text=True)
    checks = {
        "1 rename to order_total everywhere": "calc_total" not in alltext and "def order_total" in pri,
        "2 tax rate 0.09": bool(re.search(r"TAX_RATE\s*=\s*0\.09\b", cfg)),
        "3 README says 9%": "9%" in read(root, "README.md") and "7%" not in read(root, "README.md"),
        "4 apply_discount exists": bool(re.search(r"def apply_discount\(", pri)),
        "5 test for apply_discount": "apply_discount" in tests,
        "6 version 1.1.0 in config": bool(re.search(r'VERSION\s*=\s*"1\.1\.0"', cfg)),
        "7 CHANGELOG has 1.1.0": "1.1.0" in read(root, "CHANGELOG.md"),
        "8 CLI banner not 1.0.0": "v1.0.0" not in read(root, "cli.py"),
        "9 tests pass": ran.returncode == 0 and "OK" in ran.stderr,
    }
    # behaviour of apply_discount, if it exists
    try:
        out = subprocess.run([sys.executable, "-c",
            "from pricing import apply_discount as a; print(a(200.0, 10))"],
            cwd=root, capture_output=True, text=True).stdout.strip()
        checks["4 apply_discount exists"] = checks["4 apply_discount exists"] and out in ("180.0", "180")
    except Exception:
        pass
    if level == "hard":
        rep, cart, cli, readme = (read(root, n) for n in ("report.py", "cart.py", "cli.py", "README.md"))
        def run(code):
            r = subprocess.run([sys.executable, "-c", code], cwd=root, capture_output=True, text=True)
            return r.stdout.strip()
        checks.update({
            "10 SHIPPING_FEE = 5.0 in config": bool(re.search(r"SHIPPING_FEE\s*=\s*5(\.0)?\b", cfg)),
            "11 shipping_cost(): free over 100": run("from shipping import shipping_cost as s; print(s(150), s(50))") in ("0 5.0", "0.0 5.0"),
            "12 cart summary shows shipping": "shipping" in run("from cart import Cart; c=Cart(); c.add(50); print(c.summary())").lower(),
            "13 report has version header": "1.1.0" in run("from report import report; print(report({'a':[1]}))").split("\n")[0],
            "14 test for shipping_cost": "shipping_cost" in tests,
            "15 README documents shipping": "shipping" in readme.lower(),
            "16 CHANGELOG has 5+ bullets for 1.1.0": read(root, "CHANGELOG.md").split("## 1.0.0")[0].count("\n- ") >= 5,
            "17 cli --version prints version": run("import sys; sys.argv=['cli.py','--version']; import cli; cli.main(['--version'])").strip().endswith("1.1.0"),
        })
    return checks


if __name__ == "__main__":
    c = score(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "easy")
    for k, v in c.items():
        print("PASS" if v else "FAIL", k)
    print("score %d/%d" % (sum(c.values()), len(c)))
