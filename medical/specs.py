"""Evergreen bank for PARAVION MED. Run: python3 specs.py   (writes episodes/<slug>/script.json for every spec)

Two series, one evergreen Short a day at 7:30 PM IST (the 1 PM slot is the daily medical-news Short):
  * "High-Yield in 60"   exam-style clinical pearls for MBBS / NEET-PG / USMLE / nursing (triads, scores, guidelines)
  * "Myth or Medicine?"  public-facing myth-busters backed by Cochrane reviews, meta-analyses and WHO/CDC

Rules (also enforced by medcheck.py): every fact line names 2+ sources, all sources are on trusted medical domains,
no doses, no individual treatment advice, <= 130 words. Every PubMed ID below was checked through NCBI E-utilities.
The Writer agent (agents/02_evergreen_writer.md) appends new specs here each week.
"""
import datetime as dt, json, os

START = dt.date(2026, 11, 26)         # first evergreen slot (7:30 PM IST)
SLOT = "19:30:00+05:30"
CTA = ("Like and follow Paravion Med for more.", "Follow for|daily medicine.")


def ln(beat, text, ost, vis, keys=(), src=None):
    d = {"beat": beat, "text": text, "ost": ost, "visual": vis, "keys": list(keys)}
    if src: d["source"] = src
    return d


HERO = lambda note="", icon=None: {"type": "hero", "note": note, **({"icon": icon} if icon else {})}
TAGS = lambda *t: {"type": "tags", "tags": list(t)}
MNEMO = lambda title, *items: {"type": "mnemonic", "title": title, "items": [list(i) for i in items]}
GRID = lambda *t: {"type": "grid", "tiles": [list(x) for x in t]}
STAT = lambda **k: dict(type="stat", **k)
ECG = lambda pattern="normal", label="", big="", color="red": {"type": "ecg", "pattern": pattern, "label": label, "big": big, "color": color}
PUB = lambda pmid: f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def kick(series, topic):
    head = ("HIGH-YIELD · " if series == "High-Yield in 60" else "MYTH OR MEDICINE · ") + topic
    return {"HOOK": head, "SUB": head, "CONTEXT": "THE BASICS", "FACT1": "FACT 1 OF 3", "FACT2": "FACT 2 OF 3",
            "FACT3": "FACT 3 OF 3", "RECAP": "REMEMBER IT", "VERDICT": "MYTH OR MEDICINE?", "CTA": "MEDICINE, EXPLAINED"}


def build(i, t):
    hy = t["series"] == "High-Yield in 60"
    slug = f"M{i:02d}_{t['slug']}"
    when = (START + dt.timedelta(days=i - 1)).strftime("%Y-%m-%dT") + SLOT
    L = [ln("HOOK", *t["hook"]), ln("HOOK", t["q"][0], t["q"][1], {"type": "question"}, t["q"][2])]
    L.append(ln("SUB", "Sixty seconds. Exam-ready.", "60 seconds.|Exam-ready.", {"type": "timer"}, ["Exam-ready."]) if hy else
             ln("SUB", "In sixty seconds, you'll know the truth.", "60 seconds.|The truth.", {"type": "timer"}, ["truth."]))
    L += [ln("CONTEXT", *c) for c in t["ctx"]]
    L.append(ln("CONTEXT", "Stay for fact three. It's the exam favourite." if hy else "Keep watching for fact three. It's the big one.",
                "Wait for|fact 3.", {"type": "teaser", "n": 3}, ["three."]))
    for beat in ("FACT1", "FACT2", "FACT3"):
        L += [ln(beat, *c) for c in t[beat.lower()]]
    if hy:
        L.append(ln("RECAP", *t["recap"]))
    else:
        rows = [[t["myth"], "FALSE", "red"], [t["truth"][0], t["truth"][1], "green"]]
        L.append(ln("VERDICT", t["v1"], "The myth:|false.", {"type": "verdict", "shown": 1, "rows": rows}, ["false."]))
        L.append(ln("VERDICT", t["v2"][0], t["v2"][1], {"type": "verdict", "shown": 2, "rows": rows}, t["v2"][2]))
    L.append(ln("CTA", CTA[0], CTA[1], {"type": "cta"}, ["Like", "follow", "more."]))
    tags = t["tags"]
    script = {"slug": slug, "series": t["series"], "kickers": kick(t["series"], t["topic"]),
              "cover": {"kicker": ("HIGH-YIELD · " if hy else "MYTH OR MEDICINE · ") + t["topic"], "head": t["cover"],
                        "sub": t["cover_sub"], "visual": t.get("cover_visual", t["hook"][2])},
              "lines": L,
              "meta": {"titles": t["titles"], "summary": t["summary"], "hashtags": ["#shorts"] + tags,
                       "ig_tags": " ".join("#" + x.lower().lstrip("#") for x in tags + ["medicine", "medstudent", "doctor", "paravionmed"]),
                       "pinned": t["pinned"], "poll": t["poll"], "sources": t["sources"], "removed": t.get("removed", []),
                       "notes": "Evergreen: not time-sensitive. Re-check the guideline version before posting.", "schedule": when,
                       "verdict": t.get("verdict") or (f"{t['myth']}: FALSE. {t['truth'][0]}: {t['truth'][1].title()}." if not hy else t["summary"].split(". ")[0] + "."),
                       "audience": t.get("audience", "students + doctors" if hy else "public + students")}}
    os.makedirs(f"episodes/{slug}", exist_ok=True)
    p = f"episodes/{slug}/script.json"
    old = json.load(open(p)) if os.path.exists(p) else None
    if old != script:
        json.dump(script, open(p, "w"), indent=1, ensure_ascii=False)
    return slug, sum(len(l["text"].split()) for l in L)


