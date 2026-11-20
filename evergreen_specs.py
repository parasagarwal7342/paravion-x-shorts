"""30 evergreen 'Fake or Fact?' explainers (one per day at 7:30 PM IST). Run: python3 evergreen_specs.py
Each spec: hook, question, 2 context lines, facts 1-3 (1-2 lines each), myth/truth verdict, sources (2+ per fact line)."""
import datetime as dt, json, os

START = dt.date(2026, 11, 22)          # first evergreen slot
SLOT = "19:30:00+05:30"


def ln(beat, text, ost, vis, keys=(), src=None):
    d = {"beat": beat, "text": text, "ost": ost, "visual": vis, "keys": list(keys)}
    if src: d["source"] = src
    return d


S = lambda **k: dict(type="stat", **k)
TAGS = lambda *t: {"type": "tags", "tags": list(t)}
HERO = lambda note="", icon=None: {"type": "hero", "note": note, **({"icon": icon} if icon else {})}
ROWS = lambda *r: {"type": "rows", "rows": [list(x) for x in r]}
CAL = lambda m, d, y="": {"type": "calendar", "month": m, "day": d, "year": y}
TWO = lambda a, b, j="↓": {"type": "two_hats", "a": a, "b": b, "join": j}


def build(i, t):
    slug = f"E{i:02d}_{t['slug']}"
    when = dt.datetime.combine(START + dt.timedelta(days=i - 1), dt.time(19, 30)).strftime("%Y-%m-%dT") + SLOT
    hook_t, hook_o, hook_v, hook_k = t["hook"]
    L = [ln("HOOK", hook_t, hook_o, hook_v, hook_k),
         ln("HOOK", t["q"][0], t["q"][1], {"type": "question"}, t["q"][2]),
         ln("SUB", "In sixty seconds, you'll know the truth.", "60 seconds.|The truth.", {"type": "timer"}, ["truth."])]
    L += [ln("CONTEXT", *c) for c in t["ctx"]]
    L.append(ln("CONTEXT", "Keep watching for fact three. It's the big one.", "Wait for|fact 3.", {"type": "teaser", "n": 3}, ["three."]))
    for beat, key in (("FACT1", "f1"), ("FACT2", "f2"), ("FACT3", "f3")):
        L += [ln(beat, *c) for c in t[key]]
    rows = [[t["myth"], "FALSE", "red"], [t["truth"][0], t["truth"][1], "green"]]
    L.append(ln("VERDICT", t["v1"], "The myth:|false.", {"type": "verdict", "shown": 1, "rows": rows}, ["false."]))
    L.append(ln("VERDICT", t["v2"][0], t["v2"][1], {"type": "verdict", "shown": 2, "rows": rows}, t["v2"][2]))
    L.append(ln("CTA", "Like and follow Paravion X for more updates.", "Follow for|more updates.", {"type": "cta"}, ["Like", "follow", "updates."]))
    kick = "EXPLAINED · " + t["topic"]
    script = {"slug": slug, "series": "Fake or Fact?",
              "kickers": {"HOOK": kick, "SUB": kick, "CONTEXT": "THE BASICS", "FACT1": "FACT 1 OF 3", "FACT2": "FACT 2 OF 3",
                          "FACT3": "FACT 3 OF 3", "VERDICT": "FAKE OR FACT?", "CTA": "THE WORLD, EXPLAINED"},
              "cover": {"kicker": "FAKE OR FACT? · " + t["topic"], "head": t["cover"], "sub": t["cover_sub"], "visual": hook_v},
              "lines": L,
              "meta": {"titles": t["titles"], "summary": t["summary"], "hashtags": ["#shorts"] + t["tags"],
                       "ig_tags": " ".join("#" + x.lower().lstrip("#") for x in t["tags"] + ["explained", "factcheck", "learnsomethingnew", "paravionx"]),
                       "pinned": t["pinned"], "poll": t["poll"], "sources": t["sources"], "removed": t.get("removed", []),
                       "notes": "Evergreen explainer: not time-sensitive.", "schedule": when,
                       "verdict": f"{t['myth']}: FALSE. {t['truth'][0]}: {t['truth'][1].title()}."}}
    os.makedirs(f"episodes/{slug}", exist_ok=True)
    p = f"episodes/{slug}/script.json"
    old = json.load(open(p)) if os.path.exists(p) else None
    if old != script:
        json.dump(script, open(p, "w"), indent=1, ensure_ascii=False)
    return slug, sum(len(l["text"].split()) for l in L)


T = []

# 1 ─────────────────────────────────────────── Sky
T.append(dict(slug="sky_blue", topic="SCIENCE",
 hook=("The sky is not blue because of the ocean.", "It's not|the ocean.", HERO("A very common myth", "x"), ["ocean."]),
 q=("So why IS it blue?", "So why|blue?", ["blue?"]),
 ctx=[("Sunlight looks white, but it's every colour mixed together.", "White light =|all colours.", TAGS("Red", "Green", "Blue"), ["every"], "NASA, Met Office"),
      ("When it hits the air, tiny gas molecules scatter it.", "Air scatters|sunlight.", TAGS("Nitrogen", "Oxygen"), ["scatter"], "NASA, Met Office")],
 f1=[("Fact one. Blue light scatters far more than red.", "Blue scatters|most.", {"type": "versus", "sides": [{"name": "BLUE", "big": "More", "mark": "dot", "lines": ["scattered"], "color": "accent"}, {"name": "RED", "big": "Less", "mark": "dot", "lines": ["scattered"], "color": "ink"}]}, ["one.", "Blue"], "NASA, Met Office"),
     ("That spreads blue across the whole sky.", "Blue fills|the sky.", HERO("Called Rayleigh scattering"), ["whole"], "NASA, Met Office")],
 f2=[("Fact two. Violet scatters even more, but sunlight has less of it.", "Why not|violet?", ROWS(("VIOLET", "Scatters even more", "Less of it in sunlight", "dot"), ("YOUR EYES", "More sensitive to blue", "", "check")), ["two.", "Violet"], "NASA, Met Office")],
 f3=[("And the big one. At sunset, light crosses much more air.", "Sunset: more|air to cross.", TWO("Longer path", "Blue scatters away"), ["big", "sunset,"], "NASA, Met Office"),
     ("The blue scatters away, leaving reds and oranges.", "Red and orange|remain.", TAGS("Red", "Orange"), ["reds"], "NASA, Met Office")],
 myth="Sky reflects the ocean", truth=("Air scatters blue light", "TRUE"),
 v1="Verdict. The ocean myth is false.", v2=("The sky is blue because air scatters blue light the most.", "The truth:|air scatters blue.", ["most."]),
 cover=["Why is", "the sky", "blue?"], cover_sub="Hint: it's not the ocean. The 60-second science answer.",
 titles=["Why Is the Sky Blue? (It's Not the Ocean)", "The Real Reason the Sky Is Blue", "Why Sunsets Turn Red, Explained"],
 summary="The sky isn't blue because it reflects the ocean. Air molecules scatter blue sunlight far more than red (Rayleigh scattering). At sunset, light crosses more air, leaving reds and oranges.",
 tags=["#Science", "#Sky", "#Physics", "#Explained"], pinned="Did you believe the ocean myth? Be honest 👇", poll=["Knew this already?", "Yes 🧠", "No way 😮"],
 sources=[["NASA Space Place: Why is the sky blue?", "https://spaceplace.nasa.gov/blue-sky/en/"], ["Met Office: Why is the sky blue?", "https://weather.metoffice.gov.uk/learn-about/weather/optical-effects/why-is-the-sky-blue"]]))

# 2 ─────────────────────────────────────────── Leap year
T.append(dict(slug="leap_year", topic="CALENDAR",
 hook=("A leap year does NOT come every four years. Not always.", "Every 4 years?|Not always.", CAL("FEB", "29", "LEAP"), ["NOT"]),
 q=("So when does it skip?", "So when does|it skip?", ["skip?"]),
 ctx=[("Earth takes about three hundred sixty-five and a quarter days to orbit the Sun.", "One orbit:|~365¼ days.", S(text="365¼", count=False, label="DAYS PER ORBIT"), ["quarter"], "Britannica, timeanddate"),
      ("Those extra quarter days add up, so we add February twenty-ninth.", "Hence|Feb. 29.", CAL("FEB", "29", "LEAP"), ["twenty-ninth."], "Britannica, timeanddate")],
 f1=[("Fact one. Four quarter days make one extra day.", "4 quarters =|1 day.", S(text="4 × ¼ = 1", count=False, label="EVERY FOUR YEARS"), ["one.", "extra"], "Britannica, timeanddate")],
 f2=[("Fact two. But the real extra is slightly less than a quarter day.", "Slightly less|than ¼.", S(text="365.2422", count=False, label="DAYS PER ORBIT", sub="Not quite 365.25"), ["two.", "less"], "Britannica, timeanddate"),
     ("So a leap day every four years overshoots, a little.", "Every 4 years|overshoots.", HERO("About 11 minutes too much per year"), ["overshoots,"], "Britannica, timeanddate")],
 f3=[("And the big one. Century years skip it, unless divisible by four hundred.", "1900: no.|2000: yes.", ROWS(("1900", "Not a leap year", "Divisible by 100, not 400", "x"), ("2000", "Leap year", "Divisible by 400", "check")), ["big", "skip"], "Britannica, timeanddate")],
 myth="Leap year every 4 years, always", truth=("Most century years skip it", "TRUE"),
 v1="Verdict. 'Every four years, always' is false.", v2=("The next skipped leap year is twenty-one hundred.", "Next skip:|2100.", ["twenty-one"]),
 cover=["Leap year", "every 4 years?", "Not always."], cover_sub="The calendar rule most people never learned.",
 titles=["Leap Years Don't Always Come Every 4 Years", "Why 1900 Had No February 29", "The Leap Year Rule Explained"],
 summary="Earth's orbit takes about 365.2422 days, so a leap day every four years slightly overshoots. Century years skip it unless divisible by 400: 1900 wasn't a leap year, 2000 was, 2100 won't be.",
 tags=["#LeapYear", "#Calendar", "#Science", "#Explained"], pinned="Know anyone born on February 29? 👇", poll=["Knew the 400-year rule?", "Yes 📅", "No 🤯"],
 sources=[["Britannica: Leap year", "https://www.britannica.com/science/leap-year-calendar"], ["timeanddate: Leap year rules", "https://www.timeanddate.com/date/leapyear.html"]],
 removed=["'About 11 minutes per year' shown only as an on-screen note (derived: 365.25 − 365.2422 days)."]))

