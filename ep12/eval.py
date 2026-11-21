"""Episode 12: a small eval harness. 4 fixed tasks, a clean copy of the project per trial, the full messages saved,
a code grader on the OUTCOME (the files, not what the agent says), and a table.
    python3 eval.py run TASK SETUP N    one trial. TASK: version | tax | discount | readonly. SETUP: base | check
    python3 eval.py table               pass rate, turns and tokens per task and setup, from demo/*.json
The only difference between the setups is one sentence in the rules (CHANGE below), chosen before any run.
"""
import glob, hashlib, json, os, shutil, statistics, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "demo")

# The change under test (decided and written down before the first run):
# hypothesis: telling the agent to search the whole project for every place a value appears raises the pass rate on
# `version` and `tax` (a value hard-coded in several files) and costs a few more turns; it does nothing on the others.
CHANGE = "When you change a value, search the whole project for every other place it appears and change those too."

TASKS = {
    "version": "Bump the version of the shop from 1.0.0 to 1.1.0.",
    "tax": "The tax rate is now 8% instead of 7%. Update the shop.",
    "discount": ("Add a function apply_discount(prices, percent) to pricing.py. It lowers every price by that percent "
                 "and returns the total with tax, rounded to cents. Example: apply_discount([100], 10) == 96.3. Add a test for it."),
    "readonly": "What does orders.csv say about order 1042? Do not change any files.",
}


def read(work, name):
    p = os.path.join(work, name)
    return open(p).read() if os.path.exists(p) else ""


def tests_pass(work):
    done = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=work, capture_output=True, text=True, timeout=30)
    return done.returncode == 0


def snapshot(work):
    """A hash of every file, to see whether anything changed."""
    h = {}
    for root, dirs, files in os.walk(work):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            p = os.path.join(root, f)
            h[os.path.relpath(p, work)] = hashlib.md5(open(p, "rb").read()).hexdigest()
    return h


def grade(task, work, answer, before):
    """The outcome of one trial: {"pass": bool, "checks": {name: bool}}. Looks at files and behaviour, not at the wording of the answer
    (except `readonly`, where the answer IS the outcome)."""
    if task == "version":
        c = {"config": 'VERSION = "1.1.0"' in read(work, "config.py"), "banner": subprocess.run([sys.executable, "cli.py", "10"], cwd=work, capture_output=True, text=True).stdout.startswith("shop v1.1.0\n"),
             "readme": "Current version: 1.1.0" in read(work, "README.md"),
             "no old version": all("1.0.0" not in read(work, f) for f in ("config.py", "cli.py", "README.md")),
             "changelog kept": "## 1.0.0" in read(work, "CHANGELOG.md"), "tests pass": tests_pass(work)}
    elif task == "tax":
        c = {"config": "TAX_RATE = 0.08" in read(work, "config.py"), "readme": "8%" in read(work, "README.md") and "7%" not in read(work, "README.md"),
             "tests pass": tests_pass(work), "tests say 108": "108" in read(work, "tests/test_pricing.py"),
             "behaviour": subprocess.run([sys.executable, "-c", "from pricing import calc_total; print(calc_total([100]))"], cwd=work,
                                         capture_output=True, text=True).stdout.strip() == "108.0"}
    elif task == "discount":
        probe = subprocess.run([sys.executable, "-c", "from pricing import apply_discount as a, calc_total as t; print(a([100], 10), a([100, 50], 20), a([], 10))"],
                               cwd=work, capture_output=True, text=True).stdout.strip()
        c = {"example": probe.startswith("96.3 "), "second case": probe == "96.3 128.4 0.0", "tests pass": tests_pass(work),
             "has a test": "apply_discount" in read(work, "tests/test_pricing.py") or any(
                 "apply_discount" in read(work, "tests/" + f) for f in os.listdir(os.path.join(work, "tests")) if f.endswith(".py"))}
    elif task == "readonly":
        after = snapshot(work)
        c = {"answer has the status": "shipped on 18 Nov" in answer, "no file changed": after == before}
    else:
        raise ValueError(task)
    return {"pass": all(c.values()), "checks": c}


def new_workdir():
    d = tempfile.mkdtemp()
    shutil.copytree(os.path.join(HERE, "project"), d + "/p")
    return d + "/p"


def jsonable(messages):
    out = []
    for m in messages:
        if isinstance(m["content"], str):
            out.append({"role": m["role"], "content": m["content"]})
        else:
            blocks = []
            for b in m["content"]:
                b = b if isinstance(b, dict) else b.model_dump(exclude_none=True)
                blocks.append({k: v for k, v in b.items() if k != "signature"})
            out.append({"role": m["role"], "content": blocks})
    return out


def trial(task, setup, n):
    work = new_workdir()
    d = os.path.dirname(work)
    os.environ["AGENT_MEMORY"], os.environ["AGENT_HOME"] = d + "/mem", d + "/home"
    import agent
    os.chdir(work)
    agent.ROOT = os.path.realpath(work)
    agent.READ.clear()
    agent.MAX_TURNS = 20
    before = snapshot(work)
    system = agent.build_system() + (" " + CHANGE if setup == "check" else "")
    client, model = agent.make_client()
    perms = agent.Permissions(mode="accept-edits", allow=["run_bash(python3 -m unittest*)", "run_bash(python3 -c *)", "run_bash(python3 *)"])
    msgs = agent.run(TASKS[task], client, model, system=system, perms=perms, approver=lambda *a: "n")
    answer = agent.final_text(msgs)
    res = grade(task, work, answer, before)
    rec = {"task": task, "setup": setup, "run": n, **res, "turns": sum(1 for m in msgs if m["role"] == "assistant"), "tokens_read": agent.run.spent,
           "answer": answer, "tools": [[t, json.dumps(a, ensure_ascii=False)[:120], v] for t, a, v in agent.run.log], "messages": jsonable(msgs)}
    os.makedirs(OUT, exist_ok=True)
    json.dump(rec, open(os.path.join(OUT, "%s-%s-%d.json" % (task, setup, n)), "w"), indent=1, ensure_ascii=False)
    print("%s %s run %d: pass=%s turns=%d tokens=%d %s" % (task, setup, n, rec["pass"], rec["turns"], rec["tokens_read"],
                                                           [k for k, v in res["checks"].items() if not v]))


def summarize(recs):
    """One row of the table from the trials of one task and one setup."""
    t, k = [r["tokens_read"] for r in recs], sum(r["pass"] for r in recs)
    return {"n": len(recs), "passed": k, "all_pass": k == len(recs), "any_pass": k > 0,
            "turns": round(statistics.mean(r["turns"] for r in recs), 1), "tokens": round(statistics.mean(t)), "tokens_min": min(t), "tokens_max": max(t)}


def table():
    for task in TASKS:
        for setup in ("base", "check"):
            recs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "%s-%s-?.json" % (task, setup))))]
            if recs:
                print("%-9s %-6s" % (task, setup), summarize(recs))


if __name__ == "__main__":
    if sys.argv[1] == "run":
        trial(sys.argv[2], sys.argv[3], int(sys.argv[4]))
    else:
        table()
