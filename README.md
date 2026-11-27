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
| ElevenLabs | https://api.us.elevenlabs.io/v1/mcp |
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

## AI radar (weekly auto-discovery)

A GitHub Action ([`.github/workflows/ai-radar.yml`](.github/workflows/ai-radar.yml)) runs every Monday:

1. `automation/radar/discover.py` searches GitHub for new and fast-rising free/open-source AI projects
   (agents, MCP servers, local/open models, automation tools) and writes a digest to `automation/radar/digests/`.
2. `generate.py` has the LLM router draft a skill per top pick into `plugins/ai-radar/skills/` (READMEs are treated as
   untrusted; output is screened for risky commands).
3. `export.py` rebuilds the `ai-radar` index skill and exports everything for other tools.
4. A **draft PR** is opened for you to review and merge.

**Setup:** add at least one free LLM key as a repo secret (see *LLM router* below), and enable Settings > Actions > General > "Allow GitHub Actions to
create and approve pull requests". Run it any time from the Actions tab (workflow_dispatch). Without the key it
still produces the digest.

**Using the results** (after merging):

| Where | How |
|---|---|
| Claude Code | `/plugin install ai-radar@kushagra-skills` (or the existing sync hook) |
| Claude.ai chat | upload zips from `exports/claude-ai/` in Settings > Capabilities > Skills |
| Codex / Gemini CLI / others | copy `exports/AGENTS.md` / `exports/GEMINI.md` into your project |
| Cursor | copy `exports/cursor/rules/` to `.cursor/rules/` |

## Free video pipeline

[`.github/workflows/free-video.yml`](.github/workflows/free-video.yml) turns the next unused AI radar pick into a
short explainer MP4 each Tuesday (attached to the release with an editable `source.zip`; use your own voice audio by adding files under `automation/video/audio/<slug>/` and the `voice_provider` input): the LLM router writes the script in sections, Kokoro narrates on CPU, HyperFrames renders HTML to
video, and the MP4 is attached to a GitHub Release (`video-<slug>`). No GPU or Pi needed; just one free LLM key
(see *LLM router*). Run it manually from the Actions tab, optionally with a `repo` input. See the
`free-video-pipeline` skill. The render and narration steps have not been run end to end yet, so expect to tweak
on the first run.

## Mods

Claude Code mods (hook modules) installable from this marketplace:

| Mod | What it does |
|---|---|
| `obsidian-theme` | Premium dark dashboard look (desktop and mobile apps) |
| `control-board` | Side pane; `/route` picks a model per task type; `/watch` and `/daily-check` report project git status |
| `safety-guard` | Blocks `rm -rf` on broad paths, force-push, `reset --hard`, pipe-to-shell, and edits to `.env`/SSH keys |
| `session-organizer` | `/organize-sessions` tags every session by project/repo and flags junk (tags only) |

```
/plugin install obsidian-theme@kushagra-skills
```

## LLM router (free, multi-provider, rate-limit aware)

`automation/llm/router.py` lets every automation use several LLM providers at once, so no paid key is required:

- **Providers** (`automation/llm/providers.json`, in preference order): Gemini, Groq, GitHub Models, OpenRouter,
  Anthropic. A provider is used only if its key is set. GitHub Models needs no secret (the Actions `GITHUB_TOKEN`).
  Model IDs and limits change often; edit them in that file.
- **Rate limits:** per-provider rpm/rpd are counted in a sliding window (with a safety margin) and persisted via
  the Actions cache. A provider at its limit is skipped; a `429` puts it on cooldown (honouring `Retry-After`).
- **Shifting:** the call moves to the next provider on a limit, error, or invalid/unparseable output. If all are
  limited it waits when short, otherwise fails with a clear message.
- **Sectioned scripts:** `automation/video/script.py` extracts facts, plans scenes, narrates each scene with the
  previous line for continuity, then does a stitching pass (discarded if it breaks the structure). Only the facts
  step reads the untrusted README.

Secrets (all optional, add any you have): `GEMINI_API_KEY` (free, aistudio.google.com), `GROQ_API_KEY` (free),
`OPENROUTER_API_KEY` (free models), `ANTHROPIC_API_KEY` (paid). Test with `python3 automation/llm/test_router.py`.