# 3 ─────────────────────────────────────────── GPS
PHONE = {"type": "phone_alert", "banner": "GPS", "banner_sub": "No internet needed"}
T.append(dict(slug="gps", topic="TECH",
 hook=("Your phone's GPS works with zero internet.", "GPS needs|no internet.", PHONE, ["zero"]),
 q=("So how does it know where you are?", "How does it|know?", ["know"]),
 ctx=[("GPS is a US system of at least twenty-four satellites.", "24+ satellites|overhead.", S(value=24, suffix="+", label="GPS SATELLITES"), ["twenty-four"], "GPS.gov, Ohio State"),
      ("Each one keeps broadcasting its position and the exact time.", "They broadcast|time + place.", TWO("Satellite: time + place", "Your phone listens"), ["broadcasting"], "GPS.gov, Ohio State")],
 f1=[("Fact one. Your phone only listens. It sends nothing back.", "Listen-only.|No upload.", HERO("GPS receivers are passive"), ["one.", "listens."], "GPS.gov, Ohio State")],
 f2=[("Fact two. Signals from four satellites pin down your position.", "4 satellites|= your spot.", S(value=4, label="SATELLITES NEEDED", sub="3 for position + 1 for the clock"), ["two.", "four"], "Ohio State, arXiv")],
 f3=[("And the big one. Satellite clocks run about thirty-eight microseconds a day fast.", "Clocks gain|38 µs a day.", S(value=38, suffix=" µs", label="PER DAY", sub="Einstein's relativity"), ["big", "thirty-eight"], "Ohio State, arXiv"),
     ("Without that correction, positions would drift about ten kilometres a day.", "Uncorrected:|~10 km a day.", S(text="~10 km", count=False, label="DAILY DRIFT", color="red"), ["ten"], "Ohio State, arXiv")],
 myth="GPS needs mobile data", truth=("GPS is free satellite radio", "TRUE"),
 v1="Verdict. 'GPS needs data' is false.", v2=("GPS itself needs no data. Only your maps may use it.", "Maps use data.|GPS doesn't.", ["no"]),
 cover=["Does GPS", "need", "internet?"], cover_sub="How your phone finds you, and why Einstein matters.",
 titles=["Does GPS Need Internet? No. Here's How It Works", "How GPS Really Finds You", "GPS and Einstein: The 38-Microsecond Fix"],
 summary="GPS is receive-only: satellites broadcast time and position, and your phone listens. Four satellites fix your position. Satellite clocks gain about 38 microseconds a day from relativity and are corrected.",
 tags=["#GPS", "#Tech", "#Science", "#Explained"], pinned="Did you know GPS works offline? 👇", poll=["Knew GPS works offline?", "Yes 📡", "No 😮"],
 sources=[["GPS.gov (archive): Space segment", "https://archive.gps.gov/systems/gps/space/"], ["arXiv: Relativity in navigation satellite systems", "https://arxiv.org/abs/gr-qc/0507121"], ["Ohio State: GPS and relativity (PDF)", "https://www.astronomy.ohio-state.edu/thompson.1847/1144/gps.pdf"]]))

# 4 ─────────────────────────────────────────── Black holes
T.append(dict(slug="black_holes", topic="SPACE",
 hook=("Black holes don't suck everything in.", "Black holes|don't 'suck'.", HERO("Not cosmic vacuum cleaners", "x"), ["don't"]),
 q=("So what do they really do?", "So what do|they do?", ["really"]),
 ctx=[("A black hole is mass packed so tightly that not even light escapes.", "Not even light|escapes.", HERO("The edge is the event horizon"), ["light"], "NASA, EHT"),
      ("But only things that get too close fall in.", "Too close?|You fall in.", HERO(), ["close"], "NASA")],
 f1=[("Fact one. From far away, its gravity is like any object with the same mass.", "Same mass,|same pull.", {"type": "versus", "sides": [{"name": "STAR", "big": "1×", "mark": "dot", "lines": ["same mass"], "color": "ink"}, {"name": "BLACK HOLE", "big": "1×", "mark": "dot", "lines": ["same pull"], "color": "accent"}]}, ["one.", "same"], "NASA")],
 f2=[("Fact two. In 2019, scientists revealed the first image of one.", "First image:|2019.", CAL("APR", "10", "2019"), ["two.", "first"], "EHT, NASA"),
     ("It sits about fifty-five million light-years away.", "55 million|light-years.", S(value=55, suffix=" million", label="LIGHT-YEARS AWAY"), ["fifty-five"], "EHT, NASA")],
 f3=[("And the big one. It weighs about six and a half billion Suns.", "6.5 billion|Suns.", S(value=6.5, decimals=1, suffix=" billion", label="SOLAR MASSES", sub="Black hole M87*", color="accent"), ["big", "billion"], "EHT, NASA")],
 myth="Black holes suck everything in", truth=("Gravity like any mass", "TRUE"),
 v1="Verdict. The vacuum-cleaner myth is false.", v2=("Far away, a black hole pulls like any other mass.", "The truth:|normal gravity.", ["pulls"]),
 cover=["Do black", "holes really", "suck?"], cover_sub="The biggest space myth, fixed in 60 seconds.",
 titles=["Do Black Holes Suck Everything In? No.", "Black Holes Explained in 60 Seconds", "The First Black Hole Image, Explained"],
 summary="Black holes don't vacuum up everything: far away, their gravity is like any object of the same mass. The first image, of M87*, was revealed in 2019: 55 million light-years away, 6.5 billion solar masses.",
 tags=["#Space", "#BlackHole", "#Astronomy", "#Explained"], pinned="What space myth should we bust next? 👇", poll=["Believed the 'suck' myth?", "Yes 🕳️", "No 🚀"],
 sources=[["NASA Science: Black holes", "https://science.nasa.gov/universe/black-holes/"], ["Event Horizon Telescope, Apr 10 2019", "https://eventhorizontelescope.org/press-release-april-10-2019-astronomers-capture-first-image-black-hole"]]))

# 5 ─────────────────────────────────────────── Tides
T.append(dict(slug="tides", topic="OCEANS",
 hook=("One Moon… but two high tides a day.", "One Moon.|Two high tides.", TAGS("High tide", "High tide"), ["two"]),
 q=("How does that work?", "How does that|work?", ["work?"]),
 ctx=[("Tides are the ocean being pulled by gravity.", "Gravity pulls|the ocean.", HERO(), ["gravity."], "NOAA"),
      ("The Moon's pull is strongest on the side facing it.", "Strongest on|the near side.", HERO(), ["strongest"], "NOAA")],
 f1=[("Fact one. The far side bulges too, so Earth has two bulges.", "Two bulges.|Two tides.", TAGS("Near-side bulge", "Far-side bulge"), ["one.", "two"], "NOAA"),
     ("As Earth spins through both, most coasts get two high tides a day.", "2 high tides|a day.", S(value=2, label="HIGH TIDES A DAY", sub="On most coasts"), ["two"], "NOAA")],
 f2=[("Fact two. The Sun pulls tides too, about half as strongly as the Moon.", "Sun: about half|the Moon's pull.", {"type": "split_bar", "total": "Tidal pull", "parts": [{"value": 2, "value_text": "Moon", "label": "About 2/3", "color": "ink"}, {"value": 1, "value_text": "Sun", "label": "About 1/3", "color": "accent"}]}, ["two.", "half"], "NOAA")],
 f3=[("And the big one. At new and full moon, they line up for extra-big spring tides.", "Lined up =|spring tides.", TAGS("Sun", "Earth", "Moon"), ["big", "spring"], "NOAA"),
     ("And spring tides have nothing to do with the season.", "Not about|spring.", HERO("Named for the tide 'springing' up"), ["nothing"], "NOAA")],
 myth="Only the Moon makes tides", truth=("The Sun adds about half", "TRUE"),
 v1="Verdict. 'Only the Moon' is false.", v2=("The Sun adds roughly half the Moon's pull.", "The Sun:|about half.", ["half"]),
 cover=["One Moon.", "Two high", "tides?"], cover_sub="How tides really work, in 60 seconds.",
 titles=["Why Are There Two High Tides a Day?", "Tides Explained: It's Not Only the Moon", "What Are Spring Tides? (Not the Season)"],
 summary="The Moon's gravity raises two ocean bulges, giving most coasts two high tides a day. The Sun's tidal pull is about half the Moon's; when they line up at new and full moon we get spring tides.",
 tags=["#Ocean", "#Tides", "#Science", "#Explained"], pinned="Have you ever seen a huge spring tide? 👇", poll=["Knew the Sun affects tides?", "Yes 🌊", "No 🌙"],
 sources=[["NOAA: What causes tides", "https://oceanservice.noaa.gov/education/tutorial_tides/tides02_cause.html"], ["NOAA: Sun vs Moon tidal forces", "https://oceanservice.noaa.gov/education/tutorial_tides/media/supp_tide02.html"], ["NOAA: What is a spring tide?", "https://oceanservice.noaa.gov/facts/springtide.html"]]))

# 6 ─────────────────────────────────────────── Ozone
T.append(dict(slug="ozone", topic="ENVIRONMENT",
 hook=("The ozone hole is actually healing.", "The ozone hole|is healing.", S(text="2066", count=False, label="ANTARCTIC RECOVERY", color="accent"), ["healing."]),
 q=("So what fixed it?", "So what|fixed it?", ["fixed"]),
 ctx=[("High in the sky, ozone blocks harmful ultraviolet rays.", "Ozone blocks|UV rays.", HERO(), ["ultraviolet"], "UNEP, WMO"),
      ("In the 1980s, scientists found a hole over Antarctica.", "A hole over|Antarctica.", HERO(), ["hole"], "UNEP, WMO")],
 f1=[("Fact one. Chemicals called CFCs, from fridges and sprays, were destroying it.", "The culprit:|CFCs.", TAGS("Fridges", "Spray cans"), ["one.", "CFCs,"], "UNEP, WMO")],
 f2=[("Fact two. In 1987, countries signed the Montreal Protocol to phase them out.", "1987: Montreal|Protocol.", CAL("SEP", "16", "1987"), ["two.", "Montreal"], "UNEP, WMO")],
 f3=[("And the big one. Experts expect most of the world to recover by around 2040.", "Most recovered|by ~2040.", ROWS(("MOST OF THE WORLD", "~2040", "", "check"), ("ARCTIC", "~2045", "", "check"), ("ANTARCTIC", "~2066", "", "check")), ["big", "2040."], "UNEP, WMO"),
     ("And the Antarctic hole by around 2066.", "Antarctica:|~2066.", S(text="~2066", count=False, label="ANTARCTIC RECOVERY", color="accent"), ["2066."], "UNEP, WMO")],
 myth="Ozone damage can't be undone", truth=("Recovery is on track", "TRUE"),
 v1="Verdict. 'It can't be fixed' is false.", v2=("Global action worked, and recovery is on track.", "Recovery:|on track.", ["worked,"]),
 cover=["The ozone", "hole is", "healing."], cover_sub="How the world fixed a global problem, in 60 seconds.",
 titles=["The Ozone Hole Is Healing. Here's Why", "How the World Fixed the Ozone Layer", "Ozone Recovery by 2066, Explained"],
 summary="CFCs from fridges and sprays damaged the ozone layer. The 1987 Montreal Protocol phased them out. UNEP/WMO expect recovery by about 2040 for most of the world and around 2066 over Antarctica.",
 tags=["#Environment", "#Ozone", "#Science", "#Explained"], pinned="What other global problem should the world fix together? 👇", poll=["Knew the ozone is healing?", "Yes 🌍", "No 😮"],
 sources=[["UNEP: Ozone layer recovery on track", "https://www.unep.org/news-and-stories/press-release/ozone-layer-recovery-track-helping-avoid-global-warming-05degc"], ["WMO: Ozone layer recovery on track", "https://wmo.int/node/20740"]]))

