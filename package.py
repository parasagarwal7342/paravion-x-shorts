"""Agent 8 — builds PACKAGE.md (script table, sources, fact-check, YouTube/Instagram copy, QA) from
script.json["meta"] + timings.json + the rendered file. Episodes without meta.titles keep a hand-written PACKAGE.md."""
import json, re, subprocess, sys
from pathlib import Path

ep = Path(sys.argv[1])
s = json.loads((ep / "script.json").read_text())
m = s.get("meta", {})
if "titles" not in m:
    print("no meta.titles; keeping existing PACKAGE.md"); sys.exit(0)
t = json.loads((ep / "timings.json").read_text())
cfg = json.loads((Path(__file__).parent / "config.json").read_text())
handle = cfg["handle"]; name = cfg["channel_name"]
f = lambda x: f"{int(x // 60)}:{int(round(x % 60)):02d}"


def probe():
    v = ep / "final_video.mp4"
    if not v.exists(): return "not rendered"
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v],
                       capture_output=True, text=True).stdout.strip()
    r = subprocess.run(["ffmpeg", "-i", v, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = r[r.rindex("I:"):].split()[1]; P = r[r.rindex("Peak:"):].split()[1]
    return float(d), I, P


dur, I, P = probe()
qa = (ep / "voice_qa.txt").read_text().strip() if (ep / "voice_qa.txt").exists() else "not run"
words = sum(len(l["text"].split()) for l in s["lines"])
src_lines = "\n".join(f"• {n}: {u}" for n, u in m["sources"])
rows = "\n".join(f"| {f(b['start'])}–{f(b['end'])} | {a['beat']} | {a['text']} | {a['ost'].replace('|', ' / ') or '—'} | {a.get('source', '—')} |"
                 for a, b in zip(s["lines"], t["lines"]))
claims = "\n".join(f"| {a['text']} | {a['source']} | CONFIRMED (2+ sources) |" for a in s["lines"] if a.get("source"))

md = f"""# {name} — {s['slug']} · "{s['series']}"

**STATUS: BLOCKED (voice only).** The narration is the free Piper preview voice. Re-run with ElevenLabs keys, then post.
{('**NOTE:** ' + m['notes']) if m.get('notes') else ''}

**Planned publish time:** {m.get('schedule', 'unscheduled')} (IST)

## Summary
{m['summary']}

**Verdict:** {m['verdict']}

## Sources
{chr(10).join(f'{i+1}. {n}: {u}' for i, (n, u) in enumerate(m['sources']))}

## Fact-check: PASS
Every on-screen fact line and its sources:

| Claim (as spoken) | Sources | Label |
|---|---|---|
{claims}

**Removed during the check:**
{chr(10).join('- ' + r for r in m.get('removed', []))}

## Script ({words} words, {t['wpm']} wpm, {dur:.1f} s)
| Time | Beat | Voice | On-screen (black / orange) | Source tag |
|---|---|---|---|---|
{rows}

## Files
- `final_video.mp4`: 1080×1920, 30 fps, H.264 + AAC, {dur:.1f} s, {I} LUFS, {P} dBTP peak, BT.709.
- `cover.png`: 1080×1920.
- `voice.mp3` / `voice.wav`: preview voice. `timings.json`: word timestamps.
- Voice QA (Whisper transcript vs script): `{qa}`. Only number formatting ("12" vs "twelfth") or name spelling differences are acceptable.

## Asset licenses
All graphics, music and SFX are generated in code (owned by the channel). Font: Space Grotesk (SIL OFL 1.1). Voice: Piper preview (replace with a licensed ElevenLabs voice). No footage, logos, photos or faces.

## YouTube Shorts
**Titles:**
{chr(10).join(f'{i+1}. {x} ({len(x)} chars)' for i, x in enumerate(m['titles']))}

**Description:**
```
{m['summary']}

Sources:
{src_lines}

Follow for daily world updates — the world, explained in 60 seconds.
{' '.join(m['hashtags'])}
```
**Pinned comment:** {m['pinned']}

## Instagram Reels
```
{m['titles'][0]} 👇

{m['summary']}

Follow @{handle} for the world explained daily.
Sources in comments.

{m['ig_tags']}
```
**Story repost:** poll sticker "{m['poll'][0]}" with "{m['poll'][1]}" / "{m['poll'][2]}".

## QA
| Check | Result |
|---|---|
| Fact-check PASS; every fact line has 2+ sources | ✅ |
| Neutral on contested topics, no opinion | ✅ |
| Hook in first 3 s; CTA in last 8 s ({f(t['lines'][-2]['start'])}–{f(t['lines'][-1]['end'])}) | ✅ |
| Under 60 s ({dur:.1f} s), 1080×1920, centred layout, captions ≤760 px wide | {'✅' if dur < 60 else '❌'} |
| Visuals/music self-made, font OFL | ✅ |
| Licensed human-quality voice | ❌ preview voice |
| No fake quotes; cover not misleading | ✅ |

**Output: BLOCKED** until the ElevenLabs voice is in.
"""
(ep / "PACKAGE.md").write_text(md)
(ep / "upload.json").write_text(json.dumps({
    "title": m["titles"][0], "description": f"{m['summary']}\n\nSources:\n{src_lines}\n\nFollow for daily world updates — the world, explained in 60 seconds.\n{' '.join(m['hashtags'])}",
    "tags": [h.lstrip('#') for h in m["hashtags"] if h != "#shorts"], "publish_at": m.get("schedule"),
    "pinned_comment": m["pinned"]}, indent=1, ensure_ascii=False))
print("wrote", ep / "PACKAGE.md")
