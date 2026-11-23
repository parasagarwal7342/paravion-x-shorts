#!/usr/bin/env bash
# One long-form Deep Dive, end to end: medical check -> licensed images -> voice -> Whisper QA -> cinematic render -> package.
#   ./make_long.sh episodes/<slug>
# With ElevenLabs: ELEVENLABS_API_KEY=proxy-injected ELEVENLABS_VOICE_ID=<id> ./make_long.sh episodes/<slug>
# (a 7-minute episode uses about 5,000-6,000 ElevenLabs characters; the paid take is saved and reused).
set -euo pipefail
cd "$(dirname "$0")"
ep="${1%/}"
python3 medcheck.py "$ep" || { echo "medical check failed: fix script.json first"; exit 1; }
python3 media.py "$ep"
if [ -f "$ep/eleven_take.json" ]; then export ELEVENLABS_API_KEY=proxy-injected ELEVENLABS_VOICE_ID="${ELEVENLABS_VOICE_ID:-onwK4e9ZLuTAKqWW03F9}"; fi
if [ ! -f "$ep/timings.json" ] || [ "$ep/script.json" -nt "$ep/timings.json" ] || [ -n "${REVOICE:-}" ]; then
  python3 voice.py "$ep"
  python3 transcribe_check.py "$ep" 2>/dev/null | grep MISMATCH | tee "$ep/voice_qa.txt"
fi
python3 longform.py "$ep"
python3 package_long.py "$ep"
python3 medcheck.py "$ep"
