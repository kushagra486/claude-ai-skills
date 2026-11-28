#!/usr/bin/env python3
"""Pick the next video topic from the AI radar candidates (skipping repos already made into videos).

Used topics = GitHub Releases tagged video-<slug> in this repo (no state files to commit).
Override with env TOPIC_REPO=owner/name. Writes build/topic.json; exits 0 with no file if nothing to do.
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "radar"))
from common import STATE, gh_json, gh_readme, load_config, read_json, slugify, write_json  # noqa: E402

BUILD = pathlib.Path(os.environ.get("BUILD_DIR", "build"))


def used_slugs():
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        return set()
    try:
        rels = gh_json(f"/repos/{repo}/releases", {"per_page": 100})
    except Exception as e:
        print(f"warn: could not list releases: {e}", file=sys.stderr)
        return set()
    return {r["tag_name"][len("video-"):] for r in rels if r["tag_name"].startswith("video-")}


def main():
    forced = os.environ.get("TOPIC_REPO", "").strip()
    used = used_slugs()
    if forced:
        r = gh_json(f"/repos/{forced}")
        cand = {"full_name": r["full_name"], "url": r["html_url"], "description": r.get("description") or "",
                "stars": r["stargazers_count"], "license": (r.get("license") or {}).get("spdx_id")}
    else:
        files = sorted((STATE / "candidates").glob("*.json"), reverse=True)
        cand = None
        for f in files[:4]:  # most recent four radar runs
            for c in read_json(f, []):
                if slugify(c["full_name"]) not in used:
                    cand = c
                    break
            if cand:
                break
        if not cand:
            print("no unused candidates; nothing to do")
            return
    cand["slug"] = slugify(cand["full_name"])
    cand["readme"] = gh_readme(cand["full_name"], load_config()["readme_char_limit"])
    write_json(BUILD / "topic.json", cand)
    print(f"topic: {cand['full_name']}")


if __name__ == "__main__":
    main()
