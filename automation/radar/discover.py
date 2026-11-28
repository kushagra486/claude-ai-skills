#!/usr/bin/env python3
"""Step 1: search GitHub for new / trending free AI projects and pick this week's candidates.

Writes:
  automation/radar/state/picks.json     -> consumed by generate.py
  automation/radar/state/candidates/<date>.json  (full ranked list)
  automation/radar/digests/<date>.md    (human-readable weekly digest)
"""
import datetime as dt
import math
import sys

from common import RADAR, STATE, gh_json, gh_readme, load_config, read_json, write_json


def search(q, per_page=30):
    data = gh_json("/search/repositories", {"q": q, "sort": "stars", "order": "desc", "per_page": per_page})
    return data.get("items", [])


def main():
    cfg = load_config()
    today = dt.date.today()
    new_since = (today - dt.timedelta(days=cfg["new_repo_window_days"])).isoformat()
    active_since = (today - dt.timedelta(days=cfg["active_repo_window_days"])).isoformat()
    seen = read_json(STATE / "seen.json", {})
    allowed = set(cfg["allowed_licenses"])

    found = {}
    for topic in cfg["topics"]:
        queries = [
            (f"topic:{topic} created:>{new_since} stars:>{cfg['min_stars_new']}", "new"),
            (f"topic:{topic} pushed:>{active_since} stars:>{cfg['min_stars_active']}", "active"),
        ]
        for q, kind in queries:
            try:
                items = search(q)
            except Exception as e:  # keep going on partial failures
                print(f"warn: search failed for {q!r}: {e}", file=sys.stderr)
                continue
            for r in items:
                full = r["full_name"]
                if full in found or full in seen:
                    continue
                if r.get("fork") or r.get("archived") or r.get("disabled"):
                    continue
                lic = ((r.get("license") or {}).get("spdx_id") or "").lower()
                if lic not in allowed:
                    continue
                created = dt.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")).date()
                age = max((today - created).days, 0)
                # stars-per-age favours fast risers; log damps mega repos
                score = r["stargazers_count"] / (age + 7) + math.log10(r["stargazers_count"] + 1)
                found[full] = {
                    "full_name": full,
                    "url": r["html_url"],
                    "description": (r.get("description") or "")[:300],
                    "stars": r["stargazers_count"],
                    "language": r.get("language"),
                    "license": r["license"]["spdx_id"],
                    "created_at": r["created_at"],
                    "pushed_at": r["pushed_at"],
                    "topics": r.get("topics", [])[:12],
                    "kind": kind,
                    "score": round(score, 2),
                }

    ranked = sorted(found.values(), key=lambda c: c["score"], reverse=True)
    picks = ranked[: cfg["max_picks_per_run"]]
    for p in picks:
        p["readme"] = gh_readme(p["full_name"], cfg["readme_char_limit"])

    write_json(STATE / "candidates" / f"{today.isoformat()}.json", ranked)
    write_json(STATE / "picks.json", {"date": today.isoformat(), "picks": picks})

    lines = [f"# AI radar digest {today.isoformat()}", "",
             f"{len(ranked)} new candidates found; top {len(picks)} drafted as skills.", "",
             "| Repo | Stars | License | Kind | Description |", "|---|---|---|---|---|"]
    for c in ranked[:40]:
        star = "**" if c in picks else ""
        desc = c["description"].replace("|", "/")
        lines.append(f"| {star}[{c['full_name']}]({c['url']}){star} | {c['stars']} | {c['license']} | {c['kind']} | {desc} |")
    (RADAR / "digests").mkdir(exist_ok=True)
    (RADAR / "digests" / f"{today.isoformat()}.md").write_text("\n".join(lines) + "\n")
    print(f"found {len(ranked)} candidates, picked {len(picks)}")


if __name__ == "__main__":
    main()
