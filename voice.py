"""Agent 6 — Voice Producer.

Uses ElevenLabs /with-timestamps when ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID are set.
Otherwise falls back to a local Piper voice (PREVIEW ONLY — replace before posting).

Output (in the episode dir): voice.wav, voice.mp3, timings.json
timings.json = {"engine": ..., "duration": s, "lines": [{"start","end","words":[{"w","start","end"}]}]}
"""
import base64, json, os, re, subprocess, sys, wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
SR = 44100
GAP = 0.13          # silence between lines (s)
ELLIPSIS_PAUSE = 0.38


def words_of(text):
    return text.split()


# ---------------------------------------------------------------- ElevenLabs
def elevenlabs(lines, cfg):
    import urllib.request
    key, vid = os.environ["ELEVENLABS_API_KEY"], os.environ["ELEVENLABS_VOICE_ID"]
    text = " ".join(l["text"] for l in lines)
    body = json.dumps({"text": text, "model_id": cfg["elevenlabs"]["model_id"],
                       "voice_settings": cfg["elevenlabs"]["voice_settings"]}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{vid}/with-timestamps?output_format=mp3_44100_128",
        data=body, headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.load(r)
    mp3 = base64.b64decode(data["audio_base64"])
    al = data["alignment"]
    chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    # rebuild word timings from character alignment
    words, cur, ws = [], "", None
    for c, s, e in zip(chars, st, en):
        if c.isspace():
            if cur:
                words.append({"w": cur, "start": ws, "end": prev_e}); cur = ""
            continue
        if not cur:
            ws = s
        cur += c; prev_e = e
    if cur:
        words.append({"w": cur, "start": ws, "end": prev_e})
    out, i = [], 0
    for l in lines:
        n = len(words_of(l["text"]))
        lw = words[i:i + n]; i += n
        out.append({"start": lw[0]["start"], "end": lw[-1]["end"], "words": lw})
    return mp3, out, "elevenlabs"


# ---------------------------------------------------------------- Piper fallback
def piper_say(voice, syn, text):
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        voice.synthesize_wav(text, wf, syn_config=syn)
    buf.seek(0)
    with wave.open(buf, "rb") as wf:
        sr = wf.getframerate()
        a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    # trim leading/trailing silence
    nz = np.where(np.abs(a) > 0.01)[0]
    if len(nz):
        a = a[max(0, nz[0] - int(0.07 * sr)): nz[-1] + int(0.04 * sr)]
    # resample to SR (linear is fine for speech preview)
    if sr != SR:
        x = np.linspace(0, len(a) - 1, int(len(a) * SR / sr))
        a = np.interp(x, np.arange(len(a)), a)
    return a


PIPER_SAY = {}   # filled from config.json fallback_tts.say


def for_piper(t):
    out = []
    for w in t.split():
        core = re.sub(r"[^\w.'-]", "", w)
        if w in PIPER_SAY: w = PIPER_SAY[w]
        elif core in PIPER_SAY: w = w.replace(core, PIPER_SAY[core])
        elif w.isupper() and len(re.sub(r"\W", "", w)) > 2: w = w.lower()   # emphasis caps → normal word
        out.append(w)
    return " ".join(out)


# ---------------------------------------------------------------- take selection (QA)
_whisper = None
from qa_text import norm as _norm


def take_score(a, target):
    """Transcribe a take with Whisper and return similarity (0–1) to the intended words."""
    global _whisper
    import difflib
    if _whisper is None:
        from faster_whisper import WhisperModel
        _whisper = WhisperModel("small.en", device="cpu", compute_type="int8")
    x = np.linspace(0, len(a) - 1, int(len(a) * 16000 / SR))
    a16 = np.interp(x, np.arange(len(a)), a).astype(np.float32)
    heard = " ".join(s.text for s in _whisper.transcribe(a16, beam_size=5)[0])
    return difflib.SequenceMatcher(None, _norm(target).split(), _norm(heard).split()).ratio(), heard


def best_take(voice, syn, text, takes=5):
    best = (-1, None, "")
    for i in range(takes):
        a = piper_say(voice, syn, for_piper(text))
        sc, heard = take_score(a, text)
        if sc > best[0]: best = (sc, a, heard)
        if sc >= 0.999: break
    if best[0] < 0.999:
        print(f"  best of {takes} takes {best[0]:.2f}: '{text}' heard as '{best[2].strip()}'")
    return best[1]


# ---------------------------------------------------------------- per-line voice cache
# Each spoken line is stored once (keyed by text + voice settings), so editing one line only
# re-records that line, and lines shared across episodes (intro, teaser, CTA) are reused.
CACHE = ROOT / "assets" / "voice_cache"


def cache_key(text, cfg):
    import hashlib
    f = cfg["fallback_tts"]
    blob = json.dumps([text, f["piper_model"], f["length_scale"], f.get("noise_scale"), f.get("say", {})], sort_keys=True)
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def load_line(key):
    p = CACHE / f"{key}.npz"
    if not p.exists(): return None
    z = np.load(p, allow_pickle=False)
    rel = [{"w": w, "start": float(a), "end": float(b)} for w, a, b in zip(z["w"], z["s"], z["e"])]
    return z["a"].astype(np.float32), rel


def save_line(key, a, rel):
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE / f"{key}.npz", a=a.astype(np.float32), w=np.array([r["w"] for r in rel]),
                        s=np.array([r["start"] for r in rel]), e=np.array([r["end"] for r in rel]))


