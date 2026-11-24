"""Read PARAVION X's public YouTube channel pages (no login, no API key) and print every
video's id, type, title, view count and link as JSON. Used by the daily tracker-sync task.

python3 stats_sync.py            -> JSON list on stdout
Likes/comments are not on the public page; they need a YouTube Data API key.
"""
import json, re, subprocess, sys

CHANNEL = "UCE0ZwrfC8ARoL5lP1vWM78Q"
UA = "Mozilla/5.0"


def page(tab):
    return subprocess.run(["curl", "-s", "-A", UA, "-H", "Accept-Language: en-US",
                           f"https://www.youtube.com/channel/{CHANNEL}/{tab}"],
                          capture_output=True, text=True).stdout


def initial_data(html):
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html)
    return json.loads(m.group(1)) if m else {}


def views_to_int(s):
    if not s: return None
    s = s.replace(",", "").split()[0]
    mult = {"K": 1e3, "M": 1e6, "B": 1e9}
    try:
        return int(float(s[:-1]) * mult[s[-1]]) if s[-1] in mult else int(float(s))
    except ValueError:
        return None


def walk(o, out, kind):
    if isinstance(o, dict):
        if "lockupViewModel" in o:
            v = o["lockupViewModel"]
            md = v.get("metadata", {}).get("lockupMetadataViewModel", {})
            parts = [p.get("text", {}).get("content") for r in md.get("metadata", {}).get("contentMetadataViewModel", {}).get("metadataRows", []) for p in r.get("metadataParts", [])]
            out.append({"id": v.get("contentId"), "type": "long", "title": md.get("title", {}).get("content"),
                        "views": views_to_int(parts[0] if parts else None), "age": parts[1] if len(parts) > 1 else "",
                        "link": f"https://youtu.be/{v.get('contentId')}"})
        if "videoRenderer" in o:
            v = o["videoRenderer"]
            out.append({"id": v["videoId"], "type": "long", "title": v["title"]["runs"][0]["text"],
                        "views": views_to_int(v.get("viewCountText", {}).get("simpleText")),
                        "age": v.get("publishedTimeText", {}).get("simpleText", ""), "link": f"https://youtu.be/{v['videoId']}"})
        if "shortsLockupViewModel" in o:
            v = o["shortsLockupViewModel"]
            vid = v.get("onTap", {}).get("innertubeCommand", {}).get("reelWatchEndpoint", {}).get("videoId")
            om = v.get("overlayMetadata", {})
            out.append({"id": vid, "type": "short", "title": om.get("primaryText", {}).get("content"),
                        "views": views_to_int(om.get("secondaryText", {}).get("content")), "age": "",
                        "link": f"https://youtube.com/shorts/{vid}"})
        for x in o.values(): walk(x, out, kind)
    elif isinstance(o, list):
        for x in o: walk(x, out, kind)


def main():
    out = []
    for tab in ("videos", "shorts"):
        walk(initial_data(page(tab)), out, tab)
    seen, uniq = set(), []
    for v in out:
        if v["id"] and v["id"] not in seen:
            seen.add(v["id"]); uniq.append(v)
    json.dump(uniq, sys.stdout, indent=1, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
