"""Brand kit for PARAVION MED, drawn in code from config.json (no stock art). Run from medical/: python3 brand/make_brand.py
Writes: logo_800.png, youtube_banner_2560x1440.png, profile_800.png (YouTube/Instagram/X avatar), x_header_1500x500.png
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text()); T = CFG["theme"]
hx = lambda c: tuple(int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
INK, ACC, BG, MUTED, TINT = hx(T["ink"]), hx(T["accent"]), hx(T["bg"]), hx(T["muted"]), hx(T["tint"])
F = lambda s, w="head": ImageFont.truetype(str(ROOT / CFG["font_" + w]), s)
OUT = ROOT / "brand"


def cross(d, cx, cy, r, col):
    t = r * 0.36
    d.rounded_rectangle([cx - t, cy - r, cx + t, cy + r], int(t * 0.45), fill=col)
    d.rounded_rectangle([cx - r, cy - t, cx + r, cy + t], int(t * 0.45), fill=col)


def ecg(d, x0, x1, y, amp, col, w):
    pts, n = [], 400
    import math
    for i in range(n):
        u = i / (n - 1); ph = (u * 3) % 1
        g = lambda mu, s, a: a * math.exp(-((ph - mu) / s) ** 2)
        v = g(0.16, 0.035, 0.12) + g(0.30, 0.008, -0.12) + g(0.32, 0.012, 1.0) + g(0.345, 0.01, -0.25) + g(0.55, 0.05, 0.25)
        pts.append((x0 + (x1 - x0) * u, y - amp * v))
    d.line(pts, fill=col, width=w, joint="curve")


def mark(size, bg=INK):
    im = Image.new("RGB", (size, size), bg); d = ImageDraw.Draw(im)
    cross(d, size / 2, size / 2, size * 0.30, ACC)
    return im


def wordmark(d, cx, cy, size, a_col=INK):
    a, b = CFG["wordmark"]; f = F(size)
    wa, wb = f.getlength(a), f.getlength(b); x = cx - (wa + wb) / 2
    d.text((x, cy), a, font=f, fill=a_col, anchor="lm"); d.text((x + wa, cy), b, font=f, fill=ACC, anchor="lm")


# logo: mark + wordmark on white
logo = Image.new("RGB", (800, 800), BG); d = ImageDraw.Draw(logo)
logo.paste(mark(360), (220, 120)); wordmark(d, 400, 590, 92)
d.text((400, 680), CFG["tagline"], font=F(34, "body"), fill=MUTED, anchor="mm")
logo.save(OUT / "logo_800.png")

# avatar: rounded-safe (circle crop on all platforms keeps the cross)
mark(800).save(OUT / "profile_800.png")

# YouTube banner: content inside the 1546x423 centre safe area
W, H = 2560, 1440
b = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(b)
d.rectangle([0, 1000, W, H], fill=TINT)
ecg(d, 0, W, 1080, 110, ACC, 8)                     # below the 423 px-tall centre safe area (y 508-931)
fw = F(150); ww = fw.getlength(CFG["wordmark"][0] + CFG["wordmark"][1]); cx = W / 2 + 70
cross(d, cx - ww / 2 - 110, H / 2 - 90, 62, ACC)
wordmark(d, cx, H / 2 - 90, 150)
d.text((W / 2, H / 2 + 35), "Medical news + high-yield medicine, explained in 60 seconds", font=F(46, "body"), fill=MUTED, anchor="mm")
d.text((W / 2, H / 2 + 115), "NEW SHORTS DAILY  ·  1 PM + 7:30 PM IST", font=F(36), fill=ACC, anchor="mm")
b.save(OUT / "youtube_banner_2560x1440.png")

# X header
x = Image.new("RGB", (1500, 500), BG); d = ImageDraw.Draw(x)
d.rectangle([0, 330, 1500, 500], fill=TINT); ecg(d, 0, 1500, 400, 120, ACC, 6)
wordmark(d, 860, 170, 96)
d.text((860, 260), "Medicine, explained in 60 seconds.", font=F(40, "body"), fill=MUTED, anchor="mm")
x.save(OUT / "x_header_1500x500.png")
print("wrote brand kit to", OUT)
