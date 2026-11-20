"""One agent run, in its own process (like one webhook call starting one run). Usage: python3 runner.py CONFIG.json
CONFIG: root, task, db (outbox sqlite file), approver (stall | deny | nobody), timeout (seconds), out (result json), memdir"""
import json, os, signal, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(sys.argv[1]))
os.environ["AGENT_MEMORY"] = cfg["memdir"]
os.environ.setdefault("AGENT_HOME", tempfile.mkdtemp())
sys.path.insert(0, HERE)
import agent, always_on as ao

class Stalled(Exception): pass
def on_alarm(*a): raise Stalled()
signal.signal(signal.SIGALRM, on_alarm)
APPROVERS = {"deny": lambda tool, args: "n", "nobody": lambda tool, args: "nobody"}
def stall(tool, args):          # nobody answers: the run waits, like a cloud run waiting for a permission prompt
    time.sleep(10 ** 6)
APPROVERS["stall"] = stall

os.chdir(cfg["root"]); agent.ROOT = os.path.realpath(cfg["root"]); agent.READ.clear(); agent.MAX_TURNS = 40
db = ao.connect(cfg["db"]); agent.OUTBOX_HOOK = ao.Outbox(db).send
client, model = agent.make_client()
rec = {"stalled": False, "error": ""}
msgs = []
signal.alarm(cfg.get("timeout", 600))
try:
    msgs = agent.run(cfg["task"], client, model, perms=agent.Permissions(mode="accept-edits"), approver=APPROVERS[cfg["approver"]],
                     hooks=agent.Hooks.load(), todo=True, plan=True, plan_ok=lambda p: "", subagents=True, memory=True, outbox=True)
except Stalled:
    rec["stalled"] = True
except Exception as e:
    rec["error"] = repr(e)
signal.alarm(0)
rec.update(final=agent.final_text(msgs) if msgs else "", log=[[t, a, v] for t, a, v in agent.run.log], turns=sum(1 for m in msgs if m["role"] == "assistant"))
json.dump(rec, open(cfg["out"], "w"), ensure_ascii=False, indent=1)
