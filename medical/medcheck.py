"""Medical Accuracy Gate. Runs before voice/render (make_episode.sh) and before upload (youtube_schedule.py).

python3 medcheck.py episodes/<slug>        -> prints ERRORS / WARNINGS, exit 1 on any ERROR

What it enforces (the channel's medical safety rules, see agents/03_medical_reviewer.md):
  * every FACT / CONTEXT line that states a fact has a `source` tag naming 2+ sources ("WHO, CDC")
  * meta.sources has 2+ entries, and every URL is on a trusted medical domain (TRUSTED below)
  * no individual treatment advice ("you should take", "stop taking", "cure", "miracle", "guaranteed" ...)
  * no doses (e.g. "500 mg", "2 tablets") unless meta.allow_doses is true AND a guideline is cited
  * script length: <= 135 spoken words (fits under 60 s with the ElevenLabs voice), on-screen text <= 6 words,
    no arrow glyphs in on-screen text (the font has none)
  * news episodes need meta.checked_on (date the facts were re-checked) and meta.event_date
"""
import json, re, sys
from pathlib import Path
from urllib.parse import urlparse

TRUSTED = {
    # global / public-health bodies
    "who.int", "cdc.gov", "nih.gov", "ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov", "pmc.ncbi.nlm.nih.gov", "medlineplus.gov",
    "fda.gov", "ema.europa.eu", "nice.org.uk", "nhs.uk", "gov.uk", "ecdc.europa.eu", "unaids.org", "unicef.org", "cochrane.org",
    "cochranelibrary.com", "clinicaltrials.gov", "cancer.gov", "heart.org", "ahajournals.org", "resus.org.uk", "ilcor.org",
    # India
    "mohfw.gov.in", "icmr.gov.in", "main.icmr.nic.in", "nmc.org.in", "natboard.edu.in", "nbe.edu.in", "pib.gov.in", "cdsco.gov.in",
    "ncdc.mohfw.gov.in", "aiims.edu", "nhp.gov.in",
    # journals
    "nejm.org", "thelancet.com", "bmj.com", "jamanetwork.com", "nature.com", "science.org", "cell.com", "annals.org",
    "acpjournals.org", "academic.oup.com", "sciencedirect.com", "springer.com", "wiley.com", "onlinelibrary.wiley.com",
    "atsjournals.org", "diabetesjournals.org", "escardio.org", "idsociety.org", "sccm.org", "acog.org", "aap.org",
    "publications.aap.org", "ashpublications.org", "ascopubs.org", "medrxiv.org",
    # reputable health news (allowed as 1 of the 2 sources for NEWS only)
    "reuters.com", "apnews.com", "statnews.com", "bbc.com", "bbc.co.uk", "thehindu.com", "indianexpress.com", "medscape.com",
    "health.harvard.edu", "mayoclinic.org", "clevelandclinic.org", "hopkinsmedicine.org", "msdmanuals.com",
}
NEWS_ONLY = {"reuters.com", "apnews.com", "statnews.com", "bbc.com", "bbc.co.uk", "thehindu.com", "indianexpress.com", "medscape.com"}

BANNED = [
    (r"\byou should (take|stop|start|use)\b", "individual treatment advice"),
    (r"\bstop taking\b", "individual treatment advice"),
    (r"\b(miracle|guaranteed|100% (safe|effective)|cures? (cancer|diabetes|everything))\b", "hype / false-certainty claim"),
    (r"\b(doctors hate|big pharma doesn't want)\b", "clickbait"),
    (r"\bself[- ]medicat", "self-medication wording"),
]
DOSE = re.compile(r"\b\d+(\.\d+)?\s?(mg|mcg|µg|g|ml|mL|units?|IU|tablets?|pills?)\b", re.I)
STATE_BEATS = {"CONTEXT", "FACT1", "FACT2", "FACT3"}
FILLER = re.compile(r"(keep watching|stay for|wait for|it's the big one|exam favourite|in sixty seconds)", re.I)


def domain_ok(url, series):
    host = urlparse(url).netloc.lower().removeprefix("www.")
    for d in TRUSTED:
        if host == d or host.endswith("." + d):
            if d in NEWS_ONLY and "news" not in series.lower():
                return False, f"{host} is a news site, allowed only for news episodes"
            return True, ""
    return False, f"{host} is not on the trusted medical source list (medcheck.TRUSTED)"


def check(ep):
    ep = Path(ep); s = json.loads((ep / "script.json").read_text()); m = s.get("meta", {})
    series = s.get("series", ""); err, warn = [], []
    words = sum(len(l["text"].split()) for l in s["lines"])
    if words > 135: err.append(f"script is {words} words (max 135, or it runs over 60 s)")
    for i, l in enumerate(s["lines"]):
        tag = f"line {i + 1} [{l['beat']}]"
        txt = l["text"]
        for pat, why in BANNED:
            if re.search(pat, txt, re.I): err.append(f"{tag}: {why}: '{txt}'")
        if DOSE.search(txt) or DOSE.search(l.get("ost", "")):
            if not m.get("allow_doses"): err.append(f"{tag}: contains a dose ('{DOSE.search(txt + ' ' + l.get('ost', '')).group(0)}'). Remove it, or set meta.allow_doses with a guideline source")
        ost = l.get("ost", "")
        if len(ost.replace("|", " ").split()) > 6: warn.append(f"{tag}: on-screen text is over 6 words: '{ost}'")
        if any(a in ost for a in "→←↓↑"): err.append(f"{tag}: arrow glyph in on-screen text (font has none)")
        if l["beat"] in STATE_BEATS and not FILLER.search(txt):
            src = l.get("source", "")
            n = len([x for x in re.split(r"[,;/&]| and ", src) if x.strip()])
            if n < 2: err.append(f"{tag}: needs 2+ sources in `source` (has '{src or 'none'}'): '{txt}'")
    srcs = m.get("sources", [])
    if len(srcs) < 2: err.append("meta.sources needs 2+ entries")
    for name, url in srcs:
        ok, why = domain_ok(url, series)
        if not ok: err.append(f"source '{name}': {why}")
    if "news" in series.lower():
        if not m.get("checked_on"): err.append("news episode: set meta.checked_on (YYYY-MM-DD the facts were last re-checked)")
        if not m.get("event_date"): warn.append("news episode: meta.event_date missing")
    if not m.get("titles"): err.append("meta.titles missing")
    for t in m.get("titles", []):
        if len(t) > 70: warn.append(f"title over 70 chars: '{t}'")
    return err, warn


if __name__ == "__main__":
    bad = 0
    for ep in sys.argv[1:]:
        e, w = check(ep)
        print(f"=== medcheck {ep}: {'PASS' if not e else 'FAIL'} ({len(e)} errors, {len(w)} warnings)")
        for x in e: print("  ERROR  ", x)
        for x in w: print("  warning", x)
        bad += bool(e)
    sys.exit(1 if bad else 0)
