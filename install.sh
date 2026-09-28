#!/usr/bin/env bash
# Apply kushagra-toolkit (all skills + MCP connectors) to a project or globally.
#
# Usage (from inside any project):
#   curl -fsSL https://raw.githubusercontent.com/kushagra486/claude-ai-skills/main/install.sh | bash
#   bash install.sh [--mode plugin|copy|global] [--no-hook] [TARGET_DIR]
#
# Modes:
#   plugin (default)  Writes TARGET/.claude/settings.json so Claude Code auto-installs the
#                     kushagra-skills marketplace and enables the kushagra-toolkit plugin
#                     (skills + MCP servers). Also adds a SessionStart hook that syncs the
#                     skills into ~/.claude/skills, so they load even where plugins can't.
#   copy              Copies every skill into TARGET/.claude/skills and merges the MCP servers
#                     into TARGET/.mcp.json. Fully self-contained, no network at session start.
#   global            Installs for every project on this machine: skills into ~/.claude/skills,
#                     marketplace + plugin into ~/.claude/settings.json.
set -euo pipefail

REPO="${KT_REPO:-kushagra486/claude-ai-skills}"
REF="${KT_REF:-main}"
MARKETPLACE="kushagra-skills"
PLUGIN="kushagra-toolkit"

mode="plugin"
hook=1
target="$PWD"
while [ $# -gt 0 ]; do
  case "$1" in
    --mode) mode="$2"; shift 2 ;;
    --mode=*) mode="${1#*=}"; shift ;;
    --no-hook) hook=0; shift ;;
    -h|--help) sed -n '2,19p' "$0" 2>/dev/null || true; exit 0 ;;
    *) target="$1"; shift ;;
  esac
done
case "$mode" in plugin|copy|global) ;; *) echo "Unknown mode: $mode" >&2; exit 1 ;; esac
command -v python3 >/dev/null || { echo "python3 is required to merge JSON settings" >&2; exit 1; }
target="$(cd "$target" && pwd)"

# Locate the toolkit sources: this checkout if run from it, otherwise a fresh clone.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
if [ -n "$script_dir" ] && [ -d "$script_dir/plugins/$PLUGIN/skills" ]; then
  src="$script_dir"
else
  tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
  git clone --quiet --depth 1 --branch "$REF" "https://github.com/$REPO.git" "$tmp/repo"
  src="$tmp/repo"
fi
plugin_dir="$src/plugins/$PLUGIN"

# merge_json FILE: deep-merges the JSON on stdin into FILE (creating it if needed).
# Objects merge recursively, arrays are unioned, existing scalar values are kept.
MERGE_PY='
import json, os, sys
path = sys.argv[1]
patch = json.load(sys.stdin)
data = {}
if os.path.exists(path) and os.path.getsize(path) > 0:
    with open(path) as f:
        data = json.load(f)
def merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            merge(a[k], v)
        elif isinstance(v, list) and isinstance(a.get(k), list):
            a[k] += [x for x in v if x not in a[k]]
        elif k not in a:
            a[k] = v
    return a
os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
with open(path, "w") as f:
    json.dump(merge(data, patch), f, indent=2)
    f.write("\n")
'
merge_json() { python3 -c "$MERGE_PY" "$1"; }

plugin_settings() {
  cat <<JSON
{
  "extraKnownMarketplaces": {
    "$MARKETPLACE": { "source": { "source": "github", "repo": "$REPO" } }
  },
  "enabledPlugins": { "$PLUGIN@$MARKETPLACE": true }
}
JSON
}

copy_skills() {
  mkdir -p "$1"
  for skill in "$plugin_dir"/skills/*/; do
    name="$(basename "$skill")"
    rm -rf "${1:?}/$name"
    cp -R "$skill" "$1/$name"
  done
  echo "Copied $(ls -1 "$plugin_dir/skills" | wc -l | tr -d ' ') skills into $1"
}

case "$mode" in
  plugin)
    plugin_settings | merge_json "$target/.claude/settings.json"
    echo "Enabled $PLUGIN@$MARKETPLACE in $target/.claude/settings.json"
    if [ "$hook" = 1 ]; then
      mkdir -p "$target/.claude/hooks"
      cp "$src/scripts/sync-skills.sh" "$target/.claude/hooks/kushagra-sync-skills.sh"
      chmod +x "$target/.claude/hooks/kushagra-sync-skills.sh"
      merge_json "$target/.claude/settings.json" <<'JSON'
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/kushagra-sync-skills.sh" } ] }
    ]
  }
}
JSON
      echo "Added SessionStart skill-sync hook"
    fi
    ;;
  copy)
    copy_skills "$target/.claude/skills"
    python3 -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1]))))' "$plugin_dir/.mcp.json" \
      | merge_json "$target/.mcp.json"
    echo '{ "enableAllProjectMcpServers": true }' | merge_json "$target/.claude/settings.json"
    echo "Merged MCP servers into $target/.mcp.json"
    ;;
  global)
    copy_skills "$HOME/.claude/skills"
    plugin_settings | merge_json "$HOME/.claude/settings.json"
    echo "Enabled $PLUGIN@$MARKETPLACE in ~/.claude/settings.json"
    ;;
esac

cat <<'MSG'

Done. Next steps:
  - Start Claude Code in the project; trust the folder / marketplace when prompted.
  - Run /mcp to log in to each MCP server (Canva, Figma, Supabase, Vercel, ElevenLabs, ...).
  - Optional: scripts/add-credentialed-mcps.sh adds GitHub and Google Workspace servers.
  - Microsoft 365 and claude.ai-hosted connectors come from your claude.ai account:
    sign in to Claude Code with the same account.
MSG
