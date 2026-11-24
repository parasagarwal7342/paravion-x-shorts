import json, sys, soundfile as sf, numpy as np, os, re
from kokoro_onnx import Kokoro
K = os.environ.get("KOKORO_DIR", "assets/kokoro/")
k = Kokoro(K+"kokoro-v1.0.onnx", K+"voices-v1.0.bin")
EP = sys.argv[1]; voice = sys.argv[2]; speed = float(sys.argv[3]); only = sys.argv[4:] 
S = json.load(open(os.path.join(EP, "script.json")))
SAY = {"Paravion":"Para-vee-on","CEO":"C-E-O","Kress":"Kress","Leonida":"Lee-oh-nee-dah","Caminos":"Kah-mee-nos","Duval":"Doo-vahl","Zelnick":"Zel-nick","Houser":"House-er"}
os.makedirs(os.path.join(EP, "vo"), exist_ok=True)
for s in S["segments"]:
    if only and s["id"] not in only: continue
    t = s["text"]
    for a,b in SAY.items(): t = re.sub(r"\b%s\b"%re.escape(a), b, t)
    a, sr = k.create(t, voice=voice, speed=speed, lang="en-gb" if voice.startswith("b") else "en-us")
    sf.write(os.path.join(EP, "vo") + f"/{s['id']}.wav", a, sr); print(s["id"], round(len(a)/sr,1))