T = []
HY, MY = "High-Yield in 60", "Myth or Medicine?"

# 1 ── Beck's triad ─────────────────────────────────────────────────────────────
S_TAMP = [["StatPearls: Cardiac Tamponade (NBK431090)", PUB(28613742)],
          ["Adler Y et al. Cardiac tamponade. Nat Rev Dis Primers 2023", PUB(37474539)]]
T.append(dict(series=HY, slug="becks_triad", topic="CARDIOLOGY",
 hook=("Three signs. One emergency around the heart.", "3 signs.|1 emergency.", MNEMO("BECK'S TRIAD", ("1", "?"), ("2", "?"), ("3", "?")), ["emergency"]),
 q=("Can you name Beck's triad?", "Name Beck's|triad?", ["Beck's"]),
 ctx=[("In cardiac tamponade, fluid fills the sac around the heart.", "Fluid around|the heart.", HERO("The pericardial sac"), ["fluid"], "StatPearls, Nat Rev Dis Primers"),
      ("The pressure stops the heart from filling properly.", "The heart|can't fill.", HERO("Less filling, less output"), ["filling"], "StatPearls, Nat Rev Dis Primers")],
 fact1=[("Fact one. Blood pressure falls.", "Sign 1:|low BP.", GRID(("SIGN 1", "Low BP", "hypotension")), ["one.", "falls."], "StatPearls, Nat Rev Dis Primers")],
 fact2=[("Fact two. Neck veins bulge, because blood backs up.", "Sign 2:|raised JVP.", GRID(("SIGN 1", "Low BP", "hypotension"), ("SIGN 2", "JVP up", "distended neck veins")), ["two.", "bulge,"], "StatPearls, Nat Rev Dis Primers")],
 fact3=[("And the exam favourite. The heart sounds become muffled.", "Sign 3:|muffled sounds.", GRID(("SIGN 1", "Low BP", "hypotension"), ("SIGN 2", "JVP up", "neck veins"), ("SIGN 3", "Muffled", "heart sounds")), ["favourite.", "muffled."], "StatPearls, Nat Rev Dis Primers"),
        ("Echo confirms it, and draining the fluid is the emergency fix.", "Fix: drain|the fluid.", HERO("Pericardiocentesis"), ["draining"], "StatPearls, Nat Rev Dis Primers")],
 recap=("Low pressure, high neck veins, quiet heart. That's Beck's triad.", "Low, high,|quiet.", MNEMO("BECK'S TRIAD", ("1", "Hypotension"), ("2", "Raised JVP"), ("3", "Muffled heart sounds")), ["Beck's"]),
 cover=["Beck's", "triad in", "60 seconds"], cover_sub="Cardiac tamponade: the three signs every exam asks for.",
 cover_visual=MNEMO("BECK'S TRIAD", ("1", "Hypotension"), ("2", "Raised JVP"), ("3", "Muffled sounds")),
 titles=["Beck's Triad in 60 Seconds (Cardiac Tamponade)", "Cardiac Tamponade: 3 Signs to Know", "Beck's Triad Explained for NEET-PG and USMLE"],
 summary="Beck's triad of cardiac tamponade: hypotension, raised JVP (distended neck veins) and muffled heart sounds. Fluid in the pericardial sac stops the heart filling. Echo confirms it and pericardiocentesis drains it.",
 tags=["#Cardiology", "#MedicalStudent", "#NEETPG", "#USMLE"], pinned="Which triad should we do next? 👇",
 poll=["Knew all three?", "Yes 🩺", "Not yet 📚"], sources=S_TAMP))

# 2 ── Antibiotics for colds ───────────────────────────────────────────────────
S_COLD = [["Kenealy T, Arroll B. Antibiotics for the common cold. Cochrane 2025", PUB(41277585)],
          ["CDC: Common cold", "https://www.cdc.gov/common-cold/about/index.html"],
          ["WHO fact sheet: Antimicrobial resistance", "https://www.who.int/news-room/fact-sheets/detail/antimicrobial-resistance"]]
