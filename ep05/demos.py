"""A real long run with and without context management.

    python3 demos.py long [without|clear|compact|both]     a task that reads many files; prints tokens per turn
    python3 demos.py chart                   plot the saved runs (needs no key) -> demo/context.csv

Uses a real model (PROVIDER=deepseek or claude). Writes one line per turn to demo/long-<name>.csv.
"""
import os, shutil, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("AGENT_HOME", tempfile.mkdtemp())
import agent

TASK = ("Start at src/mod00.py. The first line of each file names the next file in the chain. "
        "Follow the chain one file at a time (read one file, then the next; do not use grep) until it ends. "
        "Then answer with one line per TODO comment you passed: the file and the function it names.")


def fresh():
    d = tempfile.mkdtemp()
    shutil.copytree(os.path.join(HERE, "sandbox"), d + "/p")
    os.chdir(d + "/p")
    agent.ROOT = os.path.realpath(d + "/p")
    agent.READ.clear()


def long(mode):
    fresh()
    agent.MAX_TURNS = 60
    agent.TOOLS = [t for t in agent.TOOLS if t["name"] == "read_file"]   # one tool, so the runs compare
    big = 10 ** 9
    # tokens: clear old results past 8,000; compact past 12,000
    agent.CLEAR_AT, agent.COMPACT_AT = {"without": (big, big), "clear": (8000, big),
                                        "compact": (big, 12000), "both": (8000, 12000)}[mode]
    client, model = agent.make_client()
    msgs = agent.run(TASK, client, model, perms=agent.Permissions(mode="accept-edits"),
                     approver=lambda *a: "y")
    os.makedirs(os.path.join(HERE, "demo"), exist_ok=True)
    out = os.path.join(HERE, "demo", "long-%s.csv" % mode)
    with open(out, "w") as f:
        f.write("turn,tokens,action\n")
        for t, n, a in agent.run.context:
            f.write('%d,%d,"%s"\n' % (t, n, a))
    print("\nFINAL:", agent.final_text(msgs))
    print("saved", out)


if __name__ == "__main__":
    long(sys.argv[2] if len(sys.argv) > 2 else "both")
