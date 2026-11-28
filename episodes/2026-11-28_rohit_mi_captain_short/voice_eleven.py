"""One ElevenLabs take (voice Daniel) for the whole script, split into vo/<id>.wav per segment.
The raw take is cached in eleven_take.json so re-runs never re-charge. Key comes from the environment only."""
import base64, json, os, subprocess, urllib.request
from pathlib import Path
import numpy as np, soundfile as sf
EP = Path(__file__).parent; S = json.loads((EP / "script.json").read_text())["segments"]
VID = "onwK4e9ZLuTAKqWW03F9"
SEP = " "
text = SEP.join(s["text"] for s in S)
cache = EP / "eleven_take.json"
if cache.exists() and json.loads(cache.read_text()).get("text") == text:
    data = json.loads(cache.read_text())
else:
    body = json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                       "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True}}).encode()
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VID}/with-timestamps?output_format=mp3_44100_128",
                                 data=body, headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r: data = json.load(r)
    data["text"] = text
    cache.write_text(json.dumps(data))
mp3 = EP / "voice_raw.mp3"; mp3.write_bytes(base64.b64decode(data["audio_base64"]))
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-f", "f32le", "-ac", "1", "-ar", "44100", "-"], capture_output=True).stdout
a = np.frombuffer(pcm, np.float32); SR = 44100
al = data["alignment"]; st, en = al["character_start_times_seconds"], al["character_end_times_seconds"]
pos = 0; bounds = []
for s in S:
    i0 = pos; i1 = pos + len(s["text"]) - 1
    bounds.append((st[i0], en[i1])); pos = i1 + 1 + len(SEP)
(EP / "vo").mkdir(exist_ok=True)
for k, s in enumerate(S):
    t0 = bounds[k][0] if k == 0 else (bounds[k - 1][1] + bounds[k][0]) / 2
    t1 = bounds[k][1] + 0.12 if k + 1 == len(S) else (bounds[k][1] + bounds[k + 1][0]) / 2
    t0 = max(t0, bounds[k][0] - 0.08); t1 = min(t1, bounds[k][1] + 0.15)
    seg = a[int(t0 * SR):int(t1 * SR)].copy()
    f = int(0.01 * SR); seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
    sf.write(EP / "vo" / f"{s['id']}.wav", seg, SR)
    print(s["id"], round(len(seg) / SR, 2))
print("total voice", round(len(a) / SR, 2), "chars", len(text))
