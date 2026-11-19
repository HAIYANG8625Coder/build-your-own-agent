"""Test the memory without an API key: python3 test_memory.py"""
import os, shutil, tempfile
from types import SimpleNamespace as NS

d = tempfile.mkdtemp()
os.makedirs(d + "/p")
os.chdir(d + "/p")
os.environ["AGENT_HOME"] = d + "/home"
os.environ["AGENT_MEMORY"] = d + "/mem"
import agent
agent.ROOT = os.path.realpath(d + "/p")
open("NOTES.md", "w").write("# Notes\n- run tests with python3 -m unittest\n")


def use(tool, **inp):
    use.n += 1
    return NS(type="tool_use", id="t%d" % use.n, name=tool, input=inp)
use.n = 0


class Fake:
    def __init__(self, steps):
        self.messages, self.steps, self.calls = self, steps, []

    def create(self, **kw):
        self.calls.append({"tools": [t["name"] for t in kw["tools"]], "system": kw["system"], "first": kw["messages"][0]["content"]})
        step = self.steps.pop(0)
        usage = NS(input_tokens=100)
        if isinstance(step, str):
            return NS(stop_reason="end_turn", usage=usage, content=[NS(type="text", text=step)])
        return NS(stop_reason="tool_use", usage=usage, content=step)


perms = lambda: agent.Permissions(mode="accept-edits")
yes = lambda *a: "y"

# 1. no memory flag: no memory tools, no memory rules, nothing loaded
c = Fake(["done"])
agent.run("hi", c, "m", perms=perms(), approver=yes)
assert "memory_write" not in c.calls[0]["tools"] and "memory folder" not in c.calls[0]["system"]
print("ok 1: memory is off unless asked for")

# 2. session 1: the model saves a note; the file and an index line exist, with the four-kind frontmatter
c = Fake([[use("memory_write", name="Staging deploy key", type="reference",
               description="the staging deploy key is in env var STAGING_DEPLOY_KEY",
               content="Deploy to staging with the key in STAGING_DEPLOY_KEY.")], "saved"])
agent.run("remember this", c, "m", perms=perms(), approver=yes, memory=True)
assert "memory_write" in c.calls[0]["tools"] and "memory folder" in c.calls[0]["system"]
idx = open(d + "/mem/MEMORY.md").read()
assert idx.count("\n") == 1 and "[Staging deploy key](staging-deploy-key.md)" in idx, idx
note = open(d + "/mem/staging-deploy-key.md").read()
assert note.startswith("---\nname: Staging deploy key\n") and "type: reference" in note and "modified: 20" in note
print("ok 2: memory_write saves a note with frontmatter and adds one index line")

# 3. session 2 (fresh conversation): the index is in the first message; a note is opened on demand with read_file
c = Fake([[use("read_file", path=d + "/mem/staging-deploy-key.md")], "ok"])
msgs = agent.run("how do I deploy to staging?", c, "m", perms=perms(), approver=yes, memory=True)
assert "STAGING_DEPLOY_KEY" in c.calls[0]["first"] and "staging-deploy-key.md" in c.calls[0]["first"]
res = [b["content"] for m in msgs if m["role"] == "user" and isinstance(m["content"], list) for b in m["content"]]
assert "Deploy to staging with the key" in res[0], res
print("ok 3: the next session starts with the index and can open a note on demand")

# 4. the same name replaces the note and keeps one index line; forget removes both
agent.run("x", Fake([[use("memory_write", name="Staging deploy key", type="reference", description="new key name STG_TOKEN", content="STG_TOKEN")], "ok"]),
          "m", perms=perms(), approver=yes, memory=True)
assert open(d + "/mem/MEMORY.md").read().count("\n") == 1 and "STG_TOKEN" in open(d + "/mem/staging-deploy-key.md").read()
agent.run("x", Fake([[use("memory_forget", name="Staging deploy key")], "ok"]), "m", perms=perms(), approver=yes, memory=True)
assert not os.path.exists(d + "/mem/staging-deploy-key.md") and open(d + "/mem/MEMORY.md").read() == ""
print("ok 4: same name replaces, forget deletes the note and its line")

# 5. only the first 200 lines / 25 KB of the index are loaded, and the model is told
open(d + "/mem/MEMORY.md", "w").write("\n".join("- [n%d](n%d.md) — line %d" % (i, i, i) for i in range(300)) + "\n")
text = agent.load_memory()
assert text.count("\n") == 200 and text.endswith("is not loaded: it is over 200 lines or 25 KB]") and "n199" in text and "n250" not in text
open(d + "/mem/MEMORY.md", "w").write("\n".join("- [n](n.md) — " + "x" * 1000 for i in range(40)) + "\n")
assert len(agent.load_memory().encode()) < 26 * 1024 and "not loaded" in agent.load_memory()
print("ok 5: the index is cut at 200 lines or 25 KB and says so")

# 6. a bad note type is refused as a result the model can read; the memory folder is the only place outside the project that can be read
out, bad = agent.run_tool("memory_write", dict(name="a", type="secret", description="d", content="c"))
assert bad and "type must be one of" in out
out, bad = agent.run_tool("read_file", dict(path="/etc/hosts"))
assert bad and "outside the project" in out
print("ok 6: bad types and paths outside project and memory are refused")

# 7. the first message survives compaction, so the index does too
open(d + "/mem/MEMORY.md", "w").write("- [k](k.md) — key fact\n")
agent.COMPACT_AT = 0
first = agent.first_message("task", "", agent.load_memory())
msgs = [{"role": "user", "content": first}] + [{"role": "assistant", "content": [{"type": "text", "text": "a%d" % i}]} if i % 2 == 0
        else {"role": "user", "content": "u%d" % i} for i in range(12)]
class Summ:
    messages = NS(create=lambda **kw: NS(content=[NS(type="text", text="summary")]))
new, n = agent.compact(msgs, Summ, "m", "")
assert "key fact" in new[0]["content"] and "summary" in new[0]["content"], new[0]["content"]
print("ok 7: the memory index is re-sent after compaction")
# 8. plan mode still offers the memory tools: a note is not an edit of the project
c = Fake([[use("memory_write", name="p", type="user", description="d", content="c")], "ok"])
agent.run("x", c, "m", perms=perms(), approver=yes, memory=True, plan=True, plan_ok=lambda p: "")
assert "memory_write" in c.calls[0]["tools"] and "edit_file" not in c.calls[0]["tools"]
assert os.path.exists(d + "/mem/p.md")
print("ok 8: plan mode offers the memory tools but no edit tools")
print("all passed")
