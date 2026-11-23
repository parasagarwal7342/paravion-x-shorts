"""Long-form cinematic renderer for PARAVION MED "Deep Dive" videos (16:9, 1920x1080, 30 fps).

    python3 longform.py episodes/<slug> [--thumb] [--preview START END]

Script: episodes/<slug>/script.json with "format": "long". Each line is one scene, timed to the voice (timings.json):
  visual.type = "image"    real, licensed photo (media.py downloads it; credits.json holds the licence).
                           Slow Ken Burns move ("move": in | out | left | right | up | down), colour grade, vignette,
                           film grain, lower-third headline from `ost` ("kicker|headline"), credit line bottom-right.
                           Portrait or small images are shown as a floating print over a blurred copy of themselves.
  visual.type = "chapter"  letterboxed chapter card: CHAPTER n, title, thin animated rule, optional blurred image "bg".
  visual.type = "title"    the episode title card over a darkened image ("bg").
  visual.type = "end"      subscribe card with the disclaimer and fact-check date.
  any Shorts visual         (stat, trial, grid, mnemonic, ecg, tags, versus, verdict, drug_card, ...) drawn by render.py
                           on a white card on the right, with the `ost` headline on the left, over a dark studio backdrop.
The picture leads the voice by LEAD seconds and scenes cross-dissolve; chapter and title cards dip through black.
Audio: voice + self-made cinematic score (pad, slow plucks, swells into chapter cards, low booms) ducked under the voice,
loudness-normalised to -14 LUFS. Also writes captions.srt (upload it as YouTube subtitles) and thumbnail.png (1280x720).
"""
import json, math, subprocess, sys, wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

import render as R

ROOT = Path(__file__).parent
W, H, FPS, SR = 1920, 1080, 30, 44100
CFG = R.CFG
ACC, INK, WHITE = R.ACC, R.INK, (255, 255, 255, 255)
DARK = (11, 18, 20, 255)
LEAD, XFADE, DIP = 0.30, 0.55, 0.45
F = R.F


def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)          # smoothstep for camera moves
def easeo(x): return R.ease(x)


# ------------------------------------------------------------------ image prep (grade once, move per frame)
_cache = {}


def graded(path):
    """Load, cover-scale to >= 2304x1296 and colour-grade (gentle contrast, teal shadows / warm highlights)."""
    if path in _cache: return _cache[path]
    im = Image.open(path).convert("RGB")
    portrait = im.width / im.height < 1.15 or im.width < 1600
    im = ImageEnhance.Contrast(im).enhance(1.08); im = ImageEnhance.Color(im).enhance(0.92)
    a = np.asarray(im).astype(np.float32) / 255
    lum = a.mean(axis=2, keepdims=True)
    shadow = np.array([0.0, 0.035, 0.05]) * (1 - lum) ** 2          # teal into the shadows
    high = np.array([0.03, 0.012, -0.02]) * lum ** 2                 # warmth into the highlights
    a = np.clip(a + shadow + high, 0, 1)
    im = Image.fromarray((a * 255).astype(np.uint8))
    if portrait:
        bg = im.resize(cover_size(im, W * 1.15, H * 1.15), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))
        bg = ImageEnhance.Brightness(bg).enhance(0.45)
        fg_h = int(H * 0.80); fg = im.resize((int(im.width * fg_h / im.height), fg_h), Image.LANCZOS)
        if fg.width > W * 0.8: fg = im.resize((int(W * 0.8), int(im.height * W * 0.8 / im.width)), Image.LANCZOS)
        out = (bg, fg)
    else:
        out = (im.resize(cover_size(im, W * 1.2, H * 1.2), Image.LANCZOS), None)
    _cache[path] = out
    return out


def cover_size(im, w, h):
    s = max(w / im.width, h / im.height)
    return int(im.width * s + 1), int(im.height * s + 1)


MOVES = ["in", "right", "out", "left", "up", "in", "down", "out"]


