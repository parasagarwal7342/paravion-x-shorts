# PARAVION MED: handover

A sister channel to PARAVION X, built on the same Shorts factory, for **trending medical news and high-yield medicine**.
Everything lives in `medical/` on the `medical-channel` branch of `parasagarwal7342/paravion-x-shorts`.
All commands below run from `medical/`.

## 1. The channel
- **Name:** PARAVION MED · **Handle:** @PARAVION_MED · **Tagline:** "Medicine, explained in 60 seconds."
  (Change any of these in `config.json`; the renderer, packager and brand kit all read from it.)
- **Audience:** MBBS/BDS/nursing students, NEET-PG / FMGE / NExT / USMLE aspirants, junior doctors, and curious public. India + global, English.
- **Format:** 1080×1920 Shorts/Reels, 30–59 s, white "clinic" look with teal accents, karaoke captions,
  "Educational only · Not medical advice" under the logo on every frame.
- **Three series:**
  | Series | Slot (IST) | What |
  |---|---|---|
  | **Med News in 60** | 1:00 PM daily | the day's trending medical story: approvals, big trials, guidelines, outbreaks, NEET-PG/NMC/NBEMS exam news |
  | **High-Yield in 60** | 7:30 PM | exam-style pearls: triads, scores, guideline numbers, mnemonics, ECGs |
  | **Myth or Medicine?** | 7:30 PM (about 2 a week) | popular health myths answered with Cochrane / meta-analyses / WHO / CDC |
- **Golden rule:** accurate first, useful second, viral third. 2+ trusted sources per fact. No doses, no personal advice.

## 2. What's built
| File | Job |
|---|---|
| `specs.py` | Evergreen bank. 11 Shorts written and source-checked (M01–M11). `python3 specs.py` writes their `script.json`. |
| `medcheck.py` | **Medical safety gate**: 2+ sources per fact line, trusted-domain allowlist, blocks doses/advice/hype words, length limits, news freshness fields. Runs first in `make_episode.sh` and again before any upload. |
| `voice.py` | ElevenLabs (paid takes saved and reused) or the free Piper preview voice. |
| `transcribe_check.py` + `qa_text.py` | Whisper transcript vs script (handles British/American spellings). |
| `render.py` | Video: new medical visuals `ecg` (normal / stemi / peaked_t / af / vfib), `trial` (arm bars), `mnemonic`, `grid` (value tiles), `drug_card`, plus all the original ones. |
| `package.py` | PACKAGE.md (sources, fact-check table, titles, description with disclaimer, pinned comment, Instagram caption, QA) + `upload.json`. |
| `youtube_schedule.py` | Optional direct YouTube upload (private + scheduled), gated on ElevenLabs voice + medcheck + `APPROVED`. |
| `templates/news_script.json` | Template for the daily news Short. |
| `agents/` | Six agent prompts (producer, writer, reviewer, publisher, analyst, engagement desk). |
| `brand/` | Logo, avatar, YouTube banner, X header (`python3 brand/make_brand.py` regenerates them). |

## 3. One-time setup (owner)
1. **Create the YouTube channel** (YouTube → profile → Settings → *Add or manage channels* → *Create a channel*), name
   "PARAVION MED", handle @PARAVION_MED (or the closest free one, then update `config.json`).
   - Upload `brand/profile_800.png` (picture) and `brand/youtube_banner_2560x1440.png` (banner).
   - Description and keywords: see `brand/CHANNEL_COPY.md`.
   - Audience: not made for kids. Verify the phone number to unlock longer videos and custom thumbnails.
   - Create playlists: *Med News in 60*, *High-Yield in 60*, *Myth or Medicine?*, plus one per specialty as they fill.
   - Optional: apply for YouTube's health source information panel later (needs a recognised medical organisation).
2. **Buffer:** connect the new YouTube channel (and Instagram/X if you make them). The free plan allows 3 channels and
   PARAVION X already uses 2, so either upgrade Buffer or use a second Buffer workspace for PARAVION MED.
3. **ElevenLabs:** the free plan is shared with PARAVION X (10,000 characters/month ≈ 14 Shorts total). For a daily
   medical channel, the Starter/Creator plan is needed. Pick a calm, clear voice and put its ID in the agent prompts
   (default in the scripts is "Daniel", `onwK4e9ZLuTAKqWW03F9`). The key is injected by the Claude environment
   proxy; never commit it.
4. **Turn on the agents:** create the scheduled tasks from `agents/` (see `agents/README.md`). If the PARAVION X tasks
   are still running, keep both: they work in different folders and post to different channels.

## 4. Making a Short by hand
```bash
pip install pillow numpy piper-tts faster-whisper          # plus ffmpeg
# preview voice (free, not for posting):
mkdir -p assets/piper && cd assets/piper && \
  curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/high/en_US-lessac-high.onnx && \
  curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/high/en_US-lessac-high.onnx.json && cd ../..
python3 specs.py                                            # evergreen scripts
./make_episode.sh episodes/M01_becks_triad                  # medcheck → voice → QA → render → package
ELEVENLABS_API_KEY=… ELEVENLABS_VOICE_ID=… REVOICE=1 ./make_episode.sh episodes/M01_becks_triad   # real voice
./eleven_batch.sh episodes/M0*                              # voice several while credits last
```
Then read `PACKAGE.md`, re-check facts, `touch episodes/<slug>/APPROVED`, commit, push, schedule.

## 5. Status (Nov 23, 2026)
- M01–M11 written, source-checked through PubMed E-utilities, and rendered with the **preview voice**
  (not for posting). Each needs about 600 ElevenLabs characters to re-voice.
- Planned slots: M01 on Nov 26, 7:30 PM, then one a day (see `meta.schedule` in each script).
- No news Short yet: the News Producer makes the first one on its first run.

## 6. Gotchas (inherited from PARAVION X, still true)
- Buffer needs a public direct video URL: GitHub raw works (push first).
- Space Grotesk has no arrow glyphs; don't put arrows in on-screen text (medcheck blocks them).
- Keep scripts ≤ 130 words or the ElevenLabs voice runs over 60 s.
- Whisper hears "Beck's" as "Bex" and "Paravion" as "Paravi on"; those QA mismatches are fine.
