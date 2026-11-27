"""Shrink pauses > MAXP inside each vo/<id>.wav to KEEP s, then speed up with atempo (pitch kept). Originals kept in vo_raw/."""
import sys, shutil, subprocess
from pathlib import Path
import numpy as np, soundfile as sf
EP = Path(__file__).parent; TEMPO = float(sys.argv[1]); MAXP, KEEP = 0.24, 0.16
raw = EP / "vo_raw"
if not raw.exists(): shutil.copytree(EP / "vo", raw)
tot = 0
for f in sorted(raw.glob("*.wav")):
    a, sr = sf.read(f, dtype="float32")
    win = int(0.02 * sr); e = np.sqrt(np.convolve(a ** 2, np.ones(win) / win, "same"))
    quiet = e < 0.012
    out = []; i = 0; n = len(a)
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]: j += 1
            L = j - i
            if L > MAXP * sr and i > 0 and j < n:
                k = int(KEEP * sr); out.append(a[i:i + k // 2]); out.append(a[j - k // 2:j])
            else: out.append(a[i:j])
            i = j
        else:
            j = i
            while j < n and not quiet[j]: j += 1
            out.append(a[i:j]); i = j
    b = np.concatenate(out)
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", "-af", f"atempo={TEMPO}",
                        "-f", "f32le", "-ar", str(sr), "-ac", "1", "-"], input=b.tobytes(), capture_output=True)
    c = np.frombuffer(p.stdout, np.float32)
    sf.write(EP / "vo" / f.name, c, sr); tot += len(c) / sr
    print(f.stem, round(len(a) / sr, 2), "->", round(len(c) / sr, 2))
print("total", round(tot, 2))