def ken_burns(base, move, p):
    """Crop box on the graded image for progress p (0..1): slow zoom or pan, eased."""
    bw, bh = base.size; e = ease(p)
    z0, z1 = {"in": (1.0, 1.12), "out": (1.12, 1.0)}.get(move, (1.08, 1.08))
    z = z0 + (z1 - z0) * e
    k = min(bw / (1.2 * W), bh / (1.2 * H))          # base pixels per frame pixel at zoom 1 (base is >= 1.2x the frame)
    cw, ch = min(bw, W * k / z), min(bh, H * k / z)
    fx, fy = 0.5, 0.5
    span = 0.10
    if move == "left": fx = 0.5 + span - 2 * span * e
    if move == "right": fx = 0.5 - span + 2 * span * e
    if move == "up": fy = 0.5 + span - 2 * span * e
    if move == "down": fy = 0.5 - span + 2 * span * e
    x0 = min(max(0, fx * bw - cw / 2), bw - cw); y0 = min(max(0, fy * bh - ch / 2), bh - ch)
    return (x0, y0, x0 + cw, y0 + ch)


# ------------------------------------------------------------------ overlays (made once)
def make_vignette():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    a = np.clip((d - 0.55) / 0.9, 0, 1) ** 1.6 * 200
    v = np.zeros((H, W, 4), np.uint8); v[..., 3] = a.astype(np.uint8)
    return Image.fromarray(v, "RGBA")


def make_grain(n=6):
    rng = np.random.default_rng(11); out = []
    for _ in range(n):
        g = rng.normal(128, 40, (H // 2, W // 2)).clip(0, 255).astype(np.uint8)
        g = Image.fromarray(g).resize((W, H), Image.BILINEAR)
        rgba = Image.merge("RGBA", (g, g, g, Image.new("L", (W, H), 14)))
        out.append(rgba)
    return out


VIGNETTE, GRAIN = None, None


def bottom_shade():
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for y in range(int(H * 0.55), H):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(190 * ((y - H * 0.55) / (H * 0.45)) ** 1.5)))
    return g


SHADE = None


# ------------------------------------------------------------------ scene painters
def lower_third(img, ost, lt):
    if not ost: return
    d = ImageDraw.Draw(img)
    kick, _, head = ost.partition("|")
    if not head: kick, head = "", kick
    k = easeo((lt - 0.25) / 0.45)
    if k <= 0: return
    x = 120; y = H - 230
    d.rectangle([x, y, x + 8, y + 112], fill=R.fade(ACC, k))
    if kick: R.spaced(d, (x + 34, y + 18), kick.upper(), F(26), R.fade((150, 220, 214, 255), k), track=4, anchor="l")
    f = R.fit_font(head, 1300, 62)
    d.text((x + 34 + (1 - k) * 30, y + 70), head, font=f, fill=R.fade(WHITE, k), anchor="lm")


def credit_line(img, cr):
    if not cr: return
    d = ImageDraw.Draw(img)
    t = f"Image: {cr['author'][:60]} · {cr['license']} · {cr.get('source', 'Wikimedia Commons')}"
    d.text((W - 60, H - 36), t, font=F(20, "body"), fill=(235, 235, 235, 170), anchor="rm")


def checked_nice():
    """'FACT-CHECKED AS OF 23 NOV 2026' -> 'Fact-checked as of 23 Nov 2026'."""
    c = R.CHECKED
    if not c: return ""
    head, _, date = c.partition(" AS OF ")
    d, m, y = date.split()
    return f"Fact-checked as of {d} {m.title()} {y}"


def top_shade():
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for y in range(0, 170):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(150 * (1 - y / 170) ** 1.6)))
    return g


TOPSHADE = None


def watermark(img):
    img.alpha_composite(TOPSHADE)
    d = ImageDraw.Draw(img)
    a, b = CFG["wordmark"]; f = F(30)
    d.text((60, 52), a, font=f, fill=(255, 255, 255, 190), anchor="lm")
    d.text((60 + f.getlength(a), 52), b, font=f, fill=ACC[:3] + (230,), anchor="lm")
    note = " · ".join(x for x in ("Educational only, not medical advice", checked_nice()) if x)
    d.text((60, 86), note, font=F(18, "body"), fill=(255, 255, 255, 150), anchor="lm")


