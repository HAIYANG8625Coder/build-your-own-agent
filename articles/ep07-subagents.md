# Episode 7 · Subagents

*Part C · Working at scale. Video: "Build your own agent · 07: subagents". Code: [`ep07/`](../ep07/).*

**Series:** [← README](../README.md) · [← Ep 6: Plan mode and task list](ep06-plan-and-tasks.md) · [Ep 8: Hooks →](ep08-hooks.md)

**Key idea:** A subagent runs in a fresh conversation and returns one short answer, which keeps the main context clean but costs tokens and can miss details.

This article is the whole of episode 7 in writing, so you can follow it without the video. Every claim about Claude Code is taken from the official [Subagents page](https://code.claude.com/docs/en/sub-agents) (the page is long; I read about 40,000 of 116,000 characters verbatim, so a few points rest on a summary and are marked), and every claim about multi-agent systems from Anthropic's engineering post [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (June 2025). Where the docs are silent, I say "our version does it this way".

**What you will be able to do afterwards**

- Say what a subagent is, why an agent uses one, and what it costs.
- Build the small version: a `delegate` tool that starts a fresh read-only loop and returns one final answer.
- Read a real two-setup test, and the context bug it exposed in [episode 5](ep05-context.md)'s manager.

**Before you start:** the agent from [episode 6](ep06-plan-and-tasks.md). Run the code only inside a throwaway folder.

---

## 1. The problem

Everything the agent reads stays in its context ([episode 5](ep05-context.md)). If you only want one answer, the agent has still read many files, and every later step carries them along. Our task shows it: build a table of the Xiaohongshu notes posted from 13 to 19 November (21 of them) from a log file, opening each post file to copy its topic tags.

## 2. What a subagent is

A subagent is a small helper the main agent sends out. It has its own fresh conversation, does one small job, and brings back only a short conclusion. Like sending an assistant to the library: they read many books, you receive one page.

Benefits: the main context stays clean; and ours can only read and search, so it cannot change anything. Costs: more tokens, and the page it brings back can miss details. Anthropic's post says agents use about 4 times the tokens of a chat, and their multi-agent research system about 15 times. So it is not always worth it.

## 3. What Claude Code and Anthropic say

- Claude Code: "Each subagent runs in its own context window" and returns only the summary. Built-ins include Explore (read-only, fast, for searching), Plan (the research agent used in plan mode) and general-purpose. You can define your own as a Markdown file with YAML frontmatter; only `name` and `description` are required, and fields include `tools`, `model`, `permissionMode` and `maxTurns`. The docs suggest one "when a side task would flood your main conversation with search results, logs, or file contents you won't reference again". [From a summary: non-fork subagents start fresh and do not see the conversation history.]
- Anthropic's research system: an orchestrator-worker pattern: a lead agent coordinates subagents that work in parallel and act as "intelligent filters", each condensing "the most important tokens for the lead". Its internal evaluation: a Claude Opus 4 lead with Claude Sonnet 4 subagents outperformed a single Opus 4 by 90.2%. A good brief gives each subagent "an objective, an output format, guidance on the tools and sources to use, and clear task boundaries"; a vague brief made them misread the task or duplicate searches.
- The same post says these systems "burn through tokens fast", fit poorly when agents must share context, and that coding has "fewer truly parallelizable tasks than research".

## 4. Our version

`delegate(task)` in [`ep07/agent.py`](../ep07/agent.py): start a new loop with a fresh message list, only `read_file` and `grep`, a turn limit, and return the last text of that loop to the main agent. One helper at a time, no parallelism (Anthropic's is parallel). The helper cannot see the main conversation, so the task you write is everything it knows: that is the number one thing to get right.

## 5. The real test

`deepseek-flash`, every earlier part switched on. The task above (21 notes). Scoring by code: how many table rows are right (date, platform, title), how many rows have all topic tags right, and how many model calls it took (one call is one turn of the loop). Two setups, three runs each (`ep07/demos.py`, results in [`ep07/demo/`](../ep07/demo/)): the agent on its own, and the task telling it to delegate the file reading.

| | On its own | Told to delegate |
|---|---|---|
| table fully right | 2 of 3 (the third: 20 of 21 rows) | 2 of 3 (the third: 20 rows) |
| rows with all tags right | 21, 21, 20 | 21, 20, 21 |
| model calls | 34, 40, 75 | 26, 28, 33 |

Fewer calls in all three delegated runs. But in the first delegated run no helper was used at all; the second used one, the third two. Three runs each, so I do not say delegation is better. What I can say: in this task the main context never grew past about 16,000 tokens, which is small anyway, so the benefit we expected was not visible.

## 6. A pitfall we hit

Episode 5's context manager compacted far too often. In the first round, an old-version run compacted 35 times on average. Our diagnosis: the fixed parts (system prompt, tools, notes) already sit near the trigger line, so compacting cannot bring the window under it. The fix: after a compaction, wait until the context has grown by another 3,000 tokens before compacting again. Now it is fewer than 4 compactions per run. I also raised the turn limit from 60 to 100 in the same change, because one run needed 75 calls. Both changes went in together, so I cannot say how much each helped.

## 7. What this does not do

- Sequential, not parallel; helpers are read-only; no custom subagent files, no per-subagent model.
- Claude Code's subagents do not get the main conversation's auto memory; ours do not either, but we did not test it.
- Three runs, one model, one task.

## 8. Recap

1. A subagent is a fresh conversation that returns one answer: the main context stays clean.
2. It costs tokens, and the answer can miss details.
3. Write the task as if the helper knows nothing: it cannot see your chat.
4. Measure before you believe: here the expected benefit did not show up.

**Next:** [episode 8](ep08-hooks.md), hooks.

## References

- Claude Code docs, Subagents: https://code.claude.com/docs/en/sub-agents
- Anthropic engineering, How we built our multi-agent research system (2025-06-13): https://www.anthropic.com/engineering/multi-agent-research-system
- Code and real runs: [`ep07/agent.py`](../ep07/agent.py), [`ep07/demos.py`](../ep07/demos.py), [`ep07/demo/`](../ep07/demo/)
