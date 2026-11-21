# PARAVION X: handover (as of Nov 20, 2026, ~4 PM IST)

Everything a new assistant (e.g. Grok) or a person needs to keep the channel running.
Repo: **https://github.com/parasagarwal7342/paravion-x-shorts** (public). Clone it first; all paths below are relative to it.

---

## 1. What the channel is
- **Name:** PARAVION X · **Tagline:** "The world, explained in 60 seconds."
- **Format:** 1080×1920 vertical Shorts/Reels, 35–59 s, English, Indian + global audience (16–35).
- **Two series:**
  - **News in 60 seconds** (1:00 PM IST): today's biggest story, what happened, 3 facts, verdict.
  - **Fake or Fact?** (7:30 PM IST): evergreen myth-busters (30 written, E01–E30).
- **Golden rule:** accurate first, engaging second, viral third. Every fact needs **2+ reliable, independent sources**. No invented quotes, no financial, medical or legal advice, neutral on politics. If a fact can't be confirmed, cut it.

## 2. Accounts
| Platform | Handle / ID | Notes |
|---|---|---|
| YouTube | **@PARAVION_X**, channel UCE0ZwrfC8ARoL5lP1vWM78Q | Description, keywords and upload defaults updated. Audience: **not made for kids**. |
| X | **@PARAVION_X** | Bio, header and profile picture done (brand/x/). Professional account: Media & News. |
| Instagram | not connected yet | Kit ready in brand/instagram/ (profile picture, bio, highlight covers). |
| Buffer | org "My organization" (free plan), timezone Asia/Kolkata | Channels: **YouTube** (id 6b00007dece6dfde5f2ea064), **X** (id 6b001a7fece6dfde5f2f9789). 1 free channel slot left (for Instagram). |
| ElevenLabs | free plan | 9,680 / 10,000 characters used this month. Voice: **Daniel** (built-in, id `onwK4e9ZLuTAKqWW03F9`). Indian-English library voices (Viraj, Ranbir, Riya Rao, Tia Mirza) were added to the account but need a **paid** plan to use through the API. |
| Google Drive | folder "PARAVION X — Shorts" | Older backup only; GitHub is now the source of truth. |

**Secrets:** none are in the repo. The ElevenLabs key was stored as a Claude environment network secret. With another tool, set `ELEVENLABS_API_KEY` yourself. Never commit keys.

## 3. Brand
- Colours: ink `#111111`, accent orange `#E8481C`, white page, light grey `#F3F3F1`, green `#1B8A4A` (TRUE), red `#E01E1E` (FALSE).
- Font: **Space Grotesk** 500/700 (assets/fonts, SIL OFL).
- Wordmark: "PARAVION" black + "X" orange. Logo: white P + orange X on black (brand/logo_800.png).
- Video style: white editorial look. Spaced red kicker, two-tone headline ("black part|orange part"), centred graphics, karaoke captions, orange progress bar, light brand pattern at the bottom.
- Ending line on every Short: **"Like and follow Paravion X for more updates."** No loop line after it.
- Voice of text posts: like a real person typing. Short sentences, contractions, max 1 emoji, light source mentions ("per NASA"), no "Great post!", no hashtags in replies.

## 4. How a Short is made (the pipeline)
Requirements: Python 3, ffmpeg, `pip install pillow numpy piper-tts faster-whisper`. Download the preview voice: `en_US-lessac-high.onnx` + `.onnx.json` from huggingface.co/rhasspy/piper-voices into `assets/piper/`.

1. **Script:** `episodes/<slug>/script.json`, copied from an existing one (e.g. `episodes/2026-11-19_eu_ukraine_loan/script.json`). Lines have `beat` (HOOK, SUB, CONTEXT, FACT1–3, VERDICT, CTA), `text` (spoken, sentences under 12 words), `ost` (on-screen "black|orange", ≤5 words), `visual` (a type from `render.py → draw_visual`), `keys` (highlighted words) and `source`. `meta` has titles, summary, hashtags, ig_tags, pinned, poll, sources, removed, notes, schedule and verdict. Target 100–130 words.
   - Evergreen explainers are generated from `evergreen_specs.py` (`python3 evergreen_specs.py`).
