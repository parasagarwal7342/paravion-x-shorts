"""QA: transcribe voice.wav with Whisper and diff against the script, to catch mispronounced words."""
import difflib, json, re, sys, wave
import numpy as np
from faster_whisper import WhisperModel

ep = sys.argv[1]
w = wave.open(f"{ep}/voice.wav")
a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
x = np.linspace(0, len(a) - 1, int(len(a) * 16000 / w.getframerate()))
a = np.interp(x, np.arange(len(a)), a).astype(np.float32)
segs, _ = WhisperModel("small.en", device="cpu", compute_type="int8").transcribe(a, beam_size=5)
heard = " ".join(s.text.strip() for s in segs)
script = " ".join(l["text"] for l in json.load(open(f"{ep}/script.json"))["lines"])
from qa_text import norm
h = norm(heard).split(); s = norm(script).split()
bad = [(" ".join(s[i1:i2]), " ".join(h[j1:j2])) for op, i1, i2, j1, j2 in
       difflib.SequenceMatcher(None, s, h).get_opcodes() if op != "equal"]
print("HEARD:", heard)
print("MISMATCHES:", bad if bad else "none")
