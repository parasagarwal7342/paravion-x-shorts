"""Find freely licensed photos on Wikimedia Commons and save them with credits.
python3 fetch_photo.py "search terms" [n]  -> lists candidates
python3 fetch_photo.py --get "File:Name.jpg" out_name   -> downloads 1600px version + credit to assets/photos/credits.json
"""
import json, re, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "ShortsRenderer/1.0 (educational explainer videos)"}
OK = re.compile(r"^(CC BY(-SA)? [0-9.]+|CC0|Public domain|PD)", re.I)
OUT = Path(__file__).parent / "assets" / "photos"

def api(**p):
    p.update(format="json")
    import time
    for i in range(6):
        try:
            r = urllib.request.Request(API + "?" + urllib.parse.urlencode(p), headers=UA)
            return json.load(urllib.request.urlopen(r, timeout=30))
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == 5: raise
            time.sleep(5 * (i + 1))

def info(titles):
    q = api(action="query", titles="|".join(titles), prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=1600)
    out = []
    for pg in q["query"]["pages"].values():
        if "imageinfo" not in pg: continue
        ii = pg["imageinfo"][0]; m = ii.get("extmetadata", {})
        g = lambda k: re.sub("<[^>]+>", "", m.get(k, {}).get("value", "")).strip()
        out.append(dict(title=pg["title"], w=ii["width"], h=ii["height"], thumb=ii.get("thumburl"),
                        page=ii.get("descriptionurl"), license=g("LicenseShortName"), artist=g("Artist")[:80]))
    return out

if sys.argv[1] == "--get":
    it = info([sys.argv[2]])[0]
    assert OK.match(it["license"]), it["license"]
    dst = OUT / (sys.argv[3] + ".jpg")
    urllib.request.urlretrieve
    req = urllib.request.Request(it["thumb"], headers=UA)
    dst.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    cf = OUT / "credits.json"; cr = json.loads(cf.read_text()) if cf.exists() else {}
    cr[dst.name] = {k: it[k] for k in ("title", "artist", "license", "page")}
    cf.write_text(json.dumps(cr, indent=1, ensure_ascii=False))
    print("saved", dst, it["license"], it["artist"])
else:
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    s = api(action="query", list="search", srsearch=sys.argv[1] + " filetype:bitmap", srnamespace=6, srlimit=n)
    titles = [x["title"] for x in s["query"]["search"]]
    for it in info(titles) if titles else []:
        if OK.match(it["license"]) and it["w"] >= 1200:
            print(f'{it["w"]}x{it["h"]} | {it["license"]} | {it["title"]} | {it["artist"]}')
