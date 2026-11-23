"""Video Editor. "Clinic-light" editorial theme (PARAVION MED): white page, dark grotesk headlines with a
teal second line, spaced teal kickers, hairline rules, green/amber verdict pills, red ✗, ECG / trial / mnemonic
visuals for medical topics, and a permanent "educational only" line under the header.
All graphics, music and SFX are generated here (no third-party footage).

python3 render.py episodes/<slug> [--cover]  ->  final_video.mp4, cover.png
"""
import json, math, re, subprocess, sys, wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
W, H, FPS, SR = 1080, 1920, 30, 44100
CFG = json.loads((ROOT / "config.json").read_text())
T = CFG["theme"]
def hx(c, a=255): c = c.lstrip("#"); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (a,)
BG, BAND, RULE, INK, MUTED, ACC, XRED = (hx(T[k]) for k in ("bg", "band", "rule", "ink", "muted", "accent", "x_red"))
GREEN_BG, GREEN_FG, AMBER_BG, AMBER_FG = (hx(T[k]) for k in ("pill_green_bg", "pill_green_fg", "pill_amber_bg", "pill_amber_fg"))
TINT = hx(T.get("tint", "#F3F3F1"))
WHITE = (255, 255, 255, 255)
_fc = {}
def F(size, w="head"):
    k = (int(size), w)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(str(ROOT / CFG["font_" + w]), max(8, int(size)))
    return _fc[k]

# Safe zone: avoid top 12% (<230), bottom 22% (>1498), right 15% (>918)
SAFE_L, SAFE_R = 80, 1000      # margins (symmetric)
CX = W // 2                    # 540 — true centre; text blocks kept ≤760 px wide (160–920) so they clear the right-side buttons
VY = 985                      # visual centre (full-frame layout)
VIS_SCALE = 0.98
BAND_Y = 1330                  # bottom of the content area


def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def back(x):
    x = max(0, min(1, x)); c = 1.15
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def fade(c, a): return c[:3] + (int(c[3] * max(0, min(1, a))),)


def tc(d, xy, s, font, fill, anchor="mm"):
    d.text(xy, s, font=font, fill=fill, anchor=anchor)


def spaced(d, xy, s, font, fill, track=4, anchor="m", underline=None):
    """Letter-spaced small caps label (kicker). anchor: 'm' centre or 'l' left."""
    widths = [font.getlength(ch) for ch in s]
    total = sum(widths) + track * (len(s) - 1)
    x = xy[0] - total / 2 if anchor == "m" else xy[0]
    x0 = x
    for ch, w in zip(s, widths):
        d.text((x, xy[1]), ch, font=font, fill=fill, anchor="lm"); x += w + track
    if underline:
        d.line([(x0, xy[1] + font.size * 0.75), (x0 + total, xy[1] + font.size * 0.75)], fill=underline, width=3)
    return total


def wrap(s, font, maxw):
    out, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if font.getlength(t) <= maxw or not cur: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out


def xmark(d, cx, cy, r, t=1.0, width=22):
    """Red ✗ drawn stroke by stroke."""
    a = ease(t / 0.18); b = ease((t - 0.12) / 0.18)
    if a > 0: d.line([(cx - r, cy - r), (cx - r + 2 * r * a, cy - r + 2 * r * a)], fill=XRED, width=width)
    if b > 0: d.line([(cx + r, cy - r), (cx + r - 2 * r * b, cy - r + 2 * r * b)], fill=XRED, width=width)


def check(d, cx, cy, r, col, width=20):
    d.line([(cx - r, cy), (cx - r * 0.3, cy + r * 0.7), (cx + r, cy - r * 0.8)], fill=col, width=width, joint="curve")


def pill(d, x, cy, text, kind="green", size=34, anchor="l"):
    bg, fg = {"green": (GREEN_BG, GREEN_FG), "amber": (AMBER_BG, AMBER_FG),
              "red": ((253, 226, 226, 255), XRED)}.get(kind, (ACC, WHITE))
    f = F(size, "head")
    widths = [f.getlength(ch) for ch in text]; tw = sum(widths) + 4 * (len(text) - 1)
    x0 = x if anchor == "l" else x - tw / 2 - 22
    d.rounded_rectangle([x0, cy - size * 0.85, x0 + tw + 44, cy + size * 0.85], int(size * 0.85), fill=bg)
    spaced(d, (x0 + 22, cy), text, f, fg, track=4, anchor="l")
    return tw + 44


def arrow(d, x, y, length, col, width=5):
    d.line([(x, y), (x + length, y)], fill=col, width=width)
    d.line([(x + length - 22, y - 16), (x + length, y), (x + length - 22, y + 16)], fill=col, width=width, joint="curve")


