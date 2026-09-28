#!/usr/bin/env bash
# Syncs the kushagra-toolkit skills from GitHub into ~/.claude/skills.
# Meant to run as a Claude Code SessionStart hook; it never fails the session.
set -u

REPO="${KT_REPO:-kushagra486/claude-ai-skills}"
REF="${KT_REF:-main}"
DEST="${KT_SKILLS_DIR:-$HOME/.claude/skills}"
STAMP="$DEST/.kushagra-toolkit-synced"
MAX_AGE_MIN="${KT_MAX_AGE_MIN:-720}"

# Skip if synced recently.
if [ -f "$STAMP" ] && [ -z "$(find "$STAMP" -mmin +"$MAX_AGE_MIN" 2>/dev/null)" ]; then
  exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# git clone uses the user's git credentials, so it also works for a private repo.
if ! git clone --quiet --depth 1 --branch "$REF" "https://github.com/$REPO.git" "$tmp/repo" 2>/dev/null; then
  mkdir -p "$tmp/repo"
  curl -fsSL "https://codeload.github.com/$REPO/tar.gz/refs/heads/$REF" 2>/dev/null \
    | tar -xz -C "$tmp/repo" --strip-components=1 2>/dev/null || {
      echo "kushagra-toolkit: could not fetch $REPO@$REF, skipping skill sync" >&2
      exit 0
    }
fi

src="$tmp/repo/plugins/kushagra-toolkit/skills"
[ -d "$src" ] || exit 0

mkdir -p "$DEST"
for skill in "$src"/*/; do
  name="$(basename "$skill")"
  rm -rf "${DEST:?}/$name"
  cp -R "$skill" "$DEST/$name"
done
touch "$STAMP"
echo "kushagra-toolkit: synced $(ls -1 "$src" | wc -l | tr -d ' ') skills into $DEST"
exit 0
