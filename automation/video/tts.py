#!/usr/bin/env python3
"""Narrate each scene locally with Kokoro (CPU). Writes build/scene_N.wav and build/durations.json."""
import json
import os
import pathlib

import numpy as np
import soundfile as sf
from kokoro import KPipeline

BUILD = pathlib.Path(os.environ.get("BUILD_DIR", "build"))
VOICE = os.environ.get("KOKORO_VOICE", "af_heart")
RATE = 24000


def main():
    scenes = json.loads((BUILD / "script.json").read_text())["scenes"]
    pipe = KPipeline(lang_code="a")
    durations = []
    for i, s in enumerate(scenes):
        chunks = [np.asarray(audio) for _, _, audio in pipe(s["narration"], voice=VOICE)]
        audio = np.concatenate(chunks + [np.zeros(int(RATE * 0.4))])  # 0.4s pause between scenes
        sf.write(BUILD / f"scene_{i}.wav", audio, RATE)
        durations.append(round(len(audio) / RATE, 2))
    (BUILD / "durations.json").write_text(json.dumps(durations))
    print(f"narrated {len(scenes)} scenes, {sum(durations):.1f}s total")


if __name__ == "__main__":
    main()
