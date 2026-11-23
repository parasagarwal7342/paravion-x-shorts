"""Licensed real-image fetcher for long-form videos (Wikimedia Commons, which hosts CDC PHIL / NIH / NIAID / Wellcome
public-domain and Creative Commons images).

    python3 media.py episodes/<slug>            # fetch every image the script asks for
    python3 media.py --search "petri dish penicillium"   # preview candidates and their licences

In script.json a line's visual can be:
    {"type": "image", "query": "Staphylococcus aureus electron micrograph"}     # best licensed match
    {"type": "image", "file": "File:Penicillia on Petri dish.jpg"}              # an exact Commons file (preferred)
Downloads go to episodes/<slug>/images/, and credits.json records title, author, licence and source page for every image.
The renderer shows a small credit on screen and package_long.py lists all credits in the description.

Safety rules (enforced here):
  * licence must be Public domain, CC0, CC BY or CC BY-SA (no NC/ND, no "fair use", no unknown licence)
  * no images of identifiable patients, surgery, wounds, bodies, nudity or children in clinical settings
    (BLOCK words below, checked against title + description + categories); prefer micrographs, lab scenes,
    historical photos, buildings, equipment and illustrations
  * minimum 1280 px wide (or 1000 px for historical/public-domain files) so nothing looks blurry at 1080p
"""
import hashlib, html, json, re, sys, urllib.parse, urllib.request
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "ParavionMed-longform/1.0 (educational video renderer; contact via channel)"}
OK_LICENSES = re.compile(r"^(public domain|pd|cc0|cc[- ]by(-sa)?[- ]?\d(\.\d)?( [a-z]+)?|cc[- ]by(-sa)?)$", re.I)
BLOCK = re.compile(r"\b(patient|surgery|surgical|operation|wound|lesion|ulcer|autopsy|cadaver|corpse|dead body|nude|naked|"
                   r"genital|gore|blood loss|injur|amputat|necro|gangrene|rash on|child patient|infant patient|face of)\b", re.I)


_last = [0.0]


def _open(url, timeout=60):
    """Polite GET: at most one request every 1.5 s, and back off on HTTP 429 / 503 (Wikimedia rate limits)."""
    import time, urllib.error
    for attempt in range(6):
        wait = _last[0] + 1.5 - time.time()
        if wait > 0: time.sleep(wait)
        _last[0] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or attempt == 5: raise
            time.sleep(min(90, int(e.headers.get("Retry-After") or 0) or 10 * (attempt + 1)))


def get(params):
    return json.loads(_open(API + "?" + urllib.parse.urlencode({**params, "format": "json", "maxlag": 5}), 40))


def strip(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def info(pages):
    out = []
    for p in pages.values():
        if "imageinfo" not in p: continue
        ii = p["imageinfo"][0]; m = ii.get("extmetadata", {})
        lic = strip(m.get("LicenseShortName", {}).get("value", ""))
        text = " ".join([p["title"], strip(m.get("ImageDescription", {}).get("value", "")), strip(m.get("Categories", {}).get("value", ""))])
        out.append({"title": p["title"], "url": ii.get("thumburl") or ii["url"], "width": ii.get("width", 0), "height": ii.get("height", 0),
                    "mime": ii.get("mime", ""), "license": lic, "license_url": strip(m.get("LicenseUrl", {}).get("value", "")),
                    "author": strip(m.get("Artist", {}).get("value", "")) or "Unknown", "credit": strip(m.get("Credit", {}).get("value", ""))[:160],
                    "page": ii.get("descriptionurl", ""), "blocked": bool(BLOCK.search(text)),
                    "licence_ok": bool(OK_LICENSES.match(lic.lower().replace("public domain mark", "public domain")))})
    return out


def lookup(title):
    return info(get({"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 2400})["query"]["pages"])


def search(q, n=12):
    d = get({"action": "query", "generator": "search", "gsrsearch": f"{q} filetype:bitmap", "gsrnamespace": 6, "gsrlimit": n,
             "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 2400})
    return info(d.get("query", {}).get("pages", {}))


def usable(c):
    pd = "public domain" in c["license"].lower() or "cc0" in c["license"].lower()
    return c["licence_ok"] and not c["blocked"] and c["mime"] in ("image/jpeg", "image/png") and c["width"] >= (1000 if pd else 1280)


def fetch(ep):
    ep = Path(ep); s = json.loads((ep / "script.json").read_text())
    img_dir = ep / "images"; img_dir.mkdir(exist_ok=True)
    cp = ep / "credits.json"; credits = json.loads(cp.read_text()) if cp.exists() else {}
    used = set()
    for i, l in enumerate(s["lines"]):
        v = l.get("visual", {})
        if v.get("type") != "image": continue
        key = v.get("file") or v["query"]
        if key in credits and (img_dir / credits[key]["local"]).exists():
            used.add(credits[key]["title"]); continue
        cands = lookup(v["file"]) if v.get("file") else [c for c in search(v["query"]) if usable(c) and c["title"] not in used]
        cands = [c for c in cands if usable(c)]
        if not cands:
            print(f"line {i + 1}: NO usable licensed image for {key!r} (fix the query or pick a file)"); continue
        c = max(cands, key=lambda c: c["width"]) if not v.get("file") else cands[0]
        ext = ".png" if c["mime"] == "image/png" else ".jpg"
        local = hashlib.sha1(c["title"].encode()).hexdigest()[:12] + ext
        (img_dir / local).write_bytes(_open(c["url"], 120))
        credits[key] = {**c, "local": local}; used.add(c["title"])
        print(f"line {i + 1}: {c['title']}  [{c['license']}]  {c['author'][:50]}")
    cp.write_text(json.dumps(credits, indent=1, ensure_ascii=False))
    return credits


if __name__ == "__main__":
    if sys.argv[1] == "--search":
        for c in search(" ".join(sys.argv[2:])):
            print(("OK   " if usable(c) else "SKIP ") + f"{c['width']}x{c['height']} [{c['license']}] {'BLOCKED ' if c['blocked'] else ''}{c['title']}")
    else:
        fetch(sys.argv[1])
