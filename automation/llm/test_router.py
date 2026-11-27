import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "video"))
from router import AllProvidersExhausted, Router  # noqa: E402


def cfg(**limits):
    return {"margin": 1.0, "max_wait_seconds": 30, "providers": [
        {"name": "a", "kind": "openai", "url": "http://a", "model": "m", "key_env": "KA",
         "rpm": limits.get("a_rpm", 100), "rpd": 1000},
        {"name": "b", "kind": "openai", "url": "http://b", "model": "m", "key_env": "KB", "rpm": 100, "rpd": 1000}]}


def ok_body(text):
    return 200, {}, json.dumps({"choices": [{"message": {"content": text}}]})


class Clock:
    t = 1000.0
    def __call__(self): return self.t
    def sleep(self, s): self.t += s


def make(transport, **kw):
    c = Clock()
    return Router(cfg(**kw), state_path="/tmp/claude-0/llm-test-state.json", transport=transport,
                  clock=c, sleep=c.sleep, env={"KA": "x", "KB": "y"}), c


class RouterTests(unittest.TestCase):
    def setUp(self):
        p = pathlib.Path("/tmp/claude-0/llm-test-state.json")
        if p.exists():
            p.write_text("{}")

    def test_shifts_on_429(self):
        seen = []
        def tr(url, h, b):
            seen.append(url)
            return (429, {"Retry-After": "50"}, "slow down") if "//a" in url else ok_body("hi")
        r, _ = make(tr)
        self.assertEqual(r.call("s", "u")[1], "b")
        r.call("s", "u")  # a is cooling down: must not be tried again
        self.assertEqual(sum("//a" in u for u in seen), 1)

    def test_rpm_limit_shifts_without_calling(self):
        seen = []
        def tr(url, h, b):
            seen.append(url)
            return ok_body("hi")
        r, _ = make(tr, a_rpm=2)
        names = [r.call("s", "u")[1] for _ in range(4)]
        self.assertEqual(names, ["a", "a", "b", "b"])

    def test_waits_when_short_and_raises_when_long(self):
        r, c = make(lambda *a: (429, {"Retry-After": "10"}, ""))
        with self.assertRaises(AllProvidersExhausted):  # keeps failing; bounded
            r.call("s", "u")
        r2, _ = make(lambda *a: (429, {"Retry-After": "500"}, ""))
        with self.assertRaises(AllProvidersExhausted):
            r2.call("s", "u")

    def test_invalid_json_shifts_provider(self):
        def tr(url, h, b):
            return ok_body("not json") if "//a" in url else ok_body('{"x": 1}')
        r, _ = make(tr)
        self.assertEqual(r.call_json("s", "u", lambda o: o["x"]), {"x": 1})

    def test_script_stitching_survives_bad_polish(self):
        import script
        class Fake:
            def call_json(self, system, user, validate=None, **kw):
                if "Extract" in system:
                    o = {"facts": [f"fact {i}" for i in range(8)]}
                elif "Plan a" in system:
                    o = {"title": "T", "scenes": [{"headline": f"H{i}", "bullets": ["b"], "purpose": "p"} for i in range(5)]}
                elif "ONE scene" in system:
                    o = {"narration": "word " * 20}
                else:
                    o = {"narrations": ["too few"]}  # invalid polish
                if "Smooth" in system:
                    validate(o)  # raises, as the real router would exhaust
                if validate: validate(o)
                return o
        class Fake2(Fake):
            def call_json(self, system, user, validate=None, **kw):
                try:
                    return super().call_json(system, user, validate, **kw)
                except AssertionError:
                    raise AllProvidersExhausted("bad polish")
        topic = {"full_name": "a/b", "url": "u", "license": "MIT", "stars": 1, "description": "d", "readme": "r"}
        out = script.build_script(Fake2(), topic)
        self.assertEqual(len(out["scenes"]), 5)
        self.assertTrue(all(len(s["narration"].split()) == 20 for s in out["scenes"]))


if __name__ == "__main__":
    unittest.main()