def scene_image(line, lt, ld, credits, idx):
    v = line["visual"]; key = v.get("wellcome") or v.get("file") or v.get("query")
    cr = credits.get(key)
    if not cr: return scene_missing(line)
    base, fg = graded(str(CUR_EP / "images" / cr["local"]))
    move = v.get("move") or MOVES[idx % len(MOVES)]
    p = min(1.0, lt / max(ld + 1.0, 1.0))
    img = base.resize((W, H), Image.BILINEAR, box=ken_burns(base, move, p)).convert("RGBA")
    if fg is not None:
        z = 1.0 + 0.05 * ease(p)
        f2 = fg.resize((int(fg.width * z), int(fg.height * z)), Image.BILINEAR)
        x = (W - f2.width) // 2 + (180 if line.get("ost") else 0) * 0; y = (H - f2.height) // 2 - 20
        sh = Image.new("RGBA", (f2.width + 60, f2.height + 60), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rectangle([30, 40, f2.width + 30, f2.height + 40], fill=(0, 0, 0, 120))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (x - 30, y - 30))
        img.paste(f2, (x, y))
    img.alpha_composite(SHADE)
    lower_third(img, line.get("ost", ""), lt)
    credit_line(img, cr)
    return img


def scene_missing(line):
    img = Image.new("RGBA", (W, H), DARK)
    ImageDraw.Draw(img).text((W / 2, H / 2), "[image missing: run media.py]", font=F(40), fill=(255, 80, 80, 255), anchor="mm")
    return img


def scene_graphic(line, lt, ld):
    img = Image.new("RGBA", (W, H), DARK); d = ImageDraw.Draw(img)
    # soft teal glow + fine grid: a "studio" backdrop
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.45, -H * 0.3, W * 1.3, H * 1.1], fill=ACC[:3] + (60,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(160)))
    for x in range(0, W, 80): d.line([(x, 0), (x, H)], fill=(255, 255, 255, 8))
    for y in range(0, H, 80): d.line([(0, y), (W, y)], fill=(255, 255, 255, 8))
    kick, _, head = line.get("ost", "").partition("|")
    if not head: kick, head = "", kick
    k = easeo(lt / 0.4)
    if kick: R.spaced(d, (120, 330), kick.upper(), F(28), R.fade((150, 220, 214, 255), k), track=5, anchor="l")
    yy = 400
    for ln in R.wrap(head, F(76), 700)[:4]:
        d.text((120 + (1 - k) * 30, yy), ln, font=F(76), fill=R.fade(WHITE, k), anchor="lm"); yy += 88
    if line.get("source"):
        d.text((120, yy + 40), "Source: " + line["source"], font=F(24, "body"), fill=R.fade((180, 190, 190, 255), easeo((lt - 0.3) / 0.4)), anchor="lm")
    # visual from the Shorts renderer, on a white card
    vis = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    R.draw_visual(vis, line["visual"], lt * R.VIS_SPEED, ld * R.VIS_SPEED)
    crop = vis.crop((40, 540, 1040, 1460))                              # 1000 x 920 around the visual centre
    cw, ch = 860, 792; kk = easeo(lt / 0.45)
    card = Image.new("RGBA", (cw + 80, ch + 80), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([40, 40, cw + 40, ch + 40], 36, fill=(255, 255, 255, 255))
    card.alpha_composite(crop.resize((cw, ch), Image.BILINEAR), (40, 40))
    shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([40, 56, cw + 40, ch + 56], 36, fill=(0, 0, 0, 140))
    x = int(W - cw - 160 + (1 - kk) * 60); y = (H - ch) // 2 - 40
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(24)), (x, y))
    if kk < 1: card.putalpha(card.getchannel("A").point(lambda a: int(a * kk)))
    img.alpha_composite(card, (x, y))
    return img