def stamp(layer, text, t, color=XRED, cx=CX, cy=VY, size=150, angle=-12):
    if t < 0: return
    k = back(t / 0.35); sc = 2.0 - 1.0 * k
    f = F(size * sc, "head")
    tw = int(f.getlength(text)) + 80; th = int(size * sc * 1.3)
    st = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    sd.rounded_rectangle([4, 4, tw - 4, th - 4], 16, fill=(255, 255, 255, 230), outline=color, width=max(6, int(11 * sc)))
    tc(sd, (tw // 2, th // 2), text, f, color)
    st = st.rotate(angle, expand=True, resample=Image.BICUBIC)
    a = min(1, t / 0.15)
    if a < 1: st.putalpha(st.getchannel("A").point(lambda v: int(v * a)))
    layer.alpha_composite(st, (int(cx - st.width / 2), int(cy - st.height / 2)))


def chip(d, cx, cy, s=1.0, lit=1.0, label="AI"):
    r = int(150 * s)
    for i in range(-3, 4):
        o = int(i * r / 3.6)
        for box in [(cx + o - 7, cy - r - 44, cx + o + 7, cy - r), (cx + o - 7, cy + r, cx + o + 7, cy + r + 44),
                    (cx - r - 44, cy + o - 7, cx - r, cy + o + 7), (cx + r, cy + o - 7, cx + r + 44, cy + o + 7)]:
            d.rectangle(box, fill=fade(ACC, 0.35 + 0.65 * lit))
    d.rounded_rectangle([cx - r, cy - r, cx + r, cy + r], 30, fill=INK)
    d.rounded_rectangle([cx - r + 34, cy - r + 34, cx + r - 34, cy + r - 34], 16, outline=(70, 70, 70, 255), width=3)
    tc(d, (cx, cy + 4), label, F(120 * s), ACC)


def med_cross(d, cx, cy, r, col):
    """Plus-shaped medical cross (the channel mark). r = half the arm span."""
    t = r * 0.36
    d.rounded_rectangle([cx - t, cy - r, cx + t, cy + r], int(t * 0.45), fill=col)
    d.rounded_rectangle([cx - r, cy - t, cx + r, cy + t], int(t * 0.45), fill=col)


def ecg_y(x, pattern, rng):
    """One heartbeat-ish trace value for phase x in [0,1). Illustrative only."""
    def g(mu, sig, a): return a * math.exp(-((x - mu) / sig) ** 2)
    if pattern == "flat": return 0.0
    if pattern == "vfib": return 0.0
    y = g(0.16, 0.035, 0.12)                          # P
    y += g(0.30, 0.008, -0.12) + g(0.32, 0.012, 1.0) + g(0.345, 0.01, -0.25)   # QRS
    if pattern == "stemi":
        y += 0.32 * (1 if 0.355 < x < 0.5 else 0) + g(0.52, 0.05, 0.25)
    elif pattern == "peaked_t":
        y += g(0.52, 0.03, 0.75)
    else:
        y += g(0.55, 0.05, 0.25)                       # T
    if pattern == "af":
        y -= g(0.16, 0.035, 0.12); y += 0.035 * math.sin(x * 90)
    return y


def draw_ecg(d, x0, x1, ymid, amp, p, pattern="normal", beats=3, col=None, width=8):
    rng = np.random.default_rng(5)
    n = 600; pts = []
    widths = [1.0] * beats
    if pattern == "af": widths = list(rng.uniform(0.55, 1.35, beats))
    tot = sum(widths); edges = np.cumsum([0] + widths) / tot
    for i in range(int(n * p)):
        u = i / (n - 1)
        b = min(beats - 1, int(np.searchsorted(edges, u, side="right") - 1))
        ph = (u - edges[b]) / (edges[b + 1] - edges[b])
        if pattern == "vfib":
            y = 0.35 * math.sin(u * 70 + math.sin(u * 13) * 3) * (0.6 + 0.4 * math.sin(u * 9))
        else:
            y = ecg_y(ph, pattern, rng)
        pts.append((x0 + (x1 - x0) * u, ymid - amp * y))
    if len(pts) > 1:
        d.line(pts, fill=col or XRED, width=width, joint="curve")
        d.ellipse([pts[-1][0] - 12, pts[-1][1] - 12, pts[-1][0] + 12, pts[-1][1] + 12], fill=col or XRED)


# ------------------------------------------------------------ visuals (all text/numbers come from the episode script)
KIND_COL = {"ink": INK, "accent": ACC, "red": XRED, "green": GREEN_FG, "muted": MUTED}


def mark(d, kind, x, y, r, lt, col=None):
    if kind == "x": xmark(d, x, y, r, lt, width=max(8, int(r * 0.42)))
    elif kind == "check": check(d, x, y, r, GREEN_FG, width=max(8, int(r * 0.35)))
    elif kind == "dot": d.ellipse([x - r * 0.7, y - r * 0.7, x + r * 0.7, y + r * 0.7], fill=col or ACC)
    elif kind == "q":
        d.ellipse([x - r, y - r, x + r, y + r], fill=BAND, outline=RULE, width=2)
        tc(d, (x, y + 2), "?", F(r * 1.2), MUTED)


def num_text(v, p):
    val = v["value"] * p
    dec = v.get("decimals", 0)
    s = f"{val:,.{dec}f}"
    return v.get("prefix", "") + s + v.get("suffix", "")


def draw_visual(layer, v, lt, ld):
    d = ImageDraw.Draw(layer)
    typ = v["type"]
    if typ == "chip_stamp":
        chip(d, CX, VY, 0.95, label=v.get("label", "AI"))
        stamp(layer, v["stamp"], lt - v.get("stamp_at", 1.2))
    elif typ == "chip_glow":
        chip(d, CX, VY - (40 if v.get("loop_text") else 0), 0.95, lit=0.5 + 0.5 * math.sin(lt * 5), label=v.get("label", "AI"))
        if v.get("loop_text"):
            tc(d, (CX, VY + 200), v["loop_text"], F(80), INK)
    elif typ == "question":
        k = back(lt / 0.4)
        tc(d, (CX, VY), "?", F(440 * k + 1), ACC)
    elif typ == "timer":
        p = min(1, lt / max(ld, .1))
        d.ellipse([CX - 210, VY - 210, CX + 210, VY + 210], outline=RULE, width=30)
        d.arc([CX - 210, VY - 210, CX + 210, VY + 210], -90, -90 + 360 * (1 - p), fill=ACC, width=30)
        tc(d, (CX, VY - 15), str(max(0, int(60 - 60 * ease(p)))), F(190), INK)
        spaced(d, (CX, VY + 90), "SECONDS", F(34), MUTED)
    elif typ == "counter":
        p = ease(lt / 1.2)
        val = int(round(v["from"] + (v["to"] - v["from"]) * p))
        spaced(d, (CX, VY - 175), v["label"], F(34), MUTED)
        tc(d, (CX, VY), v.get("fmt", "{:d}").format(val), F(240), INK)
        d.line([(CX - 260, VY + 135), (CX + 260, VY + 135)], fill=RULE, width=3)
        if v.get("sub"): tc(d, (CX, VY + 195), v["sub"], F(58), ACC)
    elif typ == "stat":
        # big number that counts up, label above, sub line below
        p = ease(lt / v.get("count_time", 1.1)) if v.get("count", True) else 1
        if v.get("label"): spaced(d, (CX, VY - 190), v["label"], F(34), MUTED)
        txt = num_text(v, p) if isinstance(v.get("value"), (int, float)) else v["text"]
        tc(d, (CX, VY - 10), txt, fit_font(txt, 860, v.get("size", 250)), KIND_COL[v.get("color", "ink")])
        d.line([(CX - 260, VY + 135), (CX + 260, VY + 135)], fill=RULE, width=3)
        if v.get("sub"):
            k = ease((lt - 0.5) / 0.4)
            for j, ln in enumerate(wrap(v["sub"], F(54), 820)[:2]):
                tc(d, (CX, VY + 200 + j * 64), ln, F(54), fade(ACC, k))
    elif typ == "calendar":
        k = max(back(lt / 0.4), 0.1); w2, h2 = 210 * k, 230 * k
        d.rounded_rectangle([CX - w2, VY - h2, CX + w2, VY + h2], 28, fill=WHITE, outline=INK, width=6)
        d.rounded_rectangle([CX - w2, VY - h2, CX + w2, VY - h2 + 120 * k], 28, fill=ACC)
        d.rectangle([CX - w2 + 3, VY - h2 + 80 * k, CX + w2 - 3, VY - h2 + 120 * k], fill=ACC)
        spaced(d, (CX, VY - h2 + 60 * k), v["month"] + " " + v.get("year", "2026"), F(52 * k), WHITE, track=3)
        tc(d, (CX, VY + 60 * k), v["day"], F(260 * k), INK)
    elif typ == "big_text":
        text = " ".join(v["lines"]).capitalize()
        k = ease(lt / 0.3)
        lines = wrap(text, F(76), 760)[:3]
        y0 = VY - 60 - (len(lines) - 1) * 44
        for j, ln in enumerate(lines):
            tc(d, (CX, y0 + j * 88 + (1 - k) * 40), ln, F(76), fade(INK, k))
        if v.get("badge"):
            stamp(layer, v["badge"], lt - 0.8, XRED, cy=VY + 170, size=120, angle=-6)
        else:
            d.line([(CX - 200, VY + 150), (CX + 200, VY + 150)], fill=ACC, width=6)
    elif typ in ("headline_stack", "rows"):
        rows = v["rows"]
        step = 150 if len(rows) <= 3 else 120
        top = VY - (len(rows) * step) / 2 - 10
        for i, r in enumerate(rows):
            lab, main, sub, mk = (list(r) + ["", "", "", "dot"])[:4]
            k = ease((lt - i * 0.22) / 0.35)
            y = top + i * step
            x0 = SAFE_L + 20 + (1 - k) * 60
            if k > 0: mark(d, mk, x0 + 24, y + 30, 22, lt - i * 0.22, fade(ACC, k))
            spaced(d, (x0 + 80, y + 4), lab, F(30), fade(ACC, k), track=3, anchor="l")
            tc(d, (x0 + 80, y + 50), main, fit_font(main, 820, 56), fade(INK, k), anchor="lm")
            if sub: tc(d, (x0 + 80, y + 98), sub, F(36, "body"), fade(MUTED, k), anchor="lm")
            d.line([(SAFE_L + 20, y + step - 25), (SAFE_R - 20, y + step - 25)], fill=fade(RULE, k), width=2)
    elif typ == "teaser":
        for i in range(3):
            n = i + 1; x = CX - 260 + i * 260; big = n == v["n"]
            k = back((lt - i * 0.15) / 0.35); r = (140 if big else 95) * k
            d.rounded_rectangle([x - r, VY - r, x + r, VY + r], 26, fill=ACC if big else BAND,
                                outline=None if big else RULE, width=3)
            tc(d, (x, VY + 6), "?" if big else str(n), F((170 if big else 100) * k), WHITE if big else MUTED)
    elif typ == "fact_card":
        k = ease(lt / 0.4)
        d.ellipse([CX - 100, VY - 250, CX + 100, VY - 50], fill=fade(BAND, k), outline=fade(RULE, k), width=3)
        d.ellipse([CX - 40, VY - 215, CX + 40, VY - 135], fill=fade(MUTED, k * 0.6))
        d.pieslice([CX - 70, VY - 130, CX + 70, VY - 10], 180, 360, fill=fade(MUTED, k * 0.6))
        tc(d, (CX, VY + 60 + (1 - k) * 30), v["title"], fit_font(v["title"], 860, 92), fade(INK, k))
        if lt > 0.35: pill(d, CX, VY + 175, v["sub"], "accent", size=36, anchor="m")
    elif typ == "two_hats":
        for i, (s, bg) in enumerate([(v["a"], INK), (v["b"], ACC)]):
            k = back((lt - i * 0.25) / 0.35); y = VY - 130 + i * 260
            d.rounded_rectangle([CX - 330 * k, y - 85, CX + 330 * k, y + 85], 85, fill=bg)
            tc(d, (CX, y + 4), s, fit_font(s, 600, 80 * k), WHITE)
        j = v.get("join", "+")
        if j in ("→", "↓", "->", "v"):    # font has no arrow glyphs: draw one
            d.line([(CX, VY - 30), (CX, VY + 30)], fill=MUTED, width=8)
            d.line([(CX - 22, VY + 8), (CX, VY + 32), (CX + 22, VY + 8)], fill=MUTED, width=8, joint="curve")
        else:
            tc(d, (CX, VY + 2), j, F(100), MUTED)
    elif typ == "stock_drop":
        p = ease(lt / 1.3)
        x0, x1, y0, y1 = CX - 370, CX + 370, VY - 240, VY + 80
        d.rounded_rectangle([x0 - 30, y0 - 30, x1 + 30, y1 + 30], 24, fill=BAND)
        for gy in np.linspace(y0, y1, 4):
            d.line([(x0, gy), (x1, gy)], fill=RULE, width=2)
        n = 40; noise = np.random.default_rng(7).normal(0, 7, n); pts = []
        up = v.get("direction", "down") == "up"
        for i in range(min(n, int((n - 1) * p) + 1)):
            dd = 0 if i < n * 0.55 else (i - n * 0.55) / (n * 0.45)
            y = (y1 - 50 + noise[i] - 240 * dd ** 1.5) if up else (y0 + 50 + noise[i] + 240 * dd ** 1.5)
            pts.append((x0 + (x1 - x0) * i / (n - 1), y))
        col = GREEN_FG if up else XRED
        if len(pts) > 1:
            d.line(pts, fill=col, width=10, joint="curve")
            d.ellipse([pts[-1][0] - 14, pts[-1][1] - 14, pts[-1][0] + 14, pts[-1][1] + 14], fill=col)
        spaced(d, (x0 - 10, y0 - 60), v.get("label", ""), F(26), MUTED, track=3, anchor="l")
        tc(d, (CX, VY + 205), ("+" if up else "−") + f"{v['pct'] * p:.1f}%", F(150), col)
        tc(d, (x1 + 20, y1 + 14), "illustrative chart", F(24, "body"), MUTED, anchor="rm")
    elif typ == "versus":
        sides = v.get("sides") or [
            {"name": v["left"], "mark": "check", "lines": ["Open to", "returning"], "color": "ink"},
            {"name": v["right"], "mark": "x" if v.get("reveal") else "?", "lines": ["Not", "reinstating"] if v.get("reveal") else [], "color": "accent"}]
        for side, sd in enumerate(sides):
            x = CX - 205 + side * 410
            k = back((lt - side * 0.2) / 0.35)
            d.rounded_rectangle([x - 185, VY - 230, x + 185, VY - 230 + 460 * k], 24, fill=WHITE, outline=RULE, width=4)
            if k < 0.6: continue
            col = KIND_COL[sd.get("color", "ink")]
            spaced(d, (x, VY - 170), sd["name"], fit_font(sd["name"], 300, 40), col, track=4)
            d.line([(x - 130, VY - 125), (x + 130, VY - 125)], fill=RULE, width=2)
            if sd.get("big"): tc(d, (x, VY - 10), sd["big"], fit_font(sd["big"], 320, 150), col)
            elif sd["mark"] == "?": tc(d, (x, VY - 10), "?", F(150), ACC)
            else: mark(d, sd["mark"], x, VY - 10, 62, lt - 0.25)
            lc = XRED if sd["mark"] == "x" else INK
            for j, ln in enumerate(sd.get("lines", [])):
                tc(d, (x, VY + 120 + j * 48), ln, fit_font(ln, 330, 40), lc)
        tc(d, (CX, VY + 280), v.get("join", "vs"), F(44, "body"), MUTED)
    elif typ == "search":
        k = back(lt / 0.4)
        d.ellipse([CX - 40 - 165 * k, VY - 60 - 165 * k, CX - 40 + 165 * k, VY - 60 + 165 * k], outline=INK, width=int(26 * k) + 1)
        d.line([(CX - 40 + 118 * k, VY - 60 + 118 * k), (CX - 40 + 260 * k, VY - 60 + 260 * k)], fill=INK, width=int(40 * k) + 1)
        tc(d, (CX - 40, VY - 55), v.get("word", "CEO"), F(100 * k), ACC)
        if v.get("sub"): tc(d, (CX, VY + 250), v["sub"], F(38, "body"), MUTED)
    elif typ == "verdict":
        rows = v.get("rows") or [("The exit", "CONFIRMED", "green"), ("Reason + next CEO", "STILL OPEN", "amber")]
        shown = v.get("shown") or (1 if v.get("lines", [""])[-1] == "CONFIRMED" else 2)
        d.rounded_rectangle([SAFE_L + 10, VY - 250, SAFE_R - 10, VY + 250], 24, fill=BAND)
        for i in range(shown):
            lab, val, kind = rows[i]
            k = ease((lt - (0.15 if i == shown - 1 else -1)) / 0.3)
            y = VY - 150 + i * 200
            tc(d, (SAFE_L + 60, y), lab + ":", fit_font(lab + ":", 780, 66), fade(INK, k), anchor="lm")
            if k > 0.5:
                pill(d, SAFE_L + 60, y + 92, val, kind, size=48)
            if i == 0 and len(rows) > 1: d.line([(SAFE_L + 60, y + 140), (SAFE_R - 60, y + 140)], fill=RULE, width=2)
    elif typ == "split_bar":
        # proportional bar of parts, e.g. €25B military + €20B budget
        parts = v["parts"]; tot = sum(p["value"] for p in parts)
        x0, x1, y = CX - 400, CX + 400, VY - 40
        if v.get("label"): spaced(d, (CX, VY - 220), v["label"], F(34), MUTED)
        if v.get("total"): tc(d, (CX, VY - 140), v["total"], F(110), INK)
        x = x0; p = ease(lt / 0.9)
        for i, pt in enumerate(parts):
            w = (x1 - x0) * pt["value"] / tot
            col = KIND_COL.get(pt.get("color"), [ACC, INK, MUTED][i % 3])
            d.rounded_rectangle([x + 3, y, x + 3 + max(1, (w - 6) * p), y + 110], 18, fill=col)
            kk = ease((lt - 0.6 - i * 0.2) / 0.3)
            tc(d, (x + w / 2, y + 56), pt["value_text"], fit_font(pt["value_text"], w - 30, 60), fade(WHITE, kk))
            for j, ln in enumerate(wrap(pt["label"], F(38), w - 20)[:2]):
                tc(d, (x + w / 2, y + 160 + j * 44), ln, F(38), fade(INK, kk))
            x += w
    elif typ == "phone_alert":
        k = back(lt / 0.4)
        k = max(k, 0.2)
        pw, ph = 230 * k, 400 * k; cx, cy = CX, VY + 20
        for i in range(3):   # alarm waves
            r = 290 + i * 60 + (lt * 120) % 60
            a = max(0, 1 - ((lt * 2 + i * 0.33) % 1))
            d.arc([cx - r, cy - r, cx + r, cy + r], 200, 250, fill=fade(XRED, a * 0.8), width=10)
            d.arc([cx - r, cy - r, cx + r, cy + r], 290, 340, fill=fade(XRED, a * 0.8), width=10)
        d.rounded_rectangle([cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2], 40, fill=INK)
        d.rounded_rectangle([cx - pw / 2 + 14, cy - ph / 2 + 14, cx + pw / 2 - 14, cy + ph / 2 - 14], 28, fill=WHITE)
        if k > 0.9:
            shake = math.sin(lt * 40) * 4
            d.rounded_rectangle([cx - pw / 2 + 26 + shake, cy - 140, cx + pw / 2 - 26 + shake, cy - 10], 18, fill=XRED)
            tc(d, (cx + shake, cy - 100), v.get("banner", "ALERT"), fit_font(v.get("banner", "ALERT"), pw - 80, 34), WHITE)
            tc(d, (cx + shake, cy - 55), v.get("banner_sub", ""), fit_font(v.get("banner_sub", ""), pw - 80, 24, "body"), WHITE)
            if v.get("count"):
                tc(d, (cx, cy + 90), num_text({"value": v["count"]}, ease((lt - 0.4) / 1.0)), F(110), XRED)
                tc(d, (cx, cy + 160), v.get("count_label", ""), F(26, "body"), MUTED)
    elif typ == "scoreboard":
        k = back(lt / 0.4)
        d.rounded_rectangle([CX - 420, VY - 170, CX + 420, VY + 170], 28, fill=INK)
        tA, tB = v["teams"]; sA, sB = v["score"]
        spaced(d, (CX, VY - 120), v.get("label", "FINAL"), F(28), ACC, track=5)
        for i, (t, s) in enumerate([(tA, sA), (tB, sB)]):
            x = CX - 230 + i * 460
            tc(d, (x, VY - 30), t, fit_font(t, 300, 52), WHITE)
            tc(d, (x, VY + 70), str(s), F(150 * k), ACC if s == max(sA, sB) else WHITE)
        tc(d, (CX, VY + 60), "–", F(100), MUTED)
        if v.get("sub"): tc(d, (CX, VY + 230), v["sub"], F(40, "body"), MUTED)
    elif typ == "three":
        # three labelled circles joined in a triangle (e.g. three leaders / countries)
        names = v["names"]; r = 125
        pts = [(CX, VY - 170), (CX - 250, VY + 170), (CX + 250, VY + 170)]
        p = ease(lt / 0.8)
        for a in range(3):
            b = (a + 1) % 3
            (xa, ya), (xb, yb) = pts[a], pts[b]
            d.line([(xa, ya), (xa + (xb - xa) * p, ya + (yb - ya) * p)], fill=ACC, width=6)
        for i, ((x, y), n) in enumerate(zip(pts, names)):
            kk = back((lt - i * 0.15) / 0.35)
            rr = r * kk
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=WHITE, outline=INK, width=6)
            tc(d, (x, y), n, fit_font(n, 2 * rr - 30, 56), INK)
        if v.get("center"): tc(d, (CX, VY + 50), v["center"], fit_font(v["center"], 280, 44), ACC)
    elif typ == "tags":
        tags = v["tags"]
        for i, t in enumerate(tags):
            kk = ease((lt - i * 0.25) / 0.35)
            y = VY - (len(tags) - 1) * 80 + i * 160
            f = F(72); w = f.getlength(t) + 100
            d.rounded_rectangle([CX - w / 2 + (1 - kk) * 80, y - 62, CX + w / 2 + (1 - kk) * 80, y + 62], 62,
                                fill=fade(INK if i % 2 else ACC, kk))
            tc(d, (CX + (1 - kk) * 80, y + 2), t, f, fade(WHITE, kk))
    elif typ == "ecg":
        # animated ECG strip on a grid. pattern: normal | stemi | peaked_t | af | vfib | flat (illustrative)
        x0, x1, y0, y1 = CX - 400, CX + 400, VY - 220, VY + 120
        d.rounded_rectangle([x0 - 20, y0 - 20, x1 + 20, y1 + 20], 24, fill=(255, 246, 246, 255))
        for gx in np.arange(x0, x1 + 1, 40): d.line([(gx, y0), (gx, y1)], fill=(246, 214, 214, 255), width=1)
        for gy in np.arange(y0, y1 + 1, 40): d.line([(x0, gy), (x1, gy)], fill=(246, 214, 214, 255), width=1)
        draw_ecg(d, x0, x1, (y0 + y1) / 2 + 60, 200, ease(lt / 1.6), v.get("pattern", "normal"), v.get("beats", 3), INK)
        if v.get("label"): spaced(d, (x0, y0 - 60), v["label"], F(28), MUTED, track=3, anchor="l")
        if v.get("big"):
            k = ease((lt - 0.8) / 0.4)
            tc(d, (CX, VY + 230), v["big"], fit_font(v["big"], 860, 110), fade(KIND_COL[v.get("color", "red")], k))
        tc(d, (x1 + 20, y1 + 42), "illustrative trace", F(24, "body"), MUTED, anchor="rm")
    elif typ == "trial":
        # two (or three) trial arms as horizontal bars: {"label", "arms":[{"name","value","text","color"}], "sub"}
        arms = v["arms"]; mx = max(a["value"] for a in arms) or 1
        if v.get("label"): spaced(d, (CX, VY - 240), v["label"], fit_font(v["label"], 840, 32), MUTED)
        x0, x1 = CX - 400, CX + 400; step = 190 if len(arms) <= 2 else 150
        top = VY - (len(arms) - 1) * step / 2 - 30
        for i, a in enumerate(arms):
            k = ease((lt - i * 0.25) / 0.9); y = top + i * step
            col = KIND_COL.get(a.get("color"), [ACC, MUTED, INK][i % 3])
            tc(d, (x0, y - 50), a["name"], fit_font(a["name"], 800, 44), INK, anchor="lm")
            d.rounded_rectangle([x0, y - 10, x1, y + 60], 20, fill=BAND)
            w = (x1 - x0) * a["value"] / mx * k
            if w > 40: d.rounded_rectangle([x0, y - 10, x0 + w, y + 60], 20, fill=col)
            if k > 0.6: tc(d, (min(x0 + w - 20, x1 - 20), y + 26), a["text"], fit_font(a["text"], 300, 46), WHITE, anchor="rm")
        if v.get("sub"):
            k = ease((lt - 0.9) / 0.4)
            for j, ln in enumerate(wrap(v["sub"], F(48), 820)[:2]):
                tc(d, (CX, top + len(arms) * step + 10 + j * 58), ln, F(48), fade(ACC, k))
    elif typ == "mnemonic":
        # big letters with the word each stands for: {"title", "items":[["B","Hypotension"], ...]}
        items = v["items"]; n = len(items)
        step = min(150, 560 / max(1, n - 1)) if n > 1 else 0
        top = VY - (n - 1) * step / 2 + (30 if v.get("title") else 0)
        if v.get("title"): spaced(d, (CX, top - 130), v["title"], fit_font(v["title"], 840, 34), MUTED)
        fs = 100 if n <= 4 else 78
        wmax = max(fit_font(w, 560, 64).getlength(w) for _, w in items)
        left = CX - (124 + 38 + wmax) / 2 + 62          # centre the whole block
        for i, (letter, word) in enumerate(items):
            k = 1 if i < v.get("_seen", 0) else ease((lt - (i - v.get("_seen", 0)) * 0.28) / 0.35); y = top + i * step
            bx = left + (1 - k) * 60
            d.rounded_rectangle([bx - 62, y - 62, bx + 62, y + 62], 22, fill=fade(ACC, k))
            tc(d, (bx, y + 4), letter, fit_font(letter, 110, fs), fade(WHITE, k))
            tc(d, (bx + 100, y + 2), word, fit_font(word, 560, 64), fade(INK, k), anchor="lm")
    elif typ == "grid":
        # up to 4 value tiles: {"tiles":[["LABEL","value","sub"], ...]}
        tiles = v["tiles"][:4]; cols = 1 if len(tiles) == 1 else 2
        rows_n = math.ceil(len(tiles) / cols); tw, th, gap = (380 if cols == 2 else 780), 230, 30
        y0 = VY - (rows_n * th + (rows_n - 1) * gap) / 2
        for i, tl in enumerate(tiles):
            lab, val, sub = (list(tl) + ["", "", ""])[:3]
            r, c = divmod(i, cols)
            in_row = min(cols, len(tiles) - r * cols)          # centre a lone tile on the last row
            x = CX - (in_row * tw + (in_row - 1) * gap) / 2 + c * (tw + gap); y = y0 + r * (th + gap)
            k = 1 if i < v.get("_seen", 0) else back((lt - (i - v.get("_seen", 0)) * 0.18) / 0.35)
            if k <= 0.05: continue
            d.rounded_rectangle([x, y, x + tw, y + th], 26, fill=BAND, outline=RULE, width=3)
            spaced(d, (x + tw / 2, y + 45), lab, fit_font(lab, tw - 40, 28), ACC, track=3)
            tc(d, (x + tw / 2, y + 122), val, fit_font(val, tw - 40, 84 * min(1, k)), INK)
            if sub: tc(d, (x + tw / 2, y + 190), sub, fit_font(sub, tw - 30, 32, "body"), MUTED)
    elif typ == "drug_card":
        # capsule + name + class + one-line mechanism: {"name","cls","line"}
        k = back(lt / 0.4); cy = VY - 150
        cw, ch = 230 * k, 90 * k
        if k > 0.05:
            d.rounded_rectangle([CX - cw, cy - ch, CX + cw, cy + ch], int(ch), fill=WHITE, outline=INK, width=6)
            d.rounded_rectangle([CX - cw, cy - ch, CX, cy + ch], int(ch), fill=ACC)
            d.rectangle([CX - ch * 0.6, cy - ch + 3, CX, cy + ch - 3], fill=ACC)
        kk = ease((lt - 0.3) / 0.4)
        tc(d, (CX, VY + 40), v["name"], fit_font(v["name"], 860, 96), fade(INK, kk))
        if v.get("cls") and kk > 0.5: pill(d, CX, VY + 145, v["cls"], "accent", size=34, anchor="m")
        if v.get("line"):
            k3 = ease((lt - 0.8) / 0.4)
            for j, ln in enumerate(wrap(v["line"], F(46, "body"), 820)[:2]):
                tc(d, (CX, VY + 240 + j * 56), ln, F(46, "body"), fade(MUTED, k3))
    elif typ == "cta":
        k = back(lt / 0.4)
        s = 95 * k
        d.rounded_rectangle([CX - s, VY - 150 - s, CX + s, VY - 150 + s], 26, fill=INK)
        if k > 0.2: med_cross(d, CX, VY - 150, 62 * k, ACC)
        a, b = CFG["wordmark"]; f = F(84)
        wa, wb = f.getlength(a), f.getlength(b); x = CX - (wa + wb) / 2
        tc(d, (x, VY + 10), a, f, INK, anchor="lm"); tc(d, (x + wa, VY + 10), b, f, ACC, anchor="lm")
        ck = CFG.get("cta_kicker", "FOLLOW FOR MORE UPDATES")
        spaced(d, (CX, VY + 90), ck, fit_font(ck, 820, 28), ACC, track=4)
        bounce = abs(math.sin(lt * 5)) * 10
        d.rounded_rectangle([CX - 230, VY + 150 - bounce, CX + 230, VY + 250 - bounce], 50, fill=ACC)
        tc(d, (CX - 25, VY + 200 - bounce), "Follow", F(56), WHITE)
        arrow(d, CX + 75, VY + 202 - bounce, 70, WHITE, width=6)
        tc(d, (CX, VY + 310), CFG["footer"][0], F(50), INK)


def fit_font(s, maxw, size, kind="head"):
    size = max(8, int(size))
    while size > 16 and F(size, kind).getlength(s) > maxw:
        size -= 3
    return F(size, kind)


# ------------------------------------------------------------ chrome
CHECKED = ""     # "Fact-checked as of …" stamp, set per episode from meta.checked_on


def checked_text(script):
    """'FACT-CHECKED AS OF 23 NOV 2026' from meta.checked_on (YYYY-MM-DD)."""
    import datetime as dt
    c = script.get("meta", {}).get("checked_on")
    return ("FACT-CHECKED AS OF " + dt.date.fromisoformat(c).strftime("%-d %b %Y").upper()) if c else ""


def header(d, chap=None):
    a, b = CFG["wordmark"]; f = F(54)
    wa, wb = f.getlength(a), f.getlength(b); x = CX - (wa + wb) / 2
    tc(d, (x, 170), a, f, INK, anchor="lm"); tc(d, (x + wa, 170), b, f, ACC, anchor="lm")
    d.line([(SAFE_L, 222), (SAFE_R, 222)], fill=RULE, width=2)
    note = " · ".join(x for x in (CFG.get("disclaimer", ""), CHECKED) if x)
    if note: tc(d, (CX, 246), note, fit_font(note, 900, 20, "body"), MUTED)
    if chap: tc(d, (SAFE_R, 264), chap, F(26, "body"), MUTED, anchor="rm")


def headline(d, text, y, lt=9.0, maxw=760, maxsize=104, minsize=64, img=None):
    """'black part|orange part' → centred two-tone headline, revealed word by word. Returns bottom y."""
    if not text: return y
    parts = text.split("|"); size = maxsize
    while True:
        f = F(size); lines = []
        for pi, ptxt in enumerate(parts):
            lines += [(ln, INK if pi == 0 else ACC) for ln in wrap(ptxt, f, maxw)]
        if len(lines) <= 2 or size <= minsize: break
        size -= 6
    lh = size * 1.04; wi = 0
    for i, (ln, col) in enumerate(lines):
        words = ln.split(" ")
        total = f.getlength(ln); x = CX - total / 2
        cy = y + lh * i + lh / 2
        for w in words:
            k = ease((lt - wi * 0.035) / 0.22)
            if k > 0:
                tc(d, (x, cy + (1 - k) * 26), w, f, fade(col, k), anchor="lm")
            x += f.getlength(w + " "); wi += 1
    return y + lh * len(lines)


def caption_groups(lines):
    groups = []
    for l in lines:
        nk = lambda w: re.sub(r"[^\w']", "", w).lower()
        ws = l["words"]; keys = {nk(k) for k in l.get("keys", [])}; i = 0
        while i < len(ws):
            n = 3 if len(ws) - i in (3, 6) or len(ws) - i > 4 else 2
            if len(ws) - i == 1: n = 1
            g = ws[i:i + n]
            groups.append({"start": g[0]["start"], "end": g[-1]["end"], "words": [w["w"] for w in g],
                           "starts": [w["start"] for w in g], "key": [nk(w["w"]) in keys for w in g]})
            i += n
    for a, b in zip(groups, groups[1:]):
        a["end"] = max(a["end"], min(b["start"], a["end"] + 0.3))
    return groups


CAP_DIM = (168, 168, 162, 255)
def draw_caption(d, g, t):
    """Karaoke captions: spoken words ink (key words orange), upcoming words light grey. No bounce."""
    f = F(96)
    words = g["words"]
    total = sum(f.getlength(w) for w in words) + f.getlength(" ") * (len(words) - 1)
    if total > 800:
        f = F(96 * 800 / total); total = 800
    a = ease((t - g["start"] + 0.02) / 0.12)
    x = CX - total / 2; y = 1430
    for w, k, ws in zip(words, g["key"], g["starts"]):
        col = (ACC if k else INK) if t >= ws - 0.03 else CAP_DIM
        d.text((x, y), w, font=f, fill=fade(col, a), anchor="lm")
        x += f.getlength(w + " ")


def section(beat):
    return beat.replace("SUB", "HOOK")


def content(li, lt, ld, sl, kickers):
    """Everything that belongs to one scene: kicker, headline, visual. Returned as a layer for transitions."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    beat = sl[li]["beat"]; v = sl[li]["visual"]
    kw = spaced(ImageDraw.Draw(Image.new("RGBA", (1, 1))), (0, 0), kickers.get(beat, ""), F(28), ACC, track=5)
    spaced(d, (CX, 290), kickers.get(beat, ""), F(32), ACC, track=5)
    d.line([(CX - kw / 2, 314), (CX - kw / 2 + kw * ease(lt / 0.3), 314)], fill=ACC, width=3)
    if v["type"] == "hero":
        # typography-only scene: one big statement, centred in the content area
        if v.get("icon") == "x": xmark(d, CX, 640, 70, lt, width=24)
        headline(d, sl[li].get("ost", ""), 760 if v.get("icon") else 680, lt, maxw=880, maxsize=160, minsize=100)
        if v.get("note"):
            k = ease((lt - 0.2) / 0.3)
            tc(d, (CX, 1180), v["note"], F(42, "body"), fade(MUTED, k))
        return layer
    headline(d, sl[li].get("ost", ""), 345, lt, maxw=860, maxsize=122)
    vis = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_visual(vis, v, lt * VIS_SPEED, ld * VIS_SPEED)
    z = VIS_SCALE * (1 + 0.04 * (lt / max(ld, .1)))      # slow push-in
    small = vis.resize((int(W * z), int(H * z)), Image.BILINEAR)
    layer.paste(small, (int(CX - CX * z), int(VY - VY * z)), small)
    return layer


TR = 0.22     # push transition (same section)
WIPE = 0.34   # bar sweep (new section)
LEAD = 0.36   # picture cuts this much BEFORE the line is spoken, so the visual is in place when the words land
VIS_SPEED = 1.7  # visual animations (counters, bars, tiles, ECG) play this much faster than their base timings
CONTENT_BOX = (0, 232, W, BAND_Y - 1)


def shifted(layer, dy, alpha):
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if alpha <= 0: return out
    if alpha < 1: layer = layer.copy(); layer.putalpha(layer.getchannel("A").point(lambda a: int(a * alpha)))
    out.paste(layer, (0, int(dy)), layer)
    return out.crop(CONTENT_BOX)


_deco = None
def bottom_deco():
    """Light brand pattern for the lower part of the frame (under YouTube/Instagram's overlay): fills the
    screen on mobile without putting anything important where the app's buttons and title sit."""
    global _deco
    if _deco is None:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
        top = 1500
        for y in range(top, H):
            a = int(255 * min(1, (y - top) / 260))
            d.line([(0, y), (W, y)], fill=TINT[:3] + (a,))
        for x in range(36, W, 72):
            for y in range(top + 60, H, 72):
                a = int(150 * min(1, (y - top) / 300))
                d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=ACC[:3] + (a // 3,))
        med_cross(d, W - 170, H - 170, 120, ACC[:3] + (24,))
        d.line([(SAFE_L, top + 10), (SAFE_R, top + 10)], fill=RULE, width=2)
        _deco = g
    return _deco


def frame(t, dur, li, lines, lt, ld, sl, kickers, groups):
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill=RULE); d.rectangle([0, 0, int(W * t / dur), 10], fill=ACC)
    img.alpha_composite(bottom_deco())
    header(d)
    newsec = li > 0 and section(sl[li]["beat"]) != section(sl[li - 1]["beat"])
    prev_lt = lambda: lines[li]["start"] - lines[li - 1]["start"]
    if li > 0 and newsec and lt < WIPE:
        # slim orange bar sweeps left→right, revealing the new section behind it
        p = ease(lt / WIPE); bw = 120
        bx = -bw + (W + 2 * bw) * p
        out_l = shifted(content(li - 1, prev_lt() + lt, prev_lt(), sl, kickers), 0, 1)
        in_l = shifted(content(li, lt, ld, sl, kickers), 0, 1)
        cut = int(max(0, min(W, bx)))
        if cut > 0: img.alpha_composite(in_l.crop((0, 0, cut, in_l.height)), (0, CONTENT_BOX[1]))
        if cut < W: img.alpha_composite(out_l.crop((cut, 0, W, out_l.height)), (cut, CONTENT_BOX[1]))
        d.rectangle([bx - bw / 2, CONTENT_BOX[1], bx + bw / 2, CONTENT_BOX[3]], fill=ACC)
    elif li > 0 and not newsec and lt < TR:
        p = lt / TR
        img.alpha_composite(shifted(content(li - 1, prev_lt() + lt, prev_lt(), sl, kickers), -60 * ease(p), 1 - ease(p / 0.45)), CONTENT_BOX[:2])
        img.alpha_composite(shifted(content(li, lt, ld, sl, kickers), 60 * (1 - ease(p)), ease((p - 0.25) / 0.75)), CONTENT_BOX[:2])
    else:
        img.alpha_composite(shifted(content(li, lt, ld, sl, kickers), 0, 1), CONTENT_BOX[:2])
    d = ImageDraw.Draw(img)
    src = sl[li].get("source")
    if src:
        k = ease((lt - 0.15) / 0.3)
        tc(d, (SAFE_L, BAND_Y + 22), f"Source: {src}", F(30, "body"), fade(MUTED, k), anchor="lm")
    for g in groups:
        if g["start"] - 0.02 <= t < g["end"]:
            draw_caption(d, g, t); break
    return img


def scene_at(lines, t):
    for i in range(len(lines)):
        if i + 1 == len(lines) or t < lines[i + 1]["start"]:
            return i


# ------------------------------------------------------------ audio: self-made music + sfx
def pluck(freq, dur_s, rng, decay=0.996):
    """Karplus–Strong plucked string."""
    n = int(dur_s * SR); p = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, p); out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = decay * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return out


def synth_audio(ep, dur, lines, sl):
    n = int(dur * SR); rng = np.random.default_rng(3)
    # music: calm 84 bpm plucked arpeggio over a soft pad, Am–F–C–G
    chords = [[220.0, 261.63, 329.63, 440.0], [174.61, 220.0, 261.63, 349.23], [196.0, 261.63, 329.63, 392.0], [196.0, 246.94, 293.66, 392.0]]
    beat = 60 / 84; bar = beat * 4; music = np.zeros(n + SR * 8)
    cache = {}
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]
        for s8 in range(8):
            f = ch[[0, 2, 1, 3, 2, 1, 3, 2][s8]]
            if f not in cache: cache[f] = pluck(f, 1.6, rng)
            s = int((ci * bar + s8 * beat / 2) * SR)
            music[s:s + len(cache[f])] += cache[f] * (0.55 if s8 % 2 else 0.8)
        s, e = int(ci * bar * SR), int((ci + 1) * bar * SR); tt = np.arange(e - s) / SR
        env = np.minimum(1, tt / 0.8) * np.minimum(1, (bar - tt) / 0.8)
        for f in ch[:3]:
            music[s:e] += 0.18 * env * np.sin(2 * np.pi * f / 2 * tt)
    music = music[:n]; music /= np.abs(music).max() + 1e-9
    fo = int(1.2 * SR); music[-fo:] *= np.linspace(1, 0, fo)
    # sfx: soft tick on scene pushes, whoosh on section wipes, impact on reveals
    sfx = np.zeros(n)
    def add(at, sig):
        s = int(at * SR); e = min(n, s + len(sig))
        if 0 <= s < n: sfx[s:e] += sig[:e - s]
    tn = np.arange(int(0.05 * SR)) / SR
    tick = np.sin(2 * np.pi * 1800 * tn) * np.exp(-tn * 120) * 0.35
    L = int(0.45 * SR); wt = np.arange(L) / SR
    noise = rng.normal(0, 1, L)
    whoosh = np.convolve(noise, np.ones(60) / 60, "same") * np.sin(np.pi * wt / 0.45) ** 2 * 1.4
    it = np.arange(int(0.7 * SR)) / SR
    impact = (np.sin(2 * np.pi * 50 * it) * np.exp(-it * 5) + rng.normal(0, 0.25, len(it)) * np.exp(-it * 30)) * 0.9
    for i, l in enumerate(lines):
        if i:
            newsec = section(sl[i]["beat"]) != section(sl[i - 1]["beat"])
            add(l["start"] - (0.05 if newsec else 0), whoosh if newsec else tick)
        v = sl[i]["visual"]
        if v["type"] == "chip_stamp": add(l["start"] + 1.2 / VIS_SPEED, impact)
        if v["type"] == "verdict" and (v.get("shown") == 1 or v.get("lines", [""])[-1] == "CONFIRMED"): add(l["start"] + 0.18, impact)
        if v["type"] == "versus" and v.get("reveal"): add(l["start"] + 0.18, impact * 0.8)
    def wav(name, x):
        x = (np.clip(x, -1, 1) * 32767).astype(np.int16)
        with wave.open(str(ep / name), "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(x.tobytes())
    wav("music.wav", music * 0.8)
    wav("sfx.wav", sfx / (np.abs(sfx).max() + 1e-9) * 0.8)


def mix(ep, dur, LN):
    # voice on top; music sits ~20 dB under and ducks further while the voice talks (sidechain)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", ep / "video_only.mp4", "-i", ep / "voice.wav",
                    "-i", ep / "music.wav", "-i", ep / "sfx.wav", "-filter_complex",
                    "[1:a]asplit=2[v][key];[2:a]volume=-15dB[m0];"
                    "[m0][key]sidechaincompress=threshold=0.02:ratio=5:attack=15:release=350[m];"
                    "[3:a]volume=-12dB[s];"
                    "[v][m][s]amix=inputs=3:normalize=0:duration=first" + LN + ",aresample=44100[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ac", "2",
                    "-t", f"{dur:.2f}", "-movflags", "+faststart", ep / "final_video.mp4"], check=True)