T.append(dict(series=MY, slug="antibiotics_cold", topic="INFECTION",
 hook=("Antibiotics do not cure the common cold.", "Antibiotics for|a cold?", HERO("A very common myth", "x"), ["not"]),
 q=("So why do so many people take them?", "Why take|them?", ["why"]),
 ctx=[("Colds are caused by viruses, like rhinoviruses.", "Colds are|viruses.", TAGS("Rhinovirus", "Not bacteria"), ["viruses,"], "CDC, WHO"),
      ("Antibiotics work against bacteria, not viruses.", "Antibiotics kill|bacteria.", {"type": "versus", "sides": [{"name": "BACTERIA", "big": "Yes", "mark": "check", "lines": ["antibiotics", "can work"], "color": "green"}, {"name": "VIRUSES", "big": "No", "mark": "x", "lines": ["antibiotics", "don't work"], "color": "red"}]}, ["bacteria,"], "CDC, WHO")],
 fact1=[("Fact one. In trials, people on antibiotics for colds did no better than placebo.", "No better than|placebo.", HERO("Cochrane review, 2025"), ["one.", "placebo."], "Cochrane, CDC")],
 fact2=[("Fact two. Adults on antibiotics had more side effects.", "More|side effects.", STAT(text="2.6x", count=False, label="ADULT SIDE-EFFECT RISK", sub="vs placebo, Cochrane", color="red"), ["two.", "side"], "Cochrane, WHO")],
 fact3=[("And the big one. Misuse helps bacteria become resistant.", "Misuse fuels|resistance.", HERO("A global health threat, per WHO"), ["big", "resistant."], "WHO, CDC")],
 myth="Antibiotics cure colds", truth=("Colds are viral", "TRUE"),
 v1="Verdict. Antibiotics for a cold? Myth.", v2=("Colds are viral, and antibiotics don't treat viruses.", "The truth:|colds are viral.", ["viral,"]),
 cover=["Do", "antibiotics", "cure colds?"], cover_sub="What a 2025 Cochrane review found.",
 titles=["Do Antibiotics Cure a Cold? (No, Here's Why)", "Antibiotics vs Viruses in 60 Seconds", "Why Your Doctor Won't Give Antibiotics for a Cold"],
 summary="Colds are caused by viruses, and antibiotics only work on bacteria. A 2025 Cochrane review found people given antibiotics for colds did no better than placebo, and adults had more side effects. Misuse drives antimicrobial resistance (WHO).",
 tags=["#Antibiotics", "#Health", "#MythBusting", "#AMR"], pinned="Has anyone ever offered you antibiotics for a cold? 👇",
 poll=["Believed this myth?", "Yes 😬", "No 🧠"], sources=S_COLD))

# 3 ── GCS ─────────────────────────────────────────────────────────────────────
S_GCS = [["StatPearls: Glasgow Coma Scale (NBK513298)", PUB(30020670)],
         ["NICE NG232: Head injury, assessment and early management", "https://www.nice.org.uk/guidance/ng232"],
         ["The Glasgow Coma Scale: 50-year anniversary. Neurol Sci 2024", PUB(38436790)]]
T.append(dict(series=HY, slug="glasgow_coma_scale", topic="NEUROLOGY",
 hook=("The lowest Glasgow Coma Score is three, not zero.", "Lowest score?|3, not 0.", STAT(text="3", count=False, label="LOWEST POSSIBLE GCS", sub="Not zero", color="accent"), ["three,", "zero."]),
 q=("So how is it scored?", "How is it|scored?", ["scored?"]),
 ctx=[("The Glasgow Coma Scale measures how awake and responsive someone is.", "It scores|consciousness.", HERO("Created in Glasgow, 1974"), ["responsive"], "StatPearls, Neurol Sci"),
      ("It has three parts: eyes, voice and movement.", "Eyes, voice,|movement.", TAGS("Eyes", "Verbal", "Motor"), ["three"], "StatPearls, NICE")],
 fact1=[("Fact one. Eye opening scores up to four.", "Eyes:|up to 4.", GRID(("EYES", "E4", "best score")), ["one.", "four."], "StatPearls, NICE")],
 fact2=[("Fact two. Verbal response scores up to five. Motor, up to six.", "Verbal 5.|Motor 6.", GRID(("EYES", "E4", ""), ("VERBAL", "V5", ""), ("MOTOR", "M6", "")), ["two.", "five.", "six."], "StatPearls, NICE")],
 fact3=[("And the exam favourite. Total range is three to fifteen.", "Range:|3 to 15.", STAT(text="3-15", count=False, label="TOTAL GCS RANGE", sub="Report each part, e.g. E3 V4 M5"), ["favourite.", "fifteen."], "StatPearls, Neurol Sci"),
        ("In head injury, eight or less is a classic sign the airway needs protecting.", "8 or less:|airway risk.", STAT(text="8 or less", count=False, label="HEAD INJURY", sub="Think airway", color="red"), ["eight", "airway"], "NICE, StatPearls")],
 recap=("Four, five, six. Eyes, voice, movement. Three to fifteen.", "4, 5, 6.|3 to 15.", MNEMO("GLASGOW COMA SCALE", ("E", "Eyes: 1 to 4"), ("V", "Verbal: 1 to 5"), ("M", "Motor: 1 to 6")), ["fifteen."]),
 cover=["Glasgow", "Coma Scale", "in 60s"], cover_sub="E4 V5 M6, the range, and the number that means airway.",
 cover_visual=MNEMO("GCS", ("E", "Eyes 4"), ("V", "Verbal 5"), ("M", "Motor 6")),
 titles=["Glasgow Coma Scale in 60 Seconds (E4 V5 M6)", "GCS Explained: Why the Lowest Score Is 3", "GCS for NEET-PG, USMLE and Nursing"],
 summary="The Glasgow Coma Scale scores eyes (1-4), verbal (1-5) and motor (1-6), for a total of 3 to 15. The lowest score is 3, not 0. In head injury, a GCS of 8 or less is a classic sign the airway needs protecting (NICE NG232).",
 tags=["#GCS", "#Neurology", "#EmergencyMedicine", "#NEETPG"], pinned="Quick quiz: E2 V3 M4 adds up to? 👇",
 poll=["Knew the lowest is 3?", "Yes 🧠", "Thought 0 😅"], sources=S_GCS))

