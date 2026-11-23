# PARAVION MED: the agent team

Six agents run the channel. Each `.md` file here is a complete, standalone prompt: paste it into a scheduled task
(Claude Code on the web: **Scheduled tasks → New**, repo `parasagarwal7342/paravion-x-shorts`, branch `medical-channel`)
or hand it to any other assistant. The work folder for every agent is `medical/`.

| # | Agent | When (IST) | Output |
|---|---|---|---|
| 1 | [Med News Producer](01_med_news_producer.md) | Daily 6:13 AM | Finds the day's trending medical story, fact-checks it, builds a Short, pushes it |
| 2 | [Evergreen Writer](02_evergreen_writer.md) | Mondays 10:37 AM | Writes 7 new "High-Yield in 60" / "Myth or Medicine?" specs, builds them |
| 3 | [Medical Reviewer](03_medical_reviewer.md) | Called by 1 and 2 before every push | Independent second check of every claim against the primary source |
| 4 | [Publisher](04_publisher.md) | Daily 8:47 AM | Schedules Shorts (1 PM news, 7:30 PM evergreen) and text posts through Buffer |
| 5 | [Growth Analyst](05_growth_analyst.md) | Sundays 11:13 AM | Weekly numbers, what worked, next week's topic mix in `reports/` |
| 6 | [Engagement Desk](06_engagement_desk.md) | Inside the Publisher run | Drafts comment replies, polls and community posts for the owner to approve |

## The pipeline every Short goes through

```
topic → fact file (3+ sources) → script.json → medcheck.py ─┐
                                                            ├─ fail → fix script
                                                            └─ pass → voice.py → transcribe_check.py
   → render.py → package.py → Medical Reviewer → git push → Publisher (Buffer) → human pins comment
```

`./make_episode.sh episodes/<slug>` runs medcheck → voice → Whisper QA → render → package in one go.

## Hard rules for every agent (from `../HANDOVER-MED.md`)

1. **Accuracy beats speed.** Every fact line needs 2+ independent, trusted sources (`medcheck.TRUSTED`). A claim that
   can't be confirmed is cut. Preprints are labelled "preprint, not peer-reviewed" or skipped.
2. **Education, not advice.** No doses, no "you should take/stop", no diagnosis of individuals, no product promotion.
   Every video carries the on-screen "Educational only · Not medical advice" line and the description disclaimer.
3. **No patient images, no real case details, no leaked exam papers or rumours.** Exam news (NEET-PG, NExT, FMGE, USMLE)
   comes only from the official body (NBEMS, NMC, USMLE.org) plus one reputable outlet.
4. **Neutral and kind** on contested topics (vaccines, policy, pricing). State what's confirmed and what's still open.
5. **No fake engagement.** No auto-replies, auto-follows, bought views, or fake accounts. Replies are drafted for the owner.
6. **Every Short says when it was fact-checked.** `meta.checked_on` is shown on screen and in the description as
   "Fact-checked as of <date>". Re-check and update it before posting if it is older than 1 day (news) or 90 days (evergreen).
7. **Never commit secrets.** ElevenLabs is injected by the environment proxy; YouTube OAuth files are git-ignored.
