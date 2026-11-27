"""Download Wikimedia Commons photos (CC/PD only) into ./img with credits in img/meta.json."""
import json, re, sys, time, urllib.request, urllib.parse
from pathlib import Path
D = Path(__file__).parent / "img"; UA = {"User-Agent": "ParavionX/1.0 (news explainer; contact via YouTube @PARAVION_X)"}
OK = re.compile(r"^(CC BY(-SA)? [0-9.]+|CC0|Public domain|PD)", re.I)
PICKS = {
 "dualsense": "File:DualSense Wireless Controller Cobalt Blue.jpg",
 "dualsense_sticks": "File:Playstation 5 DualSense controller in Midnight Black, 2026-02-07 (detail of joysticks).jpg",
 "ps5": "File:PlayStation 5 and DualSense (2).jpg",
 "rockstar_north": "File:20231022 Rockstar North.jpg",
 "rockstar_north2": "File:Studios Rockstar North Édimbourg 1.jpg",
 "sec_hq": "File:Facade of the U.S. Securities and Exchange Commission headquarters, Washington, D.C.jpg",
 "phone_man": "File:Man smoking and using a smartphone outside Hôtel-Dieu de Lyon (numbers 20 to 23), Lyon, France julesvernex2.jpg",
 "gamer": "File:Man playing a fighting game 2023-09-08.jpg",
 "child_console": "File:Child playing with video game console at home closeup.jpg",
 "crowd": "File:Crowd at Gamescom 2015 (19807068384).jpg",
 "datacenter": "File:BalticServers data center.jpg",
 "miami_night": "File:Night Panorama Miami Florida 5462.jpg",
}
def api(**p):
    p.update(format="json")
    for i in range(6):
        try: return json.load(urllib.request.urlopen(urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p), headers=UA), timeout=40))
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(6 * (i + 1))
meta = json.loads((D / "meta.json").read_text()) if (D / "meta.json").exists() else {}
for key, title in PICKS.items():
    if (D / f"{key}.jpg").exists(): continue
    q = api(action="query", titles=title, prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=3000)
    pg = next(iter(q["query"]["pages"].values())); ii = pg["imageinfo"][0]; m = ii.get("extmetadata", {})
    g = lambda k: re.sub("<[^>]+>", "", m.get(k, {}).get("value", "")).strip()
    lic = g("LicenseShortName"); assert OK.match(lic), (key, lic)
    url = ii.get("thumburl") or ii["url"]
    for i in range(6):
        try: data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read(); break
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(8 * (i + 1))
    (D / f"{key}.jpg").write_bytes(data)
    meta[key] = {"title": pg["title"], "artist": g("Artist")[:90], "license": lic, "page": ii.get("descriptionurl")}
    print(key, lic, meta[key]["artist"], flush=True); time.sleep(3)
(D / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