# 4 ── Vitamin C and colds ─────────────────────────────────────────────────────
S_VITC = [["Hemilä H, Chalker E. Vitamin C for preventing and treating the common cold. Cochrane 2013", PUB(23440782)],
          ["NIH Office of Dietary Supplements: Vitamin C fact sheet", "https://ods.od.nih.gov/factsheets/VitaminC-HealthProfessional/"]]
T.append(dict(series=MY, slug="vitamin_c_cold", topic="NUTRITION",
 hook=("Vitamin C does not stop most people catching colds.", "Vitamin C|stops colds?", HERO("What 29 trials found", "x"), ["not"]),
 q=("So does it do anything?", "Does it do|anything?", ["anything?"]),
 ctx=[("A Cochrane review pooled twenty nine trials, with over eleven thousand people.", "29 trials.|11,000+ people.", STAT(value=11306, label="PEOPLE IN THE TRIALS", sub="Cochrane review, 2013"), ["twenty", "eleven"], "Cochrane, NIH")],
 fact1=[("Fact one. Taking it every day didn't cut how often most people got colds.", "Daily dose:|same colds.", HERO("General population: no real change"), ["one.", "didn't"], "Cochrane, NIH")],
 fact2=[("Fact two. Colds were slightly shorter. About eight percent, in adults.", "A bit shorter.|About 8%.", STAT(value=8, suffix="%", label="SHORTER COLDS, ADULTS", sub="With regular daily use"), ["two.", "eight"], "Cochrane, NIH")],
 fact3=[("And the big one. Starting it after symptoms began showed no consistent effect.", "After symptoms?|No clear effect.", HERO("Therapeutic trials", "x"), ["big", "no"], "Cochrane, NIH"),
        ("The exception: people under extreme physical stress, like marathon runners.", "Exception:|extreme exercise.", TAGS("Marathon runners", "Skiers", "Soldiers"), ["exception:"], "Cochrane, NIH")],
 myth="Vitamin C prevents colds", truth=("Slightly shorter colds", "TRUE"),
 v1="Verdict. Vitamin C preventing colds? Mostly myth.", v2=("For most people, it only makes colds slightly shorter.", "The truth:|slightly shorter.", ["shorter."]),
 cover=["Does", "vitamin C", "stop colds?"], cover_sub="29 trials, 11,000+ people. The Cochrane answer.",
 titles=["Does Vitamin C Stop Colds? What 29 Trials Found", "Vitamin C and the Common Cold, Explained", "The Vitamin C Myth in 60 Seconds"],
 summary="A Cochrane review of 29 trials (11,306 people) found regular vitamin C did not reduce how often most people catch colds. It shortened colds slightly (about 8% in adults, 14% in children). Taking it after symptoms start showed no consistent effect. People under extreme physical stress were the exception.",
 tags=["#VitaminC", "#CommonCold", "#MythBusting", "#Health"], pinned="Do you take vitamin C when you feel a cold coming? 👇",
 poll=["Thought it prevents colds?", "Yes 🍊", "No 🧠"], sources=S_VITC))

# 5 ── qSOFA ───────────────────────────────────────────────────────────────────
S_SEP = [["Singer M et al. Sepsis-3 definitions. JAMA 2016", PUB(26903338)],
         ["Evans L et al. Surviving Sepsis Campaign guidelines 2021. Crit Care Med", PUB(34605781)]]
T.append(dict(series=HY, slug="qsofa_sepsis", topic="CRITICAL CARE",
 hook=("Three bedside checks can flag sepsis risk in seconds.", "3 checks.|Sepsis risk.", STAT(text="qSOFA", count=False, label="QUICK SOFA", sub="Sepsis-3, 2016", color="accent"), ["Three", "sepsis"]),
 q=("But should you screen with it alone?", "Screen with|it alone?", ["alone?"]),
 ctx=[("It's called q SOFA, from the 2016 Sepsis-3 definitions.", "From|Sepsis-3.", HERO("JAMA, 2016"), ["2016"], "JAMA, Crit Care Med")],
 fact1=[("Fact one. Breathing rate of twenty two or more.", "RR|22 or more.", GRID(("RESP RATE", "22+", "per minute")), ["one.", "twenty"], "JAMA, Crit Care Med")],
 fact2=[("Fact two. Altered mental state, and systolic pressure of one hundred or less.", "Confusion.|SBP 100 or less.", GRID(("RESP RATE", "22+", "per minute"), ("MENTATION", "Altered", "any change"), ("SYSTOLIC BP", "100 or less", "mmHg")), ["two.", "hundred"], "JAMA, Crit Care Med"),
        ("Two or more points flags a higher risk of a poor outcome.", "2+ points:|higher risk.", STAT(text="2+", count=False, label="qSOFA POSITIVE", sub="Higher risk of poor outcome", color="red"), ["Two", "risk"], "JAMA, Crit Care Med")],
 fact3=[("And the exam favourite. The 2021 guidelines say don't use it alone to screen.", "2021: not alone|to screen.", HERO("Surviving Sepsis Campaign 2021", "x"), ["favourite.", "alone"], "Crit Care Med, JAMA"),
        ("Compared with SIRS or early warning scores, it's not advised as a single screen.", "Not a single|screening tool.", TAGS("SIRS", "NEWS", "MEWS"), ["single"], "Crit Care Med, JAMA")],
 recap=("Breathing, brain, blood pressure. Two flags risk. Never your only screen.", "Two flags risk.|Not alone.", MNEMO("qSOFA", ("R", "Resp rate 22+"), ("A", "Altered mentation"), ("S", "Systolic BP 100 or less")), ["only"]),
 cover=["qSOFA", "in 60", "seconds"], cover_sub="The three criteria, and what the 2021 sepsis guidelines changed.",
 cover_visual=MNEMO("qSOFA", ("R", "RR 22+"), ("A", "Altered mentation"), ("S", "SBP 100 or less")),
 titles=["qSOFA in 60 Seconds: Sepsis Criteria", "qSOFA vs SIRS: What the 2021 Guidelines Say", "Sepsis Screening Explained for Med Students"],
 summary="qSOFA (Sepsis-3, 2016): respiratory rate 22 or more, altered mentation, systolic BP 100 or less. Two or more points flags a higher risk of poor outcome. The 2021 Surviving Sepsis Campaign guidelines recommend against using qSOFA alone as a screening tool compared with SIRS, NEWS or MEWS.",
 tags=["#Sepsis", "#CriticalCare", "#qSOFA", "#MedicalStudent"], pinned="SIRS, NEWS or qSOFA: what does your hospital use? 👇",
 poll=["Knew the 2021 change?", "Yes 🩺", "News to me 😮"], sources=S_SEP))

