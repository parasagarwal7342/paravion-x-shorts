# PARAVION MED: medical Shorts factory

"Medicine, explained in 60 seconds." Daily YouTube Shorts / Reels with trending medical news and high-yield medicine
for medical students, exam aspirants and doctors. A sister channel built on the PARAVION X pipeline, with a medical
safety gate added.

- **Start here:** [`HANDOVER-MED.md`](HANDOVER-MED.md) (setup, status, commands)
- **The agents:** [`agents/`](agents/README.md): news producer, evergreen writer, medical reviewer, publisher, growth analyst, engagement desk
- **Episodes:** `episodes/<slug>/` with `script.json`, `final_video.mp4`, `cover.png`, `PACKAGE.md`, `upload.json`
- **Build one:** `./make_episode.sh episodes/<slug>` (medcheck → voice → Whisper QA → render → package)
- **Safety gate:** `python3 medcheck.py episodes/<slug>`
- **Growth:** [`GROWTH-MED.md`](GROWTH-MED.md) · channel copy: [`brand/CHANNEL_COPY.md`](brand/CHANNEL_COPY.md)

Preview-voice videos (`timings.json` engine `piper-preview`) are for review only and are never posted.
