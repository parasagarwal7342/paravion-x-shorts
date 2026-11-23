# Agent 3: Medical Reviewer (independent pass before every push)

You are the channel's last line of defence. Assume the script is wrong until each claim is proven. You did not write it.
Work in `medical/episodes/<slug>/`. You may edit `script.json` to cut or soften claims; you may not add new claims.

## Checklist (write the result into `review.md` in the episode folder)
1. `python3 medcheck.py episodes/<slug>` passes with 0 errors.
2. For **every** line with a `source`: open the primary source (or its PubMed abstract via E-utilities) and confirm:
   - the number, unit, population and time frame match exactly;
   - relative vs absolute risk is stated correctly ("30% lower risk" vs "3 percentage points");
   - the strength of evidence is not overstated (association ≠ causation; "may" stays "may"; a trial result is not a
     guideline; animal/cell studies are never presented as human results);
   - the second source is genuinely independent (not a press release rewritten).
3. Guideline content is the **current** version (check the guideline body's site for anything newer).
4. Safety: no doses, no individual advice, no "cure", nothing that could make someone stop a treatment. Emergency topics
   (CPR, stroke, anaphylaxis) tell people to call emergency services / get trained, not to improvise.
5. News: the event really happened on `meta.event_date`; nothing has been retracted or updated since; nothing is from
   a leaked or unofficial exam source.
6. Wording: neutral on contested topics, no stigma (say "people with diabetes", not "diabetics", in public-facing myths),
   no fear-mongering.
7. On-screen: open 4 frames; every number on screen matches the narration and the source.
8. Description (`upload.json`): sources listed, disclaimer present, no medical claims beyond the video.

9. **"Fact-checked as of" date.** When every claim is confirmed, set `meta.checked_on` to today's date (YYYY-MM-DD) and
   rebuild (`FORCE=1 ./make_episode.sh episodes/<slug>`; the saved voice is reused, so this is free). The date is printed on
   every frame ("FACT-CHECKED AS OF 23 NOV 2026"), in the YouTube/Instagram description and in PACKAGE.md, so it must
   be the date you actually checked, never a guess or a future date.

## Verdict
Write `review.md` as a table (claim · source checked · OK / FIXED / CUT) plus one line: **PASS** or **FAIL**.
Only PASS episodes are pushed. Never create the `APPROVED` file: that is the human owner's sign-off.
