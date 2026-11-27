"""Shared helpers for the AI radar pipeline (stdlib only)."""
import json
import os
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
RADAR = ROOT / "automation" / "radar"
STATE = RADAR / "state"
PLUGIN = ROOT / "plugins" / "ai-radar"
SKILLS = PLUGIN / "skills"
INDEX_SKILL = "ai-radar"


def load_config():
    return json.loads((RADAR / "config.json").read_text())


def read_json(path, default):
    try:
        return json.loads(pathlib.Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path, data):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def http(url, headers=None, data=None, retries=3):
    req = urllib.request.Request(url, headers=headers or {}, data=data)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** (attempt + 2))
                continue
            raise
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise


def gh_headers(accept="application/vnd.github+json"):
    h = {"Accept": accept, "User-Agent": "ai-radar", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def gh_json(path, params=None):
    url = "https://api.github.com" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return json.loads(http(url, gh_headers()))


def gh_readme(full_name, limit):
    try:
        text = http(f"https://api.github.com/repos/{full_name}/readme", gh_headers("application/vnd.github.raw"))
    except urllib.error.HTTPError:
        return ""
    return text[:limit]


def slugify(full_name):
    s = re.sub(r"[^a-z0-9]+", "-", full_name.lower().replace("/", "-")).strip("-")
    return s[:60].strip("-")


FM_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)


def parse_skill(text):
    """Return (frontmatter dict, body). Frontmatter values are single-line strings."""
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm, m.group(2)
