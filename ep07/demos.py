"""Real runs of a real chore: the weekly posting summary, the main agent alone vs with a helper.

    python3 demos.py run [plain|sub] N     one run; writes demo/<setup>-N.json and .txt
    python3 demos.py table                 print the table from the saved runs (no key needed)

Uses a real model (PROVIDER=deepseek or claude). Each run works on a fresh copy of week/ (a snapshot of the
author's own posting log and post files); check_week.py scores the answer with code.
"""
import glob, json, os, shutil, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("AGENT_HOME", tempfile.mkdtemp())
import agent
sys.path.insert(0, HERE)
import check_week

TASK = ("I post every day and I need my weekly posting summary. In x-assistant/posts.md, find every "
        "Xiaohongshu note published from 2026-11-13 to 2026-11-19 (each is a heading "
        "like '## 2026-11-14 (Xiaohongshu) — title'). For each one, open its post file (the 'Post file:' line "
        "in that entry) and copy the hashtags from the last line of that file. Reply with a table, one row per "
        "post, with: date, platform, title, hashtags. Also save the table to x-assistant/weekly-summary.md.")
ASK = (" The post files are many: hand the job of reading them and listing their hashtags to a helper with the delegate tool, and use its answer.")
SETUPS = ("plain", "sub", "asked")   # both: plan mode + task list + permissions + notes + context management; "sub" adds the helper


def one(setup, n):
    d = tempfile.mkdtemp()
    shutil.copytree(os.path.join(HERE, "week"), d + "/p")
    os.chdir(d + "/p")
    agent.ROOT = os.path.realpath(d + "/p")
    agent.READ.clear()
    agent.MAX_TURNS = 100
    client, model = agent.make_client()
    asked = []
    def approve(*a):
        asked.append(a[0]); return "y"
    msgs = agent.run(TASK + (ASK if setup == "asked" else ""), client, model, perms=agent.Permissions(mode="default"), approver=approve,
                     todo=True, plan=True, plan_ok=lambda p: "", subagents=setup in ("sub", "asked"))
    final = agent.final_text(msgs)
    out_file = os.path.join(d, "p", "x-assistant", "weekly-summary.md")
    saved = open(out_file, encoding="utf-8").read() if os.path.exists(out_file) else ""
    sc = check_week.score(final + "\n" + saved, d + "/p")
    actions = [a for _, _, a in agent.run.context if a]
    turns = sum(1 for m in msgs if m["role"] == "assistant")
    peak = max([t for _, t, _ in agent.run.context] or [0])
    rec = {"setup": setup, "run": n, "turns": turns, "main_peak": peak, "main_spent": agent.run.spent,
           "subs": agent.run.subs, "asked": asked, "saved_file": bool(saved), "plans": [p for p, _ in agent.run.plans],
           "todos_final": [t["status"] for t in agent.TODOS], "context_actions": actions,
           "tools": [t[0] for t in agent.run.log], "rows": sc["rows"], "rows_of": sc["rows_of"], "tags": sc["tags"],
           "tags_of": sc["tags_of"], "missing": sc["missing"],
           "finished": not final.startswith("[") and turns < agent.MAX_TURNS, "final": final}
    os.makedirs(os.path.join(HERE, "demo"), exist_ok=True)
    json.dump(rec, open(os.path.join(HERE, "demo", "%s-%d.json" % (setup, n)), "w"), indent=1, ensure_ascii=False)
    print("\nROWS %d/%d  TAGS %d/%d  turns %d  main peak %d tokens  context actions %d  asked %d  helpers %s" % (
        sc["rows"], sc["rows_of"], sc["tags"], sc["tags_of"], turns, peak, len(actions), len(asked), [(s["turns"], s["peak"]) for s in agent.run.subs]))


def table():
    for setup in ("plain", "sub", "asked"):
        rs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(HERE, "demo", "%s-*.json" % setup)))]
        print(setup, "runs", len(rs), "rows", [r["rows"] for r in rs], "tags", [r["tags"] for r in rs],
              "turns", [r["turns"] for r in rs], "main peak", [r["main_peak"] for r in rs],
              "main spent", [r["main_spent"] for r in rs], "ctx actions", [len(r["context_actions"]) for r in rs], "saved", [r["saved_file"] for r in rs], "helper peak", [[s["peak"] for s in r["subs"]] for r in rs])


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    else:
        one(sys.argv[2], int(sys.argv[3]))
