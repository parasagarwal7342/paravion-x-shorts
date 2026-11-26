# PARAVION X: handover (as of Thu 26 Nov 2026, ~11:30 AM IST)

This file is for a new assistant or person who needs to keep the channel running.
- **Repo:** https://github.com/parasagarwal7342/paravion-x-shorts (public, branch `main`). Clone it first. All paths below are relative to it.
- **Older notes** (the Nov 20 version of this file, with the Shorts-only pipeline, brand and growth rules) are in git history (`git log -p -- HANDOVER.md`). See also `CHANNEL_AUDIT.md`, `GROWTH.md`, `ENGAGEMENT.md` and `SCHEDULE.md`.

---

## 1. What the channel is now
- **Name:** PARAVION X. **Niche, agreed with the owner on 24 Nov:** *"The world's biggest trending story, explained & fact-checked."* Any topic, same format every time.
- **Main product:** long videos of 8–10 min, landscape 1920×1080, **daily at 7 PM IST**. They must run past 8:00 so mid-roll ads are allowed, and only long videos count toward the 4,000 watch hours.
- **Supporting content:** a vertical teaser Short at **1 PM IST** that points to a long video (set "Related video" in YouTube Studio), plus X posts.
- **Structure of every long video:** hook (0:00–0:30) → chapters with curiosity names → **Fake or Fact?** verdict segment (the signature) → what happens next → a one-word comment prompt (e.g. "Comment HOLD or FOLD").
- **Title formula:** `[Big fact/number] + [Topic]: [What We Know / Explained]`.
- **Thumbnail:** one huge number or 2–3 words, one real photo, and the PX logo, in the same layout every time.
- **Playlists:** Tech & Money, Explained · World News, Explained · Gaming & Entertainment, Explained · Fake or Fact?

## 2. Hard rules (owner's)
1. **Facts first.** Every claim needs 2+ independent reliable sources and is attributed on screen ("according to Adobe"). Forecasts are labelled as forecasts. If a claim can't be confirmed, cut it. No clickbait lies; thumbnails use "~" or "record" rather than invented absolutes.
2. **Real photos only:** Wikimedia Commons CC/PD, credited in the description or pinned comment. **No AI images of real people. No game footage** (copyright).
3. **Neutral** on wars and politics.
4. **Nvidia / Alice Huang:** never call her a spy. As of 25 Nov she has not been charged and the investigation is ongoing. Say "the investigation is still running."
5. **Never commit secrets.** Don't put model names or IDs in commits.
6. **Posting:** the owner uploads **long videos manually** in YouTube Studio, because Buffer's YouTube channel only takes Shorts (≤3 min, vertical). Buffer is used for X posts and YouTube Shorts. Only change Buffer when the owner asks.

## 3. Accounts and IDs
| What | ID / handle |
|---|---|
| YouTube | @PARAVION_X, channel `UCE0ZwrfC8ARoL5lP1vWM78Q` |
| X | @PARAVION_X |
| Buffer org | "My organization" `6afff89f0d778e6235384d9f`, timezone Asia/Kolkata |
| Buffer YouTube channel | `6b00007dece6dfde5f2ea064` (Shorts only) |
| Buffer X channel | `6b001a7fece6dfde5f2f9789` |
| Google Sheet | "PARAVION X — Content Tracker", `11qhgXQCTzNlRfv0Ob7hrMjDx-NGPRJQg55Qz0jz8ttk` |
| ElevenLabs | **out of credits** (~320 chars left). All new videos use the free local Kokoro voice. |

