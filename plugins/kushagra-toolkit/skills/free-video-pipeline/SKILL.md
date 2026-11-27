---
name: free-video-pipeline
description: "Make a free explainer video about an open-source AI tool using HyperFrames (HTML to MP4), Kokoro CPU narration and GitHub Actions, with no GPU, Pi or paid service. Use when the user wants to create, run, debug or extend the free video-creation automation or make a video from an AI radar pick."
---

# Free video pipeline

Code lives in `automation/video/`; workflow in `.github/workflows/free-video.yml`.

## Flow
1. `pick_topic.py`: next unused repo from the AI radar candidates (`automation/radar/state/candidates/`), or `TOPIC_REPO=owner/name`. "Used" = GitHub Releases tagged `video-<slug>`.
2. `script.py`: sectioned via the LLM router (`automation/llm/`): facts, outline, per-scene narration, stitch pass. Providers shift automatically on rate limits or bad output. README is untrusted; only the facts step sees it; output is screened.
3. `tts.py`: voiceover per scene, `durations.json`. `VOICE_PROVIDER`: `auto` (your audio file for a scene if present, else Kokoro on CPU), `kokoro`, or `files` (only your audio, no TTS install). Put your own audio (any voice: recording, ElevenLabs, VoiceStudio, Chatterbox) at `automation/video/audio/<slug>/scene_N.wav|mp3|m4a|flac|ogg`; `<slug>` is the release tag minus `video-`. New synthesizers go in `SYNTHS` in `tts.py`.
4. `build_composition.py`: HTML with `data-start` / `data-duration` / `data-track-index` timing, text HTML-escaped.
5. `npx hyperframes render` (needs Node 22 + FFmpeg) renders the MP4; the workflow publishes it as a release together with `source.zip` (script, timing, composition, audio) so you can edit and re-render.

## Run
- Automatic: weekly (Tuesdays). Manual: Actions > "Free video (weekly)" > Run workflow (optional `repo`).
- Needs at least one LLM key as a repo secret (`GEMINI_API_KEY` or `GROQ_API_KEY` are free); GitHub Models works with none. No GPU.

## Manual workflow (no Actions)
Write script in chat, narrate in VoiceStudio or Kokoro, then `npx hyperframes init`, `preview`, `render`.

## Known gaps
- The HyperFrames render step and Kokoro install were not run end to end when this was written; the first Actions run may need tweaks to the composition format (check HyperFrames docs/`/hyperframes` skill).
- Voice model/license: confirm the Kokoro license before monetising videos.
- AI-generated footage needs a GPU (e.g. a Kaggle notebook) and is not part of this pipeline.
