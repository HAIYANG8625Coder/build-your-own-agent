"""Checks for the inbox, timers and outbox (no API key, no model). Run: python3 test_always_on.py"""
import os, tempfile, time
import always_on as ao
db = ao.connect(os.path.join(tempfile.mkdtemp(), "a.db"))
inbox, timers, outbox = ao.Inbox(db), ao.Timers(db), ao.Outbox(db)
ok = 0
def check(name, cond):
    global ok
    ok += 1
    print(("ok   " if cond else "FAIL ") + name)
    assert cond, name

# 1 the same id twice (the sender retries) is stored once
check("duplicate id is stored once", inbox.add("o1", "shop", "order 1") and not inbox.add("o1", "shop", "order 1") and inbox.counts() == {"pending": 1})
# 2 a worker takes everything pending in one claim; a second claim gets nothing
inbox.add("o2", "shop", "order 2")
rows = inbox.claim()
check("one claim takes both events, a second claim nothing", len(rows) == 2 and inbox.claim() == [])
# 3 several events become one task
check("several events become one task", "2 events arrived together" in ao.one_task(rows))
# 4 a crash: running events go back to pending, and are retried
check("recover puts running events back", inbox.recover() == 2 and inbox.counts() == {"pending": 2})
# 5 failing too often ends in 'failed'
seen = []
def boom(task): seen.append(task); raise RuntimeError("model down")
w = ao.Worker(inbox, boom)
for _ in range(ao.MAX_ATTEMPTS + 1):
    w.run_once()
check("an event that keeps failing stops after %d tries" % ao.MAX_ATTEMPTS, inbox.counts() == {"failed": 2} and db.execute("SELECT MAX(attempts) FROM inbox").fetchone()[0] == ao.MAX_ATTEMPTS)
# 6 a good run marks events done
inbox.add("o3", "shop", "order 3")
done = []
check("a good run marks the event done", ao.Worker(inbox, done.append).run_once() == 1 and inbox.counts()["done"] == 1)
# 7 a follow-up fires once, and not before it is due
timers.follow_up(100, "check on the reply")
sch = ao.Scheduler(timers, inbox)
check("a follow-up does not fire early", sch.tick(99) == 0)
check("a follow-up fires once", sch.tick(100) == 1 and sch.tick(101) == 0)
# 8 a schedule fires, moves to its next time, and a missed run is not repeated
timers.schedule(1000, 60, "daily check")
check("a schedule fires on time", sch.tick(1000) == 1)
check("a schedule waits for the next time", sch.tick(1030) == 0)
check("a missed schedule fires once, not once per missed time", sch.tick(1000 + 60 * 10 + 5) == 1 and sch.tick(1000 + 60 * 10 + 6) == 0)
# 9 the same timer at the same due time cannot make two events
n = db.execute("SELECT COUNT(*) FROM inbox WHERE source='timer'").fetchone()[0]
check("timer events are in the inbox (1 follow-up + 2 schedule runs)", n == 3)
# 10 the outbox: pacing and repeats
for t in ["a", "b", "b", "c", "d", "e", "f"]:
    outbox.send(t)
got = []
sent = ao.Dispatcher(outbox, got.append, limit=3).flush()
check("the dispatcher sends at most 3 per pass and drops the repeat", sent == ["a", "b", "c"] and db.execute("SELECT COUNT(*) FROM outbox WHERE status='dropped'").fetchone()[0] == 1)
check("the next pass sends the rest", ao.Dispatcher(outbox, got.append, limit=9).flush() == ["d", "e", "f"])
print("all %d checks passed" % ok)

# 11 send_message works in plan mode too (a message is not a project edit). We hit this bug: it was offered but refused there.
import types, agent
class Block:
    def __init__(self, **k): self.__dict__.update(k)
class FakeClient:
    def __init__(self): self.n = 0; self.messages = self
    def create(self, **kw):
        self.n += 1
        usage = Block(input_tokens=10, output_tokens=5, cache_read_input_tokens=0, cache_creation_input_tokens=0)
        if self.n == 1:
            return Block(stop_reason="tool_use", usage=usage, content=[Block(type="tool_use", id="t1", name="send_message", input={"text": "hello from plan mode"})])
        return Block(stop_reason="end_turn", usage=usage, content=[Block(type="text", text="done")])
got = []
agent.OUTBOX_HOOK = got.append
agent.run("say hello", FakeClient(), "m", notes="", perms=agent.Permissions(mode="accept-edits"), approver=lambda *a: "nobody",
          plan=True, outbox=True, hooks=agent.Hooks())
check("send_message works in plan mode", got == ["hello from plan mode"] and agent.run.log[0][2] == "allow")
print("all %d checks passed" % ok)
