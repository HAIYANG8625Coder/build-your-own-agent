# 从零做一个 Claude Code 式 Agent

One folder per episode, one small file you can read in a few minutes.

## Setup
    pip3 install anthropic
    export ANTHROPIC_API_KEY=...        # your own key from console.anthropic.com (a Claude Pro plan does not include API access)
    python3 ep01/agent.py "这个文件夹里有什么？"

## Provider switch (optional)
The same code runs on DeepSeek through its Anthropic-compatible endpoint:

    export DEEPSEEK_API_KEY=...
    PROVIDER=deepseek python3 ep01/agent.py "这个文件夹里有什么？"

Default is `PROVIDER=claude` (model `claude-haiku-5-5`). DeepSeek uses `deepseek-flash` at `https://api.deepseek.com/anthropic`.

## Test without a key
    python3 ep01/test_loop.py

| Episode | What it adds |
|---|---|
| ep01 | the loop: call the model, run the tool it asks for, append the result, repeat, stop on no tool call or max turns |

## Episodes
Each episode is one commit and one folder, so you can check out a single step.

## Notes
- Keys come from environment variables only. Never commit them (the `.gitignore` blocks `.env` files).
- The code follows Anthropic's message format. The DeepSeek option uses DeepSeek's Anthropic-compatible endpoint.
- Claude Code behavior described in the videos comes from its official documentation, not its source code.
