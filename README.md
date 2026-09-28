# claude-ai-skills

All of my Claude skills, plugin skills and MCP connectors in one repo, packaged as a Claude Code
**plugin marketplace** so they can be applied to any project with one command.

## Apply to any project

From the project root:

```bash
curl -fsSL https://raw.githubusercontent.com/kushagra486/claude-ai-skills/main/install.sh | bash
```

If this repo is private, clone it and run the script locally instead:

```bash
git clone https://github.com/kushagra486/claude-ai-skills ~/claude-ai-skills
bash ~/claude-ai-skills/install.sh --mode plugin /path/to/project
```

| Mode | What it writes | Use when |
|---|---|---|
| `plugin` (default) | `.claude/settings.json` (marketplace + plugin + SessionStart sync hook) and `.claude/hooks/kushagra-sync-skills.sh` | You want a small diff that always pulls the latest skills. Commit these so they apply in every checkout and in Claude Code on the web. |
| `copy` | `.claude/skills/*` and `.mcp.json` | You want everything vendored into the repo, no network needed. |
| `global` | `~/.claude/skills/*` and `~/.claude/settings.json` | You want it in every project on this machine without touching project files. |

Add `--no-hook` to `plugin` mode to skip the SessionStart hook. The installer deep-merges into
existing JSON and never overwrites values you already set.

Prefer doing it by hand? Copy [`templates/project-settings.json`](templates/project-settings.json)
to `<project>/.claude/settings.json`, or inside Claude Code run:

```
/plugin marketplace add kushagra486/claude-ai-skills
/plugin install kushagra-toolkit@kushagra-skills
```

After installing, restart Claude Code, accept the trust prompt and run `/mcp` to log in to each server.

## What's included

### Skills (`plugins/kushagra-toolkit/skills/`)

| Skill | Purpose |
|---|---|
| agent-introspection-debugging | Structured self-debugging for agent failures |
| agent-sort | Sort skills/commands/hooks into daily vs library for a repo |
| algorithmic-art | Generative art with p5.js |
| brand-guidelines | Anthropic brand colors and typography |
| canvas-design | Posters and static visual designs (PNG/PDF) |
| doc-coauthoring | Structured workflow for writing docs and specs |
| docx | Create, read and edit Word documents |
| import-memory | Import memory exports from other assistants |
| internal-comms | Status reports, newsletters, FAQs, incident reports |
| learn | Teaching and explanation mode |
| mcp-builder | Build MCP servers (Python / TypeScript) |
| morning | Morning brief artifact |
| pdf | Read, merge, split, fill and create PDFs |
| pptx | Create and edit PowerPoint decks |
| prompt-maximizer | Restructures every request into an optimized prompt |
| session-start-hook | Create SessionStart hooks for Claude Code on the web |
| skill-creator | Create, evaluate and improve skills |
| slack-gif-creator | Animated GIFs for Slack |
| theme-factory | 10 preset themes for artifacts |
| toolkit-setup | Applies this toolkit to the current project |
| ui-ux-pro-max | UI/UX design intelligence (styles, palettes, fonts, stacks) |
| web-artifacts-builder | Multi-component React/Tailwind/shadcn artifacts |
| xlsx | Spreadsheets: formulas, formatting, charts, cleanup |

### MCP servers (`plugins/kushagra-toolkit/.mcp.json`)

Official remote HTTP servers for every connector on my claude.ai account. They log in with OAuth on
first use via `/mcp`; no API keys are stored in this repo.

| Server | URL |
|---|---|
| Canva | https://mcp.canva.com/mcp |
| Figma | https://mcp.figma.com/mcp |
| Supabase | https://mcp.supabase.com/mcp |
| Vercel | https://mcp.vercel.com |
| Netlify | https://netlify-mcp.netlify.app/mcp |
| Cloudflare Developer Platform | https://bindings.mcp.cloudflare.com/mcp |
| Hugging Face | https://huggingface.co/mcp |
| Notion | https://mcp.notion.com/mcp |
| ElevenLabs | https://api.elevenlabs.io/v1/mcp |
| Floot | https://mcp.floot.com/mcp |
| HyperFrames by HeyGen | https://mcp.heygen.com/mcp/hyperframes/ |
| Metricool | https://ai.metricool.com/mcp |
| Typefully | https://mcp.typefully.com/mcp |
| Spotify | https://mcp-gateway-external-pilot.spotify.net/mcp |
| InstaPods | https://app.instapods.com/api/mcp |

### Servers that need your own credentials

[`scripts/add-credentialed-mcps.sh`](scripts/add-credentialed-mcps.sh) adds these at user scope
(every project), each only when its credentials are set:

- **GitHub**: `GITHUB_PAT=ghp_... scripts/add-credentialed-mcps.sh`
- **Google Workspace** (Gmail, Drive, Calendar, Docs, Sheets, Slides): Google's official servers
  require your own OAuth client. Follow
  [Google's setup guide](https://developers.google.com/workspace/guides/configure-mcp-servers),
  add `http://localhost:8765/callback` as a redirect URI, then run
  `GOOGLE_OAUTH_CLIENT_ID=... MCP_CLIENT_SECRET=... scripts/add-credentialed-mcps.sh`.

### claude.ai connectors

Microsoft 365 (and the claude.ai-hosted Gmail / Drive / Calendar connectors) run on Anthropic's own
OAuth app, so they only work through your claude.ai account. Claude Code picks up claude.ai connectors
when you sign in with the same account, so these follow you into every project automatically.

## Repository layout

```
.claude-plugin/marketplace.json        # marketplace "kushagra-skills"
plugins/kushagra-toolkit/
  .claude-plugin/plugin.json           # plugin manifest
  .mcp.json                            # MCP servers bundled with the plugin
  skills/<name>/SKILL.md               # every skill
install.sh                             # apply to a project (plugin / copy / global)
scripts/sync-skills.sh                 # SessionStart hook: sync skills into ~/.claude/skills
scripts/add-credentialed-mcps.sh       # add GitHub + Google Workspace MCP servers (your credentials)
templates/project-settings.json        # minimal .claude/settings.json to enable the plugin
```

## Updating

Add or edit skills under `plugins/kushagra-toolkit/skills/`, bump `version` in
`plugins/kushagra-toolkit/.claude-plugin/plugin.json`, and push. Projects using `plugin` mode pick up
changes via `/plugin marketplace update kushagra-skills` and the SessionStart sync hook.
