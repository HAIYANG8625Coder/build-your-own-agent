"""Real runs of a two-session test of memory.

    python3 demos.py s1 N            session 1: the user tells the agent project facts; writes demo/mem-N/ and demo/s1-N.json
    python3 demos.py s2 SETUP N      session 2: a brand-new conversation, memory from session 1 run N
    python3 demos.py table           print the tables from the saved runs (no key needed)

SETUP: A = no memory · B = memory from session 1 · C = the same memory, but the project docs now say the deploy key was
renamed (the memory is out of date) · C0 = like C, but the "check a note before you rely on it" rule is removed.
Every earlier part is on in all runs: notes, tools, permissions, context management, plan mode, task list, subagents, hooks.
"""
import glob, json, os, shutil, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("AGENT_HOME", tempfile.mkdtemp())
import agent
sys.path.insert(0, HERE)
import check_task

S1_TASK = ("Add a function apply_discount(price, percent) to pricing.py, with a test. "
           "A few things about how we work here, for the future: config.py belongs to the ops team, so never edit it; "
           "settings that change are overridden with environment variables named SHOP_<NAME>, for example SHOP_TAX_RATE. "
           "Our staging deploys use the key in the environment variable STAGING_DEPLOY_KEY, and the staging address is "
           "https://staging.shop.example. And please always answer me in Chinese, as short as you can.")
S2_TASK = ("I want free shipping for orders over 100, and a flat fee of 8 otherwise. Add a function shipping_fee(total) to "
           "pricing.py, with tests; the threshold must be adjustable. Then tell me how to deploy this to staging.")


def session(task, memory, memdir, extra_docs=False, check=True):
    d = tempfile.mkdtemp()
    shutil.copytree(os.path.join(HERE, "project"), d + "/p")
    if extra_docs:
        shutil.copy(os.path.join(HERE, "stale_docs", "deploy.md"), d + "/p/docs/deploy.md")
    os.chdir(d + "/p")
    agent.ROOT = os.path.realpath(d + "/p")
    agent.READ.clear()
    agent.MAX_TURNS = 40
    os.environ["AGENT_MEMORY"] = memdir
    client, model = agent.make_client()
    hooks = agent.Hooks.load()
    msgs = agent.run(task, client, model, perms=agent.Permissions(mode="accept-edits"), approver=lambda *a: "y", hooks=hooks,
                     todo=True, plan=True, plan_ok=lambda p: "", subagents=True, memory=memory, memory_check=check)
    return d + "/p", msgs, hooks


def common(msgs, hooks):
    turns = sum(1 for m in msgs if m["role"] == "assistant")
    return {"turns": turns, "tools": [t[0] for t in agent.run.log], "hook_calls": len(hooks.log),
            "memory_index_lines": len([l for l in agent.run.memory_index.split("\n") if l.strip()]) if agent.run.memory_index else 0,
            "main_peak": max([t for _, t, _ in agent.run.context] or [0]), "main_spent": agent.run.spent,
            "read_deploy_doc": any(t == "read_file" and "docs/deploy" in json.dumps(a) for t, a, _ in agent.run.log),
            "finished": turns < agent.MAX_TURNS}


def s1(n):
    memdir = os.path.join(HERE, "demo", "mem-%d" % n)
    shutil.rmtree(memdir, ignore_errors=True)
    work, msgs, hooks = session(S1_TASK, True, memdir)
    final = agent.final_text(msgs)
    rec = dict(common(msgs, hooks), run=n, final=final, **check_task.s1(memdir))
    rec["wrote_memory"] = [t for t in rec["tools"] if t.startswith("memory_")]
    json.dump(rec, open(os.path.join(HERE, "demo", "s1-%d.json" % n), "w"), indent=1, ensure_ascii=False)
    print("\nS1 run %d: notes %d (junk %d) facts saved %d/4 %s turns %d" % (n, rec["notes"], rec["junk_notes"], rec["facts_saved"], rec["facts"], rec["turns"]))


def s2(setup, n):
    src = os.path.join(HERE, "demo", "mem-%d" % n)
    memdir = tempfile.mkdtemp() + "/mem"
    if setup != "A":
        shutil.copytree(src, memdir)
    work, msgs, hooks = session(S2_TASK, setup != "A", memdir, extra_docs=setup in ("C", "C0"), check=setup != "C0")
    final = agent.final_text(msgs)
    rec = dict(common(msgs, hooks), setup=setup, run=n, final=final, **check_task.s2(work, final))
    json.dump(rec, open(os.path.join(HERE, "demo", "s2-%s-%d.json" % (setup, n)), "w"), indent=1, ensure_ascii=False)
    keys = ("config_untouched", "env_override", "chinese", "says_old_key", "says_new_key", "tests_pass", "function_works")
    print("\nS2 %s run %d: %s turns %d read deploy doc %s" % (setup, n, {k: rec[k] for k in keys}, rec["turns"], rec["read_deploy_doc"]))


def table():
    rs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(HERE, "demo", "s1-*.json")))]
    print("SESSION 1 runs", len(rs), "notes", [r["notes"] for r in rs], "junk", [r["junk_notes"] for r in rs], "facts saved (of 4)", [r["facts_saved"] for r in rs], "turns", [r["turns"] for r in rs])
    for setup in ("A", "B", "C", "C0"):
        rs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(HERE, "demo", "s2-%s-*.json" % setup)))]
        if not rs: continue
        f = lambda k: [int(bool(r[k])) for r in rs]
        print(setup, "runs", len(rs), "config untouched", f("config_untouched"), "env override", f("env_override"), "chinese", f("chinese"),
              "old key", f("says_old_key"), "new key", f("says_new_key"), "tests", f("tests_pass"), "works", f("function_works"), "turns", [r["turns"] for r in rs],
              "read deploy doc", f("read_deploy_doc"))


if __name__ == "__main__":
    if sys.argv[1] == "table": table()
    elif sys.argv[1] == "s1": s1(int(sys.argv[2]))
    else: s2(sys.argv[2], int(sys.argv[3]))