# 6 ── CPR quality ─────────────────────────────────────────────────────────────
S_CPR = [["2025 AHA Guidelines, Part 7: Adult Basic Life Support. Circulation", PUB(41122888)],
         ["Resuscitation Council UK: Adult basic life support guidelines", "https://www.resus.org.uk/library/2021-resuscitation-guidelines/adult-basic-life-support-guidelines"]]
T.append(dict(series=HY, slug="cpr_numbers", topic="EMERGENCY",
 hook=("Good CPR comes down to two numbers.", "CPR in|two numbers.", ECG("vfib", "CARDIAC ARREST", "Start CPR"), ["two"]),
 q=("Do you know them?", "Do you|know them?", ["know"]),
 ctx=[("When an adult collapses and isn't breathing normally, call for help and an AED.", "Call for help|and an AED.", TAGS("Call for help", "Get an AED"), ["help"], "AHA, Resus Council UK"),
      ("Then push hard and fast in the centre of the chest.", "Hard and fast.|Centre of chest.", HERO("Hands on the lower breastbone"), ["hard", "fast"], "AHA, Resus Council UK")],
 fact1=[("Fact one. Rate: one hundred to one hundred twenty compressions a minute.", "Rate:|100 to 120.", STAT(text="100-120", count=False, label="COMPRESSIONS PER MINUTE", sub="Adults"), ["one.", "twenty"], "AHA, Resus Council UK")],
 fact2=[("Fact two. Depth: about five to six centimetres in adults.", "Depth:|5 to 6 cm.", STAT(text="5-6 cm", count=False, label="COMPRESSION DEPTH", sub="Adults"), ["two.", "six"], "AHA, Resus Council UK")],
 fact3=[("And the exam favourite. Let the chest fully recoil, and keep pauses short.", "Full recoil.|Short pauses.", TAGS("Full recoil", "Minimal pauses"), ["favourite.", "recoil,"], "AHA, Resus Council UK")],
 recap=("Hard, fast, full recoil. One twenty, five to six. Don't stop.", "Hard. Fast.|Don't stop.", GRID(("RATE", "100-120", "per minute"), ("DEPTH", "5-6 cm", "adults"), ("RECOIL", "Full", "every push"), ("PAUSES", "Minimal", "keep going")), ["stop."]),
 cover=["CPR", "in two", "numbers"], cover_sub="Rate, depth and recoil from the 2025 AHA guidelines.",
 cover_visual=GRID(("RATE", "100-120", "per minute"), ("DEPTH", "5-6 cm", "adults")),
 titles=["CPR in 60 Seconds: The 2 Numbers to Know", "CPR Rate and Depth (2025 AHA Guidelines)", "High-Quality CPR Explained"],
 summary="High-quality adult CPR: 100 to 120 compressions per minute, about 5 to 6 cm deep, full chest recoil and minimal pauses (2025 AHA guidelines, Resuscitation Council UK). Call for help and an AED first. Learn hands-on CPR in a certified course.",
 tags=["#CPR", "#BLS", "#EmergencyMedicine", "#FirstAid"], pinned="Have you done a hands-on CPR course? 👇",
 poll=["Trained in CPR?", "Yes 🙌", "Not yet 📚"], sources=S_CPR, audience="students + doctors + public"))

# 7 ── Antibiotic resistance myth ──────────────────────────────────────────────
S_AMR = [["WHO fact sheet: Antimicrobial resistance", "https://www.who.int/news-room/fact-sheets/detail/antimicrobial-resistance"],
         ["CDC: About antimicrobial resistance", "https://www.cdc.gov/antimicrobial-resistance/about/index.html"]]
