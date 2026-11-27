#!/usr/bin/env python3
"""Build a HyperFrames HTML composition (build/video/index.html) from script + scene audio.

Uses HyperFrames' documented timing attributes: data-start, data-duration, data-track-index.
Text is HTML-escaped because it derives from untrusted README content.
"""
import html
import json
import os
import pathlib
import shutil

BUILD = pathlib.Path(os.environ.get("BUILD_DIR", "build"))

CSS = """
*{box-sizing:border-box;margin:0}
body{width:1920px;height:1080px;background:#0f1220;color:#f4f6ff;font-family:Inter,system-ui,sans-serif;overflow:hidden}
.scene{position:absolute;inset:0;padding:140px 160px;display:flex;flex-direction:column;justify-content:center;
  background:radial-gradient(1200px 700px at 80% 10%,#26305f 0%,#0f1220 60%)}
h1{font-size:88px;line-height:1.1;margin-bottom:48px;animation:rise .6s ease-out both}
li{font-size:46px;line-height:1.5;margin-left:56px;color:#c9d2ff;animation:rise .6s ease-out both}
li:nth-child(2){animation-delay:.25s}li:nth-child(3){animation-delay:.5s}
.src{position:absolute;left:160px;bottom:70px;font-size:30px;color:#7f8bc7}
@keyframes rise{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:none}}
"""


def main():
    topic = json.loads((BUILD / "topic.json").read_text())
    script = json.loads((BUILD / "script.json").read_text())
    durations = json.loads((BUILD / "durations.json").read_text())
    out = BUILD / "video"
    out.mkdir(parents=True, exist_ok=True)
    t = 0.0
    parts = []
    for i, (s, d) in enumerate(zip(script["scenes"], durations)):
        shutil.copy(BUILD / f"scene_{i}.wav", out / f"scene_{i}.wav")
        bullets = "".join(f"<li>{html.escape(b)}</li>" for b in s["bullets"])
        parts.append(
            f'<section class="scene" data-start="{t:.2f}" data-duration="{d:.2f}" data-track-index="0">'
            f"<h1>{html.escape(s['headline'])}</h1><ul>{bullets}</ul>"
            f'<div class="src">{html.escape(topic["full_name"])} · {html.escape(str(topic["license"]))}</div></section>'
            f'<audio src="scene_{i}.wav" data-start="{t:.2f}" data-duration="{d:.2f}" data-track-index="1"></audio>'
        )
        t += d
    doc = (f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(script["title"])}</title>'
           f"<style>{CSS}</style></head><body>" + "".join(parts) + "</body></html>")
    (out / "index.html").write_text(doc)
    print(f"composition: {t:.1f}s -> {out / 'index.html'}")


if __name__ == "__main__":
    main()
