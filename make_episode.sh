#!/usr/bin/env bash
# One episode, end to end: voice -> pronunciation QA -> render -> publishing package.
set -euo pipefail
cd "$(dirname "$0")"
ep="$1"
echo "=== $ep"
if [ -z "${FORCE:-}" ] && [ -f "$ep/final_video.mp4" ] && [ "$ep/final_video.mp4" -nt "$ep/script.json" ] && [ "$ep/final_video.mp4" -nt render.py ]; then
  echo "up to date, skipping"; exit 0
fi
# episodes with a paid ElevenLabs take always reuse it (never fall back to the preview voice)
if [ -f "$ep/eleven_take.json" ]; then export ELEVENLABS_API_KEY=proxy-injected ELEVENLABS_VOICE_ID="${ELEVENLABS_VOICE_ID:-onwK4e9ZLuTAKqWW03F9}"; fi
if [ ! -f "$ep/timings.json" ] || [ "$ep/script.json" -nt "$ep/timings.json" ] || [ -n "${REVOICE:-}" ]; then
  python3 voice.py "$ep"
  python3 transcribe_check.py "$ep" 2>/dev/null | grep MISMATCH | tee "$ep/voice_qa.txt"
fi
python3 render.py "$ep"
python3 package.py "$ep"