T.append(dict(series=MY, slug="amr_body_resistant", topic="INFECTION",
 hook=("Your body does not become resistant to antibiotics.", "Your body|resistant?", HERO("A common mix-up", "x"), ["not"]),
 q=("So what does?", "So what|does?", ["what"]),
 ctx=[("Antimicrobial resistance means germs change, so medicines stop working on them.", "Germs change.|Drugs fail.", HERO("Called AMR"), ["germs"], "WHO, CDC")],
 fact1=[("Fact one. It's the bacteria that become resistant, not the person.", "Bacteria resist.|Not you.", {"type": "versus", "sides": [{"name": "BACTERIA", "big": "Yes", "mark": "check", "lines": ["become", "resistant"], "color": "red"}, {"name": "YOUR BODY", "big": "No", "mark": "x", "lines": ["does not", "resist"], "color": "ink"}]}, ["one.", "bacteria"], "WHO, CDC")],
 fact2=[("Fact two. Resistant bacteria can spread between people.", "They can|spread.", HERO("Homes, hospitals, communities"), ["two.", "spread"], "WHO, CDC")],
 fact3=[("And the big one. Misuse and overuse of antibiotics speed this up.", "Misuse|speeds it up.", TAGS("Overuse", "Misuse"), ["big", "Misuse"], "WHO, CDC"),
        ("The WHO calls it one of the top global public health threats.", "A top global|health threat.", HERO("Per WHO"), ["top"], "WHO, CDC")],
 myth="Your body becomes resistant", truth=("Bacteria become resistant", "TRUE"),
 v1="Verdict. Your body becoming resistant? Myth.", v2=("Bacteria become resistant, and they can spread.", "The truth:|bacteria adapt.", ["Bacteria"]),
 cover=["Is it", "your body", "that resists?"], cover_sub="What antibiotic resistance really means.",
 titles=["Antibiotic Resistance: It's Not Your Body", "What Antibiotic Resistance Really Means", "AMR Explained in 60 Seconds"],
 summary="Antibiotic resistance doesn't mean your body becomes resistant. Bacteria change so medicines stop working on them, and resistant bacteria can spread between people. Misuse and overuse speed this up; WHO calls AMR one of the top global public health threats.",
 tags=["#AMR", "#Antibiotics", "#PublicHealth", "#MythBusting"], pinned="Did you think it was the body that becomes resistant? 👇",
 poll=["Believed this?", "Yes 😬", "No 🧠"], sources=S_AMR))

# 8 ── Charcot's triad ─────────────────────────────────────────────────────────
S_CHOL = [["StatPearls: Cholangitis (NBK558946)", PUB(32644372)],
          ["Kiriyama S et al. Tokyo Guidelines 2018: diagnostic criteria and severity grading of acute cholangitis", PUB(29032610)]]
T.append(dict(series=HY, slug="charcots_triad", topic="SURGERY",
 hook=("Fever, pain, jaundice. Three clues to an infected bile duct.", "Fever. Pain.|Jaundice.", MNEMO("CHARCOT'S TRIAD", ("1", "?"), ("2", "?"), ("3", "?")), ["infected"]),
 q=("And what makes it a pentad?", "Triad, or|pentad?", ["pentad?"]),
 ctx=[("Acute cholangitis is infection of the bile ducts, usually behind a blockage.", "Infected|bile ducts.", HERO("Often a stone blocking the duct"), ["blockage."], "StatPearls, Tokyo Guidelines")],
 fact1=[("Fact one. Charcot's triad is fever, right upper quadrant pain and jaundice.", "Fever, RUQ pain,|jaundice.", MNEMO("CHARCOT'S TRIAD", ("1", "Fever"), ("2", "RUQ pain"), ("3", "Jaundice")), ["one.", "jaundice."], "StatPearls, Tokyo Guidelines")],
 fact2=[("Fact two. Add low blood pressure and confusion, and it's Reynolds' pentad.", "Add shock +|confusion.", MNEMO("REYNOLDS' PENTAD", ("1", "Fever"), ("2", "RUQ pain"), ("3", "Jaundice"), ("4", "Hypotension"), ("5", "Confusion")), ["two.", "pentad."], "StatPearls, Tokyo Guidelines"),
        ("That points to severe disease.", "Pentad:|severe.", STAT(text="Severe", count=False, label="REYNOLDS' PENTAD", color="red"), ["severe"], "StatPearls, Tokyo Guidelines")],
 fact3=[("And the exam favourite. The triad is specific, but misses many cases.", "Specific, but|misses many.", HERO("Low sensitivity"), ["favourite.", "misses"], "Tokyo Guidelines, StatPearls"),
        ("So the Tokyo Guidelines use broader criteria, with blood tests and imaging.", "Tokyo: labs|+ imaging.", TAGS("Inflammation", "Cholestasis", "Imaging"), ["broader"], "Tokyo Guidelines, StatPearls")],
 recap=("Three is Charcot. Five is Reynolds. Tokyo for the diagnosis.", "3 Charcot.|5 Reynolds.", GRID(("CHARCOT", "3", "fever, RUQ, jaundice"), ("REYNOLDS", "5", "+ shock, confusion")), ["Tokyo"]),
 cover=["Charcot's", "triad vs", "Reynolds'"], cover_sub="Acute cholangitis: 3 signs, 5 signs, and the Tokyo Guidelines.",
 cover_visual=GRID(("CHARCOT", "3", "fever, RUQ, jaundice"), ("REYNOLDS", "5", "+ shock, confusion")),
 titles=["Charcot's Triad vs Reynolds' Pentad in 60s", "Acute Cholangitis: The Signs to Know", "Charcot's Triad Explained for NEET-PG"],
 summary="Acute cholangitis: Charcot's triad is fever, right upper quadrant pain and jaundice. Adding hypotension and confusion gives Reynolds' pentad, which signals severe disease. The triad is specific but has low sensitivity, so the Tokyo Guidelines 2018 use broader clinical, lab and imaging criteria.",
 tags=["#Surgery", "#Cholangitis", "#NEETPG", "#MedicalStudent"], pinned="Which pentad or triad confuses you most? 👇",
 poll=["Knew Reynolds' pentad?", "Yes 🩺", "Not yet 📚"], sources=S_CHOL))

