# Episode 12 · Testing and debugging an agent: did that change help?

*Part E · Ship it. Video: "Build your own agent · 12: testing and debugging". Code: [`ep12/`](../ep12/).*

**Series:** [← README](../README.md) · [← Ep 11: MCP and skills](ep11-mcp-and-skills.md) · [Ep 13: Putting it together →](ep13-putting-it-together.md)

**Key idea:** One run proves nothing: run fixed tasks several times, grade the outcome, save the trace, change one thing at a time, and read failed traces.

This article is the whole of episode 12 in writing, so you can follow it without the video. The ideas about evaluation come from Anthropic's engineering article "Demystifying evals for AI agents" (published 2026-01-09). The Claude Code facts come from its docs (headless mode, the command-line reference, costs, troubleshooting, sessions). Where the docs are silent, I say "our version does it this way".

**What you will be able to do afterwards**

- Say what a *task*, a *trial*, a *grader* and a *trace* are, and why one run proves nothing.
- Build a small evaluation harness: fixed tasks, a clean copy of the project for every trial, a saved trace, a grader that looks at the result, and a table.
- Change one thing, run the same tasks, and say whether it helped, did nothing, or cannot be told apart at this sample size.
- Read a failed trace, and spot a grader that is too strict.

**Before you start:** the agent from [episode 11](ep11-mcp-and-skills.md). The code for this episode is a copy of its `agent.py` plus `eval.py`. Run it only inside a throwaway folder.

---

## 1. The problem

You change one sentence in the system prompt, run the agent once, and it works. Was it the sentence, or luck? The model takes a slightly different path every time, even with the same prompt and the same project.

Here is a real case from our tests. The same task, the same setup, five runs. Four finished the work. One stopped after two model turns: its first shell command was refused by the permission rules, and it gave up as the rules say it should. If you had seen only that run, you would have thought the change broke something.

## 2. The words

- A **task** is one test: a fixed input and a rule for what counts as success.
- A **trial** is one attempt at a task. The agent varies from run to run, so you run each task several times.
- A **grader** is logic that scores a result. A code grader is fast, cheap and the same every time, but it can be too strict about a different valid answer.
- A **trace** (or *transcript*) is the full record of one trial: every message and every tool call. The score tells you *whether* it worked; the trace tells you *why*.
- An **outcome** is the final state of the environment (the files), not the sentence the agent says.

Two numbers per task are useful when you run it five times: how many runs passed, and whether all five did. For something you ship, the second one matters.

## 3. What Anthropic and Claude Code say

**The article ["Demystifying evals for AI agents"](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)** (2026-01-09):

- It uses the same words: task, trial, grader, transcript, outcome, and "evaluation harness" for the program that runs tasks, records every step, grades, and adds up.
- Grade "what the agent produced, not the path it took". Do not check an exact order of tool calls.
- Kinds of graders: code-based (fast, objective, but brittle against valid variations), model-based (flexible, but not deterministic and it needs calibration), and human (the gold standard, slow and expensive). Use code where you can, a model where you must, and humans sparingly.
- "20-50 simple tasks drawn from real failures is a great start". Early on, a change has a large effect, so small samples are enough.
- A task that scores 0% over many trials most often means a broken task or grader, not a weak agent. Read the transcripts: "You won't know if your graders are working well unless you read the transcripts and grades from many trials."
- Each trial should start from a clean environment. Leftover files and shared state cause failures that depend on each other.
- A test that is at 100% "tracks regressions but provides no signal for improvement". This is called *saturation*.

