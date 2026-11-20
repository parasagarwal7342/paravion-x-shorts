# PARAVION X — Shorts factory

"The world, explained in 60 seconds." YouTube Shorts / Instagram Reels: daily news + "Fake or Fact?" explainers.

- `episodes/<slug>/` — `script.json` (fact-checked script + metadata), `final_video.mp4`, `cover.png`, `PACKAGE.md` (sources, fact-check, titles, captions), `upload.json`
- `voice.py` — ElevenLabs (saved takes are reused, no repeat charges) or Piper preview voice
- `render.py` — 1080×1920 video, captions, graphics, music/SFX, −14 LUFS
- `make_episode.sh <episode>` — voice → transcript QA → render → package
- `evergreen_specs.py` — the 30 "Fake or Fact?" explainers
- `brand/` — logo, YouTube banner, Instagram kit, general posts

Only videos voiced with ElevenLabs are committed (`timings.json` engine = `elevenlabs`); preview-voice videos are rebuilt locally.