# 7 ─────────────────────────────────────────── El Niño
T.append(dict(slug="el_nino", topic="MONSOON",
 hook=("El Niño does not always mean drought in India.", "El Niño = drought?|Not always.", HERO("A common belief, and only half true", "x"), ["always"]),
 q=("So what is El Niño, really?", "What is|El Niño?", ["really?"]),
 ctx=[("It's a warming of the Pacific Ocean near the equator.", "A warm|Pacific.", HERO(), ["warming"], "NOAA"),
      ("It shifts winds and rainfall patterns around the world.", "It shifts|world weather.", HERO(), ["shifts"], "NOAA")],
 f1=[("Fact one. It comes back every two to seven years.", "Every 2–7|years.", S(text="2–7 yrs", count=False, label="HOW OFTEN"), ["one.", "seven"], "NOAA")],
 f2=[("Fact two. In India, it's often linked to weaker monsoon rains.", "Often: weaker|monsoon.", HERO("A higher risk, not a rule"), ["two.", "weaker"], "NOAA, IITM")],
 f3=[("And the big one. In 1997, a very strong El Niño came… and the monsoon was normal.", "1997: strong El Niño.|Normal monsoon.", S(text="102%", count=False, label="1997 MONSOON RAIN", sub="Of the long-term average", color="accent"), ["big", "normal."], "IITM, IMD Mausam")],
 myth="El Niño always means drought", truth=("It raises the risk", "TRUE"),
 v1="Verdict. 'Always drought' is false.", v2=("El Niño raises the risk of a weak monsoon. It doesn't guarantee one.", "Risk, not a|guarantee.", ["risk"]),
 cover=["El Niño", "means", "drought?"], cover_sub="What El Niño really does to India's monsoon.",
 titles=["Does El Niño Always Mean Drought? No.", "El Niño Explained in 60 Seconds", "The 1997 El Niño That Didn't Ruin the Monsoon"],
 summary="El Niño is a warming of the tropical Pacific every 2–7 years. It is often linked to weaker Indian monsoons, but not always: in 1997, despite a very strong El Niño, India's monsoon was about 102% of normal.",
 tags=["#ElNino", "#Monsoon", "#India", "#Weather"], pinned="How was the monsoon in your city this year? 👇", poll=["Knew about 1997?", "Yes 🌧️", "No ☀️"],
 sources=[["NOAA Climate.gov: ENSO in a nutshell", "https://www.climate.gov/news-features/blogs/enso/what-el-ni%C3%B1o%E2%80%93southern-oscillation-enso-nutshell"], ["IITM: The 1997 Asian summer monsoon", "https://www.tropmet.res.in/~kolli/MOL/Monsoon/year1997/summary_1997.html"], ["IMD Mausam: El Niño of 1997–98 and Indian monsoon", "https://mausamjournal.imd.gov.in/index.php/MAUSAM/article/view/1677"]]))

# 8 ─────────────────────────────────────────── Climate vs weather
T.append(dict(slug="climate_weather", topic="CLIMATE",
 hook=("A cold day does not disprove global warming.", "Cold day?|Still warming.", HERO("Weather and climate aren't the same", "x"), ["cold"]),
 q=("Why not?", "Why|not?", ["not?"]),
 ctx=[("Weather is what happens today, where you are.", "Weather =|today.", HERO(), ["today,"], "NOAA"),
      ("Climate is the long-term average of that weather.", "Climate =|the long run.", HERO(), ["average"], "NOAA, WMO")],
 f1=[("Fact one. Scientists describe climate over thirty-year periods.", "Climate:|30-year averages.", S(value=30, suffix=" yrs", label="CLIMATE NORMAL"), ["one.", "thirty-year"], "WMO, NOAA")],
 f2=[("Fact two. One cold day is a single data point.", "One day =|one data point.", HERO(), ["two.", "single"], "NOAA")],
 f3=[("And the big one. A warming climate still has cold snaps.", "Warming still|has cold days.", TAGS("Cold snaps", "Warmer average"), ["big", "cold"], "NOAA, WMO")],
 myth="A cold day disproves warming", truth=("Climate is a 30-year trend", "TRUE"),
 v1="Verdict. 'Cold day, no warming' is false.", v2=("Climate is judged over decades, not days.", "Decades,|not days.", ["decades,"]),
 cover=["It's cold.", "So no global", "warming?"], cover_sub="Weather vs climate, in 60 seconds.",
 titles=["A Cold Day Doesn't Disprove Global Warming", "Weather vs Climate Explained in 60 Seconds", "Why Climate Is Measured Over 30 Years"],
 summary="Weather is today's conditions; climate is the long-term average, which the WMO standardises over 30-year periods. A single cold day is one data point and doesn't disprove a warming trend.",
 tags=["#Climate", "#Weather", "#Science", "#Explained"], pinned="Has your city's weather changed in your lifetime? 👇", poll=["Weather = climate?", "Same thing 🤔", "Different ✅"],
 sources=[["NOAA JetStream: Climate vs weather", "https://www.noaa.gov/jetstream/global/climate-vs-weather"], ["NOAA NCEI: WMO climate normals", "https://www.ncei.noaa.gov/products/wmo-climate-normals"]]))