# ------------------------------------------------------------ cover
def make_cover(ep, script):
    c = script["cover"]
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    header(d)
    spaced(d, (SAFE_L, 400), c["kicker"], F(30), ACC, track=5, anchor="l", underline=ACC)
    y = 470
    for i, ln in enumerate(c["head"]):
        tc(d, (SAFE_L, y + 70), ln, F(140), ACC if i == len(c["head"]) - 1 else INK, anchor="lm"); y += 145
    y += 20
    for ln in wrap(c["sub"], F(40, "body"), 800):
        tc(d, (SAFE_L, y + 20), ln, F(40, "body"), MUTED, anchor="lm"); y += 54
    d.line([(SAFE_L, y + 30), (SAFE_R, y + 30)], fill=RULE, width=2)
    vis = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_visual(vis, c.get("visual", {"type": "chip_glow"}), 9.0, 9.0)
    z = 0.72; small = vis.resize((int(W * z), int(H * z)), Image.BILINEAR)
    img.paste(small, (int(CX - CX * z), int(y + 330 - VY * z)), small)
    d.line([(SAFE_L, 1650), (SAFE_R, 1650)], fill=RULE, width=2)
    tc(d, (SAFE_L, 1700), CFG["footer"][0], F(34), INK, anchor="lm")
    tc(d, (SAFE_R, 1700), CFG["footer"][1], F(30, "body"), MUTED, anchor="rm")
    img.convert("RGB").save(ep / "cover.png")


