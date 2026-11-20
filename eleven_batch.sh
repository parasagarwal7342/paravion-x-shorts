#!/usr/bin/env bash
# Re-voice episodes with ElevenLabs in the order given, while credits last. Saved takes are reused (free).
cd "$(dirname "$0")"
export ELEVENLABS_API_KEY=proxy-injected ELEVENLABS_VOICE_ID="${ELEVENLABS_VOICE_ID:-onwK4e9ZLuTAKqWW03F9}"
for ep in "$@"; do
  ep="${ep%/}"
  need=$(python3 -c "import json;print(sum(len(l['text'])+1 for l in json.load(open('$ep/script.json'))['lines']))")
  left=$(curl -s -H "xi-api-key: proxy-injected" https://api.elevenlabs.io/v1/user/subscription | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['character_limit']-d['character_count'])")
  if [ ! -f "$ep/eleven_take.json" ] && [ "$need" -gt "$left" ]; then echo "STOP: $ep needs $need chars, $left left"; break; fi
  echo "=== $ep (needs $need, $left left)"
  python3 voice.py "$ep" 2>&1 | grep -E "engine=|OVER|reusing|Error" || { echo "FAILED voice $ep"; continue; }
  python3 transcribe_check.py "$ep" 2>/dev/null | grep MISMATCH | tee "$ep/voice_qa.txt"
  FORCE=1 ./make_episode.sh "$ep" 2>&1 | grep -E "wrote .*mp4|FAILED|Error"
done
