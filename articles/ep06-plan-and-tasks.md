# Episode 6 · Plan mode and the task list

*Part C · Working at scale. Video: "Build your own agent · 06: plan mode and the task list". Code: [`ep06/`](../ep06/).*

**Series:** [← README](../README.md) · [← Ep 5: Context](ep05-context.md) · [Ep 7: Subagents →](ep07-subagents.md)

**Key idea:** Plan mode lets you review the plan before anything changes, and a task list tracks progress, at the cost of roughly double the turns in our test.

This article is the whole of episode 6 in writing, so you can follow it without the video. Every claim about Claude Code is taken from the official pages linked inline. Where the docs are silent, I say "our version does it this way".

**What you will be able to do afterwards**

- Say what plan mode and a task list are, and why a long task needs them.
- Build both in a few lines: a read-only mode with a `submit_plan` tool, and a `todo_write` tool.
- Read a real three-setup test, and say what it can and cannot show.

**Before you start:** the agent from [episode 5](ep05-context.md). The code for this episode is a copy of `ep05/agent.py` plus the two features. Run it only inside a throwaway folder.

---

## 1. The problem

The loop of [episode 1](ep01-the-loop.md) is: look, do a step, look again. The agent's plan exists only inside the model. A short task is fine. A long one is not: the conversation grows, the early requirements drift far away, and steps get missed. Two accidents follow: a step is skipped, or the agent says "done" before it is. Anthropic's article on long-running agents names the second one: the agent "declares victory on the entire project too early" ([Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)).

## 2. Plan mode

Plan mode means: before touching anything, only look, write a plan, and wait for the user to agree. It is like reading the drawings before knocking down a wall. Without it, a misunderstood task may already have changed many files. With it, the check moves to before the change, and correcting one sentence is cheap. It also forces reading before writing.

Claude Code has it. From the [Permission modes page](https://code.claude.com/docs/en/permission-modes): you cycle modes with `Shift+Tab`, or start with `claude --permission-mode plan`; in plan mode "Claude reads files, runs shell commands to explore, and writes a plan, but does not edit your source", and edits "stay blocked until you approve the plan". When the plan is ready Claude presents it and asks how to proceed; approving exits plan mode and Claude starts editing. `Ctrl+G` opens the plan in your editor.

## 3. The task list

A task list splits a big task into small items, each with one of three states: pending, in progress, done. Like a shopping list: buy one, cross one off. An agent needs it because it has no reliable notebook, so early steps get pushed out of view in a long task. In our version the list is shown to the model every turn, and while an item is unfinished the agent is not allowed to hand in a final answer.

Claude Code has it too. The [Interactive mode page](https://code.claude.com/docs/en/interactive-mode) calls it "Claude's to-do checklist"; `Ctrl+T` shows or hides it, and it persists across compaction. The [Tools reference](https://code.claude.com/docs/en/tools-reference) lists `TaskCreate`, `TaskGet`, `TaskList` and `TaskUpdate`; the older `TodoWrite` tool is "disabled by default in favor of" them. The docs do not give the task fields, so what follows is our own design: the simpler, older shape.

## 4. Our version

- **Plan mode.** A flag. In plan mode the model is offered only the read tools plus `submit_plan(plan)`; the write tools are not offered, and are refused if called anyway. `submit_plan` shows the plan and waits. Approval switches to normal mode and puts the plan in the context. (In a test, a function approves for you.)
- **Task list.** One tool, `todo_write(items)`. You pass the whole list every time; each item has a `task` and a `status` of `pending`, `in_progress` or `done`; only one item can be `in_progress`. The rule given to the model: mark an item done only after you checked it. The list is printed back as the tool result.

`python3 test_plan.py` in `ep06/` runs without an API key.

## 5. The real test

`deepseek-flash`. A sandbox repository with 4 plugins, 9 skills and 4 subagents, into which we planted 12 errors on purpose. The task: check it against the rules and fix them all, 60 places in total. Three setups, five runs each (`ep06/demos.py`, results in [`ep06/demo/`](../ep06/demo/)): nothing added; the task list; plan mode plus the task list.

| | Nothing added | Task list | Plan + task list |
|---|---|---|---|
| places fixed correctly | 59 of 60 | 60 of 60 | 60 of 60 |
| mean turns | about 15 | about 30 | about 27 |

The single miss was in the first setup: a missed link, and a final answer that said everything conformed. That is one run, not a rule. Five runs each, and one error, so I cannot say the task list is more accurate. What I can say: it roughly doubled the number of turns. Two smaller tasks, also run, were all correct. I did not test what plan mode adds; its value is mainly that you look before the change.

## 6. Two pitfalls we hit

1. My first version also blocked reading in plan mode, so the agent had to write its plan blind. Reads belong in plan mode.
2. In the first version, a long plan was cut off at the output limit, and in two of five runs not one file was changed. A truncated reply is now discarded and the model is asked for a shorter one.

One lesson on the list itself: each item should be checkable. "Fix all problems" is not an item; "fix the link in skill X, then run the check" is.

## 7. What this does not do

- Our list is the older single-tool shape; Claude Code now has separate create and update tools with more fields.
- No plan file, no editing the plan, no "approve and clear context". Claude Code has them.
- One task, one model, five runs.

## 8. Recap

1. Plan mode is for you: look at the plan before anything changes.
2. The task list shows progress, and may help the agent miss fewer steps.
3. They cost turns: about double here. A short task may not need them.
4. Every item needs a way to check it.

**Next:** [episode 7](ep07-subagents.md), subagents.

## References

- Claude Code docs, Permission modes (plan mode): https://code.claude.com/docs/en/permission-modes
- Claude Code docs, Interactive mode (the task list, `Ctrl+T`): https://code.claude.com/docs/en/interactive-mode
- Claude Code docs, Tools reference (the task tools): https://code.claude.com/docs/en/tools-reference
- Anthropic engineering, Effective harnesses for long-running agents: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents · Building effective agents: https://www.anthropic.com/engineering/building-effective-agents
- Code and real runs: [`ep06/agent.py`](../ep06/agent.py), [`ep06/demos.py`](../ep06/demos.py), [`ep06/demo/`](../ep06/demo/)
