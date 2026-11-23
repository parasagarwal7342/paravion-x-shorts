"""Cinematic 16:9 long-form renderer (the Nvidia long-form look): real CC-licensed photos with slow push-ins,
dark grade, letterbox, big titles, chapter cards, quote cards, timeline, Fake-or-Fact verdicts, a white branded
intro and outro, burned-in captions, generated music and SFX, loudness -14 LUFS.

python3 longform.py <work_dir>
  <work_dir>/script.json   segments (see episodes/*_longform*/script.json)
  <work_dir>/img/<name>.jpg  photos referenced by segments
  <work_dir>/vo/<id>.wav     narration per segment
-> <work_dir>/final_video.mp4, <work_dir>/thumb.png
"""
import json, math, os, re, subprocess, sys, difflib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
W, H, FPS, SR = 1920, 1080, 30, 48000
BAR = 70                                   # letterbox bar height
ACC = (232, 72, 28); INK = (17, 17, 17); WHITE = (255, 255, 255)
GREEN = (27, 138, 74); RED = (224, 30, 30); BGG = (243, 243, 241)
PAD_AFTER = 0.45
_fc = {}
def F(size, w="head"):
    k = (int(size), w)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(str(ROOT / "assets/fonts" / ("sg-700.woff" if w == "head" else "sg-500.woff")), int(size))
    return _fc[k]
def ease(x): x = max(0., min(1., x)); return 1 - (1 - x) ** 3
def clamp(x): return max(0., min(1., x))


# ---------------------------------------------------------------- timing / captions
def norm(w): return re.sub(r"[^a-z0-9]", "", w.lower())

def align(text, wav, model):
    """Script words with (start, end), timed from Whisper word stamps via sequence alignment."""
    a, sr = sf.read(wav, dtype="float32")
    if a.ndim > 1: a = a.mean(1)
    a16 = np.interp(np.linspace(0, len(a) - 1, int(len(a) * 16000 / sr)), np.arange(len(a)), a).astype("float32")
    segs, _ = model.transcribe(a16, word_timestamps=True)
    ww = [(w.word, w.start, w.end) for s in segs for w in s.words]
    sw = text.split()
    sm = difflib.SequenceMatcher(None, [norm(w) for w in sw], [norm(w[0]) for w in ww], autojunk=False)
    t = [None] * len(sw)
    for b in sm.get_matching_blocks():
        for k in range(b.size): t[b.a + k] = (ww[b.b + k][1], ww[b.b + k][2])
    dur = len(a) / sr
    # interpolate gaps
    known = [i for i, x in enumerate(t) if x]
    for i in range(len(sw)):
        if t[i]: continue
        lo = max([k for k in known if k < i], default=None); hi = min([k for k in known if k > i], default=None)
        s0 = t[lo][1] if lo is not None else 0.0; s1 = t[hi][0] if hi is not None else dur
        n0 = lo if lo is not None else -1; n1 = hi if hi is not None else len(sw)
        f0 = (i - n0) / (n1 - n0); f1 = (i + 1 - n0) / (n1 - n0)
        t[i] = (s0 + (s1 - s0) * f0, s0 + (s1 - s0) * f1)
    return [(w, s, e) for w, (s, e) in zip(sw, t)]

def chunks(words, maxc=42):
    out, cur = [], []
    for w in words:
        if cur and (len(" ".join(x[0] for x in cur + [w])) > maxc or cur[-1][0][-1] in ".?!:"):
            out.append(cur); cur = []
        cur.append(w)
    if cur: out.append(cur)
    return out


# ---------------------------------------------------------------- drawing helpers
def text_w(s, f): return f.getlength(s)

def spaced(d, xy, s, f, fill, track=6, anchor="m"):
    tot = sum(f.getlength(c) for c in s) + track * (len(s) - 1)
    x = xy[0] - tot / 2 if anchor == "m" else xy[0]
    for c in s:
        d.text((x, xy[1]), c, font=f, fill=fill, anchor="lm"); x += f.getlength(c) + track
    return tot

