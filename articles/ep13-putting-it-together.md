# Episode 13 · Putting it together: one finished command-line agent

*Part E · Ship it. The last episode. Video: "Build your own agent · 13: putting it together". Code: [`ep13/`](../ep13/).*

**Series:** [← README](../README.md) · [← Ep 12: Testing and debugging](ep12-testing-and-debugging.md)

**Key idea:** A finished agent is the loop plus a chat wrapper: a kept conversation, streaming, saved sessions, and a repaired half turn after Ctrl+C.

This article is the whole of episode 13 in writing, so you can follow it without the video. The Claude Code facts come from its docs (interactive mode, how it works, sessions, checkpointing, commands, security, sandboxing, sub-agents, headless mode) and the streaming facts from Anthropic's Messages API documentation. Where the docs are silent, I say "our version does it this way".

**What you will be able to do afterwards**

- Turn a one-task agent into a chat: keep the conversation between prompts, show the text as it arrives, save every turn, resume a chat later.
- Stop a turn with Ctrl+C without breaking the chat, and say why the half turn has to be closed.
- Run the finished agent and read a real, recorded session.
- Say what Claude Code has that ours does not, with the docs page for each item.

**Before you start:** the agent from [episode 12](ep12-testing-and-debugging.md). The code for this episode is a copy of its `agent.py` (changed in two places), plus `repl.py`. Run it only inside a throwaway folder.

---

## 1. The problem

For twelve episodes, our agent took one task and quit. A tool you use for an hour needs a conversation. We tested the simplest version of the problem: four questions in a row on the shop project, and the last one is "which files did you change in this chat?". If every question starts from nothing, the agent cannot know. In 5 runs it answered right 0 times.

## 2. The words

- A **chat loop** (*REPL*, read-eval-print loop) reads a line you type, runs it, prints the answer, and waits for the next line.
- **Streaming** means the model sends its reply in small pieces while it writes, and the program shows each piece as it comes, so you do not wait for the whole answer.
- A **session** is the whole conversation saved to a file, so you can come back to it.
- A **slash command** is a line that starts with `/`. It is a command to the program, not a question for the model.
- An **interrupt** (Ctrl+C) stops the current turn without closing the program.

## 3. What Claude Code and the API do (official docs)

