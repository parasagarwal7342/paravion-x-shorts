"""Episode wrapper around the PARAVION X vertical renderer (longform_vertical settings).
Adds: fully-opaque hook text at frame 1, mid-video FOLLOW pop-up, verdict card moved below the top safe zone."""
import sys
sys.path.insert(0, "/workspace/paravion-x-shorts")
import longform as L
from PIL import ImageDraw
L.W, L.H = 1080, 1920
L.BAR = 0; L.PAD_AFTER = 0.3; L.TXT = 1.4; L.TITLE_Y = 760; L.CAP_Y = 1300

_bt = L.big_title
def big_title(d, seg, lt, cy=None):
    if seg["id"].startswith("hook"): lt = lt + 1.0     # full hook text at t=0.0
    return _bt(d, seg, lt, cy)
L.big_title = big_title

CTA = (0.44, 0.54)   # fraction of runtime
_fin = L.finish
def finish(a, t, grain=True):
    im = _fin(a, t, grain)
    T = L.TOTAL or 1
    s, e = CTA[0] * T, CTA[1] * T
    if s <= t <= e:
        k = L.ease((t - s) / 0.25) * L.ease((e - t) / 0.25)
        d = ImageDraw.Draw(im, "RGBA")
        y = 300; txt = "FOLLOW  ·  PART 2 WHEN THE DEAL LANDS"
        f = L.fit_font(txt, 820, 38, "head"); tw = f.getlength(txt)
        x0 = L.W / 2 - tw / 2 - 34; x1 = L.W / 2 + tw / 2 + 34
        dy = (1 - k) * -40
        d.rounded_rectangle([x0, y - 44 + dy, x1, y + 44 + dy], radius=44, fill=L.ACC + (int(245 * k),))
        d.text((L.W / 2, y + dy), txt, font=f, fill=(255, 255, 255, int(255 * k)), anchor="mm")
    return im
L.finish = finish

def verdict_card(d, seg, lt):
    W = L.W; a = L.ease(lt / 0.5); off = 330
    L.spaced(d, (W / 2, 220 + off), "FAKE OR FACT?", L.F(40, "body"), L.ACC + (int(255 * a),), track=10)
    f = L.F(76); lines = L.wrap(seg["claim"], f, W - 160)
    y = 380 + off
    for i, ln in enumerate(lines):
        d.text((W / 2, y + i * 92), ln, font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm")
    tv = seg.get("_tv", 2.0); s = lt - tv
    if s > 0:
        k = L.ease(s / 0.25); sc = 1.6 - 0.6 * k
        col = L.GREEN if seg["verdict"] == "FACT" else (L.RED if seg["verdict"] == "FAKE" else (232, 150, 20))
        fs = L.F(int(170 * sc)); txt = seg["verdict"]
        tw = fs.getlength(txt); cy = y + len(lines) * 92 + 150
        d.rounded_rectangle([W / 2 - tw / 2 - 40, cy - 105 * sc, W / 2 + tw / 2 + 40, cy + 105 * sc], radius=18,
                            outline=col + (int(255 * k),), width=int(10 * sc), fill=(0, 0, 0, int(120 * k)))
        d.text((W / 2, cy), txt, font=fs, fill=col + (int(255 * k),), anchor="mm")
        a3 = L.ease((s - 0.4) / 0.5)
        L.spaced(d, (W / 2, cy + 175), seg["why"], L.fit_font(seg["why"], W - 120, 34, "body"), (235, 235, 235, int(255 * a3)), track=3)
L.verdict_card = verdict_card

if __name__ == "__main__":
    L.main(sys.argv[1])
