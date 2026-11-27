# PARAVION X: 2026-11-27_gta6_spy_claim_short · "Is GTA 6 Spying on You?"

**STATUS: DRAFT, WAITING FOR OWNER APPROVAL.** Not committed, not pushed, not scheduled.

- Video: `final_video.mp4`, 1080x1920, 30 fps, 59.1 s, -14.1 LUFS, H.264/AAC, 60 MB
- Voice: ElevenLabs "Daniel" (onwK4e9ZLuTAKqWW03F9), one take (896 chars, cached in `eleven_take.json`), pauses trimmed and sped up x1.16 (`tighten.py`). Whisper QA transcript matches the script word for word (`voice_qa.txt`).
- Pipeline: `render_short.py` wraps origin/main `longform.py` (the cinematic real-photo vertical look used by `longform_vertical.py` and the 26 Nov tariff Short), with a vertical welcome card and end card in the style of `build_v3.py`.
  Rebuild: `python3 get_photos.py && python3 voice_eleven.py && python3 tighten.py 1.16 && python3 render_short.py .` (voice reuses the cached take, so no new ElevenLabs charge)

## Story
A viral anonymous X post claims a fired Rockstar North engineer found "Lens", a hidden GTA VI system that scores players' impulse control and aggression, with the profiles sold to insurers by a Take-Two company called "Vantage Analytics". France 24 and What the Fact rate it fake/false. The real twist is that Take-Two's own privacy policy does build "Profile Inferences" and shares them with advertisers, and you can opt out.

**Verdict: FAKE (no evidence).** Sources: `sources.md`.

## Structure (spoken)
1. Hook (0-4.8 s): "Is GTA Six secretly profiling you, and selling it to insurers?"
2. Welcome card: "Welcome to Paravion X. Daily world news, and whether it's real or fake."
3. Claim x3 (labelled CLAIM / UNVERIFIED), then Check 1/3 (SEC filings), 2/3 (anonymous account, fake-looking email), FAKE stamp, 3/3 twist (privacy policy), opt-out
4. End card: "Should games profile players for ads? Yes or no? Comment below. Stay tuned for further updates, and subscribe to Paravion X for more." On screen: question, YES/NO, COMMENT BELOW, "Stay tuned for further updates.", SUBSCRIBE + FOLLOW, "PARAVION X for more".

## Text files
- `x.txt`: X post (276 chars; 278 if X counts the emoji as 2)
- `yt_title.txt`, `yt_desc.txt`, `tags.txt`: YouTube Short. Audience: **Not made for kids**, comments ON, tags from `tags.txt`. Optional: set "Related video" to the 24 Nov GTA VI long video (Vs0T3ewJYJY).
- `credits.txt`: photo credits (all Wikimedia Commons CC/PD; no game footage)

## Retention checklist QA
| Item | Result |
|---|---|
| Full hook text at t=0.0, motion + boom SFX within 0.5 s | PASS |
| Hook spoken in 12 words or fewer (11) | PASS |
| Fact counter 1/3, 2/3, 3/3 | PASS |
| Mid-video FOLLOW pop-up at 42-52% | PASS |
| Captions in safe zone (y=1300), karaoke highlight | PASS |
| 50% or more real photos (9 of 11 screens) | PASS |
| Source credit on every fact screen; claims labelled CLAIM / UNVERIFIED | PASS |
| Music ducked under voice; -14.1 LUFS; true peak limited to -1.5 dBTP | PASS |
| Ends on a yes/no comment question (on screen for the whole end card) | PASS |
| Length: 59.1 s. The checklist wants 45 s max, but the brief and owner format ask for 45-60 s | NOTE |
| Verdict at 61% instead of the last 20% (the twist is saved for after it) | NOTE |
| Light/dark alternation: 8 dark photo screens in a row between the light welcome card and the light end card | NOTE |
| End card about 9.5 s, longer than 2 s, because it carries the owner's required CTA lines | NOTE |
| No seamless loop back to frame 1 | NOTE |

## Posting proposal (not scheduled)
See the report in the parent chat. In short, YouTube already has 2 Buffer Shorts today (1 PM Black Friday Short, 7:30 PM GPS evergreen), and X has 7:30 PM taken by the GPS post.
