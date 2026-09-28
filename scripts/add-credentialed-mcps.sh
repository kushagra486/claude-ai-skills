#!/usr/bin/env bash
# Adds the MCP servers that need your own credentials, at user scope (all projects).
# Each server is only added when its credentials are set in the environment.
#
#   GITHUB_PAT=ghp_...                    GitHub (https://github.com/settings/tokens)
#   GOOGLE_OAUTH_CLIENT_ID=...            Gmail, Drive, Calendar, Docs, Sheets, Slides
#   MCP_CLIENT_SECRET=...                 (Google OAuth client secret)
#   GOOGLE_OAUTH_CALLBACK_PORT=8765       optional; redirect URI is http://localhost:<port>/callback
#
# Google setup: https://developers.google.com/workspace/guides/configure-mcp-servers
# (create a Web OAuth client, add the localhost redirect URI above, enable the *mcp.googleapis.com APIs).
set -euo pipefail
command -v claude >/dev/null || { echo "Claude Code CLI (claude) not found" >&2; exit 1; }

add() { claude mcp remove --scope user "$1" >/dev/null 2>&1 || true; claude mcp add --scope user "$@"; }

if [ -n "${GITHUB_PAT:-}" ]; then
  add github --transport http https://api.githubcopilot.com/mcp/ --header "Authorization: Bearer $GITHUB_PAT"
else
  echo "skip github: set GITHUB_PAT"
fi

if [ -n "${GOOGLE_OAUTH_CLIENT_ID:-}" ] && [ -n "${MCP_CLIENT_SECRET:-}" ]; then
  port="${GOOGLE_OAUTH_CALLBACK_PORT:-8765}"
  for svc in gmail drive calendar docs sheets slides; do
    add "google-$svc" --transport http "https://${svc}mcp.googleapis.com/mcp/v1" \
      --client-id "$GOOGLE_OAUTH_CLIENT_ID" --client-secret --callback-port "$port"
  done
else
  echo "skip google workspace: set GOOGLE_OAUTH_CLIENT_ID and MCP_CLIENT_SECRET"
fi

echo "Done. Run /mcp in Claude Code to finish OAuth logins."