# 9 ── Sugar and hyperactivity ─────────────────────────────────────────────────
S_SUG = [["Wolraich ML et al. The effect of sugar on behavior or cognition in children: a meta-analysis. JAMA 1995", PUB(7474248)],
         ["Vreeman RC, Carroll AE. Festive medical myths. BMJ 2008", PUB(19091758)],
         ["Hoover DW, Milich R. Effects of sugar ingestion expectancies on mother-child interactions. 1994", PUB(7963081)]]
T.append(dict(series=MY, slug="sugar_hyperactive", topic="PAEDIATRICS",
 hook=("Sugar does not make most kids hyperactive.", "Sugar makes kids|hyper?", HERO("The party myth", "x"), ["not"]),
 q=("So why do parents see it?", "Why do parents|see it?", ["see"]),
 ctx=[("Researchers tested it with blinded trials, using sugar or a sweetener.", "Blinded trials.|Sugar vs sweetener.", {"type": "versus", "sides": [{"name": "SUGAR", "big": "?", "mark": "q", "lines": ["real", "sugar"], "color": "accent"}, {"name": "PLACEBO", "big": "?", "mark": "q", "lines": ["artificial", "sweetener"], "color": "ink"}]}, ["blinded"], "JAMA, BMJ")],
 fact1=[("Fact one. A meta-analysis of twenty three studies found no effect on behaviour.", "23 studies.|No effect.", STAT(value=23, label="BLINDED STUDIES", sub="JAMA meta-analysis, 1995"), ["one.", "no"], "JAMA, BMJ")],
 fact2=[("Fact two. The myth persists even though trials keep finding no difference.", "Myth vs|evidence.", HERO("Reviewed in the BMJ, 2008"), ["two.", "no"], "BMJ, JAMA")],
 fact3=[("And the big one. Parents told their child had sugar rated them more hyperactive, even when it was placebo.", "Expectation|changes perception.", HERO("Expectation effect", "x"), ["big", "placebo."], "BMJ, Hoover 1994")],
 myth="Sugar causes hyperactivity", truth=("Expectation changes perception", "TRUE"),
 v1="Verdict. Sugar rush? Mostly myth.", v2=("Studies found no effect. Expectation shapes what adults see.", "The truth:|expectation.", ["Expectation"]),
 cover=["Does", "sugar make kids", "hyper?"], cover_sub="What 23 blinded studies found.",
 titles=["Does Sugar Make Kids Hyper? What Studies Found", "The Sugar Rush Myth in 60 Seconds", "Sugar and Hyperactivity, Explained"],
 summary="A 1995 JAMA meta-analysis of 23 blinded studies found sugar did not affect children's behaviour or cognition (a small effect in some children can't be ruled out). In one study, mothers told their child had sugar rated them as more hyperactive even when it was a placebo. Sugar still matters for teeth and weight.",
 tags=["#Parenting", "#Paediatrics", "#MythBusting", "#Health"], pinned="Parents: still believe the sugar rush? 👇",
 poll=["Believed the sugar rush?", "Yes 🍭", "No 🧠"], sources=S_SUG))

# 10 ── Horner syndrome ────────────────────────────────────────────────────────
S_HOR = [["StatPearls: Horner Syndrome (NBK500000)", PUB(29763176)],
         ["ACR Appropriateness Criteria: Horner Syndrome. J Am Coll Radiol 2025", PUB(41193044)]]