# 9 ─────────────────────────────────────────── Vaccines & autism
T.append(dict(slug="vaccines_autism", topic="HEALTH",
 hook=("Vaccines do not cause autism.", "Vaccines and|autism?", HERO("Where the myth started", "x"), ["not"]),
 q=("So where did that idea come from?", "Where did it|come from?", ["come"]),
 ctx=[("It started with a 1998 study of just twelve children.", "A 1998 study.|12 children.", S(value=12, label="CHILDREN STUDIED", sub="The 1998 paper"), ["twelve"], "NPR, PMC"),
      ("It suggested a link between the MMR vaccine and autism.", "It claimed|a link.", HERO(), ["link"], "NPR, PMC")],
 f1=[("Fact one. Investigators later found serious problems with the study.", "Serious|problems found.", HERO("Including ethics breaches"), ["one.", "serious"], "NPR, PMC")],
 f2=[("Fact two. In 2010, the journal The Lancet retracted it.", "2010:|retracted.", S(text="2010", count=False, label="PAPER RETRACTED", color="red"), ["two.", "retracted"], "NPR, PBS")],
 f3=[("And the big one. Large studies since then found no link.", "Big studies:|no link.", TAGS("Britain", "Japan", "Finland"), ["big", "no"], "PBS, NPR")],
 myth="Vaccines cause autism", truth=("No link found", "TRUE"),
 v1="Verdict. The autism claim is false.", v2=("Research has found no link between vaccines and autism.", "No link|found.", ["no"]),
 cover=["Do vaccines", "cause", "autism?"], cover_sub="Where the myth came from, and what research found.",
 titles=["Do Vaccines Cause Autism? What Research Found", "The 1998 Study Behind a Huge Myth", "Vaccines and Autism: The Facts in 60s"],
 summary="The vaccine–autism myth began with a 1998 study of 12 children. Investigators found serious problems, and The Lancet retracted it in 2010. Large studies since then have found no link.",
 tags=["#Health", "#Vaccines", "#FactCheck", "#Explained"], pinned="Please share facts kindly. What health myth should we check next? 👇", poll=["Seen this myth online?", "Yes 📱", "No 🙅"],
 sources=[["NPR: Lancet retracts Wakefield paper (2010)", "https://www.npr.org/sections/health-shots/2010/02/lancet_wakefield_autism_mmr_au.html"], ["PMC: The MMR vaccine and autism: retraction", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2831678/"], ["PBS NewsHour (2010)", "https://www.pbs.org/newshour/health/europe-jan-june10-lancet_0204"]]))

# 10 ────────────────────────────────────────── 5G myth
T.append(dict(slug="5g_myth", topic="TECH",
 hook=("5G cannot spread viruses.", "5G and|viruses?", PHONE | {"banner": "5G", "banner_sub": "Radio waves"}, ["cannot"]),
 q=("So where did that rumour start?", "Where did it|start?", ["rumour"]),
 ctx=[("In 2020, posts online linked 5G towers to COVID-19.", "2020: 5G|blamed.", HERO(), ["linked"], "UN News, Boston University"),
      ("Some towers in Europe were even damaged.", "Towers were|damaged.", HERO(), ["damaged."], "UN News")],
 f1=[("Fact one. Viruses can't travel on radio waves.", "Viruses can't ride|radio waves.", HERO("", "x"), ["one.", "can't"], "WHO via UN, UK Government")],
 f2=[("Fact two. COVID spread in countries with no 5G at all.", "It spread|without 5G.", HERO(), ["two.", "no"], "WHO via UN, UN News")],
 f3=[("And the big one. The UN's telecom agency called the link a hoax.", "UN agency:|'a hoax'.", S(text="Hoax", count=False, label="ITU VERDICT", color="red"), ["big", "hoax."], "UN News, UK Government")],
 myth="5G spreads viruses", truth=("No technical basis", "TRUE"),
 v1="Verdict. The 5G virus claim is false.", v2=("5G radio waves can't carry viruses. The claim has no technical basis.", "No technical|basis.", ["no"]),
 cover=["Can 5G", "spread a", "virus?"], cover_sub="The rumour that burned towers, fact-checked.",
 titles=["Can 5G Spread Viruses? No. Here's Why", "The 5G Rumour, Fact-Checked", "Why 5G Towers Were Burned in 2020"],
 summary="In 2020, online posts linked 5G to COVID-19 and some towers were damaged. The WHO said viruses can't travel on radio waves, COVID spread where there was no 5G, and the UN's ITU called the link a hoax.",
 tags=["#5G", "#Tech", "#FactCheck", "#Explained"], pinned="Did someone forward you this rumour? 👇", poll=["Seen this rumour?", "Yes 📲", "No 🙅"],
 sources=[["UN News (Apr 2020)", "https://news.un.org/en/story/2020/04/1062362"], ["UN Namibia: WHO myth busters", "https://namibia.un.org/en/41807-covid-19-myth-busters-knowthefacts"], ["UK Government: 5G and coronavirus", "https://www.gov.uk/guidance/5g-and-coronavirus-covid-19"], ["Boston University (2021)", "https://www.bu.edu/hic/2021/01/04/5g-doesnt-cause-covid-19-but-the-rumor-it-does-spread-like-a-virus/"]]))

# 11 ────────────────────────────────────────── UPI
T.append(dict(slug="upi", topic="MONEY",
 hook=("Your UPI app doesn't hold your money.", "UPI doesn't|hold your money.", PHONE | {"banner": "UPI", "banner_sub": "Paid"}, ["doesn't"]),
 q=("So where does it actually go?", "Where does|it go?", ["actually"]),
 ctx=[("UPI launched in April 2016.", "Launched|April 2016.", CAL("APR", "11", "2016"), ["2016."], "NPCI"),
      ("It was built by NPCI, the National Payments Corporation of India.", "Built by|NPCI.", HERO(), ["NPCI,"], "NPCI, Axis Bank")],
 f1=[("Fact one. Your UPI ID links straight to your bank account.", "UPI ID =|your bank account.", TWO("name@bank", "Your bank account"), ["one.", "bank"], "NPCI, Axis Bank")],
 f2=[("Fact two. NPCI works as the central switch between banks.", "NPCI: the|central switch.", HERO(), ["two.", "switch"], "NPCI, Razorpay")],
 f3=[("And the big one. Money moves directly, bank to bank.", "Bank to bank.|Directly.", ROWS(("STEP 1", "Your bank debits you", "", "dot"), ("STEP 2", "NPCI routes it", "", "dot"), ("STEP 3", "Their bank credits them", "", "check")), ["big", "directly,"], "NPCI, Razorpay")],
 myth="UPI apps hold your money", truth=("Bank-to-bank transfer", "TRUE"),
 v1="Verdict. 'The app holds your money' is false.", v2=("Your money stays in your bank until it moves to theirs.", "It stays in|your bank.", ["stays"]),
 cover=["Where does", "your UPI", "money go?"], cover_sub="How a UPI payment really moves, in 60 seconds.",
 titles=["Where Does Your UPI Money Actually Go?", "How UPI Works in 60 Seconds", "UPI Apps Don't Hold Your Money. Here's Why"],
 summary="UPI, launched by NPCI in April 2016, links your UPI ID directly to your bank account. NPCI acts as the switch between banks, so money moves bank to bank. The app is not a wallet.",
 tags=["#UPI", "#India", "#Money", "#Explained"], pinned="Which UPI app do you use most? 👇", poll=["Thought apps hold money?", "Yes 💸", "No 🏦"],
 sources=[["NPCI: UPI product overview", "https://www.npci.org.in/what-we-do/upi/product-overview"], ["NPCI: UPI launch press release (Apr 11 2016)", "https://www.npci.org.in/PDF/npci/press-releases/2016/UPI_Launch_Press_Release_April_11_2016.pdf"], ["Axis Bank: What is UPI", "https://www.axis.bank.in/blogs/payments/what-is-upi-and-full-form-of-upi"], ["Razorpay: What is UPI and how it works", "https://razorpay.com/blog/what-is-upi-and-how-it-works/"]],
 removed=["UPI Lite (a small preloaded on-device balance) is an exception, not covered in 60 seconds."]))

# 12 ────────────────────────────────────────── CIBIL
T.append(dict(slug="cibil_score", topic="MONEY",
 hook=("Checking your own credit score does not lower it.", "Checking your|score is safe.", S(text="300–900", count=False, label="CIBIL SCORE RANGE"), ["not"]),
 q=("So what does lower it?", "What does|lower it?", ["lower"]),
 ctx=[("In India, CIBIL scores run from three hundred to nine hundred.", "Scores:|300 to 900.", S(text="300–900", count=False, label="CIBIL SCORE RANGE"), ["nine"], "CIBIL, Bajaj Housing Finance"),
      ("Lenders use it to decide on loans and credit cards.", "Lenders|check it.", TAGS("Loans", "Credit cards"), ["loans"], "Axis Bank, BankBazaar")],
 f1=[("Fact one. Checking your own score is a soft enquiry.", "Self-check =|soft enquiry.", HERO("No effect on your score"), ["one.", "soft"], "CIBIL, Axis Bank")],
 f2=[("Fact two. A lender checking you for new credit is a hard enquiry.", "Lender check =|hard enquiry.", TWO("You apply for a loan", "Hard enquiry"), ["two.", "hard"], "Axis Bank, BankBazaar"),
     ("Many of those in a short time can slightly dent your score.", "Too many?|Small dent.", HERO(), ["dent"], "Axis Bank")],
 f3=[("And the big one. There's no single official 'good' score.", "No single|'good' cutoff.", HERO("Many lenders treat 750+ as good"), ["big", "single"], "Bajaj Housing Finance, Airtel")],
 myth="Checking your score lowers it", truth=("Self-checks are soft enquiries", "TRUE"),
 v1="Verdict. 'Checking lowers it' is false.", v2=("Only lender checks for new credit count as hard enquiries.", "Only lenders'|checks count.", ["lender"]),
 cover=["Does checking", "your score", "lower it?"], cover_sub="Credit score myths, cleared up in 60 seconds.",
 titles=["Does Checking Your CIBIL Score Lower It? No.", "CIBIL Score Explained in 60 Seconds", "Soft vs Hard Credit Enquiries, Explained"],
 summary="In India, CIBIL scores run from 300 to 900. Checking your own score is a soft enquiry and doesn't lower it. Hard enquiries come from lenders when you apply for credit; many in a short time can slightly dent it.",
 tags=["#CIBIL", "#CreditScore", "#Money", "#India"], pinned="Have you checked your score this year? 👇", poll=["Thought checking hurts?", "Yes 😬", "No ✅"],
 sources=[["Axis Bank: Check your credit score", "https://www.axis.bank.in/check-your-credit-score/"], ["Bajaj Housing Finance: CIBIL score ranges", "https://www.bajajhousingfinance.in/cibil-score-ranges"], ["BankBazaar: What is CIBIL score", "https://www.bankbazaar.com/cibil.html"], ["CIBIL", "https://www.cibil.com/choose-your-plan"]],
 removed=["Exact band labels (Poor/Good/Excellent): sources disagree, so the video says there's no single cutoff."]))

# 13 ────────────────────────────────────────── Rule of 72
T.append(dict(slug="rule_of_72", topic="MONEY",
 hook=("There's a one-line trick to know when your money doubles.", "When does money|double?", S(text="72", count=False, label="THE MAGIC NUMBER", color="accent"), ["doubles."]),
 q=("It's called the Rule of seventy-two.", "The Rule|of 72.", ["seventy-two."]),
 ctx=[("Compound interest means you earn interest on your interest.", "Interest on|interest.", HERO(), ["interest."], "Investor.gov, Investopedia"),
      ("That makes money grow faster over time.", "Growth|speeds up.", {"type": "stock_drop", "pct": 100, "direction": "up", "label": "COMPOUNDING"}, ["faster"], "Investor.gov")],
 f1=[("Fact one. Divide seventy-two by your yearly return.", "72 ÷ your|yearly return.", S(text="72 ÷ rate", count=False, label="YEARS TO DOUBLE"), ["one.", "Divide"], "CFI, Investopedia")],
 f2=[("Fact two. At eight percent a year, money doubles in about nine years.", "8% a year:|~9 years.", S(text="72 ÷ 8 = 9", count=False, label="YEARS TO DOUBLE", color="accent"), ["two.", "nine"], "CFI, Investopedia")],
 f3=[("And the big one. It works against you too.", "It works|both ways.", HERO(), ["big", "against"], "CFI, Investopedia"),
     ("At six percent inflation, prices double in about twelve years.", "6% inflation:|prices double ~12 yrs.", S(text="72 ÷ 6 = 12", count=False, label="YEARS FOR PRICES TO DOUBLE", color="red"), ["twelve"], "CFI, Investopedia")],
 myth="The Rule of 72 is exact", truth=("A close estimate", "TRUE"),
 v1="Verdict. 'It's exact' is false.", v2=("It's a quick estimate, most accurate for moderate rates.", "A quick|estimate.", ["estimate,"]),
 cover=["When will", "your money", "double?"], cover_sub="The Rule of 72, in 60 seconds.",
 titles=["When Will Your Money Double? The Rule of 72", "The Rule of 72 Explained in 60 Seconds", "How Inflation Doubles Prices: The Rule of 72"],
 summary="The Rule of 72: divide 72 by the yearly rate to estimate years to double. At 8%, money doubles in about 9 years. It works against you too: at 6% inflation, prices double in about 12 years. It's an estimate.",
 tags=["#PersonalFinance", "#Investing", "#Money", "#Explained"], pinned="What return do you expect on your savings? 👇", poll=["Knew the Rule of 72?", "Yes 💰", "No 🤯"],
 sources=[["Investopedia: Rule of 72", "https://www.investopedia.com/terms/r/ruleof72.asp"], ["Corporate Finance Institute: Rule of 72", "https://corporatefinanceinstitute.com/resources/wealth-management/rule-of-72/"], ["Investor.gov: Compound interest calculator", "https://www.investor.gov/financial-tools-calculators/calculators/compound-interest-calculator"]],
 removed=["Not financial advice: illustrative maths only."]))

# 14 ────────────────────────────────────────── RBI inflation target
T.append(dict(slug="inflation_target", topic="ECONOMY",
 hook=("India's inflation target is four percent… not zero.", "Target: 4%.|Not zero.", S(text="4%", count=False, label="RBI INFLATION TARGET", color="accent"), ["four"]),
 q=("Why would anyone want prices to rise?", "Why want prices|to rise?", ["rise?"]),
 ctx=[("Inflation is how fast prices rise overall.", "Inflation =|price rise speed.", HERO(), ["prices"], "IMF, RBI"),
      ("India measures it with the Consumer Price Index.", "Measured by|CPI.", HERO(), ["Consumer"], "Outlook Money, Drishti IAS")],
 f1=[("Fact one. RBI's target is four percent, with a band of two to six.", "4%, with a|2–6% band.", S(text="4% ±2", count=False, label="RBI TARGET", color="accent"), ["one.", "four"], "Outlook Money, Drishti IAS")],
 f2=[("Fact two. That target was renewed through March 2031.", "Renewed to|March 2031.", CAL("MAR", "31", "2031"), ["two.", "2031."], "Outlook Money, Drishti IAS")],
 f3=[("And the big one. Prices falling can hurt too, as people delay spending.", "Falling prices|hurt too.", HERO("That's called deflation"), ["big", "delay"], "IMF"),
     ("If RBI misses the band three quarters in a row, it must explain why.", "Miss 3 quarters?|Explain why.", HERO(), ["explain"], "Outlook Money, Drishti IAS")],
 myth="Zero inflation is the goal", truth=("Target is a steady 4%", "TRUE"),
 v1="Verdict. 'Zero is the goal' is false.", v2=("A small, steady rise is the target: four percent.", "Target:|4%.", ["four"]),
 cover=["Why India", "targets 4%", "inflation"], cover_sub="Why zero isn't the goal, in 60 seconds.",
 titles=["Why India's Inflation Target Is 4%, Not 0%", "RBI's Inflation Target Explained", "Inflation Explained in 60 Seconds"],
 summary="Inflation is how fast prices rise. India's target, renewed through March 2031, is 4% CPI inflation with a 2–6% band. Falling prices (deflation) can hurt too, as people delay spending.",
 tags=["#Inflation", "#RBI", "#Economy", "#India"], pinned="What price rise have you noticed most this year? 👇", poll=["Thought 0% was the goal?", "Yes 🤔", "No 📈"],
 sources=[["Outlook Money: RBI to maintain 4% target until 2031", "https://www.outlookmoney.com/banking/rbi-to-maintain-4-per-cent-inflation-target-until-2031-centre"], ["Drishti IAS: India retains 4% inflation target", "https://www.drishtiias.com/daily-updates/daily-news-analysis/india-retains-4-inflation-target-for-rbi"], ["IMF F&D: Inflation, back to basics", "https://www.imf.org/external/pubs/ft/fandd/2010/03/basics.htm"]]))

# 15 ────────────────────────────────────────── Sensex & Nifty
T.append(dict(slug="sensex_nifty", topic="MARKETS",
 hook=("Sensex and Nifty are not the whole stock market.", "Not the whole|market.", TAGS("Sensex", "Nifty 50"), ["not"]),
 q=("So what are they, really?", "So what|are they?", ["really?"]),
 ctx=[("They're indexes: scorecards for a group of big companies.", "Indexes =|scorecards.", HERO(), ["scorecards"], "Wikipedia, NSE Indices"),
      ("When they rise, those companies' shares rose overall.", "Index up =|those shares up.", {"type": "stock_drop", "pct": 1.2, "direction": "up", "label": "INDEX"}, ["rise,"], "Wikipedia, NSE Indices")],
 f1=[("Fact one. Sensex tracks thirty companies on the BSE.", "Sensex:|30 companies.", S(value=30, label="SENSEX COMPANIES", sub="Bombay Stock Exchange"), ["one.", "thirty"], "Wikipedia, Business Standard")],
 f2=[("Fact two. Nifty fifty tracks fifty companies on the NSE.", "Nifty 50:|50 companies.", S(value=50, label="NIFTY 50 COMPANIES", sub="National Stock Exchange", color="accent"), ["two.", "fifty"], "NSE Indices, Britannica")],
 f3=[("And the big one. Thousands of listed companies are in neither.", "Thousands|left out.", HERO("Indexes show the big names only"), ["big", "Thousands"], "Wikipedia, NSE Indices")],
 myth="Sensex is the whole market", truth=("A snapshot of big firms", "TRUE"),
 v1="Verdict. 'Sensex is the whole market' is false.", v2=("They're a snapshot of the biggest companies, not every stock.", "A snapshot,|not everything.", ["snapshot"]),
 cover=["What is", "Sensex,", "really?"], cover_sub="Sensex vs Nifty in 60 seconds.",
 titles=["Sensex vs Nifty Explained in 60 Seconds", "What Sensex Really Measures", "Sensex Isn't the Whole Stock Market"],
 summary="Sensex tracks 30 big companies on the BSE; the Nifty 50 tracks 50 on the NSE. They're scorecards for the biggest names, not the whole market: thousands of listed companies are in neither.",
 tags=["#Sensex", "#Nifty", "#StockMarket", "#India"], pinned="Do you follow the markets daily? 👇", poll=["Thought Sensex = market?", "Yes 📊", "No 🧠"],
 sources=[["Wikipedia: BSE SENSEX", "https://en.wikipedia.org/wiki/BSE_SENSEX"], ["Business Standard: What is Sensex", "https://www.business-standard.com/about/what-is-sensex"], ["NSE Indices: Nifty 50", "https://www.niftyindices.com/indices/equity/broad-based-indices/NIFTY--50"], ["Britannica: Bombay Stock Exchange", "https://www.britannica.com/topic/Bombay-Stock-Exchange"]],
 removed=["Not investment advice."]))

# 16 ────────────────────────────────────────── IPO
T.append(dict(slug="ipo", topic="MARKETS",
 hook=("An IPO does not guarantee you a profit.", "IPO = profit?|Not always.", S(text="IPO", count=False, label="INITIAL PUBLIC OFFERING", color="accent"), ["not"]),
 q=("So what is an IPO, really?", "What is an|IPO?", ["really?"]),
 ctx=[("IPO stands for Initial Public Offering.", "Initial Public|Offering.", HERO(), ["Initial"], "Investor.gov, SEBI"),
      ("It's when a company first sells shares to the public.", "First shares|for the public.", TWO("Private company", "Listed company"), ["first"], "Investor.gov, SEBI")],
 f1=[("Fact one. In India, the market regulator SEBI oversees IPOs.", "Regulator:|SEBI.", HERO(), ["one.", "SEBI"], "SEBI, NSE")],
 f2=[("Fact two. Companies publish a document with risks you should read.", "Read the|risk factors.", HERO("It's called the offer document"), ["two.", "risks"], "SEBI, Investor.gov")],
 f3=[("And the big one. Shares can list below their IPO price.", "Can list|below price.", {"type": "stock_drop", "pct": 10, "label": "LISTING DAY"}, ["big", "below"], "Investor.gov, SEBI")],
 myth="IPOs always make money", truth=("Prices can fall too", "TRUE"),
 v1="Verdict. 'IPOs always pay' is false.", v2=("Like any share, an IPO can go up or down.", "Up or|down.", ["down."]),
 cover=["Is every", "IPO a", "win?"], cover_sub="What an IPO really is, in 60 seconds.",
 titles=["What Is an IPO? Explained in 60 Seconds", "Do IPOs Always Make Money? No.", "IPO Basics Before You Apply"],
 summary="An IPO is when a company first sells shares to the public. In India, SEBI oversees IPOs and companies publish offer documents with risk factors. Shares can list below their issue price.",
 tags=["#IPO", "#StockMarket", "#Investing", "#India"], pinned="Have you ever applied for an IPO? 👇", poll=["Thought IPOs always win?", "Yes 🚀", "No 📉"],
 sources=[["Investor.gov: Initial public offerings", "https://www.investor.gov/introduction-investing/investing-basics/glossary/initial-public-offering-ipo"], ["SEBI: Guide to understand an offer document", "https://www.sebi.gov.in/sebi_data/docfiles/20612_t.html"], ["NSE: How to invest in an IPO (PDF)", "https://nsearchives.nseindia.com/web/sites/default/files/inline-files/How_to_invest_in_Intial_Public_Offer.pdf"]],
 removed=["Not investment advice."]))

# 17 ────────────────────────────────────────── Recession
T.append(dict(slug="recession", topic="ECONOMY",
 hook=("'Two bad quarters' is not the official recession rule everywhere.", "Two bad quarters?|Not official.", S(text="2 quarters", count=False, label="THE RULE OF THUMB"), ["not"]),
 q=("So what is a recession?", "So what is a|recession?", ["recession?"]),
 ctx=[("It's a broad fall in economic activity.", "A broad|slowdown.", {"type": "stock_drop", "pct": 3, "label": "ECONOMIC ACTIVITY"}, ["fall"], "IMF, NBER"),
      ("Jobs, spending and production all weaken.", "Jobs, spending,|output fall.", TAGS("Jobs", "Spending", "Output"), ["weaken."], "IMF, NBER")],
 f1=[("Fact one. A common rule of thumb is two quarters of shrinking GDP.", "Rule of thumb:|2 quarters.", S(value=2, label="QUARTERS OF FALLING GDP"), ["one.", "two"], "IMF, NBER")],
 f2=[("Fact two. In the US, an expert committee looks at much more than GDP.", "US: experts|decide.", TAGS("Jobs", "Income", "Spending", "Output"), ["two.", "committee"], "NBER, IMF")],
 f3=[("And the big one. They often confirm a recession months after it starts.", "Confirmed|months later.", HERO("They wait for solid data"), ["big", "months"], "NBER")],
 myth="2 quarters is the official rule", truth=("It's a rule of thumb", "TRUE"),
 v1="Verdict. 'Two quarters is official' is false.", v2=("It's a handy rule of thumb, not an official definition everywhere.", "A rule of|thumb.", ["thumb,"]),
 cover=["What really", "is a", "recession?"], cover_sub="The two-quarter rule, fact-checked.",
 titles=["What Is a Recession, Really?", "The 'Two Quarters' Recession Rule, Fact-Checked", "Recession Explained in 60 Seconds"],
 summary="Two quarters of falling GDP is a common rule of thumb, not an official definition everywhere. In the US, the NBER committee weighs jobs, income, spending and output, often confirming recessions months later.",
 tags=["#Recession", "#Economy", "#Finance", "#Explained"], pinned="Does your country feel like it's in a slowdown? 👇", poll=["Thought 2 quarters was official?", "Yes 📉", "No 🧠"],
 sources=[["IMF: Recession, back to basics", "https://www.imf.org/external/pubs/ft/fandd/basics/recess.htm"], ["NBER: Business cycle dating", "https://www.nber.org/research/business-cycle-dating"]]))

# 18 ────────────────────────────────────────── GDP
T.append(dict(slug="gdp", topic="ECONOMY",
 hook=("GDP does not measure how happy a country is.", "GDP isn't|happiness.", S(text="GDP", count=False, label="GROSS DOMESTIC PRODUCT", color="accent"), ["not"]),
 q=("So what does it measure?", "So what does|it measure?", ["measure?"]),
 ctx=[("GDP means Gross Domestic Product.", "Gross Domestic|Product.", HERO(), ["Gross"], "IMF"),
      ("It's the value of all final goods and services a country produces.", "Value of all|goods + services.", TAGS("Goods", "Services"), ["value"], "IMF, Britannica")],
 f1=[("Fact one. It's usually measured per quarter, or per year.", "Per quarter|or per year.", HERO(), ["one.", "quarter,"], "IMF, Britannica")],
 f2=[("Fact two. It can be counted three ways: spending, income, or production.", "3 ways to|count it.", TAGS("Spending", "Income", "Production"), ["two.", "three"], "IMF, Britannica")],
 f3=[("And the big one. Unpaid work, like cooking at home, isn't counted.", "Home cooking?|Not counted.", HERO("Neither is wellbeing", "x"), ["big", "Unpaid"], "IMF, Wikipedia")],
 myth="GDP measures wellbeing", truth=("It measures output", "TRUE"),
 v1="Verdict. 'GDP measures happiness' is false.", v2=("GDP measures economic output, not how well people live.", "Output,|not wellbeing.", ["output,"]),
 cover=["What does", "GDP really", "measure?"], cover_sub="GDP in 60 seconds, and what it misses.",
 titles=["What Is GDP? Explained in 60 Seconds", "GDP Doesn't Measure Happiness", "What GDP Misses (Your Unpaid Work)"],
 summary="GDP is the value of all final goods and services a country produces in a period, counted by spending, income or production. It leaves out unpaid work like home cooking, and doesn't measure wellbeing.",
 tags=["#GDP", "#Economy", "#India", "#Explained"], pinned="Should countries measure happiness too? 👇", poll=["Thought GDP = wellbeing?", "Yes 📊", "No 🙂"],
 sources=[["Wikipedia: Gross domestic product", "https://en.wikipedia.org/wiki/Gross_domestic_product"], ["IMF F&D: Recession, back to basics", "https://www.imf.org/external/pubs/ft/fandd/basics/recess.htm"], ["Britannica: Gross domestic product", "https://www.britannica.com/topic/gross-domestic-product"]]))

# 19 ────────────────────────────────────────── Tariffs
T.append(dict(slug="tariffs", topic="TRADE",
 hook=("A tariff is not paid by the other country.", "Who pays|a tariff?", TWO("Foreign goods arrive", "Importer pays tax"), ["not"]),
 q=("So who actually pays it?", "Who actually|pays?", ["actually"]),
 ctx=[("A tariff is a tax on goods coming into a country.", "A tax on|imports.", HERO(), ["tax"], "Tax Foundation, Britannica"),
      ("Governments use them to protect local industries, or as leverage.", "Protection or|leverage.", TAGS("Protect industry", "Leverage"), ["protect"], "Tax Foundation, Britannica")],
 f1=[("Fact one. It's collected at the border, from the importing business.", "The importer|pays at the border.", HERO(), ["one.", "importing"], "Tax Foundation, Britannica")],
 f2=[("Fact two. That cost often passes on to shoppers through higher prices.", "Often: higher|shop prices.", {"type": "stock_drop", "pct": 5, "direction": "up", "label": "PRICES"}, ["two.", "higher"], "Tax Foundation")],
 f3=[("And the big one. Foreign sellers may cut prices to compete, sharing the cost.", "Sometimes|shared.", HERO("Who bears it depends on the market"), ["big", "sharing"], "Tax Foundation")],
 myth="The other country pays", truth=("Importers pay at the border", "TRUE"),
 v1="Verdict. 'The other country pays' is false.", v2=("Importers pay it, and costs often reach shoppers.", "Importers pay.|Shoppers feel it.", ["Importers"]),
 cover=["Who really", "pays a", "tariff?"], cover_sub="Trade wars, explained in 60 seconds.",
 titles=["Who Really Pays a Tariff?", "Tariffs Explained in 60 Seconds", "Tariffs: The Other Country Doesn't Pay"],
 summary="A tariff is a tax on imported goods, collected at the border from the importing business. The cost often reaches shoppers as higher prices, though foreign sellers sometimes cut prices and share it.",
 tags=["#Tariffs", "#Trade", "#Economy", "#Explained"], pinned="Have tariffs changed prices where you live? 👇", poll=["Thought the other country pays?", "Yes 🌍", "No 🧾"],
 sources=[["Tax Foundation: Tariff", "https://taxfoundation.org/taxedu/glossary/tariff/"], ["Britannica: Tariff", "https://www.britannica.com/topic/tariff"]]))

# 20 ────────────────────────────────────────── Strait of Hormuz
T.append(dict(slug="strait_of_hormuz", topic="ENERGY",
 hook=("About a fifth of the world's oil passes through one narrow strait.", "1/5 of world oil.|One strait.", S(text="~20%", count=False, label="OF WORLD OIL USE", color="accent"), ["fifth"]),
 q=("Why does that matter to you?", "Why does it|matter to you?", ["matter"]),
 ctx=[("It's the Strait of Hormuz, between Iran and Oman.", "The Strait|of Hormuz.", TAGS("Iran", "Oman"), ["Hormuz,"], "EIA"),
      ("It links the Persian Gulf to the open ocean.", "Gulf to|open ocean.", HERO(), ["links"], "EIA")],
 f1=[("Fact one. About twenty million barrels a day flowed through it in 2024.", "~20 million|barrels a day.", S(value=20, suffix="M", label="BARRELS PER DAY (2024)"), ["one.", "twenty"], "EIA, Statista")],
 f2=[("Fact two. Most of that crude oil heads to Asia.", "Most goes|to Asia.", S(text="84%", count=False, label="OF CRUDE TO ASIA (2024)", color="accent"), ["two.", "Asia."], "EIA")],
 f3=[("And the big one. Pipelines can bypass only a small part of it.", "Bypass:|only a little.", {"type": "split_bar", "total": "~20M barrels/day", "parts": [{"value": 2.6, "value_text": "2.6M", "label": "Bypass", "color": "accent"}, {"value": 17.4, "value_text": "Rest", "label": "No alternative route", "color": "ink"}]}, ["big", "small"], "EIA")],
 myth="Oil can easily go around it", truth=("Bypass covers a small part", "TRUE"),
 v1="Verdict. 'Oil can just go around' is false.", v2=("Disruption there can move fuel prices worldwide.", "It can move|global prices.", ["worldwide."]),
 cover=["One strait.", "A fifth of", "world oil."], cover_sub="Why the Strait of Hormuz matters to your fuel price.",
 titles=["Why the Strait of Hormuz Matters to Your Fuel Price", "One Strait, a Fifth of the World's Oil", "Strait of Hormuz Explained in 60 Seconds"],
 summary="About 20 million barrels a day, roughly a fifth of world oil use, passed through the Strait of Hormuz in 2024 (EIA), mostly to Asia. Pipelines can bypass only about 2.6 million barrels a day.",
 tags=["#Oil", "#Energy", "#Geopolitics", "#Explained"], pinned="How much did fuel cost where you live this month? 👇", poll=["Knew a fifth of oil goes here?", "Yes 🛢️", "No 😮"],
 sources=[["EIA: Strait of Hormuz chokepoint (2025)", "https://www.eia.gov/todayinenergy/detail.php?id=65504"], ["EIA: Strait of Hormuz (2023 data)", "https://www.eia.gov/todayinenergy/detail.php?id=63446"]],
 removed=["Current conflict details: kept out so the explainer stays evergreen and neutral."]))

# 21 ────────────────────────────────────────── UN Security Council
T.append(dict(slug="un_security_council", topic="WORLD",
 hook=("UN General Assembly votes are not binding.", "UN votes?|Not binding.", HERO("Most people assume they are", "x"), ["not"]),
 q=("So which UN body can actually order things?", "Who can|order things?", ["order"]),
 ctx=[("The UN has a General Assembly with every member country.", "Assembly:|all members.", HERO(), ["every"], "UN"),
      ("And a Security Council, with fifteen members.", "Council:|15 members.", S(value=15, label="SECURITY COUNCIL MEMBERS"), ["fifteen"], "UN")],
 f1=[("Fact one. Five are permanent: the US, China, Russia, the UK and France.", "5 permanent|members.", TAGS("US", "China", "Russia", "UK", "France"), ["one.", "permanent:"], "UN")],
 f2=[("Fact two. Each of those five can veto a resolution.", "Each has|a veto.", HERO("One 'no' blocks it", "x"), ["two.", "veto"], "UN")],
 f3=[("And the big one. Council decisions bind members. Assembly resolutions don't.", "Council binds.|Assembly advises.", {"type": "versus", "sides": [{"name": "COUNCIL", "big": "Binding", "mark": "check", "lines": ["decisions"], "color": "accent"}, {"name": "ASSEMBLY", "big": "Advice", "mark": "dot", "lines": ["recommendations"], "color": "ink"}]}, ["big", "bind"], "UN")],
 myth="General Assembly votes are binding", truth=("Only Council decisions bind", "TRUE"),
 v1="Verdict. 'Assembly votes are binding' is false.", v2=("The Assembly recommends. The Security Council can decide.", "Assembly advises.|Council decides.", ["decide."]),
 cover=["Who really", "runs the", "UN?"], cover_sub="The UN Security Council, explained in 60 seconds.",
 titles=["Who Really Has Power at the UN?", "UN Security Council Explained in 60 Seconds", "What Is the UN Veto?"],
 summary="The UN General Assembly includes every member, but its resolutions are recommendations. The 15-member Security Council's decisions bind members, and its five permanent members can each veto.",
 tags=["#UN", "#WorldNews", "#Geopolitics", "#Explained"], pinned="Should the veto system change? Share respectfully 👇", poll=["Thought UN votes were binding?", "Yes 🌐", "No 🧠"],
 sources=[["UN Security Council: Current members", "https://www.un.org/securitycouncil/content/current-members"], ["UN General Assembly: Functions and powers", "https://www.un.org/en/ga/about/background.shtml"], ["UN Charter, Article 25", "https://www.un.org/en/about-us/un-charter/chapter-5"]]))

# 22 ────────────────────────────────────────── NATO Article 5
T.append(dict(slug="nato_article5", topic="WORLD",
 hook=("NATO's Article 5 does not mean automatic war.", "Article 5 =|automatic war?", S(text="Art. 5", count=False, label="NATO TREATY", color="accent"), ["not"]),
 q=("So what does it actually say?", "What does it|actually say?", ["actually"]),
 ctx=[("NATO is a military alliance founded in 1949.", "Founded|1949.", S(text="1949", count=False, label="NATO FOUNDED"), ["1949."], "NATO"),
      ("Article 5 says an attack on one is an attack on all.", "Attack on one =|attack on all.", HERO(), ["all."], "NATO")],
 f1=[("Fact one. Each ally takes the action it deems necessary.", "Each ally|decides.", HERO("Not necessarily troops"), ["one.", "necessary."], "NATO, Wikipedia")],
 f2=[("Fact two. It has been invoked only once in history.", "Invoked|only once.", S(value=1, label="TIMES INVOKED"), ["two.", "once"], "NATO, Wikipedia")],
 f3=[("And the big one. That was after the September eleventh attacks, in 2001.", "After 9/11,|in 2001.", CAL("SEP", "12", "2001"), ["big", "eleventh"], "NATO, Wikipedia")],
 myth="Article 5 means automatic war", truth=("Each ally chooses its response", "TRUE"),
 v1="Verdict. 'Automatic war' is false.", v2=("It's a promise to help, but each ally chooses how.", "Help: yes.|How: each decides.", ["chooses"]),
 cover=["NATO's", "Article 5,", "explained."], cover_sub="What 'an attack on one is an attack on all' really means.",
 titles=["NATO Article 5 Explained in 60 Seconds", "Does Article 5 Mean Automatic War? No.", "The Only Time NATO Invoked Article 5"],
 summary="NATO's Article 5 says an attack on one ally is an attack on all, but each ally takes the action it deems necessary. It has been invoked only once: after the September 11, 2001 attacks.",
 tags=["#NATO", "#WorldNews", "#Geopolitics", "#Explained"], pinned="What should we explain next about world alliances? 👇", poll=["Thought it meant automatic war?", "Yes ⚔️", "No 🧠"],
 sources=[["NATO: Collective defence and Article 5", "https://www.nato.int/cps/en/natohq/topics_110496.htm"], ["Wikipedia: 2001 NATO Article 5 contingency", "https://en.wikipedia.org/wiki/2001_NATO_Article_5_contingency"]]))

# 23 ────────────────────────────────────────── G20
T.append(dict(slug="g20", topic="WORLD",
 hook=("The G20 is not twenty countries.", "G20 = 20|countries?", S(text="G20", count=False, label="GROUP OF TWENTY", color="accent"), ["not"]),
 q=("So who's actually in it?", "Who's actually|in it?", ["actually"]),
 ctx=[("The G20 brings together the world's major economies.", "The big|economies.", HERO(), ["major"], "G20, CNBC"),
      ("Its leaders meet every year at a summit.", "A yearly|summit.", HERO(), ["summit."], "G20, CNBC")],
 f1=[("Fact one. It has nineteen countries, plus the European Union.", "19 countries|+ the EU.", {"type": "split_bar", "total": "G20 members", "parts": [{"value": 19, "value_text": "19 countries", "label": "Countries", "color": "ink"}, {"value": 3, "value_text": "EU", "label": "European Union", "color": "accent"}, {"value": 3, "value_text": "AU", "label": "African Union", "color": "muted"}]}, ["one.", "nineteen"], "CNBC, RNZ")],
 f2=[("Fact two. In 2023, the African Union joined as a permanent member.", "2023: African|Union joins.", CAL("SEP", "9", "2023"), ["two.", "African"], "CNBC, RNZ")],
 f3=[("And the big one. That happened at India's summit, in New Delhi.", "Announced in|New Delhi.", HERO("Under India's G20 presidency"), ["big", "India's"], "CNBC, RNZ")],
 myth="G20 is 20 countries", truth=("19 countries + EU + AU", "TRUE"),
 v1="Verdict. 'Twenty countries' is false.", v2=("It's nineteen countries plus two unions: the EU and the African Union.", "19 countries +|2 unions.", ["two"]),
 cover=["Is the G20", "really 20", "countries?"], cover_sub="Who's in the G20, in 60 seconds.",
 titles=["The G20 Isn't 20 Countries. Here's Who's In", "G20 Explained in 60 Seconds", "How India Brought the African Union Into the G20"],
 summary="The G20 is 19 countries plus the European Union and, since India's New Delhi summit in September 2023, the African Union as a permanent member.",
 tags=["#G20", "#India", "#WorldNews", "#Explained"], pinned="Which G20 country should we explain next? 👇", poll=["Thought it was 20 countries?", "Yes 🌍", "No 🧠"],
 sources=[["CNBC: G20 admits African Union (Sep 9 2023)", "https://www.cnbc.com/2023/09/09/g20-african-union-au.html"], ["RNZ: G20 admits AU at New Delhi summit", "https://www.rnz.co.nz/news/world/497646/g20-admits-african-union-as-permanent-member-at-new-delhi-summit"]]))

# 24 ────────────────────────────────────────── IST
T.append(dict(slug="india_time_zone", topic="INDIA",
 hook=("India did not always have one time zone.", "One time zone?|Not always.", S(text="UTC+5:30", count=False, label="INDIAN STANDARD TIME", color="accent"), ["not"]),
 q=("So how did we end up with IST?", "How did we|get IST?", ["IST?"]),
 ctx=[("Today, all of India runs on Indian Standard Time.", "All of India:|one clock.", HERO(), ["all"], "Wikipedia, timeanddate"),
      ("That's five and a half hours ahead of UTC.", "5½ hours|ahead of UTC.", S(text="+5:30", count=False, label="AHEAD OF UTC"), ["five"], "timeanddate, Wikipedia")],
 f1=[("Fact one. It's based on a line of longitude near Mirzapur, in Uttar Pradesh.", "Based near|Mirzapur.", S(text="82.5°E", count=False, label="REFERENCE LONGITUDE"), ["one.", "Mirzapur,"], "Wikipedia, Live History India")],
 f2=[("Fact two. India adopted IST nationwide in 1947, soon after independence.", "Adopted|1947.", CAL("SEP", "1", "1947"), ["two.", "1947,"], "Wikipedia, Maps of India")],
 f3=[("And the big one. Mumbai kept its own Bombay Time until 1955.", "Bombay Time|until 1955.", S(text="1955", count=False, label="BOMBAY TIME ENDS", color="accent"), ["big", "1955."], "Wikipedia, Live History India")],
 myth="India always had one time zone", truth=("Bombay Time lasted to 1955", "TRUE"),
 v1="Verdict. 'Always one time zone' is false.", v2=("Mumbai switched to IST only in 1955.", "Mumbai joined|in 1955.", ["1955."]),
 cover=["India had", "more than", "one clock."], cover_sub="The story of Indian Standard Time, in 60 seconds.",
 titles=["India Didn't Always Have One Time Zone", "Why IST Is UTC+5:30", "Bombay Time: The Clock Mumbai Kept Until 1955"],
 summary="IST is UTC+5:30, based on 82.5°E near Mirzapur. India adopted it nationwide in 1947, but Mumbai kept its own Bombay Time until 1955.",
 tags=["#India", "#IST", "#History", "#Explained"], pinned="Should India have two time zones? 👇", poll=["Knew about Bombay Time?", "Yes 🕰️", "No 😮"],
 sources=[["Wikipedia: Indian Standard Time", "https://en.wikipedia.org/wiki/Indian_Standard_Time"], ["Wikipedia: Bombay Time", "https://en.wikipedia.org/wiki/Bombay_Time"], ["Live History India: When setting the clock divided the subcontinent", "https://livehistoryindia.com/story/eras/indian-standard-time"], ["timeanddate: India time zone", "https://timeanddate.com/time/zone/india"]],
 removed=["Calcutta Time (ended 1948) and the exact 1905/1906 adoption details, which sources state differently."]))

# 25 ────────────────────────────────────────── Black box
T.append(dict(slug="black_box", topic="AVIATION",
 hook=("A plane's black box is not black.", "The black box|isn't black.", S(text="Orange", count=False, label="REAL COLOUR", color="accent"), ["not"]),
 q=("So what is it, really?", "So what|is it?", ["really?"]),
 ctx=[("It's the flight recorder investigators look for after a crash.", "The flight|recorder.", HERO(), ["recorder"], "Airbus, NBC News"),
      ("It helps explain what went wrong.", "It explains|what happened.", HERO(), ["wrong."], "Airbus, NBC News")],
 f1=[("Fact one. It's painted bright orange, to be easier to find.", "Bright orange,|easy to find.", S(text="Orange", count=False, label="REAL COLOUR", color="accent"), ["one.", "orange,"], "Airbus, NBC News")],
 f2=[("Fact two. There are usually two: one records voices, one records flight data.", "Two boxes:|voice + data.", TAGS("Cockpit voice", "Flight data"), ["two.", "voices,"], "Airbus, NBC News")],
 f3=[("And the big one. They're built to survive huge impacts and fierce fires.", "Built for|crash + fire.", S(text="3,400 g", count=False, label="IMPACT STANDARD", sub="Plus over 1,000°C fire tests", color="red"), ["big", "survive"], "Airbus, Wikipedia")],
 myth="Black boxes are black", truth=("They're bright orange", "TRUE"),
 v1="Verdict. 'Black boxes are black' is false.", v2=("They're bright orange, so search teams can spot them.", "Orange, to be|found fast.", ["orange,"]),
 cover=["The black", "box isn't", "black."], cover_sub="What flight recorders really are, in 60 seconds.",
 titles=["Why a Plane's 'Black Box' Is Orange", "Black Boxes Explained in 60 Seconds", "How Flight Recorders Survive a Crash"],
 summary="Aircraft 'black boxes' are flight recorders painted bright orange to help recovery. There are usually two: cockpit voice and flight data. They're built to standards like 3,400 g impact and 1,000°C+ fire.",
 tags=["#Aviation", "#Planes", "#Science", "#Explained"], pinned="What aviation myth should we bust next? ✈️👇", poll=["Thought they were black?", "Yes ⬛", "No 🟧"],
 sources=[["Airbus: What is a black box and how does it work (2024)", "https://www.airbus.com/en/newsroom/stories/2024-05-what-is-a-black-box-and-how-does-it-work"], ["NBC News: Plane black boxes", "https://www.nbcdfw.com/news/national-international/plane-black-boxes-plane-crash-investigations/"], ["Wikipedia: Flight recorder", "https://en.wikipedia.org/wiki/Flight_recorder"]]))

# 26 ────────────────────────────────────────── Bitcoin
T.append(dict(slug="bitcoin", topic="CRYPTO",
 hook=("Bitcoin is not truly anonymous.", "Bitcoin isn't|anonymous.", S(text="₿", count=False, label="BITCOIN", color="accent"), ["not"]),
 q=("So who can see your transactions?", "Who can see|your payments?", ["see"]),
 ctx=[("Bitcoin launched in 2009, created by someone using the name Satoshi Nakamoto.", "Launched|2009.", S(text="2009", count=False, label="BITCOIN LAUNCHED"), ["2009,"], "bitcoin.org, Britannica"),
      ("Its total supply is capped at twenty-one million coins.", "Max supply:|21 million.", S(value=21, suffix="M", label="MAX BITCOINS"), ["twenty-one"], "bitcoin.org, Britannica")],
 f1=[("Fact one. Every transaction is recorded on a public ledger, the blockchain.", "Every payment:|public ledger.", HERO("Anyone can view it"), ["one.", "public"], "bitcoin.org, Britannica")],
 f2=[("Fact two. Wallets show as addresses, not names. That's pseudonymous.", "Addresses,|not names.", HERO("Pseudonymous, not anonymous"), ["two.", "pseudonymous."], "bitcoin.org, Britannica")],
 f3=[("And the big one. Linking an address to a person can reveal their whole history.", "One link reveals|the history.", ROWS(("ADDRESS", "Seen by everyone", "", "dot"), ("LINKED TO YOU", "All past payments visible", "", "x")), ["big", "whole"], "bitcoin.org")],
 myth="Bitcoin is anonymous", truth=("Public and pseudonymous", "TRUE"),
 v1="Verdict. 'Bitcoin is anonymous' is false.", v2=("Every payment is public. Only the names are hidden.", "Payments public.|Names hidden.", ["public."]),
 cover=["Is Bitcoin", "really", "anonymous?"], cover_sub="How the blockchain sees everything, in 60 seconds.",
 titles=["Is Bitcoin Anonymous? Not Really.", "Bitcoin Explained in 60 Seconds", "Why Every Bitcoin Payment Is Public"],
 summary="Bitcoin launched in 2009 with a 21 million coin cap. Every transaction is recorded on a public blockchain under addresses, not names: pseudonymous, not anonymous.",
 tags=["#Bitcoin", "#Crypto", "#Tech", "#Explained"], pinned="Do you think crypto is private? 👇", poll=["Thought Bitcoin was anonymous?", "Yes 🕶️", "No 🔍"],
 sources=[["bitcoin.org: FAQ", "https://bitcoin.org/en/faq"], ["bitcoin.org: Protect your privacy", "https://bitcoin.org/en/protect-your-privacy"], ["Britannica: Bitcoin", "https://www.britannica.com/money/bitcoin"]],
 removed=["Not investment advice."]))

# 27 ────────────────────────────────────────── Deepfakes
T.append(dict(slug="deepfakes", topic="AI",
 hook=("You can't always spot a deepfake just by looking.", "Can you spot|a deepfake?", PHONE | {"banner": "VIDEO", "banner_sub": "Real or fake?"}, ["always"]),
 q=("So how do you protect yourself?", "How do you|stay safe?", ["protect"]),
 ctx=[("A deepfake is a fake video or audio, made with AI.", "AI-made|fake media.", TAGS("Fake video", "Fake voice"), ["fake"], "MIT Media Lab, Britannica"),
      ("It can show real people saying things they never said.", "Words they|never said.", HERO(), ["never"], "MIT Media Lab, Britannica")],
 f1=[("Fact one. Some fakes have tell-tale glitches, like odd blinking or lip sync.", "Glitches:|eyes, lips.", TAGS("Odd blinking", "Lip sync", "Lighting"), ["one.", "glitches,"], "MIT Media Lab")],
 f2=[("Fact two. But better tools make those glitches harder to see.", "Glitches are|disappearing.", HERO(), ["two.", "harder"], "MIT Media Lab, Britannica")],
 f3=[("And the big one. Check the source, not just the pixels.", "Check the|source.", ROWS(("WHO POSTED IT?", "Official account?", "", "q"), ("WHERE ELSE?", "Trusted outlets reporting it?", "", "q"), ("TOO SHOCKING?", "Pause before sharing", "", "check")), ["big", "source,"], "MIT Media Lab, Britannica")],
 myth="You can always spot one by eye", truth=("Check the source", "TRUE"),
 v1="Verdict. 'Always spot it by eye' is false.", v2=("Verify where it came from before you share it.", "Verify before|you share.", ["Verify"]),
 cover=["Can you", "spot a", "deepfake?"], cover_sub="How to protect yourself from AI fakes, in 60 seconds.",
 titles=["Can You Spot a Deepfake? Not Always.", "Deepfakes Explained in 60 Seconds", "3 Checks Before You Share a Viral Video"],
 summary="Deepfakes are AI-made fake videos or audio. Some show glitches like odd blinking or lip sync, but better tools hide them. The safest check: who posted it, and are trusted outlets reporting it?",
 tags=["#Deepfake", "#AI", "#FactCheck", "#Explained"], pinned="Have you ever been fooled by a fake video? 👇", poll=["Confident you can spot one?", "Yes 👀", "Not sure 🤔"],
 sources=[["MIT Media Lab: Detect Fakes", "https://www.media.mit.edu/projects/detect-fakes/overview/"], ["Britannica: Deepfake", "https://www.britannica.com/technology/deepfake"]]))

# 28 ────────────────────────────────────────── How AI chatbots work
T.append(dict(slug="ai_chatbots", topic="AI",
 hook=("AI chatbots don't look up answers in a fact database.", "AI chatbots|don't 'look up'.", {"type": "chip_glow", "label": "AI"}, ["don't"]),
 q=("So how do they answer you?", "So how do they|answer?", ["answer"]),
 ctx=[("They run on large language models, or LLMs.", "Large language|models.", S(text="LLM", count=False, label="LARGE LANGUAGE MODEL", color="accent"), ["language"], "IBM, Google"),
      ("These are trained on huge amounts of text.", "Trained on|huge text.", HERO(), ["huge"], "IBM, Google")],
 f1=[("Fact one. They predict the next word, again and again.", "They predict|the next word.", TAGS("The", "next", "word"), ["one.", "predict"], "IBM, Google")],
 f2=[("Fact two. That's why they can sound sure and still be wrong.", "Confident,|can be wrong.", HERO("Often called 'hallucinations'", "x"), ["two.", "wrong."], "IBM, Google")],
 f3=[("And the big one. Some chatbots connect to search to check facts.", "Some add|web search.", TWO("Model writes", "Search checks"), ["big", "search"], "IBM, Google")],
 myth="Chatbots look up a fact database", truth=("They predict text", "TRUE"),
 v1="Verdict. 'They look facts up' is false.", v2=("They predict text, so double-check important answers.", "Double-check|what matters.", ["double-check"]),
 cover=["How do AI", "chatbots", "really work?"], cover_sub="LLMs explained in 60 seconds.",
 titles=["How AI Chatbots Really Work", "Why AI Chatbots Can Be Confidently Wrong", "LLMs Explained in 60 Seconds"],
 summary="AI chatbots run on large language models trained on huge amounts of text. They predict the next word, which is why they can sound sure and still be wrong. Some connect to search to check facts.",
 tags=["#AI", "#ChatGPT", "#Tech", "#Explained"], pinned="What do you use AI chatbots for most? 👇", poll=["Thought AI looks things up?", "Yes 🤖", "No 🧠"],
 sources=[["IBM: What are large language models?", "https://www.ibm.com/think/topics/large-language-models"], ["Google for Developers: Introduction to LLMs", "https://developers.google.com/machine-learning/resources/intro-llms"]]))

# 29 ────────────────────────────────────────── Delhi winter air
T.append(dict(slug="delhi_air", topic="INDIA",
 hook=("Stubble burning is not the only reason Delhi's air turns toxic.", "Only stubble|burning?", S(text="AQI", count=False, label="AIR QUALITY INDEX", color="red"), ["only"]),
 q=("So why does winter get so bad?", "Why is winter|so bad?", ["winter"]),
 ctx=[("India rates air from zero to five hundred on the AQI.", "AQI:|0 to 500.", S(text="0–500", count=False, label="AQI SCALE"), ["five"], "CPCB, Wikipedia"),
      ("Above four hundred is 'severe'.", "400+ =|severe.", ROWS(("0–100", "Good to satisfactory", "", "check"), ("201–300", "Poor", "", "dot"), ("401–500", "Severe", "", "x")), ["severe'."], "CPCB")],
 f1=[("Fact one. In winter, cool air gets trapped under warmer air.", "Trapped|cold air.", HERO("Called a temperature inversion"), ["one.", "trapped"], "CPCB, Wikipedia")],
 f2=[("Fact two. Calm winds let smoke and dust pile up.", "No wind,|no escape.", TAGS("Vehicles", "Dust", "Industry"), ["two.", "Calm"], "CPCB, Wikipedia")],
 f3=[("And the big one. Crop fires in nearby states add a big seasonal spike.", "Crop fires|add a spike.", HERO("A big factor, but not the only one"), ["big", "spike."], "CPCB, Wikipedia")],
 myth="Stubble burning is the only cause", truth=("Weather + local sources too", "TRUE"),
 v1="Verdict. 'Only stubble burning' is false.", v2=("Winter weather traps pollution from many sources at once.", "Many sources,|trapped air.", ["many"]),
 cover=["Why Delhi's", "air turns", "toxic."], cover_sub="It's not only stubble burning. The winter science in 60s.",
 titles=["Why Delhi's Air Turns Toxic Every Winter", "Is Stubble Burning the Only Cause? No.", "AQI Explained in 60 Seconds"],
 summary="India's AQI runs 0–500; above 400 is severe. In winter, temperature inversions and calm winds trap pollution from vehicles, dust and industry, and crop fires in nearby states add a seasonal spike.",
 tags=["#Delhi", "#AirPollution", "#AQI", "#India"], pinned="What's the AQI in your city today? 👇", poll=["Thought it was only stubble?", "Yes 🔥", "No 🌫️"],
 sources=[["CPCB: National Air Quality Index", "https://cpcb.nic.in/National-Air-Quality-Index/"], ["Wikipedia: Air quality index (India)", "https://en.wikipedia.org/wiki/Air_quality_index"], ["Wikipedia: Air pollution in Delhi", "https://en.wikipedia.org/wiki/Air_pollution_in_Delhi"]]))

# 30 ────────────────────────────────────────── Great circle flights
T.append(dict(slug="flight_paths", topic="TRAVEL",
 hook=("A straight line on a map is not the shortest flight.", "Straight line =|shortest?", HERO("Look at any flight tracker", "x"), ["not"]),
 q=("So why do flights curve?", "Why do flights|curve?", ["curve?"]),
 ctx=[("Earth is a sphere, but most maps are flat.", "Round Earth.|Flat maps.", TAGS("Sphere", "Flat map"), ["sphere,"], "Britannica, Wikipedia"),
      ("Flattening it stretches distances, especially near the poles.", "Maps stretch|distances.", HERO(), ["stretches"], "Britannica, Wikipedia")],
 f1=[("Fact one. The shortest path on a sphere is called a great circle.", "Shortest path:|great circle.", HERO(), ["one.", "great"], "Britannica, Wikipedia")],
 f2=[("Fact two. On a flat map, that path looks curved.", "On a flat map:|it curves.", HERO(), ["two.", "curved."], "Britannica, Wikipedia")],
 f3=[("And the big one. That's why many long flights arc toward the poles.", "Long flights|arc north.", HERO("Winds and airspace change routes too"), ["big", "poles."], "Britannica, Wikipedia")],
 myth="Map straight lines are shortest", truth=("Great circles are shortest", "TRUE"),
 v1="Verdict. 'Straight on a map is shortest' is false.", v2=("On a globe, the curve is the shortcut.", "The curve is|the shortcut.", ["shortcut."]),
 cover=["Why do", "flights fly", "curved?"], cover_sub="Great circle routes, explained in 60 seconds.",
 titles=["Why Do Planes Fly Curved Routes?", "The Shortest Flight Isn't a Straight Line", "Great Circle Routes Explained in 60s"],
 summary="Earth is a sphere, so flat maps stretch distances. The shortest path on a sphere is a great circle, which looks curved on a flat map; that's why many long flights arc toward the poles.",
 tags=["#Aviation", "#Travel", "#Geography", "#Explained"], pinned="What's the longest flight you've taken? ✈️👇", poll=["Thought straight was shortest?", "Yes 🗺️", "No 🌍"],
 sources=[["Britannica: Great circle", "https://www.britannica.com/science/great-circle"], ["Wikipedia: Great-circle navigation", "https://en.wikipedia.org/wiki/Great-circle_navigation"], ["Wikipedia: Map projection", "https://en.wikipedia.org/wiki/Map_projection"]]))


if __name__ == "__main__":
    for i, t in enumerate(T, 1):
        slug, n = build(i, t)
        print(f"{slug:32} {n:4d} words")