# ------------------------------------------------------------ main
def visual_timeline(lines):
    """Scene start times for the picture: each scene cuts in LEAD s before its line is spoken (never before the
    previous line's last word has started, and at least 0.4 s after the previous scene)."""
    out = [dict(lines[0], start=0.0)]
    for i in range(1, len(lines)):
        prev = lines[i - 1]
        st = lines[i]["start"] - LEAD
        st = max(st, prev["words"][-1]["start"] + 0.05, out[-1]["start"] + 0.4)
        out.append(dict(lines[i], start=min(st, lines[i]["start"])))
    return out


def mark_seen(sl):
    """When a scene repeats the previous scene's list (grid tiles, mnemonic rows) and adds to it, the items already
    on screen stay still and only the new ones animate."""
    for a, b in zip(sl, sl[1:]):
        va, vb = a["visual"], b["visual"]
        if va["type"] == vb["type"] and va["type"] in ("grid", "mnemonic"):
            key = "tiles" if va["type"] == "grid" else "items"
            n = 0
            for x, y in zip(va[key], vb[key]):
                if list(x) != list(y): break
                n += 1
            vb["_seen"] = n


def render(ep_dir, only_cover=False):
    ep = Path(ep_dir)
    script = json.loads((ep / "script.json").read_text())
    tim = json.loads((ep / "timings.json").read_text())
    sl, lines = script["lines"], tim["lines"]
    for s, l in zip(sl, lines): l["keys"] = s.get("keys", [])
    dur = tim["duration"]
    global CHECKED; CHECKED = checked_text(script)
    make_cover(ep, script)
    if only_cover: return
    groups = caption_groups(lines)          # captions follow the voice exactly
    vlines = visual_timeline(lines)         # scenes start LEAD seconds earlier
    mark_seen(sl)
    synth_audio(ep, dur, vlines, sl)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", str(ep / "video_only.mp4")], stdin=subprocess.PIPE)
    nframes = int(dur * FPS)
    for fi in range(nframes):
        t = fi / FPS; li = scene_at(vlines, t)
        start = vlines[li]["start"] if li else 0
        nxt = vlines[li + 1]["start"] if li + 1 < len(vlines) else dur
        img = frame(t, dur, li, vlines, t - start, nxt - start, sl, script.get("kickers", {}), groups)
        ff.stdin.write(img.convert("RGB").tobytes())
        if fi % 300 == 0: print(f"frame {fi}/{nframes}", flush=True)
    ff.stdin.close(); ff.wait()
    LN = ""
    for _pass in (1, 2):   # two-pass loudnorm to exactly -14 LUFS
        mix(ep, dur, LN)
        if _pass == 1:
            r = subprocess.run(["ffmpeg", "-i", ep / "final_video.mp4", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                                "-f", "null", "-"], capture_output=True, text=True).stderr
            m = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
            LN = (f",loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
                  f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    # final trim: measure integrated loudness, nudge to -14 LUFS, true-peak limit at -1.5 dBTP
    for _ in range(2):
        r = subprocess.run(["ffmpeg", "-i", ep / "final_video.mp4", "-af", "ebur128=peak=true", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        I = float(r[r.rindex("I:"):].split()[1])
        if abs(I + 14) < 0.15: break
        tmp = ep / "final_tmp.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", ep / "final_video.mp4", "-c:v", "copy",
                        "-af", f"volume={-14 - I:.2f}dB,alimiter=limit=0.84:level=false", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", tmp], check=True)
        tmp.replace(ep / "final_video.mp4")
    (ep / "video_only.mp4").unlink()
    print("wrote", ep / "final_video.mp4", f"({I:.1f} LUFS before final trim)")


if __name__ == "__main__":
    render(sys.argv[1], only_cover="--cover" in sys.argv)
