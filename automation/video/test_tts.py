import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
TTS = HERE / "tts.py"


def tone(path, secs, ext="wav"):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency=440:duration={secs}",
                    str(path)], check=True)


def run(env, *args):
    return subprocess.run([sys.executable, str(TTS), *args], env={**os.environ, **env}, capture_output=True, text=True)


class TtsTests(unittest.TestCase):
    def setUp(self):
        self.d = pathlib.Path(tempfile.mkdtemp())
        self.build, self.audio = self.d / "build", self.d / "audio"
        (self.audio / "acme-x").mkdir(parents=True)
        self.build.mkdir()
        (self.build / "topic.json").write_text(json.dumps({"slug": "acme-x"}))
        (self.build / "script.json").write_text(json.dumps({"scenes": [{"narration": "a"}, {"narration": "b"}]}))
        self.env = {"BUILD_DIR": str(self.build), "AUDIO_ROOT": str(self.audio)}

    def test_files_mode_uses_wav_and_mp3_and_pads(self):
        tone(self.audio / "acme-x" / "scene_0.wav", 2.0)
        tone(self.audio / "acme-x" / "scene_1.mp3", 1.0)
        r = run({**self.env, "VOICE_PROVIDER": "files"})
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads((self.build / "durations.json").read_text())
        self.assertAlmostEqual(d[0], 2.4, delta=0.15)
        self.assertAlmostEqual(d[1], 1.4, delta=0.2)
        self.assertTrue((self.build / "scene_1.wav").exists())

    def test_files_mode_fails_when_scene_missing(self):
        tone(self.audio / "acme-x" / "scene_0.wav", 1.0)
        r = run({**self.env, "VOICE_PROVIDER": "files"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("scene 1", r.stderr)

    def test_needs_synth_reporting(self):
        tone(self.audio / "acme-x" / "scene_0.wav", 1.0)
        self.assertEqual(run({**self.env, "VOICE_PROVIDER": "auto"}, "--needs-synth").stdout.strip(), "true")
        tone(self.audio / "acme-x" / "scene_1.wav", 1.0)
        self.assertEqual(run({**self.env, "VOICE_PROVIDER": "auto"}, "--needs-synth").stdout.strip(), "false")
        self.assertEqual(run({**self.env, "VOICE_PROVIDER": "kokoro"}, "--needs-synth").stdout.strip(), "true")

    def test_bad_provider_rejected(self):
        self.assertNotEqual(run({**self.env, "VOICE_PROVIDER": "nope"}).returncode, 0)


if __name__ == "__main__":
    unittest.main()
