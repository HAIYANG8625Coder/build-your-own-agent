# A · Core (episodes 1 to 3)

This part does one thing: get a loop running, then give it hands and a sense of direction.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/part-a-dark.svg">
  <img alt="Architecture: the system prompt and notes file and the model API both connect to the agent loop; the loop uses tools through tool_use and tool_result." src="img/part-a.svg">
</picture>


**You need Python and an API key.**

## Episodes in this part

- **Episode 1 · The loop** (code: `ep01/`): Call the model, check stop_reason, run the tool it asks for, append the result, repeat until it stops asking.
- **Episode 2 · Tools** (code: `ep02/`): read_file, grep, run_bash and edit_file; a tool's description is a prompt for the model; an error is just another result.
- **Episode 3 · The system prompt and the notes file** (code: `ep03/`): A short system prompt plus a notes file loaded at the start, with a few fixed tasks to compare before and after a change.

## What you have afterwards

A minimal agent that reads files, edits files and runs commands, following rules you wrote.

Back to the [syllabus](../SYLLABUS.md) or the [project home](../README.md).
