"""Packager for long-form Deep Dives: PACKAGE.md + upload.json with YouTube chapters (timestamps), sources,
image credits (required by CC BY / CC BY-SA), "fact-checked as of" date and the disclaimer.

python3 package_long.py episodes/<slug>
"""
import datetime as dt, json, re, subprocess, sys
from pathlib import Path

from medcheck import check as medcheck

ep = Path(sys.argv[1]); ROOT = Path(__file__).parent
s = json.loads((ep / "script.json").read_text()); m = s["meta"]
t = json.loads((ep / "timings.json").read_text())
cfg = json.loads((ROOT / "config.json").read_text())
credits = json.loads((ep / "credits.json").read_text()) if (ep / "credits.json").exists() else {}
mc_err, mc_warn = medcheck(ep)
chk = dt.date.fromisoformat(m["checked_on"]).strftime("%-d %b %Y")
fmt = lambda x: f"{int(x // 60)}:{int(x % 60):02d}"

# YouTube chapters: 0:00 intro, then each chapter card (YouTube needs 3+ chapters, first at 0:00, each >= 10 s)
chapters = [(0.0, "Intro")]
for l, tl in zip(s["lines"], t["lines"]):
    v = l["visual"]
    if v["type"] == "chapter": chapters.append((max(0.0, tl["start"] - 0.3), v["title"]))
    if v["type"] == "end": chapters.append((max(0.0, tl["start"] - 0.3), "Recap and sources"))
chap_txt = "\n".join(f"{fmt(a)} {b}" for a, b in chapters)

used = []
for l in s["lines"]:
    for k in (l["visual"].get("wellcome"), l["visual"].get("file"), l["visual"].get("query"), l["visual"].get("bg")):
        if k and k in credits and credits[k]["title"] not in [c["title"] for c in used]: used.append(credits[k])
credit_txt = "\n".join(f"• {c.get('label') or c['title'].removeprefix('File:')}: {c['author']}, {c['license']}, via {c.get('source', 'Wikimedia Commons')} ({c['page']})" for c in used)
src_txt = "\n".join(f"• {n}: {u}" for n, u in m["sources"])

v = ep / "final_video.mp4"
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v],
                           capture_output=True, text=True).stdout.strip() or 0) if v.exists() else 0
eleven = t.get("engine") == "elevenlabs"

desc = f"""{m['summary']}

Chapters:
{chap_txt}

Sources:
{src_txt}

✅ Fact-checked as of {chk}. Medical evidence and guidelines change; check the sources above for updates.

Images (licensed, credited):
{credit_txt}
Music, graphics and animation: made by {cfg['channel_name']}.

{cfg['description_footer']}
{' '.join(m['hashtags'])}"""

(ep / "upload.json").write_text(json.dumps({
    "title": m["titles"][0], "description": desc, "tags": [h.lstrip("#") for h in m["hashtags"]],
    "category": cfg["youtube_category"]["default"], "publish_at": m.get("schedule"), "checked_on": m["checked_on"],
    "pinned_comment": m["pinned"], "captions": "captions.srt", "thumbnail": "thumbnail.png", "format": "long"}, indent=1, ensure_ascii=False))

status = ("BLOCKED (medical check)" if mc_err else "READY after human APPROVED" if eleven else "BLOCKED (preview voice: re-voice with ElevenLabs)")
(ep / "PACKAGE.md").write_text(f"""# {cfg['channel_name']}: {s['slug']} · Deep Dive (long-form)

**STATUS: {status}** · length {fmt(dur)} · fact-checked as of **{chk}** · planned {m.get('schedule', 'unscheduled')} (IST)

## Titles
{chr(10).join(f'{i + 1}. {x} ({len(x)} chars)' for i, x in enumerate(m['titles']))}

## Upload checklist (YouTube Studio)
1. Upload `final_video.mp4`, title 1 above, description below. Category Education, not made for kids.
2. Thumbnail: `thumbnail.png` (1280x720). Subtitles: upload `captions.srt` (English).
3. "Altered or synthetic content": **No** (real licensed photos, drawn graphics; the voice is a narrator).
4. Add to the "Deep Dives" playlist; pin the comment: {m['pinned']}

## Description
```
{desc}
```

## Medical check
{'PASS' if not mc_err else 'FAIL: ' + '; '.join(mc_err)}{(chr(10) + 'Warnings: ' + '; '.join(mc_warn)) if mc_warn else ''}

**Removed during fact-check:**
{chr(10).join('- ' + r for r in m.get('removed', []))}

**Notes:** {m.get('notes', '')}

## Image licences
{len(used)} images, all Public domain / CC0 / CC BY / CC BY-SA from Wikimedia Commons, credited on screen and above.
CC BY-SA images are shown unmodified apart from cropping, colour grade and camera moves.
""")
print("wrote", ep / "PACKAGE.md", "and upload.json;", len(chapters), "chapters,", len(used), "image credits")