**Channel stats (owner's Studio screenshot, ~25 Nov):** about 15 subscribers and 2.7 public watch hours. YPP needs 1,000 subs plus 4,000 long-form watch hours.

## 4. Google Sheet (tracker)
Tabs: **Dashboard** (KPIs, monetization progress, where B9 = subs and B10 = watch hours are yellow inputs the owner types, top videos, long vs short, by area, queue, 3 charts), **Summary**, **X Posts**, **Instagram Posts**, **YouTube**, **Replies**.
- **YouTube tab columns:** A # · B Date · C Time · D Series ("Long-form" / "Short" / …) · E slug · F Title · G Status · H Link · I Views · J–L Likes/Comments/Shares · **M Subs gained (owner's; never write)** · N Area · **O Format (ARRAYFORMULA; never write)** · **P/Q formulas (never write)** · R Last updated · S Notes.
- **X Posts tab:** H Status · I Link · J Views (impressions) · K Likes · L Replies · M Reposts · P/Q formulas (never write) · R Last updated · S Notes.
- **Status values must be exactly one of:** Posted, Scheduled, Pending, In production, Draft, Cancelled, Failed.

**Automatic sync:** the scheduled task **"PARAVION X — tracker sync"** (`trig_01V5EphtKLun5eyQhvRHBxTp`) runs at **11:27 AM and 11:27 PM IST**. It runs `python3 stats_sync.py`, which scrapes the public /videos and /shorts pages (views only; no API key). It also reads Buffer's `list_posts` with metrics for X, then updates the sheet. It never posts anything. Last run: 26 Nov 11:27 AM, when YouTube had 343 total views and X had 187.

## 5. How a long video is made
Requirements: Python 3, ffmpeg, Pillow, numpy, soundfile, `kokoro-onnx` (voice `af_heart`; model files in a local `kok/` folder pointed to by `KOKORO_DIR`), and `faster-whisper` (small.en, used for word timing and QA).
1. **Research** with 2+ sources per claim. Write `sources.txt`.
2. **Photos:** search Wikimedia Commons (standard thumb width 1920; slow down on 429 errors). Save to `<work>/img/<key>.jpg` and keep a `meta.json` with author, licence and page. **Look at every photo before using it.** On 25 Nov, the "Cyber Monday at Amazon HQ" photos turned out to be a union protest and had to be dropped.
3. **Script:** `<work>/script.json` → `{"segments":[…]}`. Segment kinds: `photo` (img, optional img2 for a mid-scene crossfade, big, sub, text), `chapter` (n, label, img), `chart` ({title, bars:[[label, sub, value, display]], vmax, step, highlight, source}, bg), `verdict` (claim, verdict FACT/FAKE/other→amber, why, bg), `quote`, `timeline`, `outro` (photo, name, role, q). Copy from `episodes/2026-11-28_bf_vs_cyber_monday_longform/script.json`. About 1,000–1,150 words gives ~8 min at speed 0.92.
4. **Voice:** `KOKORO_DIR=… python3 longform_voice.py <work> af_heart 0.92 [ids…]`. Name respellings go in `SAY` in that file.
5. **Render:** `python3 longform_pad.py <work> <pad_seconds>`. Pick a pad so the total lands just over 8:00: pad = (488 − voice total) / number of segments, ideally 0.8–1.6 s. The render resumes; delete `parts/NN.mp4` to redo one scene. Vertical Short: `python3 longform_vertical.py <work>/short` with its own `script.json`, voiced at speed 1.1.
6. **QA:** grab frames into a grid and look at them. **Space Grotesk has no arrow glyphs** (→ shows as boxes), so don't use arrows in on-screen text.
7. **Encode for GitHub (100 MB limit):** long video `-c:v libx264 -preset veryfast -b:v 1250k -maxrate 2500k -bufsize 5000k -c:a aac -b:a 160k -movflags +faststart` (≈86 MB for 8 min). Short: `-crf 21 -maxrate 10M`.
8. **Thumbnail:** 1280×720 using `longform.L.grade`, `L.F(size)`, `L.ACC`/`RED`/`GREEN`, `L.logo_img`. See the BF-vs-CM thumbnail code in its episode folder history.
9. **Episode folder:** `episodes/<date>_<slug>_longform/` with final_video.mp4, thumbnail.png, yt_title.txt, yt_desc.txt (hook lines, what you'll learn, timestamped chapters, comment prompt, sources, hashtags), sources.txt, credits.txt and script.json. Commit and push.

## 6. Long videos: status and schedule (owner uploads in YouTube Studio)
| Date (IST) | Video | Folder | Status |
|---|---|---|---|
| 22 Nov | Why Nvidia CEO Jensen Huang Resigned | `2026-11-22_nvidia_longform` | Live (utpX4Q9lxPY) |
| 23 Nov | Jensen Huang Is BACK as Nvidia CEO | `2026-11-23_nvidia_return_longform` | Live (y2-cLR8VZFA) |
| 24 Nov | GTA VI Made $3.79 BILLION in One Day | `2026-11-24_gta6_longform` | Live (Vs0T3ewJYJY), best long so far |
| 25 Nov | Ukraine Says 7 Sea Drones Sank a Russian Warship in LIBYA | `2026-11-24_ukraine_libya_longform` | Live (29_AgL6Mjdo) |
| 25 Nov 7 PM | Nvidia Added ~$1 TRILLION in One Day | `2026-11-25_nvidia_1t_longform` | Live (j0gY8O4e7WA) |
| **26 Nov 7 PM** | Black Friday 2026: Are the Deals FAKE? 5 Tricks Shops Use | `2026-11-26_black_friday_longform` | Owner to schedule |
| **27 Nov 7 PM** | CrowdStrike Buys Zscaler for $43.9 BILLION | `2026-11-26_crowdstrike_zscaler_longform` | Owner to schedule |
| **28 Nov 7 PM** | Black Friday vs Cyber Monday 2026: Which Day Is ACTUALLY Cheaper? | `2026-11-28_bf_vs_cyber_monday_longform` | Owner to schedule |

Shorts the owner uploads by hand: **BF vs Cyber Monday Short on 29 Nov at 1 PM** (`2026-11-28_bf_vs_cyber_monday_short/`, text in `captions.md`, plus an X post for 30 Nov at 9 AM).
Note: another session made a separate `2026-11-26_black_friday_guide` Short (51 s). Don't post both it and the Black Friday Short.

## 7. Buffer queue (checked 26 Nov ~11:30 AM IST)
**Ours (planned):**
- YouTube Shorts: Black Friday Short 27 Nov 1 PM (`6b05788698255767f8684e58`); CrowdStrike teaser 28 Nov 1 PM (`6b05625c637ab97445e1f01b`). The Ukraine and Nvidia teasers have already gone out.
- Drafts: Nvidia series Parts 2 and 3 (YouTube and X). Parked on purpose because the story moved on.

**⚠️ Needs the owner's decision.** On 25 Nov another session queued evergreen Fake-or-Fact posts (E02 leap year, E03 GPS, E04 black holes, E05 tides, E06 ozone). These are YouTube Shorts and X posts at 7:30 PM IST from 26 to 30 Nov, plus X text posts at 4 PM / 5 PM. They clash with the 7 PM long-video slot and with the owner's 21 Nov instruction not to re-add E01–E14. Two have already gone out on X: "sky is blue" (25 Nov, 7:31 PM) and "1900 wasn't a leap year" (26 Nov, 10 AM). The second one promises a "full explainer tonight at 7:30 PM". **Ask the owner** whether to keep them or move them to drafts.

## 8. Story notes (as of 25–26 Nov)
- **Nvidia:** Huang resigned 12 Nov; the board said no on 17 Nov; he was reinstated unanimously on 23 Nov; the stock rose about 31% on 23 Nov. The investigation is ongoing and **no charges have been filed**. A reported SEC review is **unconfirmed**. Congressional interviews are expected around **1–2 Dec**, which is a possible "comeback under fire" follow-up.
- **Ideas offered but not confirmed by the owner:** a Fed/PCE inflation explainer and the Nvidia follow-up above.

## 9. Owner to-dos
1. Schedule the 26, 27 and 28 Nov long videos in Studio, and the 29 Nov Short.
2. Pin the comment prompt on each video after it goes live, plus photo credits on the BF-vs-CM video.
3. Set "Related video" on each teaser Short.
4. Fix the channel's upload-default tags: they had comedy and kids tags. Keep "Not made for kids".
5. Every Sunday, check CTR (aim 5%+), average view duration (aim 40%+) and the retention graph, and share the numbers.
6. Biggest monetization risk: the same template with an AI voice can be flagged as "inauthentic content". Recording your own voice-over, or a short on-camera intro, would help a lot.

## 10. Gotchas
- Buffer needs a **public direct** video URL. GitHub raw links work: `https://raw.githubusercontent.com/parasagarwal7342/paravion-x-shorts/main/<path>`.
- GitHub rejects files over 100 MB. Re-encode with the long-video settings above.
- Wikimedia returns 429 when you go too fast. Use 1920-wide thumbs and wait between downloads.
- faster-whisper: pass numpy audio, not a file path (there's an `av` version error).
- When updating the sheet, a null value skips a cell. Never overwrite headers or the formula columns.
