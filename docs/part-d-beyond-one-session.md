# D · Beyond one session (episodes 9 to 11)

What does the agent remember after a session ends, can it work while you are away, and can it use tools someone else wrote?

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/part-d-dark.svg">
  <img alt="Architecture: memory is loaded when a new session starts; an inbox and timers feed events into the same loop; an MCP server provides tools that others wrote." src="img/part-d.svg">
</picture>


**You need the code from parts A to C.**

## Episodes in this part

- **Episode 9 · Memory** (code: `ep09/`): A notes folder that stores only what can't be looked up again, an index loaded at the start, and an optional offline cleanup.
- **Episode 10 · Always on** (code: `ep10/`): An inbox, timers, the loop running as a daemon, an outbox, and what the agent may do when nobody can approve.
- **Episode 11 · MCP and skills** (code: `ep11/`): Connect to an MCP server's tools and load skill files on demand; these tools still go through the permission gate.

## What you have afterwards

An agent that works over time, remembers things, and can use external tools.

Back to the [syllabus](../SYLLABUS.md) or the [project home](../README.md).