T.append(dict(series=HY, slug="horner_syndrome", topic="NEUROLOGY",
 hook=("A droopy eyelid and a tiny pupil can point to the lung or neck.", "Droopy lid.|Tiny pupil.", MNEMO("HORNER SYNDROME", ("P", "?"), ("M", "?"), ("A", "?")), ["droopy", "tiny"]),
 q=("Why would the eye warn you?", "Why the|eye?", ["warn"]),
 ctx=[("Horner syndrome happens when the sympathetic nerve path to the eye is interrupted.", "Sympathetic path|cut.", HERO("A long, three-neuron route"), ["sympathetic"], "StatPearls, ACR")],
 fact1=[("Fact one. Ptosis. A mildly droopy upper eyelid.", "P:|ptosis.", MNEMO("HORNER SYNDROME", ("P", "Ptosis"), ("M", "?"), ("A", "?")), ["one.", "Ptosis."], "StatPearls, ACR")],
 fact2=[("Fact two. Miosis, a small pupil, and anhidrosis, less sweating on that side.", "M: miosis.|A: anhidrosis.", MNEMO("HORNER SYNDROME", ("P", "Ptosis"), ("M", "Miosis"), ("A", "Anhidrosis")), ["two.", "Miosis,", "anhidrosis,"], "StatPearls, ACR")],
 fact3=[("And the exam favourite. The cause can be serious.", "The cause|can be serious.", HERO("Always look for it"), ["favourite.", "serious."], "StatPearls, ACR"),
        ("Classic examples are a lung apex tumour, or carotid artery dissection.", "Pancoast tumour.|Carotid dissection.", TAGS("Pancoast tumour", "Carotid dissection"), ["tumour,", "dissection."], "StatPearls, ACR")],
 recap=("Ptosis, miosis, anhidrosis. Same side. Then find the cause.", "PMA.|Find the cause.", MNEMO("HORNER SYNDROME", ("P", "Ptosis"), ("M", "Miosis"), ("A", "Anhidrosis")), ["cause."]),
 cover=["Horner", "syndrome", "in 60s"], cover_sub="Ptosis, miosis, anhidrosis, and the causes you can't miss.",
 cover_visual=MNEMO("HORNER", ("P", "Ptosis"), ("M", "Miosis"), ("A", "Anhidrosis")),
 titles=["Horner Syndrome in 60 Seconds (PMA)", "Ptosis, Miosis, Anhidrosis: Horner Syndrome", "Horner Syndrome Causes You Can't Miss"],
 summary="Horner syndrome is interruption of the sympathetic pathway to the eye: ptosis, miosis and anhidrosis on the same side. Causes can be serious, classically a lung apex (Pancoast) tumour or carotid artery dissection, so the cause is always investigated.",
 tags=["#Neurology", "#Ophthalmology", "#NEETPG", "#USMLE"], pinned="Which eye sign should we cover next? 👇",
 poll=["Knew PMA?", "Yes 👁️", "Not yet 📚"], sources=S_HOR))

# 11 ── Apgar ──────────────────────────────────────────────────────────────────
S_APG = [["StatPearls: APGAR Score (NBK470569)", PUB(29262097)],
         ["AAP Committee on Fetus and Newborn, ACOG. The Apgar Score. Pediatrics 2015", PUB(26416932)]]
T.append(dict(series=HY, slug="apgar_score", topic="NEONATOLOGY",
 hook=("Every newborn gets scored out of ten within a minute.", "Out of 10|at 1 minute.", STAT(text="0-10", count=False, label="APGAR SCORE", sub="At 1 and 5 minutes", color="accent"), ["ten"]),
 q=("What does each letter mean?", "What do the|letters mean?", ["letter"]),
 ctx=[("The Apgar score was created by anaesthesiologist Virginia Apgar.", "Named after|Virginia Apgar.", HERO("An anaesthesiologist, 1950s"), ["Virginia"], "StatPearls, Pediatrics")],
 fact1=[("Fact one. Five signs: appearance, pulse, grimace, activity, respiration.", "Five signs.|A-P-G-A-R.", MNEMO("APGAR", ("A", "Appearance"), ("P", "Pulse"), ("G", "Grimace"), ("A", "Activity"), ("R", "Respiration")), ["one.", "Five"], "StatPearls, Pediatrics")],
 fact2=[("Fact two. Each scores zero to two, checked at one and five minutes.", "0-2 each.|1 and 5 min.", GRID(("EACH SIGN", "0-2", "points"), ("TOTAL", "0-10", "points"), ("WHEN", "1 + 5", "minutes")), ["two.", "five"], "StatPearls, Pediatrics")],
 fact3=[("And the exam favourite. Never wait for the score to start resuscitation.", "Don't wait|to resuscitate.", HERO("Start before the 1-minute score", "x"), ["favourite.", "Never"], "Pediatrics, StatPearls"),
        ("And a low score alone doesn't prove birth asphyxia.", "Low score alone|isn't asphyxia.", HERO("Per AAP and ACOG"), ["alone"], "Pediatrics, StatPearls")],
 recap=("Five letters, two points each, at one and five minutes. Resus never waits.", "Resus never|waits.", MNEMO("APGAR", ("A", "Appearance"), ("P", "Pulse"), ("G", "Grimace"), ("A", "Activity"), ("R", "Respiration")), ["waits."]),
 cover=["Apgar", "score", "in 60s"], cover_sub="The five signs, the timing, and the rule examiners love.",
 cover_visual=MNEMO("APGAR", ("A", "Appearance"), ("P", "Pulse"), ("G", "Grimace"), ("A", "Activity"), ("R", "Respiration")),
 titles=["Apgar Score in 60 Seconds", "APGAR Explained: 5 Signs, 10 Points", "Apgar Score for NEET-PG, USMLE and Nursing"],
 summary="The Apgar score rates 5 signs (appearance, pulse, grimace, activity, respiration) from 0 to 2 each, at 1 and 5 minutes after birth. Resuscitation should start before the 1-minute score if needed, and a low score alone doesn't prove asphyxia (AAP/ACOG).",
 tags=["#Neonatology", "#Paediatrics", "#Nursing", "#NEETPG"], pinned="Quick quiz: what does the G stand for? 👇",
 poll=["Knew the resus rule?", "Yes 👶", "Not yet 📚"], sources=S_APG))


if __name__ == "__main__":
    for i, t in enumerate(T, 1):
        slug, n = build(i, t)
        print(f"{slug:28} {n:3d} words  {t['series']}")
