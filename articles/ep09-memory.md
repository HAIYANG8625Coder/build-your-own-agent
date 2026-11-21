# Episode 9 · Memory between sessions

*Part D · Beyond one session. Video: "Build your own agent · 09: memory". Code: [`ep09/`](../ep09/).*

**Series:** [← README](../README.md) · [← Ep 8: Hooks](ep08-hooks.md) · [Ep 10: Always on →](ep10-always-on.md)

**Key idea:** Memory is a folder of short notes plus an index, written by the agent, so the next session starts knowing what you said once.

This article is the whole of episode 9 in writing, so you can follow it without the video. Every claim about Claude Code is taken from the official [Memory page](https://code.claude.com/docs/en/memory), which I read in full. Where the docs are silent, I say "our version does it this way".

**What you will be able to do afterwards**

- Say what a *session* is, and why a new one starts empty.
- Say what memory is: a folder of short notes plus an index, and how it differs from the notes file of [episode 3](ep03-system-prompt-and-notes.md).
- Explain what Claude Code stores, where, and what it loads at the start.
- Build the small version: a `memory_write` tool, a `memory_forget` tool, and an index that goes into the first message.
- Read a real two-session test (25 runs), and say what it can and cannot show.

**Before you start:** the agent from [episode 8](ep08-hooks.md). The code for this episode is a copy of `ep08/agent.py` plus a memory section. Run it only inside a throwaway folder.

---

## 1. The problem

A *session* is one conversation, from the first message to the last. A new session starts with an empty head: everything said in chat is gone. The notes file of episode 3 only holds what you wrote down in advance. Some things you say only once: "this file belongs to the ops team, never edit it", "answer me in Chinese".

The test below shows it. In session 1 the user tells the agent four things. In session 2, a brand-new conversation, the agent gets a task where those four things matter.

| Told in session 1 | Why it matters in session 2 |
|---|---|
| `config.py` belongs to the ops team, never edit it | the task invites editing a settings file |
| settings that change are overridden with environment variables named `SHOP_<NAME>` | where the adjustable threshold must live |
| the staging deploy key is in the variable `STAGING_DEPLOY_KEY`, the address is `https://staging.shop.example` | the last question is "how do I deploy to staging?" |
| always answer in Chinese, as short as possible | the language of the answer |

(An *environment variable* is a value set outside the files; a *deploy key* is the secret that lets you put a program on a server. The key here is a made-up name.)

## 2. What memory is

Memory is a folder of short notes that survives between sessions, plus an *index*, a table of contents with one line per note. At the start of a session only the index is loaded. A note is opened when it looks relevant. What to store: only what you cannot look up again, so who the user is, how they want you to work, decisions, and where things live outside the code. Anything you can read from the code is not stored.

The notes file is what *you* write. Memory is what the *agent* writes.

## 3. What Claude Code does (official docs)

From the [Memory page](https://code.claude.com/docs/en/memory):

- Two kinds. `CLAUDE.md` files are written by you ("instructions and rules"). Auto memory is written by Claude ("learnings and patterns"). Both are loaded every session; both are described as "context, not enforced configuration".
- `CLAUDE.md` is delivered as a user message after the system prompt. The project-root file survives compaction: Claude re-reads it from disk and re-injects it.
- Auto memory lives in `~/.claude/projects/<project>/memory/`: an index `MEMORY.md` and one file per memory (`user_role.md` and `feedback_testing.md` are the page's examples). It is machine-local, one folder per git repository.
- Loading: "the first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first". Topic files are not loaded at startup; Claude opens them on demand with its normal file tools. Subagents do not get the main conversation's auto memory.
- Four types in a `type` field: user, feedback, project, reference. Claude skips anything it can derive from the code, such as architecture, file paths or debugging fixes.
- "always use pnpm, not npm": when you ask Claude to remember something like that, it saves it to auto memory.
- `/memory` lists the memory files, switches auto memory on and off, and opens the folder. The files are plain markdown you can edit or delete.
- Near the limit, Claude Code tells Claude to keep one line per entry, move detail into topic files, and merge or drop stale entries. Past the limit the write works, but everything after the limit is dropped on the next load.
- For things that must happen every time, the page says to use a hook ([episode 8](ep08-hooks.md)), because hooks "apply regardless of what Claude decides to do".

## 4. Our version

All of it is in the memory section of [`ep09/agent.py`](../ep09/agent.py).

- `memory_write(name, type, description, content)` checks the type (one of the four), writes one note file with a small header (name, description, type, modified time), and writes one line for it in `MEMORY.md`. If the index is near its limit, the result says so: one line per note, merge or drop old ones.
- `memory_forget(name)` deletes the note and its index line.
- The memory folder is `AGENT_MEMORY`, or `~/.agent/projects/<folder>-<hash>/memory`, one per project.
- `load_memory()` returns the first 200 lines or 25 KB of the index (the documented limits). It goes into the **first message**, next to the notes file. Because it is in the first message, it survives the context management of [episode 5](ep05-context.md), the same way `CLAUDE.md` does.
- Two prompt rules. First: save what the user tells you that you cannot look up again, not what you can read in the code. Second (optional, tested below): notes can be out of date, so check a note before you rely on it.
- A real note, written by the agent in one of the runs:

```
---
name: Staging deploy details
description: Staging deploy key env var name and staging URL
type: project
modified: 2026-11-20T00:18:40
---

Staging deploys use the key in env var STAGING_DEPLOY_KEY; staging address is https://staging.shop.example.
```

The index line for it is the name plus the description. `python3 test_memory.py` runs eight checks without an API key.

## 5. The real test

`deepseek-flash`, every earlier part switched on (notes, tools, permissions, context management, plan mode and task list, subagents, hooks). Session 1 once per run; session 2 in four setups, five runs each (`ep09/demos.py`, results in [`ep09/demo/`](../ep09/demo/)).

- **A:** no memory.
- **B:** the memory the same run's session 1 wrote.
- **C:** like B, but the project docs now say the deploy key was renamed (`STG_DEPLOY_TOKEN`, a new address). The note is out of date, and we made it so on purpose.
- **C0:** like C, but without the "check a note before you rely on it" rule.

Session 2's task: "free shipping for orders over 100, a flat fee of 8 otherwise, a function `shipping_fee(total)` in `pricing.py` with tests, the threshold must be adjustable; then tell me how to deploy to staging."

**Session 1.** In all 5 runs the agent saved all four facts, and wrote no junk notes (3 or 4 notes per run: 4, 3, 3, 4, 4).

**Session 2.**

| | A: no memory | B: memory |
|---|---|---|
| left `config.py` alone | 0 of 5 | 5 of 5 |
| used a `SHOP_` environment variable | 0 of 5 | 5 of 5 |
| answered in Chinese | 0 of 5 | 5 of 5 |
| gave the deploy key name | 0 of 5 | 5 of 5 |
| shipping function and tests right | 5 of 5 | 5 of 5 |
| mean turns | 23.0 | 16.2 |
| mean tokens read | 124,585 | 79,434 |

Without memory the agent did the job and broke every rule it had never heard. With memory it kept them all. The token difference is the mean of five runs; do not read it as "memory saves 36%".

**A stale note.**

| | C: with the check rule | C0: without it |
|---|---|---|
| gave the new key | 3 of 5 | 4 of 5 |
| believed the old note | 2 of 5 | 1 of 5 |
| read `docs/deploy.md` | 3 of 5 | 4 of 5 |

In all ten runs, reading the docs and giving the new key went together. The "check first" rule showed no benefit here; the run with the rule was one run worse, which five runs cannot tell apart from chance. What the table does show is the risk: a wrong note is believed.

## 6. A pitfall we hit

In the first pilot, the agent said "I have no memory tool" and saved nothing. Cause: in plan mode only read tools were offered, and the memory tools were hidden with them. Saving a note is not an edit of the project, so the fix is to offer the memory tools in plan mode too (still no edit tools), and `test_memory.py` now has a check for it. Also: I once started the batch twice by mistake, so I threw those numbers away and reran everything once.

## 7. What this does not do

- Five runs, one model, one task: the table shows what memory is *for*, not how much it helps in general.
- Whether the agent saves something unprompted, beyond the prompt rule, was not measured separately.
- Not built: an offline pass that reviews old notes and merges or drops stale ones (the syllabus lists it as optional), `/memory`, `CLAUDE.local.md`, and rules folders.
- Notes are plain text in a folder you control. Never let the agent store secrets there.

## 8. Recap

1. A session starts empty; memory is how the next one learns what you said.
2. Notes in a folder, one index line each; load the index, open notes on demand.
3. Store only what you cannot look up again.
4. A note can be wrong. Check it against the code or the docs before acting on it, and expect that the agent will sometimes not.

**Next:** episode 10, an agent that keeps working while you are away.

**Try it:** `python3 test_memory.py` in `ep09/`, then run `python3 agent.py --memory "..."` twice in a throwaway folder and tell it something in the first run.

## References

- Claude Code docs, Memory (CLAUDE.md vs auto memory, loading limits, types, `/memory`): https://code.claude.com/docs/en/memory
- Code and real runs: [`ep09/agent.py`](../ep09/agent.py), [`ep09/test_memory.py`](../ep09/test_memory.py), [`ep09/demos.py`](../ep09/demos.py), [`ep09/demo/`](../ep09/demo/)
