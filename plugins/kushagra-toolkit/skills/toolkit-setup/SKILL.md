---
name: toolkit-setup
description: Apply Kushagra's full Claude toolkit (all skills, the kushagra-toolkit plugin and its MCP connectors) to the current project or machine. Use when the user asks to "set up my skills", "add my toolkit / plugins / connectors / MCPs to this project", "bootstrap Claude in this repo", or when a project is missing skills or MCP servers they expect to have.
---

# Toolkit setup

Installs everything from https://github.com/kushagra486/claude-ai-skills into a project.

## What gets installed

- **Skills** (23): agent-introspection-debugging, agent-sort, algorithmic-art, brand-guidelines,
  canvas-design, doc-coauthoring, docx, import-memory, internal-comms, learn, mcp-builder, morning,
  pdf, pptx, prompt-maximizer, session-start-hook, skill-creator, slack-gif-creator, theme-factory,
  toolkit-setup, ui-ux-pro-max, web-artifacts-builder, xlsx.
- **MCP servers** (via the plugin's `.mcp.json`, OAuth on first use): Canva, Figma, Supabase,
  Vercel, Netlify, Cloudflare Developer Platform, Hugging Face, Notion.
- **claude.ai-only connectors** (Gmail, Google Drive, Google Calendar, Floot, HyperFrames,
  Metricool, ElevenLabs, Spotify, Typefully, Microsoft 365, InstaPods): these can't be put in a file.
  They come from the user's claude.ai account when Claude Code is signed in with that account.

## Steps

1. Pick a mode. Default to `plugin` unless the user says otherwise.
   - `plugin`: project `.claude/settings.json` registers the marketplace, enables the plugin and adds
     a SessionStart hook that syncs skills into `~/.claude/skills`. Small diff, always up to date.
   - `copy`: vendors all skills into `.claude/skills/` and MCP servers into `.mcp.json`. Works offline,
     but adds ~13 MB to the repo.
   - `global`: installs for every project on this machine (`~/.claude`), touching no project files.
2. Run from the project root:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/kushagra486/claude-ai-skills/main/install.sh | bash -s -- --mode plugin
   ```
   If the repo is private, clone it first and run `bash /path/to/claude-ai-skills/install.sh --mode plugin .`
3. The installer merges into existing JSON; it never overwrites the user's own settings values.
   Show the user the resulting `.claude/settings.json` / `.mcp.json` diff.
4. Tell the user to restart Claude Code, accept the marketplace/trust prompt, and run `/mcp` to log in
   to each MCP server.
