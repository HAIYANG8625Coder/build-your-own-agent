"""A tiny fixed set of tasks, run with and without the notes file.

    python3 evals.py [repeats]      (default 3)

Each check is plain code that looks at the files and the tool calls.
The model's own opinion of its work is never used.
"""
import ast, importlib, json, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
import agent


def load(folder, module):
    """Import a module from the task folder, as the project itself would."""
    for name in [m for m in sys.modules if m.split(".")[0] in ("pricing", "helpers")]:
        del sys.modules[name]
    sys.path.insert(0, folder)
    try:
        return importlib.import_module(module)
    finally:
        sys.path.remove(folder)


def commands(messages):
    out = []
    for m in messages:
        if m["role"] == "assistant":
            for b in m["content"]:
                if b.type == "tool_use" and b.name == "run_bash":
                    out.append(b.input.get("command", ""))
    return out


def has_done_line(messages):
    return any(l.startswith("Done:")
               for l in agent.final_text(messages).split("\n"))


def check_discount(folder, messages):
    """apply_discount returns integer cents, rounds half up, has a docstring."""
    src = open(os.path.join(folder, "pricing.py")).read()
    tree = ast.parse(src)
    fn = [n for n in tree.body if isinstance(n, ast.FunctionDef)
          and n.name == "apply_discount"]
    f = load(folder, "pricing").apply_discount
    return {
        "integer result": type(f(1999, 10)) is int and f(1999, 10) == 1799,
        "rounds half up": f(1005, 50) == 503,
        "docstring": bool(fn and ast.get_docstring(fn[0])),
        "Done: line": has_done_line(messages),
    }


def check_helper(folder, messages):
    """The new helper is in helpers/round_down_5.py, as the notes say."""
    path = os.path.join(folder, "helpers", "round_down_5.py")
    ok = os.path.exists(path)
    work = False
    if ok:
        f = getattr(load(folder, "helpers.round_down_5"), "round_down_5", None)
        work = bool(f) and f(1999) == 1995 and f(1995) == 1995
    return {
        "file in helpers/": ok,
        "works": work,
        "Done: line": has_done_line(messages),
    }


TASKS = [
    ("discount", "Add a function apply_discount(cents, percent) to "
                 "pricing.py. It returns the price after the discount.",
     check_discount),
    ("helper", "Add a helper round_down_5(cents) that rounds a price "
               "down to a multiple of 5 cents.",
     check_helper),
]


def run_one(task, check, with_notes, client, model):
    folder = tempfile.mkdtemp()
    shutil.copytree(os.path.join(HERE, "sandbox"), folder + "/p")
    folder += "/p"
    if not with_notes:
        os.remove(os.path.join(folder, "NOTES.md"))
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.chdir(folder)
    agent.ROOT = os.path.realpath(folder)
    agent.READ.clear()
    msgs = agent.run(task, client, model)
    try:
        return check(folder, msgs)
    except Exception as e:
        return {"check crashed: %s" % type(e).__name__: False}


if __name__ == "__main__":
    repeats = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    client, model = agent.make_client()
    results = {}
    for with_notes in (False, True):
        label = "with notes" if with_notes else "no notes"
        for name, task, check in TASKS:
            for i in range(repeats):
                print("\n== %s | %s | run %d" % (label, name, i + 1))
                r = run_one(task, check, with_notes, client, model)
                print("  ->", r)
                results.setdefault((label, name), []).append(r)
    print("\n=== summary (passes out of %d runs) ===" % repeats)
    for (label, name), runs in results.items():
        keys = sorted({k for r in runs for k in r})
        row = ", ".join("%s %d" % (k, sum(r.get(k, False) for r in runs))
                        for k in keys)
        print("%-10s %-9s %s" % (label, name, row))
