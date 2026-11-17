"""Episode 1: an agent is a loop.

    python3 agent.py "这个文件夹里有什么？"

PROVIDER=claude (default) -> ANTHROPIC_API_KEY, claude-haiku-5-5
PROVIDER=deepseek         -> DEEPSEEK_API_KEY, deepseek-flash
"""
import os
import sys

import anthropic

MAX_TURNS = 10

SYSTEM = ("You are a small assistant. "
          "Use tools, then answer briefly.")

TOOLS = [{
    "name": "list_files",
    "description": "List the files in a folder.",
    "input_schema": {
        "type": "object",
        "properties": {"path": {"type": "string"}},
    },
}]


def list_files(path="."):
    return "\n".join(sorted(os.listdir(path)))


def run_tool(name, args):
    if name != "list_files":
        return "error: unknown tool"
    try:
        return list_files(**args)
    except Exception as e:
        return "error: %s" % e


def run(task, client, model):
    messages = [{"role": "user", "content": task}]
    for turn in range(1, MAX_TURNS + 1):
        resp = client.messages.create(
            model=model, max_tokens=1024,
            system=SYSTEM, tools=TOOLS,
            messages=messages)
        reply = {"role": "assistant",
                 "content": resp.content}
        messages.append(reply)
        print("turn", turn, resp.stop_reason)
        if resp.stop_reason != "tool_use":
            return messages
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                out = run_tool(block.name,
                               block.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": out})
        messages.append(
            {"role": "user", "content": results})
    return messages


def final_text(messages):
    last = messages[-1]["content"]
    return "".join(b.text for b in last if b.type == "text")


PROVIDERS = {
    "claude": ("ANTHROPIC_API_KEY", None, "claude-haiku-5-5"),
    "deepseek": ("DEEPSEEK_API_KEY",
                 "https://api.deepseek.com/anthropic",
                 "deepseek-flash"),
}


def make_client():
    key, url, model = PROVIDERS[os.environ.get("PROVIDER", "claude")]
    return anthropic.Anthropic(api_key=os.environ[key], base_url=url), model


if __name__ == "__main__":
    client, model = make_client()
    task = " ".join(sys.argv[1:]) or "这个文件夹里有什么？"
    print(final_text(run(task, client, model)))