def synth_line(voice, syn, text):
    """Synthesise one script line (best take per part, pause at '…'). Returns audio and word timings relative to 0."""
    parts = text.split("…")
    if len(parts) == 2 and len(parts[1].split()) <= 2:
        parts = [parts[0] + ", " + parts[1]]
    seg_audio, seg_spans = [], []
    for pi, p in enumerate(parts):
        if not p.strip():
            continue
        a = best_take(voice, syn, p.strip())
        seg_spans.append((p.strip(), sum(len(x) for x in seg_audio) / SR, len(a) / SR))
        seg_audio.append(a)
        if pi < len(parts) - 1:
            seg_audio.append(np.zeros(int(ELLIPSIS_PAUSE * SR), np.float32))
    a = np.concatenate(seg_audio)
    rel, src = [], words_of(text)
    for txt, s0, d in seg_spans:
        ws = txt.split(); tot = sum(len(w) + 1 for w in ws); acc = 0
        for w in ws:
            ww = len(w) + 1
            rel.append({"start": s0 + d * acc / tot, "end": s0 + d * (acc + ww) / tot}); acc += ww
    for w, sw in zip(rel, src):
        w["w"] = sw
    return a, rel


def seed_cache(ep):
    """Fill the cache from an episode's existing preview voice.wav + timings.json (no re-recording)."""
    ep = Path(ep); cfg = json.loads((ROOT / "config.json").read_text())
    tim = json.loads((ep / "timings.json").read_text())
    if tim.get("engine") != "piper-preview": return 0
    lines = json.loads((ep / "script.json").read_text())["lines"]
    with wave.open(str(ep / "voice.wav")) as wf:
        pcm = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
    n = 0
    for l, tl in zip(lines, tim["lines"]):
        if [w["w"] for w in tl["words"]] != words_of(l["text"]): continue   # text changed since recording
        key = cache_key(l["text"], cfg)
        if (CACHE / f"{key}.npz").exists(): continue
        a = pcm[int(round(tl["start"] * SR)): int(round(tl["end"] * SR))]
        save_line(key, a, [{"w": w["w"], "start": w["start"] - tl["start"], "end": w["end"] - tl["start"]} for w in tl["words"]])
        n += 1
    return n


def piper(lines, cfg):
    from piper import PiperVoice, SynthesisConfig
    PIPER_SAY.update(cfg["fallback_tts"].get("say", {}))
    voice = PiperVoice.load(str(ROOT / cfg["fallback_tts"]["piper_model"]))
    syn = SynthesisConfig(length_scale=cfg["fallback_tts"]["length_scale"], noise_scale=cfg["fallback_tts"].get("noise_scale"))
    audio, t, out = [], 0.0, []
    for l in lines:
        key = cache_key(l["text"], cfg)
        hit = load_line(key)
        if hit is None:
            a, rel = synth_line(voice, syn, l["text"])
            save_line(key, a, rel)
        else:
            a, rel = hit
        words = [{"w": w["w"], "start": t + w["start"], "end": t + w["end"]} for w in rel]
        out.append({"start": t, "end": t + len(a) / SR, "words": words})
        audio += [a, np.zeros(int(GAP * SR), np.float32)]
        t += len(a) / SR + GAP
    pcm = (np.clip(np.concatenate(audio), -1, 1) * 32767).astype(np.int16)
    return pcm, out, "piper-preview"