def letterbox(img, k=1.0):
    d = ImageDraw.Draw(img); bar = int(132 * k)
    d.rectangle([0, 0, W, bar], fill=(0, 0, 0, 255)); d.rectangle([0, H - bar, W, H], fill=(0, 0, 0, 255))


def blurred_bg(credits, v, p):
    key = v.get("bg")
    cr = credits.get(key) if key else None
    if not cr: return Image.new("RGBA", (W, H), DARK), None
    base, _ = graded(str(CUR_EP / "images" / cr["local"]))
    im = base.resize((W, H), Image.BILINEAR, box=ken_burns(base, "in", p)).filter(ImageFilter.GaussianBlur(6))
    return Image.alpha_composite(im.convert("RGBA"), Image.new("RGBA", (W, H), (5, 10, 12, 175))), cr


def scene_chapter(line, lt, ld, credits):
    v = line["visual"]; img, cr = blurred_bg(credits, v, min(1, lt / (ld + 1)))
    letterbox(img, easeo(lt / 0.5)); d = ImageDraw.Draw(img)
    k = easeo((lt - 0.2) / 0.5)
    R.spaced(d, (W / 2, H / 2 - 110), f"CHAPTER {v['n']}", F(30), R.fade(ACC, k), track=10)
    f = R.fit_font(v["title"], 1500, 110)
    d.text((W / 2, H / 2 + 10 + (1 - k) * 20), v["title"], font=f, fill=R.fade(WHITE, k), anchor="mm")
    w = 520 * easeo((lt - 0.4) / 0.9)
    d.line([(W / 2 - w / 2, H / 2 + 110), (W / 2 + w / 2, H / 2 + 110)], fill=ACC, width=4)
    if v.get("sub"): d.text((W / 2, H / 2 + 170), v["sub"], font=F(34, "body"), fill=R.fade((200, 210, 210, 255), easeo((lt - 0.7) / 0.5)), anchor="mm")
    if cr: credit_line(img, cr)
    return img


def scene_title(line, lt, ld, credits):
    v = line["visual"]; img, cr = blurred_bg(credits, v, min(1, lt / (ld + 1)))
    letterbox(img); d = ImageDraw.Draw(img)
    k = easeo((lt - 0.1) / 0.6)
    a, b = CFG["wordmark"]; f = F(34); x = W / 2 - (f.getlength(a) + f.getlength(b)) / 2
    d.text((x, H / 2 - 190), a, font=f, fill=R.fade(WHITE, k), anchor="lm"); d.text((x + f.getlength(a), H / 2 - 190), b, font=f, fill=R.fade(ACC, k), anchor="lm")
    R.spaced(d, (W / 2, H / 2 - 135), v.get("kicker", "DEEP DIVE"), F(26), R.fade(ACC, k), track=10)
    yy = H / 2 - 40
    for i, ln in enumerate(v["lines"]):
        kk = easeo((lt - 0.3 - i * 0.25) / 0.6)
        d.text((W / 2, yy + (1 - kk) * 24), ln, font=R.fit_font(ln, 1600, 120), fill=R.fade(ACC if i == len(v["lines"]) - 1 else WHITE, kk), anchor="mm"); yy += 128
    if cr: credit_line(img, cr)
    return img


