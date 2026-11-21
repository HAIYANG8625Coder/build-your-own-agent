"""Real runs for episode 13 (DeepSeek, every earlier part on). One run per process.
    python3 demos.py t1 SETUP N    four prompts in a row. SETUP: kept (one chat) | fresh (each prompt starts from nothing)
    python3 demos.py t2 MODE N     one prompt, no tools. MODE: stream | plain. Time until the first text is on screen
    python3 demos.py t3 MODE N     Ctrl+C at the first tool call, then another prompt. MODE: repair | control (no repair)
    python3 demos.py t4 N          two separate processes: a chat, then `repl.py --continue` asking about it
    python3 demos.py table
"""
import glob, json, os, re, shutil, statistics as st, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "demo")
os.makedirs(OUT, exist_ok=True)

P = ["What does cart.py do? One sentence.", "Which file holds the tax rate?", "Change the tax rate to 8% and update whatever else needs it.",
     "List every file you changed in this chat, one path per line, nothing else."]


def workdir():
    d = tempfile.mkdtemp()
    shutil.copytree(os.path.join(HERE, "project"), d + "/p")
    os.environ["AGENT_HOME"], os.environ["AGENT_MEMORY"] = d + "/home", d + "/mem"
    return d, d + "/p"


def setup():
    d, work = workdir()
    import agent
    os.chdir(work)
    agent.ROOT = os.path.realpath(work)
    agent.READ.clear()
    agent.MAX_TURNS = 20
    return d, work, agent


def rel(p, work):
    full = p if os.path.isabs(p) else os.path.join(work, p)
    return os.path.relpath(os.path.realpath(full), os.path.realpath(work))


def tax_ok(work):
    t = lambda f: open(os.path.join(work, f)).read()
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=work, capture_output=True, text=True).returncode == 0
    c = {"config": "TAX_RATE = 0.08" in t("config.py"), "readme": "8%" in t("README.md") and "7%" not in t("README.md"), "tests pass": tests,
         "tests say 108": "108" in t("tests/test_pricing.py")}
    return {"ok": all(c.values()), "checks": c}


def t1(setup_name, n):
    d, work, agent = setup()
    import repl
    client, model = agent.make_client()
    chat = repl.Chat(client, model, out=open(os.devnull, "w"), mode="accept-edits", ask=lambda *a: "n")
    perms = agent.Permissions(mode="accept-edits", allow=["run_bash(python3 -m unittest*)", "run_bash(python3 *)"])
    chat.perms = perms
    answers, calls, spent, edited = [], [], [], []
    for i, p in enumerate(P):
        if setup_name == "kept":
            msgs = chat.turn(p)
        else:
            chat.messages = None            # forget everything: the same as running the prompt as a new one-shot run
            msgs = chat.turn(p)
        answers.append(agent.final_text(msgs))
        calls.append([t for t, a, v in agent.run.log])
        spent.append(agent.run.spent)
        edited += [rel(a["path"], work) for t, a, v in agent.run.log if t == "edit_file" and v == "allow"]
    truth = sorted(set(edited))
    listed = sorted(set(l.strip().strip("`*- ") for l in answers[3].split("\n") if re.search(r"\.\w+$", l.strip().strip("`*- "))))
    listed = sorted(set(rel(x, work) for x in listed))
    rec = {"setup": setup_name, "run": n, "p3": tax_ok(work), "edited": truth, "listed": listed, "p4_ok": bool(truth) and listed == truth,
           "answers": answers, "calls": calls, "tokens_read": spent, "total_tokens": sum(spent), "p2_calls": len(calls[1])}
    json.dump(rec, open(os.path.join(OUT, "t1-%s-%d.json" % (setup_name, n)), "w"), indent=1, ensure_ascii=False)
    print("T1 %s run %d: p3 %s p4 %s (edited %s listed %s) tokens %d p2 calls %d" % (setup_name, n, rec["p3"]["ok"], rec["p4_ok"], truth, listed, rec["total_tokens"], rec["p2_calls"]))


def t2(mode, n):
    d, work, agent = setup()
    import repl
    client, model = agent.make_client()
    chat = repl.Chat(client, model, out=open(os.devnull, "w"), mode="accept-edits", stream=(mode == "stream"), ask=lambda *a: "n")
    first = []
    t0 = time.time()
    orig = chat.on_text
    def mark(p):
        if not first:
            first.append(time.time() - t0)
        orig(p)
    chat.on_text = mark
    msgs = chat.turn("Write a four sentence explanation of how a shopping cart total with tax is worked out.")
    total = time.time() - t0
    if not first:
        first.append(total)      # not streamed: the text is on screen only when the turn is done
    text = agent.final_text(msgs)
    rec = {"mode": mode, "run": n, "first_text_s": round(first[0], 2), "total_s": round(total, 2), "chars": len(text), "text": text}
    json.dump(rec, open(os.path.join(OUT, "t2-%s-%d.json" % (mode, n)), "w"), indent=1, ensure_ascii=False)
    print("T2 %s run %d: first text %.2f s, done %.2f s, %d chars" % (mode, n, first[0], total, len(text)))


