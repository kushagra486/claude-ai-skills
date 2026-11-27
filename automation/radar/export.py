#!/usr/bin/env python3
"""Step 3: rebuild the index skill and export every ai-radar skill to other tools.

  plugins/ai-radar/skills/ai-radar/SKILL.md  index so Claude can route to discovered tools
  exports/claude-ai/<slug>.zip               upload in Claude.ai > Settings > Capabilities > Skills
  exports/AGENTS.md, exports/GEMINI.md       Codex / Gemini CLI / other terminal agents
  exports/cursor/rules/<slug>.mdc            Cursor rules
"""
import shutil
import zipfile

from common import INDEX_SKILL, ROOT, SKILLS, parse_skill

EXPORTS = ROOT / "exports"


def collect():
    items = []
    for d in sorted(SKILLS.iterdir()):
        f = d / "SKILL.md"
        if d.name == INDEX_SKILL or not f.exists():
            continue
        fm, body = parse_skill(f.read_text())
        items.append({"slug": d.name, "fm": fm, "body": body.strip(), "path": f})
    return items


def write_index(items):
    rows = "\n".join(
        f"- **{i['slug']}**: {i['fm'].get('description', '')} ([source]({i['fm'].get('source', '')}))" for i in items
    )
    text = (
        "---\n"
        f"name: {INDEX_SKILL}\n"
        'description: "Index of newly discovered free and open-source AI tools, agents, MCP servers and models '
        'found by the weekly GitHub radar. Use when the user asks what AI tools exist, wants a free or open-source '
        'alternative, or needs an automation tool for a task."\n'
        "---\n\n# AI radar index\n\n"
        "Each entry below has its own skill with details. Entries are auto-drafted and may need verification.\n\n"
        f"{rows}\n"
    )
    (SKILLS / INDEX_SKILL).mkdir(exist_ok=True)
    (SKILLS / INDEX_SKILL / "SKILL.md").write_text(text)


def write_zip(item):
    out = EXPORTS / "claude-ai" / f"{item['slug']}.zip"
    info = zipfile.ZipInfo(f"{item['slug']}/SKILL.md", date_time=(2020, 1, 1, 0, 0, 0))
    info.external_attr = 0o644 << 16
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(info, item["path"].read_text())


def main():
    items = collect()
    write_index(items)
    if EXPORTS.exists():
        shutil.rmtree(EXPORTS)
    (EXPORTS / "claude-ai").mkdir(parents=True)
    (EXPORTS / "cursor" / "rules").mkdir(parents=True)

    agents = ["# AI radar: free & open-source AI tools\n",
              "Auto-drafted from public READMEs; verify before relying on them.\n"]
    for i in items:
        write_zip(i)
        desc = i["fm"].get("description", "")
        (EXPORTS / "cursor" / "rules" / f"{i['slug']}.mdc").write_text(
            f"---\ndescription: {desc}\nalwaysApply: false\n---\n\n{i['body']}\n")
        agents.append(f"\n## {i['slug']}\n\n_{desc}_\n\n{i['body']}\n")
    text = "\n".join(agents)
    (EXPORTS / "AGENTS.md").write_text(text)
    (EXPORTS / "GEMINI.md").write_text(text)
    print(f"exported {len(items)} skills")


if __name__ == "__main__":
    main()
