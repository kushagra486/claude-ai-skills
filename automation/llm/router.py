"""Multi-provider LLM router with rate-limit accounting and automatic failover ("shift").

- Every provider has rpm/rpd limits (providers.json). Calls are counted in a sliding window and a provider
  at its limit is skipped; the next provider takes over.
- 429 / 5xx / network errors put the provider on cooldown (honouring Retry-After) and the call shifts on.
- Bad output (invalid JSON or failed validation) shifts the retry to a different provider.
- If everything is limited, wait for the shortest cooldown when it is short, else raise AllProvidersExhausted.
- State (call timestamps, cooldowns) is saved to LLM_STATE (default .llm-state/state.json) so a cache can carry
  daily counts across runs.
"""
import json
import math
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent


class AllProvidersExhausted(RuntimeError):
    pass


def http_post(url, headers, body, timeout=90):
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return 0, {}, str(e)


def build_request(p, key, system, user, max_tokens):
    """Return (url, headers, body_bytes, parse_fn) for the provider kind."""
    kind = p["kind"]
    if kind == "openai":
        url = p["url"].rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        body = {"model": p["model"], "max_tokens": max_tokens, "temperature": 0.4,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        parse = lambda d: d["choices"][0]["message"]["content"]  # noqa: E731
    elif kind == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{p['model']}:generateContent"
        headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
        body = {"systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.4}}
        parse = lambda d: "".join(x.get("text", "") for x in d["candidates"][0]["content"]["parts"])  # noqa: E731
    elif kind == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        body = {"model": p["model"], "max_tokens": max_tokens, "system": system,
                "messages": [{"role": "user", "content": user}]}
        parse = lambda d: "".join(b.get("text", "") for b in d["content"])  # noqa: E731
    else:
        raise ValueError(f"unknown provider kind {kind}")
    return url, headers, json.dumps(body).encode(), parse


def extract_json(text):
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


class Router:
    def __init__(self, config=None, state_path=None, transport=http_post, clock=time.time,
                 sleep=time.sleep, env=None):
        cfg = config or json.loads((HERE / "providers.json").read_text())
        self.env = os.environ if env is None else env
        self.margin = cfg.get("margin", 0.8)
        self.max_wait = cfg.get("max_wait_seconds", 120)
        self.total_wait = cfg.get("total_wait_seconds", 300)
        self.providers = [p for p in cfg["providers"] if self.env.get(p["key_env"])]
        self.transport, self.clock, self.sleep = transport, clock, sleep
        self.state_path = pathlib.Path(state_path or self.env.get("LLM_STATE", ".llm-state/state.json"))
        self.state = self._load()
        self.stats = {}  # provider -> {"ok": n, "shifted_from": n}

    # ---- state -------------------------------------------------------
    def _load(self):
        try:
            return json.loads(self.state_path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self):
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(self.state))
        except OSError:
            pass

    def _st(self, name):
        return self.state.setdefault(name, {"calls": [], "cooldown_until": 0})

    def _log(self, msg):
        print(f"llm: {msg}", file=sys.stderr)

    # ---- limits ------------------------------------------------------
    def wait_needed(self, p):
        """Seconds until provider p may be called again (0 = now)."""
        now, st = self.clock(), self._st(p["name"])
        st["calls"] = [t for t in st["calls"] if now - t < 86400]
        wait = max(0.0, st["cooldown_until"] - now)
        for window, limit in ((60, p.get("rpm")), (86400, p.get("rpd"))):
            if not limit:
                continue
            cap = max(1, math.floor(limit * self.margin))
            recent = sorted(t for t in st["calls"] if now - t < window)
            if len(recent) >= cap:
                wait = max(wait, recent[len(recent) - cap] + window - now)
        return wait

    def _cooldown(self, p, seconds):
        self._st(p["name"])["cooldown_until"] = self.clock() + seconds
        self._save()

    # ---- calls -------------------------------------------------------
    def call(self, system, user, max_tokens=1500, exclude=()):
        """Return (text, provider_name). Shifts across providers; raises AllProvidersExhausted."""
        candidates = [p for p in self.providers if p["name"] not in exclude]
        if not candidates:
            raise AllProvidersExhausted("no provider has an API key set (or all were excluded)")
        waited = 0.0
        for _ in range(60):
            waits = []
            for p in candidates:
                w = self.wait_needed(p)
                if w > 0:
                    waits.append(w)
                    continue
                text = self._attempt(p, system, user, max_tokens)
                if text is not None:
                    return text, p["name"]
            waits = [self.wait_needed(p) for p in candidates]
            soonest = min(waits)
            if soonest <= 0:
                continue  # a provider recovered during this pass
            if soonest > self.max_wait:
                raise AllProvidersExhausted(
                    f"all providers limited; soonest available in {int(soonest)}s (> {self.max_wait}s)")
            self._log(f"all providers limited, waiting {soonest:.0f}s")
            if waited + soonest > self.total_wait:
                raise AllProvidersExhausted(f"waited {int(waited)}s already; giving up")
            waited += soonest + 0.5
            self.sleep(soonest + 0.5)
        raise AllProvidersExhausted("gave up after repeated failures")

    def _attempt(self, p, system, user, max_tokens):
        name = p["name"]
        st = self._st(name)
        st["calls"].append(self.clock())  # count the attempt before sending
        self._save()
        url, headers, body, parse = build_request(p, self.env[p["key_env"]], system, user, max_tokens)
        status, resp_headers, text = self.transport(url, headers, body)
        stats = self.stats.setdefault(name, {"ok": 0, "shifted_from": 0})
        if status == 200:
            try:
                out = parse(json.loads(text))
                if out and out.strip():
                    stats["ok"] += 1
                    return out
            except (KeyError, IndexError, TypeError, json.JSONDecodeError):
                pass
            self._log(f"{name}: empty/unparseable response, shifting")
            self._cooldown(p, 30)
        elif status == 429:
            retry = resp_headers.get("Retry-After") or resp_headers.get("retry-after")
            daily = any(w in text.lower() for w in ("per day", "daily", "quota"))
            secs = float(retry) if retry and retry.replace(".", "", 1).isdigit() else (3600 if daily else 60)
            self._log(f"{name}: rate limited (429), cooldown {int(secs)}s, shifting")
            self._cooldown(p, secs)
        elif status in (401, 403, 404):
            self._log(f"{name}: HTTP {status} (bad key/model/access), disabled for this run")
            self._cooldown(p, 86400)
        else:
            self._log(f"{name}: HTTP {status}, cooldown 30s, shifting")
            self._cooldown(p, 30)
        stats["shifted_from"] += 1
        return None

    def call_json(self, system, user, validate=None, max_tokens=1500, attempts=4):
        """Call, parse JSON and validate; a bad answer shifts the retry to a different provider."""
        tried = set()
        last = None
        for _ in range(attempts):
            text, name = self.call(system, user, max_tokens, exclude=tried)
            try:
                obj = extract_json(text)
                if validate:
                    validate(obj)
                return obj
            except (ValueError, KeyError, TypeError) as e:  # JSONDecodeError is a ValueError
                last = e
                self._log(f"{name}: invalid output ({e}), trying another provider")
                tried.add(name)
        raise AllProvidersExhausted(f"no provider produced valid output: {last}")

    def summary(self):
        if not self.stats:
            return "no LLM calls made"
        return ", ".join(f"{n}: {s['ok']} ok / {s['shifted_from']} shifted" for n, s in self.stats.items())
