#!/usr/bin/env python3
"""Voiceover for each scene. Writes build/scene_N.wav and build/durations.json.

VOICE_PROVIDER (env, default "auto"):
  auto    use your own audio file for a scene when one exists, otherwise synthesize it with Kokoro
  kokoro  ignore audio files, synthesize every scene with Kokoro (CPU)
  files   use only your audio files; fail if any scene has none (no TTS dependency needed)

Your own audio (any voice: a recording, ElevenLabs, VoiceStudio, Chatterbox...):
  automation/video/audio/<slug>/scene_0.wav, scene_1.mp3, ...   (wav, mp3, m4a, flac, ogg)
<slug> is the topic's slug (shown in build/topic.json and in the release tag video-<slug>).
Files are converted to 24 kHz mono WAV with ffmpeg and padded with 0.4 s of silence.

New synthesizers: add a function (text, voice) -> (samples, rate) to SYNTHS and set VOICE_PROVIDER.
`--needs-synth` prints true/false (does any scene still need a synthesizer?) so CI can skip heavy installs.
"""
import json
import os
import pathlib
import subprocess
import sys
import wave

BUILD = pathlib.Path(os.environ.get("BUILD_DIR", "build"))
AUDIO_ROOT = pathlib.Path(os.environ.get("AUDIO_ROOT", pathlib.Path(__file__).resolve().parent / "audio"))
VOICE = os.environ.get("KOKORO_VOICE", "af_heart")
RATE = 24000
PAD = 0.4
EXTS = ("wav", "mp3", "m4a", "flac", "ogg")
MODES = ("auto", "kokoro", "files")

_kokoro = None


def synth_kokoro(text, voice):
    """Return (list of float samples, sample rate). Imported lazily so file-only runs need no torch."""
    global _kokoro
    import numpy as np
    from kokoro import KPipeline
    if _kokoro is None:
        _kokoro = KPipeline(lang_code="a")
    chunks = [np.asarray(a) for _, _, a in _kokoro(text, voice=voice)]
    return np.concatenate(chunks), RATE


SYNTHS = {"kokoro": synth_kokoro}


def mode():
    m = (os.environ.get("VOICE_PROVIDER") or "auto").strip().lower()
    if m not in MODES:
        sys.exit(f"VOICE_PROVIDER must be one of {MODES}, got {m!r}")
    return m


def find_override(slug, i):
    for ext in EXTS:
        p = AUDIO_ROOT / slug / f"scene_{i}.{ext}"
        if p.exists():
            return p
    return None


def plan(slug, n):
    """Per scene: ('file', path) or ('synth', None)."""
    m, out = mode(), []
    for i in range(n):
        f = find_override(slug, i) if m != "kokoro" else None
        if f:
            out.append(("file", f))
        elif m == "files":
            sys.exit(f"VOICE_PROVIDER=files but no audio for scene {i}: expected "
                     f"{AUDIO_ROOT / slug}/scene_{i}.(" + "|".join(EXTS) + ")")
        else:
            out.append(("synth", None))
    return out


def normalize(src, dst):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ar", str(RATE), "-ac", "1",
           "-af", f"apad=pad_dur={PAD}", str(dst)]
    subprocess.run(cmd, check=True)


def wav_seconds(path):
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def write_synth(samples, rate, dst):
    import numpy as np
    import soundfile as sf
    pad = np.zeros(int(rate * PAD))
    sf.write(dst, np.concatenate([np.asarray(samples), pad]), rate)


def main():
    topic = json.loads((BUILD / "topic.json").read_text())
    scenes = json.loads((BUILD / "script.json").read_text())["scenes"]
    steps = plan(topic["slug"], len(scenes))
    if "--needs-synth" in sys.argv:
        print("true" if any(k == "synth" for k, _ in steps) else "false")
        return
    synth = SYNTHS["kokoro"]
    durations, used = [], {"file": 0, "synth": 0}
    for i, (s, (kind, src)) in enumerate(zip(scenes, steps)):
        dst = BUILD / f"scene_{i}.wav"
        if kind == "file":
            normalize(src, dst)
        else:
            samples, rate = synth(s["narration"], VOICE)
            write_synth(samples, rate, dst)
        used[kind] += 1
        durations.append(round(wav_seconds(dst), 2))
    (BUILD / "durations.json").write_text(json.dumps(durations))
    print(f"voiceover: {used['file']} from your files, {used['synth']} synthesized; {sum(durations):.1f}s total")


if __name__ == "__main__":
    main()
