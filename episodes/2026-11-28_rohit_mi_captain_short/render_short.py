"""PARAVION X vertical Short (cinematic real-photo look of longform_vertical) for the Rohit Sharma MI captaincy Real-or-Fake Short.
Hook first (full text at frame 1) -> welcome card -> claim -> 3 checks + FAKE verdict -> twist -> end card
(spoken + on-screen yes/no, comment below, stay tuned, subscribe/follow). Uses longform.py from origin/main.
python3 render_short.py <episode_dir>"""
import json, os, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw
sys.path.insert(0, "/workspace/paravion/px_origin_ref")   # git archive of origin/main: longform.py, fonts, brand
import longform as L
L.W, L.H = 1080, 1920
L.BAR = 0; L.PAD_AFTER = 0.12; L.TXT = 1.4; L.TITLE_Y = 760; L.CAP_Y = 1300
W, H = 1080, 1920
LEAD = {"intro": 0.10, "outro": 0.15}
TAIL = {"intro": 0.15, "outro": 1.2, "verdict": 0.45}

def _tracked_w(s, f, track): return sum(f.getlength(c) for c in s) + track * (len(s) - 1)
def big_title(d, seg, lt, cy=None):
    if seg["id"] == "hook": lt = lt + 1.0          # full hook text, fully opaque, at t=0.0
    cy = L.TITLE_Y; a = L.ease(lt / 0.5)
    if seg.get("big"):
        f = L.fit_font(seg["big"], W - 140, 150); off = (1 - a) * 40
        d.text((W / 2 + 4, cy - 26 + off), seg["big"], font=f, fill=(0, 0, 0, int(120 * a)), anchor="mm")
        d.text((W / 2, cy - 30 + off), seg["big"], font=f, fill=(255, 255, 255, int(245 * a)), anchor="mm")
    if seg.get("sub"):
        a2 = L.ease((lt - 0.2) / 0.5); f = L.F(36, "body"); tr = 4
        parts = [p.strip() for p in seg["sub"].split("·")]; lines = []; cur = ""
        for p in parts:
            t = (cur + "  ·  " + p) if cur else p
            if _tracked_w(t, f, tr) <= W - 160 or not cur: cur = t
            else: lines.append(cur); cur = p
        lines.append(cur)
        for j, ln in enumerate(lines[:2]):
            ff = f
            while _tracked_w(ln, ff, tr) > W - 140 and ff.size > 24: ff = L.F(ff.size - 2, "body")
            L.spaced(d, (W / 2, cy + 85 + j * 52), ln, ff, (255, 255, 255, int(235 * a2)), track=tr)
        yl = cy + 85 + len(lines[:2]) * 52 - 8
        d.rectangle([W / 2 - 60 * a2, yl, W / 2 + 60 * a2, yl + 4], fill=L.ACC + (int(255 * a2),))
L.big_title = big_title

def gbar(d, seg, lt):
    """global progress bar across the whole Short (bottom)."""
    T = L.TOTAL or 1
    d.rectangle([0, H - 8, W * min(1, (seg.get("_start", 0) + lt) / T), H], fill=L.ACC)

CTA = (0.42, 0.52)
_fin = L.finish
def finish(a, t, grain=True):
    im = _fin(a, t, grain); T = L.TOTAL or 1
    s, e = CTA[0] * T, CTA[1] * T
    if s <= t <= e:
        k = L.ease((t - s) / 0.25) * L.ease((e - t) / 0.25)
        d = ImageDraw.Draw(im, "RGBA"); y = 300; txt = "FOLLOW  ·  DAILY FAKE OR FACT"
        f = L.fit_font(txt, 820, 40, "head"); tw = f.getlength(txt); dy = (1 - k) * -40
        d.rounded_rectangle([W / 2 - tw / 2 - 34, y - 44 + dy, W / 2 + tw / 2 + 34, y + 44 + dy], radius=44, fill=L.ACC + (int(245 * k),))
        d.text((W / 2, y + dy), txt, font=f, fill=(255, 255, 255, int(255 * k)), anchor="mm")
    return im
L.finish = finish