def scene_end(line, lt, ld, credits):
    v = line["visual"]; img, cr = blurred_bg(credits, v, min(1, lt / (ld + 1)))
    d = ImageDraw.Draw(img); k = R.back(lt / 0.5)
    R.med_cross(d, W / 2, H / 2 - 210, 70 * max(k, 0.01), ACC)
    a, b = CFG["wordmark"]; f = F(80); x = W / 2 - (f.getlength(a) + f.getlength(b)) / 2
    d.text((x, H / 2 - 60), a, font=f, fill=WHITE, anchor="lm"); d.text((x + f.getlength(a), H / 2 - 60), b, font=f, fill=ACC, anchor="lm")
    d.text((W / 2, H / 2 + 20), CFG["tagline"], font=F(36, "body"), fill=(210, 220, 220, 255), anchor="mm")
    bounce = abs(math.sin(lt * 4)) * 8
    d.rounded_rectangle([W / 2 - 220, H / 2 + 90 - bounce, W / 2 + 220, H / 2 + 180 - bounce], 46, fill=(230, 33, 23, 255))
    d.text((W / 2, H / 2 + 135 - bounce), "SUBSCRIBE", font=F(48), fill=WHITE, anchor="mm")
    d.text((W / 2, H - 150), "Educational content only, not medical advice. Sources and image credits are in the description.", font=F(26, "body"), fill=(190, 200, 200, 255), anchor="mm")
    if R.CHECKED: d.text((W / 2, H - 110), checked_nice(), font=F(24, "body"), fill=(160, 175, 175, 255), anchor="mm")
    return img


def paint(i, lt, ld, sl, credits):
    line = sl[i]; t = line["visual"]["type"]
    if t == "image": img = scene_image(line, lt, ld, credits, i)
    elif t == "chapter": img = scene_chapter(line, lt, ld, credits)
    elif t == "title": img = scene_title(line, lt, ld, credits)
    elif t == "end": img = scene_end(line, lt, ld, credits)
    else: img = scene_graphic(line, lt, ld)
    return img


DIPPED = {"chapter", "title", "end"}


def frame(t, dur, vl, sl, credits):
    i = R.scene_at(vl, t); start = vl[i]["start"]
    nxt = vl[i + 1]["start"] if i + 1 < len(vl) else dur
    lt, ld = t - start, nxt - start
    img = paint(i, lt, ld, sl, credits)
    if i > 0 and lt < XFADE:
        kind = sl[i]["visual"]["type"]; pkind = sl[i - 1]["visual"]["type"]
        if kind in DIPPED or pkind in DIPPED:                       # dip through black
            if lt < DIP / 2:
                prev = paint(i - 1, start - vl[i - 1]["start"] + lt, start - vl[i - 1]["start"], sl, credits)
                img = Image.blend(prev, Image.new("RGBA", (W, H), (0, 0, 0, 255)), easeo(lt / (DIP / 2)))
            elif lt < DIP:
                img = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, easeo((lt - DIP / 2) / (DIP / 2)))
        else:                                                       # cross-dissolve
            prev = paint(i - 1, start - vl[i - 1]["start"] + lt, start - vl[i - 1]["start"], sl, credits)
            img = Image.blend(prev, img, easeo(lt / XFADE))
    if sl[i]["visual"]["type"] not in ("title", "end"): watermark(img)
    img.alpha_composite(VIGNETTE)
    img.alpha_composite(GRAIN[int(t * 24) % len(GRAIN)])
    if t < 0.8: img = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, easeo(t / 0.8))
    if dur - t < 1.2: img = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, easeo((dur - t) / 1.2))
    return img