**Claude Code** ([headless mode](https://code.claude.com/docs/en/headless), [command-line reference](https://code.claude.com/docs/en/cli-reference), [costs](https://code.claude.com/docs/en/costs), [sessions](https://code.claude.com/docs/en/sessions)):

- `claude -p` runs once without a screen. `--output-format json` returns the result, a session ID and an estimated cost. `stream-json` gives one event per line.
- `--max-turns` and `--max-budget-usd` are caps (the cost is an estimate computed from token counts, so it can overshoot).
- `--debug` takes category filters and `--debug-file` writes the log to a file. `--safe-mode` starts with all your customizations off: if the problem goes away, one of those caused it. `--restricted` is described as intended for evaluation harnesses.
- Session transcripts are saved as JSONL files, but the docs say the format is internal and changes between versions. The docs do not offer a test harness for your own tasks, so you build one.

## 4. Our version

`eval.py` has four fixed tasks on the small shop project.

| Task | Prompt | The grader checks |
|---|---|---|
| version | bump the version from 1.0.0 to 1.1.0 | config, README, the program prints the new version, no old version left (the changelog history must stay), tests pass |
| tax | the tax rate is now 8% instead of 7% | config, README, tests pass, tests expect 108, and `calc_total([100])` gives 108.0 |
| discount | add `apply_discount(prices, percent)` and a test | the example gives 96.3, a second case gives 128.4, tests pass, a test exists |
| readonly | what does `orders.csv` say about order 1042? Do not change any files | the answer has "shipped on 18 Nov" and no file changed |

Four design rules:

1. **A clean copy for every trial.** A check proves that one trial's changes do not reach the next.
2. **The grader looks at the result.** It runs the program and reads the files.
3. **Every trial saves its whole message list as JSON**, with the turns and tokens read.
4. **One change at a time.** The two setups differ by one sentence in the rules, and everything else is the same.

A table prints, for each task and setup: passed out of 5, mean turns, mean tokens read, and the least and most tokens. There are 20 checks in `test_eval.py`. They need no API key: hand-made workspaces play the agent's result, and the checks confirm that the grader passes a right result and fails a wrong one.

## 5. The real tests

Model: DeepSeek (`deepseek-flash`). 4 tasks × 2 setups × 5 trials = 40 runs.

**The change under test.** We wrote it down before the first run. The sentence added to the rules: "When you change a value, search the whole project for every other place it appears and change those too." Our guess: the version and the tax rate are written in several files, so the agent will get them all right more often, at the cost of a few more turns. We expected no effect on the discount task and the read-only task.

## 6. Results

| Task | Passed, rules only | Passed, with the sentence | Mean tokens read, rules only | Mean tokens read, with the sentence |
|---|---|---|---|---|
| version | 5 / 5 | 4 / 5 | 13,918 | 18,040 |
| tax | 5 / 5 | 5 / 5 | 13,822 | 19,240 |
| discount | 5 / 5 | 4 / 5 | 22,137 | 22,464 |
| readonly | 5 / 5 | 5 / 5 | 3,625 | 3,506 |

Together: 20 of 20 without the sentence, 18 of 20 with it.

**What this says.**

- The sentence did not help. Without it the agent already passed every run, so these tasks were too easy to show an improvement (Anthropic's *saturation*).
- With the sentence, the agent read about a third to two fifths more tokens on the version and tax tasks. The runs vary a lot (with the sentence, the version task read between 12,472 and 23,424 tokens), so this is a hint, not a proof. The discount average is pulled down by one run that stopped early (1,775 tokens). The other four runs average 27,637, about a quarter more.
- Two failures, both read in the trace:
  - **version, with the sentence, run 2.** The agent hunted for every "1.0.0" and merged the changelog's first entry into the new one, so the history was lost. This is a harm the sentence could cause, but it is one run of five.
  - **discount, with the sentence, run 5.** The first command was a long "find and show" command that the permission rules did not allow. The agent obeyed and stopped after two turns. This looks unrelated to the sentence, but the rules-only runs did not hit it, and with five runs we cannot be sure.

## 7. Two pitfalls we hit

1. **A grader that was too strict.** In the first trial of the version task, our grader failed a right answer. It wanted the exact text `shop v1.1.0` in the file, but the agent had made the banner read the version from the config, which is better. The program printed the right banner, and the grader could not see it. We changed the grader to run the program and read its output, before the counted runs, and both setups use the same grader. If nobody had read that trace, the wrong score would have been believed.
2. **A trial that ends early looks like a weak agent.** The run that stopped after two turns lowered an average and could have been blamed on the change. Read the trace before you trust a number.

## 8. What this does not do

- Four easy tasks, five trials, one model. The test could not show an improvement because the baseline was already perfect.
- No model-based grader, no large task set, no automatic run on every change.
- Our token numbers count what the model read in all calls of a run. They are not a bill.

## 9. Recap

1. One run proves nothing. Run each task several times.
2. A grader should look at the outcome, and the outcome should be checked by running the program, not by comparing the wording.
3. Save the whole trace. Read at least one failed trace before you trust a score.
4. Change one thing at a time, and write down what you expect before you run.
5. If the baseline is already perfect, the test cannot show a gain.

**Next:** episode 13, putting it together into one command-line agent.

**Try it:** `python3 test_eval.py` in `ep12/`. Then run `python3 eval.py run tax base 1` in a throwaway folder and open the saved trace.

## References

- Anthropic Engineering, Demystifying evals for AI agents (2026-01-09): https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- Claude Code docs: headless mode, the command-line reference, costs, troubleshooting, sessions: https://code.claude.com/docs/en/
- Code and real runs: [`ep12/eval.py`](../ep12/eval.py), [`ep12/test_eval.py`](../ep12/test_eval.py), [`ep12/agent.py`](../ep12/agent.py), [`ep12/demo/`](../ep12/demo/)