def verdict_card(d, seg, lt):
    a = L.ease(lt / 0.4); off = 330
    L.spaced(d, (W / 2, 220 + off), "FAKE OR FACT?", L.F(40, "body"), L.ACC + (int(255 * a),), track=10)
    f = L.F(76); lines = L.wrap(seg["claim"], f, W - 160); y = 380 + off
    for i, ln in enumerate(lines):
        d.text((W / 2, y + i * 92), ln, font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm")
    s = lt - seg.get("_tvx", 1.0)
    if s > 0:
        k = L.ease(s / 0.25); sc = 1.6 - 0.6 * k; col = L.GREEN if seg["verdict"] in ("REAL", "FACT") else L.RED
        fs = L.F(int(170 * sc)); txt = seg["verdict"]; tw = fs.getlength(txt); cy = y + len(lines) * 92 + 150
        d.rounded_rectangle([W / 2 - tw / 2 - 40, cy - 105 * sc, W / 2 + tw / 2 + 40, cy + 105 * sc], radius=18,
                            outline=col + (int(255 * k),), width=int(10 * sc), fill=(0, 0, 0, int(120 * k)))
        d.text((W / 2, cy), txt, font=fs, fill=col + (int(255 * k),), anchor="mm")
        a3 = L.ease((s - 0.3) / 0.4)
        L.spaced(d, (W / 2, cy + 175), seg["why"], L.fit_font(seg["why"], W - 120, 32, "body"), (235, 235, 235, int(255 * a3)), track=3)
L.verdict_card = verdict_card

def intro_card(work, seg, lt, dur):
    im = Image.new("RGB", (W, H), L.BGG)
    im = L.faint_x(im, (W - 120, H - 420), 30); d = ImageDraw.Draw(im, "RGBA")
    a = L.ease(lt / 0.3)
    lg = L.logo_img(300); im.paste(lg, (int(W / 2 - 150), int(470 - (1 - a) * 40)), lg); d = ImageDraw.Draw(im, "RGBA")
    d.text((W / 2, 880), "Welcome to", font=L.F(56, "body"), fill=L.INK + (int(255 * a),), anchor="mm")
    f = L.F(124); tw = f.getlength("PARAVION X"); x = W / 2 - tw / 2
    d.text((x, 1010), "PARAVION ", font=f, fill=L.INK + (int(255 * a),), anchor="lm")
    d.text((x + f.getlength("PARAVION "), 1010), "X", font=f, fill=L.ACC + (int(255 * a),), anchor="lm")
    a2 = L.ease((lt - 0.8) / 0.4)
    L.spaced(d, (W / 2, 1130), "DAILY WORLD NEWS", L.F(40, "body"), L.ACC + (int(255 * a2),), track=8)
    a3 = L.ease((lt - 2.2) / 0.4)
    d.rounded_rectangle([W / 2 - 330, 1200, W / 2 + 330, 1290], radius=45, fill=L.INK + (int(255 * a3),))
    d.text((W / 2, 1245), "REAL OR FAKE?", font=L.F(50), fill=(255, 255, 255, int(255 * a3)), anchor="mm")
    gbar(d, seg, lt)
    return im
L.intro_card = intro_card

def outro_card(work, seg, lt, dur, words):
    im = Image.new("RGB", (W, H), L.WHITE)
    im = L.faint_x(im, (W - 140, H - 300), 34); d = ImageDraw.Draw(im, "RGBA")
    f = L.F(40); tw = f.getlength("PARAVION X"); x = W / 2 - tw / 2
    d.text((x, 150), "PARAVION ", font=f, fill=L.INK, anchor="lm"); d.text((x + f.getlength("PARAVION "), 150), "X", font=f, fill=L.ACC, anchor="lm")
    L.spaced(d, (W / 2, 200), "THE WORLD, EXPLAINED", L.F(24, "body"), L.ACC, track=6)
    ph = Image.open(work / "img" / (seg["photo"] + ".jpg")).convert("RGB"); ph = L.grade(ph)
    pw, phh = 760, 420; s = max(pw / ph.width, phh / ph.height)
    ph = ph.resize((int(ph.width * s), int(ph.height * s)), Image.LANCZOS)
    l, t0 = (ph.width - pw) // 2, (ph.height - phh) // 2; ph = ph.crop((l, t0, l + pw, t0 + phh))
    px, py = (W - pw) // 2, 260
    d.rectangle([px - 10, py - 10, px + pw + 10, py + phh + 10], fill=L.WHITE, outline=(220, 220, 220), width=2); im.paste(ph, (px, py))
    d = ImageDraw.Draw(im, "RGBA")
    a = 1.0   # question fully visible from the first frame of the card
    f2 = L.F(80); lines = L.wrap(seg["q"].rstrip("?") + "?", f2, 900); y0 = 800
    for i, ln in enumerate(lines): d.text((W / 2, y0 + i * 96), ln, font=f2, fill=L.INK + (int(255 * a),), anchor="mm")
    yy = y0 + len(lines) * 96 + 10
    d.text((W / 2, yy), "Yes or no?", font=L.F(72), fill=L.ACC, anchor="mm")
    by = yy + 130
    for i, (lab, col) in enumerate([("YES", L.GREEN), ("NO", L.RED)]):
        k = L.ease((lt - 0.4 - i * 0.2) / 0.3); xx = W / 2 - 170 + i * 340
        d.rounded_rectangle([xx - 140, by - 55, xx + 140, by + 55], radius=14, fill=col + (int(255 * k),))
        d.text((xx, by), lab, font=L.F(54), fill=(255, 255, 255, int(255 * k)), anchor="mm")
    def at(prefix, dflt):
        return next((w[1] for w in words if L.norm(w[0]).startswith(prefix)), dflt)
    tc, ts, tsub = at("comment", 1.5), at("stay", 3.0), at("subscribe", dur - 2.5)
    k = L.ease((lt - tc + 0.05) / 0.3)
    d.text((W / 2, by + 115), "COMMENT BELOW", font=L.F(46), fill=L.INK + (int(255 * k),), anchor="mm")
    k = L.ease((lt - ts + 0.05) / 0.3)
    d.text((W / 2, by + 190), "Stay tuned for further updates.", font=L.F(40, "body"), fill=(70, 70, 70, int(255 * k)), anchor="mm")
    k = L.ease((lt - tsub + 0.05) / 0.3)
    if k > 0:
        sy = by + 300
        d.rounded_rectangle([W / 2 - 400, sy - 50, W / 2 - 10, sy + 50], radius=50, fill=(204, 0, 0, int(255 * k)))
        d.text((W / 2 - 205, sy), "SUBSCRIBE", font=L.F(44), fill=(255, 255, 255, int(255 * k)), anchor="mm")
        d.rounded_rectangle([W / 2 + 10, sy - 50, W / 2 + 400, sy + 50], radius=50, fill=L.INK + (int(255 * k),))
        d.text((W / 2 + 205, sy), "FOLLOW", font=L.F(44), fill=(255, 255, 255, int(255 * k)), anchor="mm")
        d.text((W / 2, sy + 95), "PARAVION X for more", font=L.F(40), fill=L.ACC + (int(255 * k),), anchor="mm")
    gbar(d, seg, lt)
    return im
L.outro_card = outro_card

def main(work):
    work = Path(work); S = json.loads((work / "script.json").read_text()); segs = S["segments"]
    from faster_whisper import WhisperModel
    model = WhisperModel("small.en", compute_type="int8")
    cache = work / "words.json"; words_all = json.loads(cache.read_text()) if cache.exists() else {}
    voice, starts, durs = [], [], []; t = 0.0; SR = L.SR
    for s in segs:
        wav = work / "vo" / f"{s['id']}.wav"; key = s["text"] + "|" + str(os.path.getmtime(wav))
        if words_all.get(s["id"], {}).get("key") != key:
            words_all[s["id"]] = {"key": key, "w": L.align(s["text"], wav, model)}
        a, sr = sf.read(wav, dtype="float32")
        if a.ndim > 1: a = a.mean(1)
        a = np.interp(np.linspace(0, len(a) - 1, int(len(a) * SR / sr)), np.arange(len(a)), a).astype(np.float32)
        lead = LEAD.get(s["kind"], 0.0); tail = TAIL.get(s["kind"], L.PAD_AFTER)
        dur = lead + len(a) / SR + tail
        starts.append(t); durs.append(dur); voice.append((t + lead, a)); words_all[s["id"]]["lead"] = lead
        s["_start"] = t
        if s["kind"] == "verdict":
            vw = next((w for w in words_all[s["id"]]["w"] if L.norm(w[0]) == L.norm(s["verdict"])), None)
            s["_tvx"] = lead + (vw[1] if vw else 1.0)
        t += dur
    cache.write_text(json.dumps(words_all)); L.TOTAL = t; print(f"total {t:.2f}s", flush=True)
    (work / "parts").mkdir(exist_ok=True); jobs = []
    for i, s in enumerate(segs):
        lead = words_all[s["id"]]["lead"]
        words = [(w, a + lead, b + lead) for w, a, b in words_all[s["id"]]["w"]]
        jobs.append((str(work), i, s, starts[i], durs[i], words, [], str(work / "parts" / f"{i:02d}.mp4")))
    with ProcessPoolExecutor(os.cpu_count() or 2, initializer=L._set_total, initargs=(t,)) as ex:
        for o in ex.map(L.render_segment, jobs): print("rendered", o, flush=True)
    (work / "parts.txt").write_text("".join(f"file 'parts/{i:02d}.mp4'\n" for i in range(len(segs))))
    n = int(t * SR); vo = np.zeros(n, np.float32)
    for st, a in voice: s0 = int(st * SR); vo[s0:s0 + len(a)] += a[: n - s0]
    marks = [("boom", 0.02)]
    for i, s in enumerate(segs):
        if s["kind"] in ("photo", "verdict") and i > 0: marks.append(("whoosh", max(0, starts[i] - 0.12)))
        if s["kind"] in ("intro", "outro"): marks.append(("boom", starts[i] + 0.03))
        if s["kind"] == "verdict":
            vw = next((w for w in words_all[s["id"]]["w"] if L.norm(w[0]) == L.norm(s["verdict"])), None)
            if vw: marks.append(("stamp", starts[i] + words_all[s["id"]]["lead"] + vw[1]))
    mus, sfx = L.music_and_sfx(t, marks)
    env = np.abs(vo); k = int(0.25 * SR); env = np.convolve(env, np.ones(k) / k, "same"); duck = 1 - 0.6 * np.clip(env / 0.03, 0, 1)
    fade = np.ones(n, np.float32); fl = int(1.2 * SR); fade[-fl:] = np.linspace(1, 0, fl)
    mix = vo * 1.0 + mus * duck * 0.55 * fade + sfx * 0.9
    sf.write(work / "mix.wav", np.stack([mix, mix], 1), SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "parts.txt"), "-i", str(work / "mix.wav"),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "10M", "-bufsize", "20M",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest",
                    str(work / "final_video.mp4")], check=True)
    print("done", work / "final_video.mp4")

if __name__ == "__main__":
    main(sys.argv[1])