def fit_font(s, maxw, size, w="head"):
    while size > 20 and F(size, w).getlength(s) > maxw: size -= 4
    return F(size, w)

def wrap(s, f, maxw):
    lines, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if f.getlength(t) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def grade(img):
    """Cinematic grade: slight desaturation, teal-shadow/warm-highlight, contrast."""
    a = np.asarray(img).astype(np.float32) / 255
    lum = a.mean(2, keepdims=True)
    a = lum + (a - lum) * 0.82
    a = np.clip((a - 0.5) * 1.12 + 0.47, 0, 1)
    sh = (1 - lum) ** 2
    a[..., 0] -= 0.03 * sh[..., 0]; a[..., 2] += 0.035 * sh[..., 0]
    a[..., 0] += 0.03 * lum[..., 0] ** 2
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

_vig = None
def vignette():
    global _vig
    if _vig is None:
        y, x = np.mgrid[0:H, 0:W]
        r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
        _vig = np.clip(1 - 0.55 * np.clip(r - 0.35, 0, None) ** 1.6, 0.25, 1)[..., None].astype(np.float32)
    return _vig

def load_photo(work, name, blur=False):
    im = Image.open(work / "img" / f"{name}.jpg").convert("RGB")
    s = max(W * 1.18 / im.width, H * 1.18 / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    if blur: im = im.filter(ImageFilter.GaussianBlur(28))
    return grade(im)

def kenburns(im, p, seed):
    """Slow push-in with a gentle drift; p in 0..1."""
    rng = np.random.RandomState(seed)
    z0, z1 = 1.0, 1.10 + rng.rand() * 0.05
    if rng.rand() < 0.3: z0, z1 = z1, z0
    dx, dy = rng.uniform(-0.5, 0.5), rng.uniform(-0.35, 0.35)
    z = z0 + (z1 - z0) * (0.5 - 0.5 * math.cos(math.pi * p))
    cw, ch = im.width / (1.18 * z) * 1.0, im.height / (1.18 * z)
    cw, ch = min(cw, im.width), min(ch, im.height)
    # keep 16:9
    if cw / ch > W / H: cw = ch * W / H
    else: ch = cw * H / W
    cx = im.width / 2 + dx * (im.width - cw) * (p - 0.5)
    cy = im.height / 2 + dy * (im.height - ch) * (p - 0.5) - (im.height - ch) * 0.08
    cx = min(max(cx, cw / 2), im.width - cw / 2); cy = min(max(cy, ch / 2), im.height - ch / 2)
    return im.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

def darken(frame, amt):
    a = np.asarray(frame).astype(np.float32) * vignette() * amt
    return a

def finish(a, t, grain=True):
    if grain:
        rng = np.random.default_rng(int(t * 1000) % 100000)
        a = a + rng.normal(0, 5.0, (H // 4, W // 4, 1)).repeat(4, 0).repeat(4, 1)
    a = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(a)

def letterbox(d):
    d.rectangle([0, 0, W, BAR], fill=(0, 0, 0)); d.rectangle([0, H - BAR, W, H], fill=(0, 0, 0))

def bug(d):
    """Small corner brand + live tag."""
    f = F(24)
    d.text((60, BAR + 34), "PARAVION", font=f, fill=WHITE, anchor="lm")
    d.text((60 + f.getlength("PARAVION "), BAR + 34), "X", font=f, fill=ACC, anchor="lm")

def caption(d, words, t):
    cur = None
    for c in chunks(words):
        if c[0][1] - 0.05 <= t <= c[-1][2] + 0.25: cur = c
    if not cur: return
    f = F(34, "body"); s = " ".join(w[0] for w in cur)
    tw = f.getlength(s); x0 = W / 2 - tw / 2; y = H - BAR - 58
    d.rounded_rectangle([x0 - 20, y - 30, x0 + tw + 20, y + 28], radius=6, fill=(255, 255, 255, 235))
    x = x0
    for w, s0, e0 in cur:
        col = ACC if s0 <= t <= e0 + 0.08 else INK
        d.text((x, y), w, font=f, fill=col, anchor="lm"); x += f.getlength(w + " ")


# ---------------------------------------------------------------- segment painters
def big_title(d, seg, lt, cy=H / 2):
    a = ease(lt / 0.6)
    if seg.get("big"):
        f = fit_font(seg["big"], W - 300, 170)
        off = (1 - a) * 40
        d.text((W / 2, cy - 30 + off), seg["big"], font=f, fill=(255, 255, 255, int(235 * a)), anchor="mm")
    if seg.get("sub"):
        a2 = ease((lt - 0.25) / 0.6)
        spaced(d, (W / 2, cy + 85), seg["sub"], F(30, "body"), (255, 255, 255, int(220 * a2)), track=5)
        d.rectangle([W / 2 - 60 * a2, cy + 120, W / 2 + 60 * a2, cy + 124], fill=ACC + (int(255 * a2),))

def lower_third(d, seg, lt):
    a = ease(lt / 0.5); name, role = seg["lower"]
    x = 90 - (1 - a) * 80; y = H - BAR - 230
    fN, fR = F(54), F(28, "body")
    wN = max(fN.getlength(name), fR.getlength(role)) + 70
    d.rectangle([x, y, x + wN, y + 120], fill=(10, 10, 10, int(200 * a)))
    d.rectangle([x, y, x + 8, y + 120], fill=ACC + (int(255 * a),))
    d.text((x + 34, y + 40), name, font=fN, fill=(255, 255, 255, int(255 * a)), anchor="lm")
    d.text((x + 34, y + 90), role, font=fR, fill=(220, 220, 220, int(255 * a)), anchor="lm")

def quote_card(d, seg, lt):
    a = ease(lt / 0.6)
    d.text((W / 2, 300 - (1 - a) * 30), "“", font=F(220), fill=ACC + (int(255 * a),), anchor="mm")
    f = F(76); lines = wrap(seg["quote"], f, W - 420)
    y = H / 2 - (len(lines) - 1) * 48 + 10
    for i, ln in enumerate(lines):
        ai = ease((lt - 0.15 - i * 0.15) / 0.6)
        d.text((W / 2, y + i * 96 + (1 - ai) * 25), ln, font=f, fill=(255, 255, 255, int(255 * ai)), anchor="mm")
    a3 = ease((lt - 0.7) / 0.6)
    fw = fit_font(seg["who"], W - 300, 28, "body")
    spaced(d, (W / 2, y + len(lines) * 96 + 40), seg["who"], fw, ACC + (int(255 * a3),), track=4)

def chapter_card(d, seg, lt):
    a = ease(lt / 0.5)
    spaced(d, (W / 2, H / 2 - 110), "CHAPTER " + seg["n"], F(34, "body"), ACC + (int(255 * a),), track=10)
    f = fit_font(seg["label"], W - 260, 140)
    d.text((W / 2, H / 2 + 10 + (1 - a) * 30), seg["label"], font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm")
    wl = 260 * ease((lt - 0.3) / 0.7)
    d.rectangle([W / 2 - wl, H / 2 + 110, W / 2 + wl, H / 2 + 114], fill=ACC)

def timeline_card(d, seg, lt, tl):
    n = len(tl); x0, x1, y = 220, W - 220, H / 2 + 120
    step = seg["step"]
    prog = step - 1 + ease(lt / 0.9) if step > 0 else ease(lt / 0.9) * 0.0001
    d.line([(x0, y), (x1, y)], fill=(255, 255, 255, 90), width=4)
    xp = x0 + (x1 - x0) * max(0, prog) / (n - 1)
    d.line([(x0, y), (xp, y)], fill=ACC, width=6)
    for i, (date, lab) in enumerate(tl):
        x = x0 + (x1 - x0) * i / (n - 1)
        on = i <= step; now = i == step
        r = 20 if now else 13
        if now:
            pulse = 0.5 + 0.5 * math.sin(lt * 4)
            d.ellipse([x - r - 10 - 6 * pulse, y - r - 10 - 6 * pulse, x + r + 10 + 6 * pulse, y + r + 10 + 6 * pulse], outline=ACC + (150,), width=3)
        d.ellipse([x - r, y - r, x + r, y + r], fill=ACC if on else (90, 90, 90), outline=WHITE if now else None, width=3)
        col = (255, 255, 255, 255 if on else 110)
        d.text((x, y - 60), date, font=F(36 if now else 30), fill=col, anchor="mm")
        d.text((x, y + 58), lab, font=F(26, "body"), fill=col, anchor="mm")
    date, lab = tl[step]; a = ease(lt / 0.6)
    d.text((W / 2, H / 2 - 150 + (1 - a) * 30), date, font=F(150), fill=(255, 255, 255, int(255 * a)), anchor="mm")
    spaced(d, (W / 2, H / 2 - 50), lab.upper(), F(34, "body"), ACC + (int(255 * a),), track=8)

def verdict_card(d, seg, lt):
    a = ease(lt / 0.5)
    spaced(d, (W / 2, 220), "FAKE OR FACT?", F(34, "body"), ACC + (int(255 * a),), track=10)
    f = F(72); lines = wrap(seg["claim"], f, W - 380)
    y = 380
    for i, ln in enumerate(lines):
        d.text((W / 2, y + i * 90), ln, font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm")
    # stamp lands ~ when the verdict word is said (t_verdict set by caller)
    tv = seg.get("_tv", 2.0); s = lt - tv
    if s > 0:
        k = ease(s / 0.25); sc = 1.6 - 0.6 * k
        col = GREEN if seg["verdict"] == "FACT" else RED
        fs = F(int(150 * sc)); txt = seg["verdict"]
        tw = fs.getlength(txt); cy = y + len(lines) * 90 + 120
        d.rounded_rectangle([W / 2 - tw / 2 - 40, cy - 95 * sc, W / 2 + tw / 2 + 40, cy + 95 * sc], radius=18,
                            outline=col + (int(255 * k),), width=int(10 * sc), fill=(0, 0, 0, int(120 * k)))
        d.text((W / 2, cy), txt, font=fs, fill=col + (int(255 * k),), anchor="mm")
        a3 = ease((s - 0.4) / 0.5)
        d.text((W / 2, cy + 150), seg["why"], font=F(32, "body"), fill=(230, 230, 230, int(255 * a3)), anchor="mm")

CHART = [("FRI 20 NOV", "CLOSE", 125.50), ("MON 23 NOV", "PREMARKET", 161.59)]
def chart_card(d, seg, lt):
    a = ease(lt / 0.5)
    spaced(d, (W / 2, 190), "NVDA SHARE PRICE (USD)", F(32, "body"), ACC + (int(255 * a),), track=8)
    base = H - BAR - 190; top = 300; vmax = 175.0
    bw = 300; xs = [W / 2 - 330, W / 2 + 330]
    d.line([(W / 2 - 620, base), (W / 2 + 620, base)], fill=(255, 255, 255, 120), width=3)
    for i, ((day, kind, v), x) in enumerate(zip(CHART, xs)):
        k = ease((lt - 0.3 - i * 1.6) / 1.2)
        if k <= 0: continue
        h = (base - top) * v / vmax * k
        col = (120, 120, 120) if i == 0 else ACC
        d.rectangle([x - bw / 2, base - h, x + bw / 2, base], fill=col + (235,))
        d.text((x, base - h - 50), f"${v * k:.2f}" if k < 1 else f"${v:.2f}", font=F(64), fill=WHITE, anchor="mm")
        d.text((x, base + 40), day, font=F(30), fill=WHITE, anchor="mm")
        d.text((x, base + 78), kind, font=F(22, "body"), fill=(200, 200, 200), anchor="mm")
    k = ease((lt - 3.4) / 0.6)
    if k > 0:
        pct = (CHART[1][2] / CHART[0][2] - 1) * 100
        d.rounded_rectangle([W / 2 - 150, 360, W / 2 + 150, 450], radius=12, fill=GREEN + (int(255 * k),))
        d.text((W / 2, 405), f"+{pct:.0f}%", font=F(60), fill=(255, 255, 255, int(255 * k)), anchor="mm")
    d.text((W - 90, H - BAR - 25), "Source: Benzinga premarket quote; Friday close per JFeed. Reports range +25% to +30%.",
           font=F(20, "body"), fill=(170, 170, 170), anchor="rm")

def logo_img(size):
    im = Image.open(ROOT / "brand/logo_800.png").convert("RGBA")
    return im.resize((size, size), Image.LANCZOS)

def faint_x(im, xy, alpha):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text(xy, "X", font=F(900), fill=ACC + (alpha,), anchor="mm")
    return Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")

def intro_card(work, seg, lt, dur):
    im = Image.new("RGB", (W, H), BGG); d = ImageDraw.Draw(im, "RGBA")
    a = ease(lt / 0.5)
    # big faint X
    im = faint_x(im, (W - 260, H / 2 + 60), 28); d = ImageDraw.Draw(im, "RGBA")
    lg = logo_img(220); im.paste(lg, (int(W / 2 - 110), int(250 - (1 - a) * 30)), lg)
    f = F(84)
    d.text((W / 2, 580), "Welcome to", font=F(44, "body"), fill=INK + (int(255 * a),), anchor="mm")
    tw = f.getlength("PARAVION X"); x = W / 2 - tw / 2
    d.text((x, 670), "PARAVION ", font=f, fill=INK + (int(255 * a),), anchor="lm")
    d.text((x + f.getlength("PARAVION "), 670), "X", font=f, fill=ACC + (int(255 * a),), anchor="lm")
    a2 = ease((lt - 0.5) / 0.6)
    spaced(d, (W / 2, 760), "THE WORLD, EXPLAINED", F(30, "body"), ACC + (int(255 * a2),), track=8)
    a3 = ease((lt - 1.2) / 0.6)
    d.text((W / 2, 850), "Daily world updates · fact-checks · is the news real or fake?", font=F(30, "body"), fill=(90, 90, 90, int(255 * a3)), anchor="mm")
    d.rectangle([0, 0, W * clamp(lt / dur), 10], fill=ACC)
    return im

def outro_card(work, seg, lt, dur, words):
    im = Image.new("RGB", (W, H), WHITE); d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, 0, W, 10], fill=ACC)
    im = faint_x(im, (W - 230, H - 230), 40); d = ImageDraw.Draw(im, "RGBA")
    f = F(30); tw = f.getlength("PARAVION X"); x = W / 2 - tw / 2
    d.text((x, 70), "PARAVION ", font=f, fill=INK, anchor="lm"); d.text((x + f.getlength("PARAVION "), 70), "X", font=f, fill=ACC, anchor="lm")
    spaced(d, (W / 2, 115), "THE WORLD, EXPLAINED", F(20, "body"), ACC, track=5)
    ph = Image.open(work / "img" / "jensen_portrait.jpg").convert("RGB")
    s = 560 / ph.height; ph = ph.resize((int(ph.width * s), 560), Image.LANCZOS)
    if ph.width > 430: l = (ph.width - 430) // 2; ph = ph.crop((l, 0, l + 430, 560))
    px, py = 220, 210
    d.rectangle([px - 12, py - 12, px + ph.width + 12, py + ph.height + 12], fill=WHITE, outline=(220, 220, 220), width=2)
    im.paste(ph, (px, py))
    d.rounded_rectangle([px - 12, py + ph.height + 30, px + ph.width + 12, py + ph.height + 120], radius=8, fill=INK)
    d.text((px + ph.width / 2, py + ph.height + 60), "JENSEN HUANG", font=F(32), fill=WHITE, anchor="mm")
    d.text((px + ph.width / 2, py + ph.height + 96), "Reinstated as Nvidia CEO, 23 Nov", font=F(22, "body"), fill=(210, 210, 210), anchor="mm")
    a = ease(lt / 0.5); f2 = F(76); lines = wrap(seg["q"].replace("?", "") + "?", f2, 900)
    for i, ln in enumerate(lines):
        d.text((1200, 330 + i * 95), ln, font=f2, fill=INK + (int(255 * a),), anchor="mm")
    d.text((1200, 330 + len(lines) * 95 + 10), "Yes or no.", font=F(66), fill=ACC + (int(255 * a),), anchor="mm")
    by = 330 + len(lines) * 95 + 130
    for i, (lab, col) in enumerate([("YES", GREEN), ("NO", RED)]):
        k = ease((lt - 0.8 - i * 0.3) / 0.4)
        x = 1040 + i * 330
        d.rounded_rectangle([x - 130, by - 50, x + 130, by + 50], radius=12, fill=col + (int(255 * k),))
        d.text((x, by), lab, font=F(48), fill=(255, 255, 255, int(255 * k)), anchor="mm")
    # subscribe button appears on "subscribe"
    ts = next((w[1] for w in words if norm(w[0]).startswith("subscribe")), dur - 2.5)
    k = ease((lt - ts) / 0.35)
    if k > 0:
        sy = by + 150
        d.rounded_rectangle([1200 - 210, sy - 45, 1200 + 210, sy + 45], radius=45, fill=(204, 0, 0, int(255 * k)))
        d.text((1200, sy), "SUBSCRIBE", font=F(40), fill=(255, 255, 255, int(255 * k)), anchor="mm")
    d.rectangle([0, H - 10, W * clamp(lt / dur), H], fill=ACC)
    return im


def render_segment(args):
    work, i, seg, start, dur, words, tl, out = args
    work = Path(work)
    if os.path.exists(out):   # resume: keep parts that are complete
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True)
        try:
            if abs(float(r.stdout) - round(dur * FPS) / FPS) < 0.05: return out
        except ValueError: pass
    kind = seg["kind"]
    bg = None
    if kind in ("photo", "quote", "chapter", "timeline", "verdict", "chart"):
        name = seg.get("img") or {"verdict": "die", "chart": "racks"}[kind]
        bg = load_photo(work, name, blur=kind in ("quote", "chapter", "verdict", "chart"))
    dim = {"photo": 0.78, "quote": 0.45, "chapter": 0.40, "timeline": 0.42, "verdict": 0.32, "chart": 0.28}.get(kind, 1)
    if kind == "photo" and seg.get("big"): dim = 0.6
    if kind == "verdict":
        vw = next((w for w in words if norm(w[0]) in ("fact", "fake") and w[1] > 1.0), None)
        seg["_tv"] = vw[1] if vw else 2.0
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n = int(round(dur * FPS))
    for fi in range(n):
        lt = fi / FPS; t = start + lt
        if kind == "intro": im = intro_card(work, seg, lt, dur)
        elif kind == "outro": im = outro_card(work, seg, lt, dur, words)
        else:
            fr = kenburns(bg, fi / max(1, n - 1), i * 7 + 3)
            im = finish(darken(fr, dim), t)
            d = ImageDraw.Draw(im, "RGBA")
            if kind == "photo":
                big_title(d, seg, lt)
                if seg.get("lower"): lower_third(d, seg, lt)
            elif kind == "quote": quote_card(d, seg, lt)
            elif kind == "chapter": chapter_card(d, seg, lt)
            elif kind == "timeline": timeline_card(d, seg, lt, tl)
            elif kind == "verdict": verdict_card(d, seg, lt)
            elif kind == "chart": chart_card(d, seg, lt)
            letterbox(d); bug(d)
            # orange progress line along the bottom bar
            d.rectangle([0, H - 6, W * t / TOTAL, H], fill=ACC)
            # fade in from black on chapter cards
            if kind == "chapter" and lt < 0.25:
                im = Image.blend(Image.new("RGB", (W, H)), im, lt / 0.25); d = ImageDraw.Draw(im, "RGBA")
        d = ImageDraw.Draw(im, "RGBA")
        if kind not in ("intro", "outro", "chapter"): caption(d, words, lt)
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
    return out


# ---------------------------------------------------------------- audio
def music_and_sfx(total, marks):
    """Generated score: dark pad + pulse, risers into chapter cards, impacts on hits."""
    n = int(total * SR); t = np.arange(n) / SR
    mus = np.zeros(n, np.float32)
    chords = [[55.0, 82.41, 130.81], [49.0, 73.42, 116.54], [43.65, 65.41, 103.83], [51.91, 77.78, 123.47]]
    bar = 60 / 92 * 4
    for ci in range(int(total / bar) + 1):
        s0 = int(ci * bar * SR); s1 = min(n, int((ci + 1) * bar * SR) + SR // 2)
        if s0 >= n: break
        tt = t[s0:s1] - t[s0]; env = np.minimum(1, tt / 0.8) * np.exp(-np.maximum(0, tt - bar) * 3)
        for fq in chords[ci % 4]:
            mus[s0:s1] += (0.05 * np.sin(2 * np.pi * fq * tt) + 0.02 * np.sin(2 * np.pi * fq * 2.003 * tt)) * env
    # pulse (soft kick on beats)
    beat = 60 / 92
    for b in range(int(total / beat)):
        s0 = int(b * beat * SR); L = int(0.25 * SR)
        if s0 + L >= n: break
        tt = np.arange(L) / SR
        mus[s0:s0 + L] += 0.10 * np.sin(2 * np.pi * (48 + 60 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 14)
    # ticking hi-hat 8ths for tension
    rng = np.random.default_rng(1)
    for b in range(int(total / (beat / 2))):
        s0 = int(b * beat / 2 * SR); L = int(0.04 * SR)
        if s0 + L >= n: break
        mus[s0:s0 + L] += rng.normal(0, 0.012, L) * np.exp(-np.arange(L) / SR * 90)
    sfx = np.zeros(n, np.float32)
    for kind, at in marks:
        s0 = int(at * SR)
        if kind == "riser":
            L = int(1.2 * SR); s0 -= L
            if s0 < 0: continue
            tt = np.arange(L) / SR
            nz = rng.normal(0, 1, L).astype(np.float32)
            nz = np.convolve(nz, np.ones(6) / 6, "same")
            sfx[s0:s0 + L] += 0.07 * nz * (tt / 1.2) ** 2
        elif kind == "boom":
            L = int(1.6 * SR)
            if s0 + L > n: L = n - s0
            tt = np.arange(L) / SR
            sfx[s0:s0 + L] += 0.32 * np.sin(2 * np.pi * (38 + 70 * np.exp(-tt * 18)) * tt) * np.exp(-tt * 3.2)
            sfx[s0:s0 + L] += 0.05 * rng.normal(0, 1, L) * np.exp(-tt * 25)
        elif kind == "whoosh":
            L = int(0.5 * SR)
            if s0 + L > n: continue
            tt = np.arange(L) / SR
            nz = np.convolve(rng.normal(0, 1, L), np.ones(12) / 12, "same")
            sfx[s0:s0 + L] += 0.12 * nz * np.sin(np.pi * tt / 0.5) ** 2
        elif kind == "stamp":
            L = int(0.5 * SR)
            if s0 + L > n: continue
            tt = np.arange(L) / SR
            sfx[s0:s0 + L] += 0.25 * np.sin(2 * np.pi * (70 + 90 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 9) + 0.06 * rng.normal(0, 1, L) * np.exp(-tt * 40)
    return mus, sfx


TOTAL = 0.0
def main(work):
    global TOTAL
    work = Path(work); S = json.loads((work / "script.json").read_text()); segs = S["segments"]
    from faster_whisper import WhisperModel
    model = WhisperModel("small.en", compute_type="int8")
    cache = work / "words.json"
    words_all = json.loads(cache.read_text()) if cache.exists() else {}
    voice, starts, durs = [], [], []
    t = 0.0
    for s in segs:
        wav = work / "vo" / f"{s['id']}.wav"
        key = s["text"] + "|" + str(os.path.getmtime(wav))
        if words_all.get(s["id"], {}).get("key") != key:
            words_all[s["id"]] = {"key": key, "w": align(s["text"], wav, model)}
        a, sr = sf.read(wav, dtype="float32")
        if a.ndim > 1: a = a.mean(1)
        a = np.interp(np.linspace(0, len(a) - 1, int(len(a) * SR / sr)), np.arange(len(a)), a).astype(np.float32)
        lead = {"chapter": 0.6, "intro": 0.5, "outro": 0.3}.get(s["kind"], 0.0)
        tail = {"chapter": 0.5, "intro": 0.6, "outro": 2.5, "verdict": 0.9, "chart": 0.6}.get(s["kind"], PAD_AFTER)
        dur = lead + len(a) / SR + tail
        starts.append(t); durs.append(dur)
        voice.append((t + lead, a))
        words_all[s["id"]]["lead"] = lead
        t += dur
    cache.write_text(json.dumps(words_all))
    TOTAL = t
    print(f"total {t:.1f}s")
    # ----- video, parallel by segment
    (work / "parts").mkdir(exist_ok=True)
    jobs = []
    for i, s in enumerate(segs):
        lead = words_all[s["id"]]["lead"]
        words = [(w, a + lead, b + lead) for w, a, b in words_all[s["id"]]["w"]]
        jobs.append((str(work), i, s, starts[i], durs[i], words, S.get("timeline", []), str(work / "parts" / f"{i:02d}.mp4")))
    with ProcessPoolExecutor(max(1, os.cpu_count() or 2), initializer=_set_total, initargs=(TOTAL,)) as ex:
        for o in ex.map(render_segment, jobs): print("rendered", o, flush=True)
    (work / "parts.txt").write_text("".join(f"file 'parts/{i:02d}.mp4'\n" for i in range(len(segs))))
    # ----- audio
    n = int(TOTAL * SR); vo = np.zeros(n, np.float32)
    for st, a in voice:
        s0 = int(st * SR); vo[s0:s0 + len(a)] += a[: n - s0]
    marks = []
    for i, s in enumerate(segs):
        if s["kind"] == "chapter": marks += [("riser", starts[i]), ("boom", starts[i] + 0.05)]
        elif s["kind"] == "photo" and s.get("big") and s["id"].startswith(("hook", "end")): marks += [("boom", starts[i] + 0.05)]
        elif s["kind"] in ("photo", "quote", "timeline", "chart"): marks += [("whoosh", max(0, starts[i] - 0.15))]
        if s["kind"] == "verdict":
            vw = next((w for w in words_all[s["id"]]["w"] if norm(w[0]) in ("fact", "fake") and w[1] > 1.0), None)
            if vw: marks.append(("stamp", starts[i] + vw[1]))
    mus, sfx = music_and_sfx(TOTAL, marks)
    # duck music under voice
    env = np.abs(vo); k = int(0.25 * SR)
    env = np.convolve(env, np.ones(k) / k, "same"); duck = 1 - 0.55 * np.clip(env / 0.03, 0, 1)
    fade = np.ones(n, np.float32); fl = int(2.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
    mix = vo * 1.0 + mus * duck * 0.9 * fade + sfx
    mix = np.stack([mix, mix], 1)
    sf.write(work / "mix.wav", mix, SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "parts.txt"), "-i", str(work / "mix.wav"),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", str(work / "final_video.mp4")], check=True)
    print("done", work / "final_video.mp4")

def _set_total(t):
    global TOTAL
    TOTAL = t

if __name__ == "__main__":
    main(sys.argv[1])