def t3(mode, n):
    d, work, agent = setup()
    import repl
    client, model = agent.make_client()
    chat = repl.Chat(client, model, out=open(os.devnull, "w"), mode="accept-edits", ask=lambda *a: "n")
    stopped = []
    def ctrl_c(name, args, verdict):
        if not stopped:
            stopped.append(name)
            raise KeyboardInterrupt           # the user presses Ctrl+C right after the first tool call was announced
    chat.tool_line = ctrl_c
    agent.run.tool_line = ctrl_c
    # Chat.turn sets agent.run.tool_line itself; swap it so that our key press happens inside the run
    orig_turn_line = chat.tool_line
    msgs_after = None
    err = None
    try:
        def turn_with_press(text):
            agent.run.tool_line = ctrl_c
            plan, chat.plan_next = chat.plan_next, False
            opts = chat.options(); opts["plan"] = plan
            try:
                chat.messages = agent.run(text, client, model, messages=chat.messages, **opts)
            except KeyboardInterrupt:
                chat.messages = repair_or_not(agent.run.messages)
        def repair_or_not(m):
            return repl.repair(m) if mode == "repair" else m
        turn_with_press("Look at pricing.py and tell me what calc_total does.")
        interrupted_state = [m["role"] for m in chat.messages][-2:]
        agent.run.tool_line = None
        try:
            chat.messages = agent.run("What is the tax rate in this project? One short answer.", client, model, messages=chat.messages,
                                      **{**chat.options(), "plan": False})
            answer = agent.final_text(chat.messages)
        except Exception as e:
            answer, err = "", "%s: %s" % (type(e).__name__, str(e)[:200])
    except Exception as e:
        answer, err, interrupted_state = "", "setup %s: %s" % (type(e).__name__, str(e)[:200]), []
    rec = {"mode": mode, "run": n, "stopped_at": stopped, "ended_with": interrupted_state, "answer": answer, "error": err,
           "ok": bool(answer) and ("0.07" in answer or "7%" in answer or "7 %" in answer)}
    json.dump(rec, open(os.path.join(OUT, "t3-%s-%d.json" % (mode, n)), "w"), indent=1, ensure_ascii=False)
    print("T3 %s run %d: stopped at %s, next prompt ok=%s %s" % (mode, n, stopped, rec["ok"], err or ""))


def t4(n):
    d, work = workdir()
    env = dict(os.environ, AGENT_HOME=d + "/home", AGENT_MEMORY=d + "/mem", PROVIDER="deepseek")
    cmd = [sys.executable, os.path.join(HERE, "repl.py")]
    a = subprocess.run(cmd, cwd=work, env=env, input="What does cart.py do? One sentence.\n/exit\n", capture_output=True, text=True, timeout=180)
    b = subprocess.run(cmd + ["--continue"], cwd=work, env=env, input="Which file did you read first in this chat? Answer with the path only.\n", capture_output=True, text=True, timeout=180)
    files = os.listdir(d + "/home/sessions")
    rec = {"run": n, "first_process": a.stdout, "second_process": b.stdout, "stderr": (a.stderr + b.stderr)[-300:],
           "resumed": "resumed" in b.stdout, "ok": "cart.py" in b.stdout.split("\n", 1)[-1] and "resumed" in b.stdout, "sessions_saved": len([f for f in files if f.endswith(".json")])}
    json.dump(rec, open(os.path.join(OUT, "t4-%d.json" % n), "w"), indent=1, ensure_ascii=False)
    print("T4 run %d: resumed=%s ok=%s sessions=%d" % (n, rec["resumed"], rec["ok"], rec["sessions_saved"]))


def table():
    mean = lambda xs: round(st.mean(xs), 2)
    for s in ("kept", "fresh"):
        rs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "t1-%s-?.json" % s)))]
        if rs:
            print("t1", s, len(rs), "p3 ok", sum(r["p3"]["ok"] for r in rs), "p4 ok", sum(r["p4_ok"] for r in rs), "mean tokens", round(st.mean(r["total_tokens"] for r in rs)),
                  "mean p2 calls", mean([r["p2_calls"] for r in rs]), "p2 calls", [r["p2_calls"] for r in rs])
    for m in ("stream", "plain"):
        rs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "t2-%s-?.json" % m)))]
        if rs:
            print("t2", m, len(rs), "first text", [r["first_text_s"] for r in rs], "mean", mean([r["first_text_s"] for r in rs]), "total mean", mean([r["total_s"] for r in rs]))
    for m in ("repair", "control"):
        rs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "t3-%s-?.json" % m)))]
        if rs:
            print("t3", m, len(rs), "next prompt ok", sum(r["ok"] for r in rs), "errors", [r["error"] for r in rs if r["error"]][:2])
    rs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "t4-?.json")))]
    if rs:
        print("t4", len(rs), "resumed and right", sum(r["ok"] for r in rs))


if __name__ == "__main__":
    a = sys.argv
    {"t1": lambda: t1(a[2], int(a[3])), "t2": lambda: t2(a[2], int(a[3])), "t3": lambda: t3(a[2], int(a[3])), "t4": lambda: t4(int(a[2])), "table": table}[a[1]]()
