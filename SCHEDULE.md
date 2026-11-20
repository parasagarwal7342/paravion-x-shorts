# Posting schedule — PARAVION X

All times IST. YouTube publishes each Short automatically at its time once it has been uploaded as private with `youtube_schedule.py --upload`.

| # | When (IST) | Episode | YouTube title | Length | Re-check before posting |
|---|---|---|---|---|---|
| 1 | Fri 20 Nov, 08:00 AM | `2026-11-19_trilateral` | Trump, Xi and Putin Meet: What We Know | 43.1 s | TIME-SENSITIVE: outcomes may be announced within hours. Re-check for a readout or joint statement and update fact 3 and the verdict before posting. Political: neutral, no opinion. |
| 2 | Fri 20 Nov, 01:00 PM | `2026-11-19_csat_alerts` | South Korea Rang Every Phone to Catch Cheaters | 54.3 s | The 22-phone count is preliminary. Re-check for a final figure before posting. |
| 3 | Fri 20 Nov, 07:30 PM | `2026-11-19_nvidia` | Nvidia's CEO Quit After 33 Years — What Happened? | 57.6 s | Re-check whether a permanent CEO was named. |
| 4 | Sat 21 Nov, 08:00 AM | `2026-11-19_eu_ukraine_loan` | EU's €45B Ukraine Loan Explained in 60 Seconds | 51.0 s | Political topic: the script states only the proposal's terms, with no opinion. Re-check whether EU leaders have acted before posting. |
| 5 | Sat 21 Nov, 01:00 PM | `2026-11-19_saff_final` | India's Comeback vs Pakistan Explained in 60s | 45.0 s | No wire-service source was found. Facts agree across three sports outlets, one of which cites the AIFF match report. The tone stays neutral on India–Pakistan. |
| 6 | Sat 21 Nov, 07:30 PM | `2026-11-19_amazon_india` | Amazon's $7B India Clean Power Plan Explained | 50.4 s | Company announcement: figures are Amazon's own, reported by two trade outlets. |

## Before each goes out
1. Add the ElevenLabs key and voice ID, then rebuild: `REVOICE=1 ./run_batch.sh` (voice, QA, render and package for every episode).
2. Re-check the facts flagged above, then mark the episode approved: `touch episodes/<slug>/APPROVED`.
3. Schedule: `python3 youtube_schedule.py` (dry run), then `python3 youtube_schedule.py --upload`.
4. Pin the posted comment in YouTube Studio (the API can't pin comments).