2. **Build:** `./make_episode.sh episodes/<slug>` runs voice → transcript QA → render → PACKAGE.md + upload.json.
   - With ElevenLabs: `ELEVENLABS_API_KEY=… ELEVENLABS_VOICE_ID=onwK4e9ZLuTAKqWW03F9 ./make_episode.sh episodes/<slug>`. Paid takes are saved (`voice_raw.mp3`, `eleven_take.json`) and reused, so rebuilds never cost credits. Pauses over 0.3 s are trimmed and tempo is ×1.08 so Daniel fits under 60 s. Deleting script lines is free (they're cut from the saved take).
   - Without a key: free Piper preview voice. **Not for posting.**
   - `./eleven_batch.sh ep1 ep2 …` voices several episodes while credits last.
3. **QA:** `voice_qa.txt` (Whisper transcript vs script). Only number formatting or name spelling differences are OK. Check length < 60 s and loudness −14 LUFS (both printed). Look at a few frames.
4. **Publish:** video link for Buffer = `https://raw.githubusercontent.com/parasagarwal7342/paravion-x-shorts/main/episodes/<slug>/final_video.mp4`. Commit and push the episode first.

## 5. Status of all 36 Shorts
- **Real ElevenLabs voice (18), committed to GitHub:** Nvidia, EU loan, SAFF final, Amazon India, E01–E14.
- **Preview voice only (18), need re-voicing before posting:** Trump–Xi–Putin summit and South Korea exam alerts (both stale now, skip them), and **E15–E30**. About 650 characters each with ElevenLabs.

## 6. What's scheduled in Buffer (all IST)
**Nov 21 update (owner request):** Amazon $7B India and E01–E06 were **unscheduled and deleted from Buffer on Nov 21** at the owner's request (he wants daily trending, fact-checked Shorts instead). **Do not re-add Amazon or E01–E14 to Buffer** unless the owner asks again. The failed SAFF YouTube entry was also removed.

| Date | YouTube | X |
|---|---|---|
| Nov 20, 7:30 PM | Nvidia CEO exit (sent) | same (sent) |
| Nov 21, 8:00 AM | EU €45B Ukraine loan (sent) | same (sent) |
| Nov 21, 1:00 PM | SAFF final (failed: YouTube daily limit) | sent |
| Nov 23, 1:00 PM | Nvidia series Part 1 (`episodes/2026-11-23_nvidia_part01`) | same |
| Nov 24, 1:00 PM | Nvidia series Part 2 | same |
| Nov 25, 1:00 PM | Nvidia series Part 3 | same |

Nvidia Parts 4–10 are added one a day at 1 PM (Nov 26 – Dec 2) by a Grok Bot routine as Buffer slots open. YouTube descriptions now end with "Subscribe to PARAVION X for more".

**Waiting for a free X slot:** the G20 poll answer post for Nov 22 at 5 PM (text in `growth/approved.md`).
**Owner posts by hand:** the G20 native X poll on **Nov 21 at 5 PM**: "Quick one 🌐 How many members does the G20 actually have?" with options `20 countries` / `19 + EU + African Union` / `25 countries`, 1 day.

**Buffer free-plan limits:** 10 queued posts per channel, YouTube max 2 posts/day. Keep topping up as posts go out with the daily trending Shorts and the remaining Nvidia parts (not E07–E14, see the Nov 21 note above). Use YouTube category 27 (Education) or 28 (Science & Tech) for explainers, 25 for news, 17 for sports. Set madeForKids false and public.

## 7. Automations (currently running in Claude Code; they keep running unless paused)
| Name | When (IST) | What |
|---|---|---|
| PARAVION X — daily current-topic Short | 6:23 AM daily | Researches the day's top story, fact-checks it, builds a Short, pushes it to GitHub. Uses the preview voice while ElevenLabs credits are under 900. |
| PARAVION X — daily Publisher | 8:47 AM daily | Auto-schedules our own posts (news Short at 1 PM, explainers at 7:30 PM, 2 X text posts at 10 AM and 5 PM), drafts the daily poll for the owner, plus 3 optional replies. Never replies to, mentions, follows or DMs other accounts. |
| PARAVION X — weekly Growth Analyst | Sundays 11:13 AM | Buffer metrics → best hooks and topics → next week's plan in `reports/<date>.md`. |

If Grok takes over these jobs, **pause them in Claude** (claude.ai → Scheduled tasks), or posts will be duplicated.

## 8. Daily routine (if done by hand or by another assistant)
1. **Morning:** pick the top story → fact file (3+ sources) → keep only claims confirmed by 2+ → script → build → QA → push → schedule at 1 PM on YouTube + X.
2. Top up Buffer with the next explainer at 7:30 PM.
3. Schedule 2 X text posts (10 AM fact, 5 PM poll answer or "did you know").
4. Draft tomorrow's native X poll for the owner.
5. Owner: post the poll (5 PM), reply to people who comment on our posts.
6. Sundays: review numbers, keep what works (hook type, topic, length).

## 9. Growth rules (see GROWTH.md and ENGAGEMENT.md)
- Speed on news, strong first 2 seconds, 2 Shorts a day at fixed times, keyword-first titles, playlists ("Fake or Fact?", "News in 60 Seconds"), a pinned question on every Short, the same video native on every platform.
- **Never:** auto-replies to others, auto-follow/like, bought engagement, fake accounts, clickbait lies. X bans unsolicited automated replies.
- 60 target accounts for manual replies: `growth/x_targets.md`.

## 10. Ready-made assets
- `brand/`: logo, YouTube banner (2560×1440), Instagram kit + bio, X header/profile + bio, social posts (6 Instagram, 2 YouTube Community images, POSTS.md with captions and polls).
- `episodes/*/PACKAGE.md`: per Short: sources, fact-check table, script with timestamps, titles, description, pinned comment, Instagram caption.
- `brand/x/X_POSTS.json`: the X post texts for the 10 scheduled Shorts (the house style).

## 11. Open to-dos
1. More ElevenLabs credits (paid **Starter/Creator**, or a new key): re-voice E15–E30, voice daily news, and unlock the Indian-English voices.
2. Connect **Instagram** in Buffer (last free channel), then schedule Reels and the 6 Instagram posts.
3. Optional: YouTube Data API key (console.cloud.google.com → YouTube Data API v3) to read comments for replies.
4. YouTube Studio: create the 2 playlists; verify the phone number (Feature eligibility → Intermediate features).
5. Pin a comment on each Short after it goes live (Buffer can't pin).

## 12. Known gotchas
- Buffer needs a **public direct** video URL (GitHub raw works; Drive links didn't).
- Space Grotesk has no arrow glyphs (→ ↓). The renderer draws arrows as shapes, so don't put arrows in on-screen text.
- The preview voice mispronounces names. Always check `voice_qa.txt`; respellings go in `config.json → fallback_tts.say`.
- Daniel (ElevenLabs) speaks ~126 wpm raw. Keep scripts ≤130 words, or the Short runs over 60 s.