**The loop and the keys** ([interactive mode](https://code.claude.com/docs/en/interactive-mode), [how Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)):

- The loop has three phases that blend into one another: "gather context, take action, verify results". You can interrupt at any point.
- `Esc` stops the current response or tool call and keeps the work done so far. When nothing is running, the first `Ctrl+C` clears the prompt and a second one exits. `Ctrl+D` exits when pressed twice within 800 ms.
- Input can span several lines (a backslash then Enter, or Ctrl+J). The history is kept per working directory.

**Sessions** ([sessions page](https://code.claude.com/docs/en/sessions)):

- Every message, tool call and result is written to a plain-text file under `~/.claude/projects/`. The docs warn that the format is internal and changes between versions.
- `claude --continue` reopens the latest session of this folder, and `claude --resume` lets you pick one. A resumed session gets its history, model and permission mode back. A tool call that was interrupted is not run again.
- `/clear` starts a new conversation, `/compact` summarizes, `/context` shows what fills the window.

**Checkpoints** ([checkpointing page](https://code.claude.com/docs/en/checkpointing)): every prompt that starts a turn creates a checkpoint, and `/rewind` can restore the files, the conversation, or both. Only changes made by the file-edit tools are tracked, not changes made by shell commands. The docs say it is not a replacement for git.

**Streaming** ([Anthropic's streaming documentation](https://platform.claude.com/docs/en/build-with-claude/streaming)): the events come in order: a message starts, each content block starts, sends zero or more *delta* events and stops, and the message ends. Text arrives as `text_delta`. A tool call arrives as `input_json_delta` pieces of JSON that you collect and parse when the block ends. The Python SDK has a helper for this: `client.messages.stream(...)` gives `text_stream` (the text pieces) and `get_final_message()` (the same object a normal call returns). For scripts, Claude Code offers `--output-format stream-json` with `--include-partial-messages`.

## 4. Our version

Two small changes in the engine, `agent.py`:

1. `run()` can continue a conversation. If you pass the message list that an earlier call returned, the new task becomes the next user message.
2. The model call is one function. With streaming on, it hands the text pieces to a callback and then gets the final message, so the loop does not change. Content blocks are plain dictionaries, so a whole conversation saves to JSON as it is and loads back without any conversion.

`repl.py` is the finished agent (301 lines). It adds:

- the chat loop, with multi-line input (a backslash continues the line);
- text that appears while the model writes, and one short line for every tool call;
- a save to disk after every turn, `--continue` and `--resume ID`;
- **Ctrl+C**: during a turn it stops the turn and keeps the chat. At the prompt the first press only warns, and a second in a row leaves;
- 12 slash commands: `/help`, `/exit`, `/clear`, `/context`, `/compact`, `/plan`, `/todo`, `/perms`, `/memory`, `/features`, `/sessions`, `/usage`.

Episodes 1 to 9 and 11 are switched on: tools, notes, permissions, context management, the task list, plan mode (`/plan`), helpers, hooks (if `.agent/hooks.json` exists), memory, skills (if the folder exists), and MCP (with a switch). Episode 10's always-on runner shares the same engine, but it is a separate program and it is not part of the chat.

All of it is 1,486 lines (`agent.py` 1,075, `repl.py` 301, `mcp_client.py` 110, comments and blank lines included).

There are 38 checks in `test_repl.py`. They need no API key because they use a scripted **fake model**, not a real one. They test our code: that the second prompt sees the first answer, that text arrives in order, that a chat is saved and resumed, that Ctrl+C closes the turn, that the slash commands and plan mode work, and that the permission gate asks. They do not test how the real model behaves. For that, the real runs below need a key.

## 5. A real session

We recorded one real session in a terminal, with the real model (DeepSeek, `deepseek-flash`). `screen/record_demo.py` types the user's side and presses a real Ctrl+C (the byte 0x03). Everything else is printed by the program. The recording and its recorder are in [`ep13/screen/`](../ep13/screen/). Here is the part with the interrupt and the resume (lines cut with `…`):

```text
> Read every .py file in this folder and describe each one in two sentences.
  Allow run_bash {"command": "find . -name \"*.py\" -not -path \"./.git/*\" | sort"} ?
  [y] once  [a] always this session  [n] no > a
  . run_bash {"command": "find . -name \"*.py\" -not -path \"./.git/*\" | sort"} -> allow
^C[stopped]
> What is the tax rate now? One short answer.
8% (`TAX_RATE = 0.08` in `config.py`).
> /context
36 messages, about 6053 tokens (last call: 7152)
> /exit
bye

$ python3 repl.py --continue
agent chat …  (model deepseek-flash, resumed)  /help for commands, Ctrl+D to leave
> Which file did you read first in this chat? Answer with the path only.
cart.py
```

What happens, step by step:

1. "What does cart.py do?" The answer streams in. Two tool calls: list the folder, read a file.
2. "Which file holds the tax rate?" It remembers the chat and finds the config file.
3. "Change the tax rate to 8% and update whatever else needs it." The agent loads the project's pricing skill, reads files, and **asks before every edit or command that changes something**. We answer "always this session". It changes the config, the README and the changelog, updates the tests and runs them.
4. "List every file you changed in this chat." It answers with the four files.
5. A real Ctrl+C in the middle of a turn. The screen shows `^C[stopped]`.
6. "What is the tax rate now?" The chat still works: 8%.
7. `/context` shows 36 messages. `/exit`.
8. A new process with `--continue`. "Which file did you read first?" It answers: `cart.py`.

## 6. The real tests

Model: DeepSeek, every earlier part on, 5 runs per setup, 30 runs.

**Test 1 · a kept chat.** Four prompts: what does `cart.py` do; where is the tax rate; change it to 8% and update what needs it; list every file you changed. *Kept*: one chat. *Fresh*: every prompt starts from nothing.

**Test 2 · streaming.** One question that needs no tools. We measure the time from sending it to the first text on the screen. *Stream* and *plain* take turns, one run at a time, so the API load is the same.

**Test 3 · Ctrl+C.** At the first tool call we raise the interrupt, then ask another question. *Repair*: the half turn is closed before the next prompt. *Control*: it is not. (We raise `KeyboardInterrupt` from the code, because a key press cannot be scripted. It happens when the first tool call has just been announced and its result has not arrived yet. Other moments were not tested. The recorded session above used a real key.)

**Test 4 · resume.** Run a chat and leave. Start a new process with `--continue` and ask which file it read first.

## 7. Results

**Test 1.** The tax change was right in 5 of 5 runs in both setups. "List every file you changed": kept 5 of 5, fresh 0 of 5. That one is obvious: the fresh agent cannot know. The second question took 2.4 tool calls on average in the kept chat and 4.6 when fresh, probably because the kept chat has already read the files (this is our guess). Tokens read in total: kept 101,105, fresh 88,425 on average, with runs from 59,533 to 153,509. So we cannot say a kept chat costs more or less.

**Test 2.** The first text appeared after 5.1 seconds on average when streamed (the five runs: 0.69, 4.41, 6.46, 6.64, 7.30) and after 7.04 seconds when not streamed. Compared with each run's own end, streaming showed text 1 to 7 seconds earlier. The whole text was not finished sooner: 7.44 seconds streamed against 7.04 not. We think the model thinks silently before it writes, which is why the first text is late; this is our reading, not a measured result.

**Test 3.** With the repair, the next prompt worked in 4 of 5 runs. Without it, in 0 of 5: the API refused every time ("`tool_use` ids were found without `tool_result` blocks").

**Test 4.** The new process resumed the chat and answered right in 5 of 5.

**Summary.** The chat works, and resume works. Streaming brings the first text earlier but does not finish sooner. The repair for Ctrl+C is necessary. Five runs each, one model, one small project.

## 8. Three pitfalls we hit

1. **Ctrl+C leaves a half turn.** The last message is the model asking for a tool and the result never came. The next prompt is rejected by the API, and the chat is dead (0 of 5 without the repair). The fix is short. Before the next prompt, give every open tool call a result ("stopped by the user") and add a short assistant message, so the turns alternate and every call has a result.
2. **The model may take "stopped" as final.** In 1 of 5 repaired runs, the model read "stopped by the user" as the answer and replied "I don't know" instead of looking again. We did not fix this.
3. **`--no-stream` printed nothing.** The first version showed no answer at all when streaming was off. We found it ourselves before the real tests and print the final text at the end of the turn.

## 9. What Claude Code has that ours does not

From the official docs, each with its page:

- **A sandbox for commands** ([sandboxing page](https://code.claude.com/docs/en/sandboxing)). It is off by default. When on, it limits writes to the working directory and sends network traffic through a proxy with an allowed-domain list. Our permission gate only decides whether a command runs, not what it can touch once it runs.
- **An automatic permission mode** where a separate model reviews actions, a trust dialog for new folders, and approval for project MCP servers ([security page](https://code.claude.com/docs/en/security)).
- **Subagents as files** with their own tools, model, permission mode and memory, plus built-in read-only helpers (sub-agents page).
- **Checkpoints and `/rewind`** (checkpointing page), a **session picker** and **branching** (sessions page).
- **Richer input**: line-editing keys, history search, image paste (interactive mode page).
- **Many more commands**, **managed (company-wide) settings** and **cloud sessions** (commands, security and sandboxing pages).

## 10. Recap

1. A chat needs a kept conversation, streamed text, a saved session and an interrupt.
2. The changes to the engine were small: continue a list of messages, one function for the model call, messages as plain dictionaries.
3. Close the half turn after Ctrl+C, or the next prompt is refused.
4. Streaming shows the first text sooner, not the last.
5. An agent is a loop, some tools, and a few boundaries. The rest is plumbing you can read.

**The series is finished.** In thirteen episodes you built an agent of about 1,500 lines that reads and writes files, asks before it acts, manages its context, plans, delegates, uses hooks, remembers, takes outside tools and skills, can be tested, and now chats.

**What comes next (a plan, not done).** The next series is planned as an enterprise-class agent: what changes when many people use it, who is who, what it may touch, what happened and what it cost. The plan is a draft and will change. If you read this and have a request for what should come first, say so in the comments on the video.

**Try it:** `python3 test_repl.py` in `ep13/` (38 checks, no key). Then, in a throwaway folder, `python3 ../repl.py` with `PROVIDER=deepseek` and `DEEPSEEK_API_KEY` set, and ask it something.

## References

- Claude Code docs: interactive mode, how Claude Code works, sessions, checkpointing, commands, security, sandboxing, sub-agents, headless mode: https://code.claude.com/docs/en/
- Anthropic, the Messages API streaming documentation (event order, text and JSON deltas, the SDK stream helpers): https://platform.claude.com/docs/en/build-with-claude/streaming
- Code, tests and real runs: [`ep13/repl.py`](../ep13/repl.py), [`ep13/agent.py`](../ep13/agent.py), [`ep13/test_repl.py`](../ep13/test_repl.py), [`ep13/demos.py`](../ep13/demos.py), [`ep13/demo/`](../ep13/demo/), [`ep13/screen/`](../ep13/screen/)
