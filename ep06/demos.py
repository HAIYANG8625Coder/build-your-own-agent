"""Real runs: the same 8-part task, three setups.

    python3 demos.py run [plain|todo|plan] N [easy|hard]   one run; writes demo/<level>-<setup>-N.json and .txt
    python3 demos.py table                       print the table from the saved runs (no key needed)

Uses a real model (PROVIDER=deepseek or claude). Each run works on a fresh copy of sandbox/,
then check.py scores the result with 9 yes/no checks.
"""
import glob, json, os, shutil, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("AGENT_HOME", tempfile.mkdtemp())
import agent
sys.path.insert(0, HERE)
import check, check_work, make_workrepo

TASK = ("Please make these changes to the shop project: "
        "(1) rename the function calc_total to order_total everywhere, including tests and docs; "
        "(2) raise the tax rate to 9%; "
        "(3) update the README so it states the new tax rate; "
        "(4) add a function apply_discount(total, percent) to pricing.py that returns the total "
        "minus that percent, rounded to 2 decimals; "
        "(5) add a test for apply_discount; "
        "(6) bump the version to 1.1.0 in config.py; "
        "(7) add a 1.1.0 entry to CHANGELOG.md; "
        "(8) make the command line banner show the new version. "
        "The tests must pass at the end.")


HARD = TASK + (" Also: (9) add SHIPPING_FEE = 5.0 to config.py; "
        "(10) add shipping.py with shipping_cost(total): 0 when the total is over 100, otherwise SHIPPING_FEE; "
        "(11) make the cart summary also show the shipping, like '..., shipping 5.00'; "
        "(12) make the first line of the report show the version, like 'Sales report v1.1.0'; "
        "(13) add a test for shipping_cost; (14) document the shipping rule in the README; "
        "(15) list at least five separate bullets under 1.1.0 in the CHANGELOG; "
        "(16) make 'python3 cli.py --version' print the version and nothing else. "
        "Fix any test that breaks because of these changes. The tests must pass at the end.")


WORK = ("I am about to commit. Check this repo against the rules in CLAUDE.md and fix everything "
        "that breaks them. Then reply with a short table: what was wrong, and what you changed.")


def one(setup, n, level="easy"):
    d = tempfile.mkdtemp()
    if level == "work":
        make_workrepo.build(d + "/p")
    else:
        shutil.copytree(os.path.join(HERE, "sandbox"), d + "/p")
    os.chdir(d + "/p")
    agent.ROOT = os.path.realpath(d + "/p")
    agent.READ.clear()
    agent.MAX_TURNS = 60 if level == 'work' else 40
    agent.CLEAR_AT = agent.COMPACT_AT = 10 ** 9      # no context management in this episode's runs
    client, model = agent.make_client()
    msgs = agent.run({'easy': TASK, 'hard': HARD, 'work': WORK}[level], client, model, perms=agent.Permissions(mode="accept-edits"),
                     approver=lambda *a: "y", todo=setup in ("todo", "plan"), plan=setup == "plan",
                     plan_ok=lambda p: "")
    final = agent.final_text(msgs)
    broke = []
    if level == "work":
        ref = tempfile.mkdtemp(); make_workrepo.build(ref); make_workrepo.fingerprint_ref = make_workrepo.fingerprint(ref)
        check_work.M.fingerprint_ref = make_workrepo.fingerprint(ref)
        checks, broke = check_work.score(agent.ROOT)
    else:
        checks = check.score(agent.ROOT, level)
    turns = sum(1 for m in msgs if m["role"] == "assistant")
    writes = sum(1 for t in agent.run.log if t[0] == "edit_file")
    rec = {"level": level, "setup": setup, "run": n, "turns": turns, "edits": writes,
           "score": sum(checks.values()), "broke": broke, "of": len(checks), "checks": checks,
           "finished": not final.startswith("[") and turns < agent.MAX_TURNS,
           "todos_final": [t["status"] for t in agent.TODOS],
           "plans": [p for p, _ in agent.run.plans], "final": final}
    os.makedirs(os.path.join(HERE, "demo"), exist_ok=True)
    out = os.path.join(HERE, "demo", "%s-%s-%d" % (level, setup, n))
    json.dump(rec, open(out + ".json", "w"), indent=1, ensure_ascii=False)
    print("\nSCORE %d/%d in %d turns" % (rec["score"], len(checks), turns))


def table():
    for level, setup in [(l, s) for l in ("easy", "hard", "work") for s in ("plain", "todo", "plan")]:
        rs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(HERE, "demo", "%s-%s-*.json" % (level, setup))))]
        print(level, setup, "turns", [r["turns"] for r in rs], "edits", [r["edits"] for r in rs],
              "score", [r["score"] for r in rs], "broke", [len(r.get("broke", [])) for r in rs])


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    else:
        one(sys.argv[2], int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else "easy")
