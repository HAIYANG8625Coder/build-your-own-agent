"""Build a small repo shaped like a real Claude Code plugin marketplace, with 12 known faults.

    python3 make_workrepo.py <folder>

The shape (4 plugins, 9 skills, 4 subagents, links in .claude/) copies how the author's own
workspace is organised. The rules in CLAUDE.md are the author's real pre-commit rules.
The faults are put in on purpose, so a run can be scored by whether each one got fixed.
"""
import hashlib, json, os, sys

PLUGINS = {
    "x-assistant": {"skills": ["x-post", "x-research", "x-image", "xhs-post", "youtube-post"],
                    "agents": ["x-drafter", "x-reviewer"]},
    "avatar-video": {"skills": ["avatar-video", "voice-video", "article-explainer"],
                     "agents": ["video-scripter", "video-reviewer"]},
    "outlook-email": {"skills": ["outlook-email"], "agents": []},
    "diagrams": {"skills": ["chart-draw"], "agents": []},
}
THIRD_PARTY = ["heygen-avatar", "heygen-video", "hyperframes", "media-use"]

CLAUDE_MD = """# Working in this repo

This repo is a Claude Code plugin marketplace. The short version of the rules:

- Every skill lives in `plugins/<plugin>/skills/<name>/SKILL.md` and every subagent in `plugins/<plugin>/agents/<name>.md`. Never create one directly in `.claude/`. Then link it: `ln -s ../../plugins/<plugin>/skills/<name> .claude/skills/<name>` (subagents: `ln -s ../../plugins/<plugin>/agents/<name>.md .claude/agents/<name>.md`).
- A plugin needs `plugins/<name>/.claude-plugin/plugin.json` (`name` = folder name, `version`, `description`) and an entry in `.claude-plugin/marketplace.json`.
- Every SKILL.md and every subagent file starts with frontmatter that has `name` and `description`.
- README.md has one table row for every skill and subagent (its path in backticks).
- Don't edit the third-party skills in `.claude/skills/` (`heygen-avatar`, `heygen-video`, `hyperframes`, `media-use`). They are updated by their installer.
- Before a commit, all of the above must hold.
"""


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(text)


def skill_md(name, describe=True):
    d = "description: Does the %s job for the author. Use when asked.\n" % name if describe else ""
    return "---\nname: %s\n%s---\n\n# %s\n\nSteps for %s go here.\n" % (name, d, name, name)


def agent_md(name, named=True):
    n = "name: %s\n" % name if named else ""
    return "---\n%sdescription: The %s subagent.\ntools: Read\n---\n\nInstructions for %s.\n" % (n, name, name)


def build(root, faults=True):
    market = []
    rows = []
    for plugin, parts in PLUGINS.items():
        manifest = {"name": plugin, "version": "0.1.0", "description": "The %s plugin." % plugin}
        market.append({"name": plugin, "source": "./plugins/" + plugin, "description": manifest["description"]})
        if faults and plugin == "diagrams":
            manifest["name"] = "diagram"                       # F4 name does not match the folder
        if faults and plugin == "outlook-email":
            del manifest["version"]                            # F5 no version
        if faults and plugin == "avatar-video":
            del manifest["description"]                        # F6 no description
        write(f"{root}/plugins/{plugin}/.claude-plugin/plugin.json", json.dumps(manifest, indent=2) + "\n")
        for s in parts["skills"]:
            write(f"{root}/plugins/{plugin}/skills/{s}/SKILL.md",
                  skill_md(s, describe=not (faults and s == "xhs-post")))          # F8
            rows.append("| `plugins/%s/skills/%s/` | the %s skill |" % (plugin, s, s))
        for a in parts["agents"]:
            write(f"{root}/plugins/{plugin}/agents/{a}.md",
                  agent_md(a, named=not (faults and a == "video-scripter")))       # F9
            rows.append("| `plugins/%s/agents/%s.md` | the %s subagent |" % (plugin, a, a))
    if faults:
        market = [m for m in market if m["name"] != "diagrams"]                    # F7
        rows = [r for r in rows if "youtube-post" not in r and "video-reviewer" not in r]   # F10, F11
    write(f"{root}/.claude-plugin/marketplace.json",
          json.dumps({"name": "claude-agents", "plugins": market}, indent=2) + "\n")
    write(f"{root}/README.md", "# claude-agents\n\nMy skills and subagents.\n\n| Path | What it is |\n|---|---|\n"
          + "\n".join(rows) + "\n")
    write(f"{root}/CLAUDE.md", CLAUDE_MD)
    for d in ("skills", "agents"):
        os.makedirs(f"{root}/.claude/{d}", exist_ok=True)
    for plugin, parts in PLUGINS.items():
        for s in parts["skills"]:
            if faults and s == "x-image":                                          # F1 no link
                continue
            target = "../../plugins/%s/skills/%s" % (plugin, s)
            if faults and s == "voice-video":
                target = "../../plugins/avatar-video/skills/voice_video"           # F3 broken link
            os.symlink(target, f"{root}/.claude/skills/{s}")
        for a in parts["agents"]:
            if faults and a == "x-reviewer":                                       # F2 no link
                continue
            os.symlink("../../plugins/%s/agents/%s.md" % (plugin, a), f"{root}/.claude/agents/{a}.md")
    for t in THIRD_PARTY:                                                          # not ours: must stay untouched
        write(f"{root}/.claude/skills/{t}/SKILL.md", skill_md(t))
    if faults:
        write(f"{root}/.claude/skills/quick-notes/SKILL.md", skill_md("quick-notes"))   # F12 skill in the wrong place


def fingerprint(root):
    """Hash of the files that must not change: third-party skills."""
    h = hashlib.sha256()
    for t in sorted(THIRD_PARTY):
        h.update(open(f"{root}/.claude/skills/{t}/SKILL.md", "rb").read())
    return h.hexdigest()


if __name__ == "__main__":
    build(sys.argv[1])
    print("built", sys.argv[1])
