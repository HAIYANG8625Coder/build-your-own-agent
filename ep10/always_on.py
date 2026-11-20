"""Episode 10: the parts around the loop that make an agent work while you are away.
The article "Building always-on agents" names five: inbox, timers, memory, permissions, outbox.
Memory and permissions were episodes 9 and 4. This file adds inbox, timers and outbox, all in one SQLite file.

    Inbox      events from outside, one row each: id (given by the sender), body, status
    Worker     takes the pending events, runs the agent once, marks them done (or puts them back)
    Timers     follow-ups and schedules, in their own table; a scheduler turns a due timer into an inbox event
    Outbox     messages for the user; a dispatcher delivers them
"""
import sqlite3, time

MAX_ATTEMPTS = 3


def connect(path):
    db = sqlite3.connect(path, timeout=30, isolation_level=None)      # autocommit, we use explicit transactions
    db.executescript("""
        CREATE TABLE IF NOT EXISTS inbox  (id TEXT PRIMARY KEY, source TEXT, body TEXT, status TEXT DEFAULT 'pending',
                                           received REAL, attempts INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS timers (id INTEGER PRIMARY KEY AUTOINCREMENT, due REAL, every REAL, body TEXT, done INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS outbox (id INTEGER PRIMARY KEY AUTOINCREMENT, body TEXT, status TEXT DEFAULT 'pending', created REAL);
    """)
    return db


class Inbox:
    def __init__(self, db):
        self.db = db

    def add(self, event_id, source, body, now=None):
        """The handler: write the event down and return at once. False if this id was seen before (a retry from the sender)."""
        cur = self.db.execute("INSERT OR IGNORE INTO inbox (id, source, body, received) VALUES (?,?,?,?)",
                              (event_id, source, body, now or time.time()))
        return cur.rowcount == 1

    def claim(self, limit=20):
        """The worker: take every pending event (up to a limit) in one step, so two workers never get the same one."""
        self.db.execute("BEGIN IMMEDIATE")
        rows = self.db.execute("SELECT id, source, body FROM inbox WHERE status='pending' ORDER BY received, rowid LIMIT ?", (limit,)).fetchall()
        for r in rows:
            self.db.execute("UPDATE inbox SET status='running', attempts=attempts+1 WHERE id=?", (r[0],))
        self.db.execute("COMMIT")
        return rows

    def finish(self, ids, ok=True):
        for i in ids:
            if ok:
                self.db.execute("UPDATE inbox SET status='done' WHERE id=?", (i,))
            else:       # the run failed: back to pending, unless it already failed too often
                self.db.execute("UPDATE inbox SET status=CASE WHEN attempts>=? THEN 'failed' ELSE 'pending' END WHERE id=?", (MAX_ATTEMPTS, i))

    def recover(self):
        """After a crash: events a dead worker had taken go back to pending. The inbox is the source of truth."""
        return self.db.execute("UPDATE inbox SET status='pending' WHERE status='running'").rowcount

    def counts(self):
        return dict(self.db.execute("SELECT status, COUNT(*) FROM inbox GROUP BY status").fetchall())


def one_task(rows):
    """Several events waiting at once become one task, so the agent answers once."""
    if len(rows) == 1:
        return "An event arrived (id %s, from %s):\n%s" % rows[0]
    return "%d events arrived together:\n" % len(rows) + "\n".join("%d. (id %s, from %s) %s" % (k, r[0], r[1], r[2]) for k, r in enumerate(rows, 1))


class Worker:
    def __init__(self, inbox, handle):
        self.inbox, self.handle = inbox, handle      # handle(task) runs the agent; it raises if the run failed

    def run_once(self):
        rows = self.inbox.claim()
        if not rows:
            return 0
        try:
            self.handle(one_task(rows))
        except Exception as e:
            self.inbox.finish([r[0] for r in rows], ok=False)
            return -len(rows)
        self.inbox.finish([r[0] for r in rows])
        return len(rows)


class Timers:
    def __init__(self, db):
        self.db = db

    def follow_up(self, due, body):
        self.db.execute("INSERT INTO timers (due, body) VALUES (?,?)", (due, body))

    def schedule(self, first, every, body):
        self.db.execute("INSERT INTO timers (due, every, body) VALUES (?,?,?)", (first, every, body))


class Scheduler:
    """Polls the timers. A timer does not run the agent: it puts an event in the inbox."""
    def __init__(self, timers, inbox):
        self.timers, self.inbox = timers, inbox

    def tick(self, now):
        fired = 0
        for tid, due, every, body in self.timers.db.execute("SELECT id, due, every, body FROM timers WHERE done=0 AND due<=?", (now,)).fetchall():
            self.inbox.add("timer-%d-%d" % (tid, due), "timer", body, now)      # same timer + same due time = same event id
            if every:       # a schedule: next time after now (a missed run is not repeated; Claude Code's /loop does the same)
                nxt = due + every
                while nxt <= now:
                    nxt += every
                self.timers.db.execute("UPDATE timers SET due=? WHERE id=?", (nxt, tid))
            else:
                self.timers.db.execute("UPDATE timers SET done=1 WHERE id=?", (tid,))
            fired += 1
        return fired


class Outbox:
    def __init__(self, db):
        self.db = db

    def send(self, body):
        self.db.execute("INSERT INTO outbox (body, created) VALUES (?,?)", (body, time.time()))


class Dispatcher:
    """Reads pending messages and delivers them. It may hold back: it sends at most `limit` per pass and drops exact repeats."""
    def __init__(self, outbox, deliver, limit=5):
        self.outbox, self.deliver, self.limit = outbox, deliver, limit

    def flush(self):
        db, sent = self.outbox.db, []
        seen = {r[0] for r in db.execute("SELECT body FROM outbox WHERE status='sent'")}
        for oid, body in db.execute("SELECT id, body FROM outbox WHERE status='pending' ORDER BY id").fetchall():
            if len(sent) >= self.limit:
                break
            if body in seen:
                db.execute("UPDATE outbox SET status='dropped' WHERE id=?", (oid,))
                continue
            self.deliver(body)
            db.execute("UPDATE outbox SET status='sent' WHERE id=?", (oid,))
            seen.add(body)
            sent.append(body)
        return sent