# ---------------------------------------------------------------- post-edit for slow voices
def tighten(ep, tl, cfg):
    """Shorten long pauses to max_gap and apply a gentle tempo (<=1.1x, pitch kept). Updates word timings."""
    e = cfg["elevenlabs"]; max_gap = e.get("max_gap", 0.3); tempo = e.get("tempo", 1.0)
    with wave.open(str(ep / "voice.wav")) as wf:
        sr = wf.getframerate(); a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16)
    words = [w for l in tl for w in l["words"]]
    keep, cuts, prev_end = [], [], 0.0      # cuts: (time, seconds removed before it)
    removed = 0.0; pieces = []; cursor = 0
    for w in words:
        gap = w["start"] - prev_end
        if gap > max_gap:
            cut_from = prev_end + max_gap / 2; cut_to = w["start"] - max_gap / 2
            pieces.append(a[cursor:int(cut_from * sr)]); cursor = int(cut_to * sr)
            removed += cut_to - cut_from
        w["start"] -= removed; w["end"] -= removed
        prev_end = w["end"] + removed
    pieces.append(a[cursor:])
    out = np.concatenate(pieces)
    with wave.open(str(ep / "voice_tight.wav"), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(out.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", ep / "voice_tight.wav", "-af", f"atempo={tempo}",
                    "-ar", str(SR), "-ac", "1", ep / "voice.wav"], check=True)
    (ep / "voice_tight.wav").unlink()
    for l in tl:
        for w in l["words"]:
            w["start"] /= tempo; w["end"] /= tempo
        l["start"], l["end"] = l["words"][0]["start"], l["words"][-1]["end"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", ep / "voice.wav", "-b:a", "128k", ep / "voice.mp3"], check=True)
    return tl


def main(ep_dir):
    ep = Path(ep_dir)
    cfg = json.loads((ROOT / "config.json").read_text())
    lines = json.loads((ep / "script.json").read_text())["lines"]
    if os.environ.get("ELEVENLABS_API_KEY") and os.environ.get("ELEVENLABS_VOICE_ID"):
        import hashlib, copy
        e = cfg["elevenlabs"]
        take_key = hashlib.sha1(json.dumps([[l["text"] for l in lines], os.environ["ELEVENLABS_VOICE_ID"], e["model_id"],
                                            e["voice_settings"]], sort_keys=True).encode()).hexdigest()
        tk = ep / "eleven_take.json"
        subset = None
        if (ep / "voice_raw.mp3").exists() and tk.exists():
            saved = json.loads(tk.read_text())
            if saved["key"] != take_key:      # script lines removed since the take? slice them out, free
                said = [[w["w"] for w in l["words"]] for l in saved["lines"]]
                idx, j = [], 0
                for l in lines:
                    while j < len(said) and said[j] != words_of(l["text"]): j += 1
                    if j == len(said): idx = None; break
                    idx.append(j); j += 1
                subset = idx
        if (ep / "voice_raw.mp3").exists() and tk.exists() and (json.loads(tk.read_text())["key"] == take_key or subset):
            saved = json.loads(tk.read_text()); engine = "elevenlabs"
            print("reusing saved ElevenLabs take (no credits used)" + (f", keeping {len(subset)}/{len(saved['lines'])} lines" if subset else ""))
            tl = saved["lines"] if not subset else [saved["lines"][i] for i in subset]
        else:
            mp3, tl, engine = elevenlabs(lines, cfg)
            (ep / "voice_raw.mp3").write_bytes(mp3)       # keep the paid take, so re-editing never costs credits
            tk.write_text(json.dumps({"key": take_key, "lines": tl}))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", ep / "voice_raw.mp3", "-ar", str(SR), "-ac", "1", ep / "voice.wav"], check=True)
        tl = copy.deepcopy(tl)
        if subset:
            with wave.open(str(ep / "voice.wav")) as wf:
                a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16)
            segs, t = [], 0.0
            for l in tl:
                s0, s1 = max(0, l["start"] - 0.05), l["end"] + 0.12
                segs.append(a[int(s0 * SR):int(s1 * SR)]); segs.append(np.zeros(int(0.22 * SR), np.int16))
                off = t - s0
                for w in l["words"]: w["start"] += off; w["end"] += off
                t += (s1 - s0) + 0.22
            with wave.open(str(ep / "voice.wav"), "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(np.concatenate(segs).tobytes())
        tl = tighten(ep, tl, cfg)
    else:
        print("ELEVENLABS_API_KEY/VOICE_ID not set -> Piper PREVIEW voice (not for posting)")
        pcm, tl, engine = piper(lines, cfg)
        with wave.open(str(ep / "voice.wav"), "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", ep / "voice.wav", "-b:a", "128k", ep / "voice.mp3"], check=True)
    dur = tl[-1]["end"] + 0.4
    nwords = sum(len(l["words"]) for l in tl)
    wpm = nwords / (tl[-1]["end"] / 60)
    (ep / "timings.json").write_text(json.dumps({"engine": engine, "duration": dur, "wpm": round(wpm), "lines": tl}, indent=1))
    print(f"engine={engine} duration={dur:.1f}s words={nwords} pace={wpm:.0f} wpm")
    if dur > 59.5:
        print("OVER 60s — ask Agent 5 to cut words (do not speed voice above 1.1x)"); sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1])