# ------------------------------------------------------------------ score + sfx
def score(ep, dur, vl, sl):
    n = int(dur * SR); rng = np.random.default_rng(7); tt = np.arange(n) / SR
    chords = [[110.0, 164.81, 220.0, 261.63], [87.31, 130.81, 174.61, 220.0], [130.81, 196.0, 261.63, 329.63], [98.0, 146.83, 196.0, 246.94]]
    bar = 60 / 66 * 4; music = np.zeros(n)
    # warm pad: detuned sines per chord, long crossfades, slow tremolo
    for ci in range(int(dur / bar) + 2):
        s = int(ci * bar * SR); e = min(n, int((ci + 1.25) * bar * SR))
        if s >= n: break
        t0 = np.arange(e - s) / SR; L = (e - s) / SR
        env = np.minimum(1, t0 / 1.6) * np.minimum(1, (L - t0) / 1.6)
        for f in chords[ci % 4]:
            for det in (-0.6, 0.6):
                music[s:e] += 0.05 * env * np.sin(2 * np.pi * (f + det) * t0 + rng.uniform(0, 6))
    music *= 1 + 0.15 * np.sin(2 * np.pi * 0.11 * tt)
    # sparse plucks (one every half bar, an octave up)
    cache = {}
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]
        for j, idx in enumerate((2, 3, 1, 3)):
            f = ch[idx] * 2
            if f not in cache: cache[f] = R.pluck(f, 2.2, rng, 0.997)
            s = int((ci * bar + j * bar / 4) * SR)
            if s < n: music[s:s + len(cache[f])] += cache[f][:max(0, n - s)] * 0.22
    # swell into each chapter/title card and a lift through it
    auto = np.ones(n) * 0.8
    for l, s_ in zip(vl, sl):
        if s_["visual"]["type"] in DIPPED:
            a = int(max(0, l["start"] - 2.5) * SR); b = int(l["start"] * SR); c = min(n, int((l["start"] + 3.0) * SR))
            if b > a: auto[a:b] = np.maximum(auto[a:b], np.linspace(0.8, 1.6, b - a))
            if c > b: auto[b:c] = np.maximum(auto[b:c], np.linspace(1.6, 0.8, c - b))
    music *= auto
    music /= np.abs(music).max() + 1e-9
    fo = int(2.0 * SR); music[-fo:] *= np.linspace(1, 0, fo); music[:int(SR)] *= np.linspace(0, 1, int(SR))
    sfx = np.zeros(n)
    def add(at, sig):
        s = int(at * SR); e = min(n, s + len(sig))
        if 0 <= s < n: sfx[s:e] += sig[:e - s]
    bt = np.arange(int(2.2 * SR)) / SR
    boom = np.sin(2 * np.pi * (55 - 18 * bt) * bt) * np.exp(-bt * 2.2) * 0.9
    L = int(0.8 * SR); wt = np.arange(L) / SR
    whoosh = np.convolve(rng.normal(0, 1, L), np.ones(90) / 90, "same") * np.sin(np.pi * wt / 0.8) ** 2 * 1.2
    for i, (l, s_) in enumerate(zip(vl, sl)):
        if i == 0: continue
        if s_["visual"]["type"] in DIPPED: add(l["start"], boom)
        elif i % 2 == 0: add(l["start"] - 0.2, whoosh * 0.35)
    for name, x, g in (("music.wav", music, 0.8), ("sfx.wav", sfx / (np.abs(sfx).max() + 1e-9), 0.7)):
        x = (np.clip(x * g, -1, 1) * 32767).astype(np.int16)
        with wave.open(str(ep / name), "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(x.tobytes())


def pad_voice(ep, dur):
    """Extend voice.wav with silence to the video length, so the score plays through the outro (mix stops at the voice's end)."""
    with wave.open(str(ep / "voice.wav")) as wf:
        sr, n, a = wf.getframerate(), wf.getnframes(), wf.readframes(wf.getnframes())
    need = int(dur * sr) - n
    if need > 0:
        with wave.open(str(ep / "voice.wav"), "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(a + b"\x00\x00" * need)


def finalize(ep, dur):
    """Mix voice + score + sfx (render.mix: sidechain ducking), then two-pass loudnorm to -14 LUFS."""
    LN = ""
    for _pass in (1, 2):
        R.mix(ep, dur, LN)
        if _pass == 1:
            r = subprocess.run(["ffmpeg", "-i", ep / "final_video.mp4", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                                "-f", "null", "-"], capture_output=True, text=True).stderr
            m = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
            LN = (f",loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
                  f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    (ep / "video_only.mp4").unlink()


# ------------------------------------------------------------------ captions + thumbnail
def srt(ep, lines):
    def ts(x): h, r = divmod(x, 3600); m, s = divmod(r, 60); return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    out, n = [], 1
    for l in lines:
        ws = l["words"]
        for j in range(0, len(ws), 9):
            g = ws[j:j + 9]
            out.append(f"{n}\n{ts(g[0]['start'])} --> {ts(g[-1]['end'] + 0.15)}\n{' '.join(w['w'] for w in g)}\n"); n += 1
    (ep / "captions.srt").write_text("\n".join(out))


def thumbnail(ep, script, credits):
    th = script["meta"].get("thumbnail", {})
    key = th.get("image", ""); key = key[2:] if key.startswith("W:") else key; cr = credits.get(key)
    img = Image.new("RGBA", (W, H), DARK)
    if cr:
        base, fg = graded(str(ep / "images" / cr["local"]))
        img = base.resize((W, H), Image.LANCZOS, box=ken_burns(base, "in", 0.6)).convert("RGBA")
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(shade)
    for x in range(W): sd.line([(x, 0), (x, H)], fill=(5, 10, 12, int(235 * max(0, 1 - x / (W * 0.72)))))
    img.alpha_composite(shade); d = ImageDraw.Draw(img)
    R.med_cross(d, 150, 150, 46, ACC)
    yy = 330
    for i, ln in enumerate(th.get("lines", ["DEEP DIVE"])):
        f = R.fit_font(ln, 1100, 170)
        d.text((110, yy), ln, font=f, fill=ACC if i == len(th["lines"]) - 1 else WHITE, anchor="lm"); yy += 185
    if th.get("tag"):
        tw = F(44).getlength(th["tag"]) + 60
        d.rounded_rectangle([110, yy + 10, 110 + tw, yy + 90], 18, fill=(230, 33, 23, 255))
        d.text((140, yy + 50), th["tag"], font=F(44), fill=WHITE, anchor="lm")
    img.convert("RGB").resize((1280, 720), Image.LANCZOS).save(ep / "thumbnail.png")


# ------------------------------------------------------------------ main
CUR_EP = None


def main(ep_dir, thumb_only=False, preview=None):
    global CUR_EP, VIGNETTE, GRAIN, SHADE, TOPSHADE
    ep = CUR_EP = Path(ep_dir)
    script = json.loads((ep / "script.json").read_text())
    tim = json.loads((ep / "timings.json").read_text())
    credits = json.loads((ep / "credits.json").read_text()) if (ep / "credits.json").exists() else {}
    sl, lines = script["lines"], tim["lines"]
    R.CHECKED = R.checked_text(script)
    VIGNETTE, GRAIN, SHADE, TOPSHADE = make_vignette(), make_grain(), bottom_shade(), top_shade()
    thumbnail(ep, script, credits)
    if thumb_only: return
    dur = tim["duration"] + 2.0
    vl = [dict(lines[0], start=0.0)]
    for i in range(1, len(lines)):
        st = max(lines[i]["start"] - LEAD, lines[i - 1]["words"][-1]["start"] + 0.05, vl[-1]["start"] + 0.6)
        vl.append(dict(lines[i], start=min(st, lines[i]["start"])))
    if preview:
        for t in preview:
            frame(t, dur, vl, sl, credits).convert("RGB").save(ep / f"preview_{t:.1f}.png")
        return
    srt(ep, lines)
    score(ep, dur, vl, sl)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv", "-c:v", "libx264", "-preset", "medium",
                           "-crf", "20", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
                           "-color_trc", "bt709", "-color_range", "tv", str(ep / "video_only.mp4")], stdin=subprocess.PIPE)
    nf = int(dur * FPS)
    for fi in range(nf):
        ff.stdin.write(frame(fi / FPS, dur, vl, sl, credits).convert("RGB").tobytes())
        if fi % 900 == 0: print(f"frame {fi}/{nf}", flush=True)
    ff.stdin.close(); ff.wait()
    pad_voice(ep, dur)
    finalize(ep, dur)
    print("wrote", ep / "final_video.mp4", f"({dur / 60:.1f} min)")


if __name__ == "__main__":
    a = sys.argv[1:]
    prev = [float(x) for x in a[a.index("--preview") + 1:]] if "--preview" in a else None
    main(a[0], thumb_only="--thumb" in a, preview=prev)
