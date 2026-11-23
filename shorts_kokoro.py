"""Free Kokoro narration for a Short when ElevenLabs credits run out: writes voice.wav/voice.mp3 + timings.json
(engine=kokoro) in the format render.py expects. python3 shorts_kokoro.py episodes/<slug> [voice] [speed]"""
import json, re, subprocess, sys, wave
from pathlib import Path
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
import longform
ROOT = Path(__file__).parent; SR = 44100
ep = Path(sys.argv[1]); voice = sys.argv[2] if len(sys.argv) > 2 else "af_heart"; speed = float(sys.argv[3]) if len(sys.argv) > 3 else 1.1
import os
K = os.environ.get("KOKORO_DIR", str(ROOT / "assets/kokoro")) + "/"
k = Kokoro(K + "kokoro-v1.0.onnx", K + "voices-v1.0.bin")
SAY = {"Paravion": "Para-vee-on", "CEO": "C-E-O", "CEO.": "C-E-O.", "Nvidia's": "En-vidia's", "Nvidia": "En-vidia"}
from faster_whisper import WhisperModel
model = WhisperModel("small.en", compute_type="int8")
lines = json.loads((ep / "script.json").read_text())["lines"]
pcm, tl, t, gap = [], [], 0.0, 0.22
tmp = ep / "_line.wav"
for l in lines:
    s = l["text"]
    for a, b in SAY.items(): s = re.sub(r"(?<![\w-])%s(?![\w'])" % re.escape(a), b, s)
    a, sr = k.create(s, voice=voice, speed=speed, lang="en-us")
    a = np.interp(np.linspace(0, len(a) - 1, int(len(a) * SR / sr)), np.arange(len(a)), a).astype(np.float32)
    sf.write(tmp, a, SR)
    ws = longform.align(l["text"], tmp, model)
    words = [{"w": w, "start": t + s0, "end": t + e0} for w, s0, e0 in ws]
    tl.append({"start": words[0]["start"], "end": words[-1]["end"], "words": words})
    pcm += [a, np.zeros(int(gap * SR), np.float32)]; t += len(a) / SR + gap
tmp.unlink()
a = np.concatenate(pcm); a = (np.clip(a / max(1e-6, np.abs(a).max()) * 0.9, -1, 1) * 32767).astype(np.int16)
with wave.open(str(ep / "voice.wav"), "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(a.tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", ep / "voice.wav", "-b:a", "128k", ep / "voice.mp3"], check=True)
dur = tl[-1]["end"] + 0.4; n = sum(len(l["words"]) for l in tl)
(ep / "timings.json").write_text(json.dumps({"engine": "kokoro", "duration": dur, "wpm": round(n / (tl[-1]["end"] / 60)), "lines": tl}, indent=1))
print(f"engine=kokoro duration={dur:.1f}s words={n}")
