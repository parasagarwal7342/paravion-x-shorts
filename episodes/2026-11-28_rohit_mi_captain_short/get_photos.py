"""Download Wikimedia Commons photos (CC/PD only) into ./img with credits in img/meta.json."""
import json, re, sys, time, urllib.request, urllib.parse
from pathlib import Path
D = Path(__file__).parent / "img"; UA = {"User-Agent": "ParavionX/1.0 (news explainer; contact via YouTube @PARAVION_X)"}
OK = re.compile(r"^(CC BY(-SA)? [0-9.]+|CC0|Public domain|PD|GODL-India)", re.I)
PICKS = {
 "rohit_mi": "File:RohitSharma MumbaiIndians.png",
 "rohit_bat": "File:2015 CWC I v UAE 02-28 Sharma (06).JPG",
 "rohit_bat2": "File:2015 CWC I v UAE 02-28 Sharma (10).JPG",
 "rohit_bat3": "File:Rohit Sharma Batting.jpg",
 "rohit_test": "File:Rohit Sharma during the India vs Australia 4th Test match at Narendra Modi Stadium.jpg",
 "rohit_flag": "File:Rohit Sharma Hoists Indian Flag in Barbados.jpg",
 "rohit_bowl": "File:Rohit Sharma bowling 2014.jpg",
 "hardik": "File:Hardik Pandya 2020.jpg",
 "arshdeep": "File:Arshdeep Singh 2022.jpg",
 "wankhede": "File:Wankhede Stadium as seen from Marine Lines, Mumbai.jpg",
 "wankhede2": "File:Wankhede-1.JPG",
 "wankhede3": "File:Wankhede ICC WCF.jpg",
 "wankhede_pano": "File:Wankhede Panoramic ICC WCF.jpg",
 "mi_edu": "File:Mumbai Indians Supports Education for All.jpg",
 "ashwin_rohit": "File:Ashwin to Rohit sharma.JPG",
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
    (D / f"{key}.jpg").write_bytes(data) if not url.lower().endswith(".png") else __import__("PIL.Image",fromlist=["x"]).open(__import__("io").BytesIO(data)).convert("RGB").save(D / f"{key}.jpg", quality=93)
    meta[key] = {"title": pg["title"], "artist": g("Artist")[:90], "license": lic, "page": ii.get("descriptionurl")}
    print(key, lic, meta[key]["artist"], flush=True); time.sleep(3)
(D / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
