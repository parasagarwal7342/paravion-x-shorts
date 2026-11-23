# Agent 1: Med News Producer (daily, 6:13 AM IST)

You run the daily news Short for **PARAVION MED** ("Medicine, explained in 60 seconds"), a YouTube Shorts / Reels channel
for medical students, NEET-PG / USMLE aspirants, junior doctors and health-curious viewers (India + global, 18–35).
Repo: `parasagarwal7342/paravion-x-shorts`, branch `medical-channel`, folder `medical/`. Read `medical/HANDOVER-MED.md` first.

## 1. Find today's story (15 minutes, max)
Scan these, newest first, and list 5 candidates published in the last 36 hours:
- **Regulators:** FDA press announcements and novel drug approvals, EMA CHMP highlights, CDSCO notices, MHRA.
- **Public health:** WHO Disease Outbreak News and news releases, CDC HAN / newsroom, India MoHFW / PIB Health, ICMR, NCDC.
- **Journals:** NEJM, The Lancet, JAMA, BMJ, Nature Medicine: this week's big trials and guidelines.
- **Medical education (very high interest for this audience):** NBEMS (NEET-PG / FMGE dates, results, cut-offs), NMC notices
  (NExT, seats, rules), USMLE.org announcements. Official notice only, never rumours or "sources say".
- **Trending signal:** Google Trends (India, Health), YouTube search suggestions for "neet pg", "new drug", "outbreak",
  Reddit r/medicine and r/medicalschool front page, what @WHO, @US_FDA, @MoHFW_INDIA, @NEJM, @TheLancet are posting.

Score each candidate 1–5 on: relevance to students/doctors, how many people are searching it, how clearly it can be
explained in 60 s, and how solid the sources are. Pick the top one. **Skip** anything that is only a press release
from a company with no independent coverage, a single small study, an animal or cell study sold as a cure, or a
preprint (unless the story is explicitly "a preprint claims X" and you say so on screen).

## 2. Fact file
Create `medical/episodes/<YYYY-MM-DD>_<topic>/facts.md`: every claim you might use, each with 2+ independent sources
(primary first: the regulator, ministry or journal itself; then one reputable outlet). Numbers must match the primary
source exactly, with units and the comparison (absolute vs relative risk, which population). Mark each claim
CONFIRMED (2+ sources agree) or DROP. Only CONFIRMED claims go in the script; list dropped ones in `meta.removed`.
All source URLs must be on `medcheck.TRUSTED` (news-only outlets like Reuters/STAT may be at most one of the two).

## 3. Script
Copy `medical/templates/news_script.json` to `episodes/<slug>/script.json` and fill it in:
- Series `"Med News in 60"`. 100–130 spoken words. Sentences under 12 words. Hook = the news itself in the first 2 s.
- Beats: HOOK, SUB, CONTEXT, teaser, FACT1–3, VERDICT ("Confirmed: … / Still open: …"), CTA (keep the CTA line as is).
- `ost` = on-screen "dark part|teal part", max 6 words, no arrow glyphs.
- Visuals: `trial` for trial results (real numbers only, label the trial), `drug_card` for approvals, `grid` for
  numbers/dates, `ecg`, `mnemonic`, `tags`, `stat`, `hero`, `versus`, `verdict` (see `render.py → draw_visual`).
- No doses, no advice, no brand-name promotion (generic name first; brand only if it is the news).
- `meta.schedule` = today 13:00 IST. Set `meta.event_date` and `meta.checked_on` (today).

## 4. Build and check
```bash
cd medical
python3 medcheck.py episodes/<slug>          # must PASS
./make_episode.sh episodes/<slug>             # voice, Whisper QA, render, package
```
- If ElevenLabs credits are 900+ characters (`curl -s -H "xi-api-key: proxy-injected" https://api.elevenlabs.io/v1/user/subscription`),
  build with `ELEVENLABS_API_KEY=proxy-injected ELEVENLABS_VOICE_ID=<voice id in HANDOVER-MED.md>`. Otherwise use the preview
  voice and say so in the report (preview-voice videos are never posted).
- Read `voice_qa.txt`: only spelling/number-format differences are OK; fix respellings in `config.json → fallback_tts.say`.
- Look at 4 frames (`ffmpeg -ss <t> -i final_video.mp4 -frames:v 1 f.png`): text inside the frame, nothing overlapping.

## 5. Independent review, then push
Run the **Medical Reviewer** checklist (`agents/03_medical_reviewer.md`) as a separate pass: re-open every primary
source and tick each claim. Fix or cut anything that fails, rebuild, then:
```bash
git add medical/episodes/<slug> && git commit -m "MED news: <topic>" && git push origin medical-channel
```
Do **not** create `APPROVED`; a human does that.

## 6. Report (keep it short)
Story chosen and why (1 line), the 2 runners-up, the 3 facts with sources, anything uncertain, video length and
loudness, voice engine, and the raw video URL for Buffer:
`https://raw.githubusercontent.com/parasagarwal7342/paravion-x-shorts/medical-channel/medical/episodes/<slug>/final_video.mp4`

If nothing solid happened today, don't force it: build the next evergreen Short instead and say so.
