"""Deep Dive L01: When Antibiotics Stop Working (antimicrobial resistance). Run from medical/:
    python3 longform_specs/L01_antibiotic_resistance.py      -> episodes/L01_antibiotic_resistance/script.json

Fact sources (all checked on 2026-11-23):
  Lancet 2024 GRAM 1990-2021 (PMID 39299261): 4.71 M associated / 1.14 M attributable deaths in 2021; MRSA 130,000
      attributable deaths in 2021; south Asia forecast among highest AMR death rates in 2050.
  Lancet 2022 GRAM 2019 (PMID 35065702): MRSA > 100,000 attributable deaths in 2019; six leading pathogens incl. E. coli,
      S. aureus, K. pneumoniae, A. baumannii.
  WHO fact sheet (updated 16 Jul 2026): definition; "more than 4.7 million deaths in 2021"; misuse/overuse main driver;
      raises complication risk of surgeries; "a major global health threat"; 1 in 6 infections resistant (2023).
  WHO news release 13 Oct 2025 (GLASS 2025): 1 in 6; SE Asia + E Med 1 in 3; >40% E. coli, >55% K. pneumoniae resistant
      to 3rd-gen cephalosporins (first-choice treatment); resistance rose in >40% of combinations 2018-2023.
  CDC About AR (25 Oct 2026): "germs develop the ability to defeat the drugs"; enzymes, pumps, target change, restricted
      entry; sharing resistance with other germs; medical advances (joint replacements, transplants, cancer therapy) depend
      on antibiotics. CDC Causes (28 Oct 2026): use pressures adaptation; spread in healthcare, community, environment,
      food, between people and animals. CDC Prevention (26 Oct 2026): vaccines, clean hands, use only when needed.
  Munita & Arias, Microbiol Spectr 2016 (PMID 27227291): mutation, acquired genetic material, "survival of the fittest".
  Fleming 1928: Chhabra et al., Cureus 2024 (PMID 39176366); Geddes, Int J Antimicrob Agents 2008 (PMID 18715766).
  Antibiotics don't treat colds: Cochrane 2025 (PMID 41277585); CDC common cold page.
"""
import json, os, sys

SLUG = "L01_antibiotic_resistance"
L = []


def ln(text, visual, ost="", source=None, nofact=False):
    d = {"beat": "DEEP", "text": text, "ost": ost, "visual": visual, "keys": []}
    if source: d["source"] = source
    if nofact: d["nofact"] = True
    L.append(d)


def IMG(key, move=None):
    """'W:<id>' = Wellcome Collection image id, 'File:...' = Wikimedia Commons file."""
    v = {"type": "image", "wellcome": key[2:]} if key.startswith("W:") else {"type": "image", "file": key}
    if move: v["move"] = move
    return v


BG = lambda key: key[2:] if key.startswith("W:") else key
# Wikimedia Commons (CC BY 2.0 / CC BY-SA 3.0 / public domain)
MRSA = "File:Methicillin-Resistant Staphylococcus Aureus (MRSA) Bacteria colorized scanning electron micrograph - 11.jpg"
PILLS = "File:VariousPills.jpg"
LAB = "File:Medical laboratory, Where science, medicine converge 140417-F-FM358-007.jpg"
# Wellcome Collection (CC BY 4.0 / public domain)
FLEMING = "W:L0000655"      # Sir Alexander Fleming (photograph)
PEN = "W:B0004843"          # SEM Penicillium mould & spores, close-up
PENTEAM = "W:L0012312"      # Seven of the early researchers on penicillin, 194-
PENPOT = "W:L0012314"       # The high potency of penicillin when first partially purified, 194-
PENAPP = "W:L0032175"       # Penicillin: apparatus used in the production
GUT = "W:B0006981"          # Intestinal bacteria (micrograph)
GUT2 = "W:B0006979"
GUT3 = "W:B0006983"
SAMPLES = "W:N0038013"      # Samples in a laboratory
RESEARCH = "W:B0000376"     # Researcher in laboratory
MICRO = "W:V0029664"        # Tuberculosis and other bacilli seen through a microscope (historic plate)
WHOB = "W:V0028053"         # Members of a WHO committee (photograph)
MUKT = "W:V0037748"         # Imperial Bacteriological Laboratory, Muktesar, India
CALC = "W:V0012306"         # The new medical college hospital, Calcutta, 1853
HANDS = "W:V0047895ER"      # The regular washing of hands, lithograph c. 1960
POULTRY = "W:V0021616"      # Chickens and ducks in a farm building, lithograph

LAN, WHO_, CDC_ = "Lancet 2024", "WHO", "CDC"

# ── cold open ────────────────────────────────────────────────────────────────────────────────────
ln("In twenty twenty one, more than a million deaths worldwide were caused directly by bacteria that antibiotics could no longer kill.",
   IMG(MRSA, "in"), "Drug-resistant bacteria|1.14 million deaths in 2021", "Lancet 2024, WHO")
ln("Resistant infections were linked to about four point seven million deaths that year.",
   {"type": "stat", "text": "4.7 million", "count": False, "label": "DEATHS ASSOCIATED WITH AMR, 2021", "sub": "1.14 million directly caused", "color": "red"},
   "The scale|Deaths linked to resistance", "Lancet 2024, WHO")
ln("The medicines that changed modern medicine are slowly losing their power.", IMG(PILLS, "out"), "", nofact=True)
ln("This is the story of how it happened, and what still works.", IMG(LAB, "right"), "", nofact=True)
ln("When antibiotics stop working.", {"type": "title", "lines": ["When antibiotics", "stop working"], "kicker": "A PARAVION MED DEEP DIVE", "bg": BG(MRSA)}, nofact=True)

# ── chapter 1 ───────────────────────────────────────────────────────────────────────────────────
ln("Chapter one. The mould that changed medicine.", {"type": "chapter", "n": 1, "title": "The mould that changed medicine", "sub": "London, 1928", "bg": BG(PEN)}, nofact=True)
ln("In nineteen twenty eight, Alexander Fleming noticed something strange on a culture plate.", IMG(FLEMING, "in"), "1928|Alexander Fleming", "Cureus 2024, Int J Antimicrob Agents 2008")
ln("A mould had landed on it, and the bacteria around it had died.", IMG(PEN, "in"), "Penicillium|The mould that killed bacteria", "Cureus 2024, Int J Antimicrob Agents 2008")
ln("That mould gave us penicillin, the first antibiotic to change medicine.", IMG(PENTEAM, "left"), "1940s|Turning a mould into a medicine", "Cureus 2024, Int J Antimicrob Agents 2008")
ln("Before antibiotics, a simple infection could be a death sentence. Afterwards, medicine could take risks it never could before.", IMG(PENAPP, "in"), "", nofact=True)
ln("Today, joint replacements, organ transplants and cancer therapy all depend on being able to treat infections.",
   {"type": "tags", "tags": ["Joint replacements", "Organ transplants", "Cancer therapy"]}, "Modern medicine|Built on antibiotics", "CDC, WHO")
ln("Resistance raises the risk of complications from procedures like surgery.", IMG(LAB, "right"), "Higher risk|Surgery and procedures", "WHO, CDC")

# ── chapter 2 ───────────────────────────────────────────────────────────────────────────────────
ln("Chapter two. How bacteria fight back.", {"type": "chapter", "n": 2, "title": "How bacteria fight back", "sub": "Evolution, in fast-forward", "bg": BG(GUT2)}, nofact=True)
ln("Resistance happens when germs develop the ability to defeat the drugs designed to kill them.", IMG(GUT, "in"), "Resistance|Germs defeat the drug", "CDC, WHO")
ln("Every time an antibiotic is used, it puts pressure on bacteria to adapt.", IMG(SAMPLES, "out"), "Selection pressure|Every use counts", "CDC, Munita 2016")
ln("Picture billions of bacteria in an infection. A few carry a random genetic change that helps them survive the drug.", IMG(GUT2, "left"), "Random change|A few survivors", "Munita 2016, CDC")
ln("The antibiotic kills the rest. The survivors now have room to multiply.", IMG(GUT3, "out"), "Survival of the fittest|The resistant ones multiply", "Munita 2016, CDC")
ln("That's evolution, happening in days instead of millions of years.", IMG(MICRO, "right"), "", nofact=True)
ln("They have four main tricks.", {"type": "mnemonic", "title": "HOW BACTERIA RESIST", "items": [["1", "Destroy the drug"], ["2", "Pump it out"], ["3", "Change the target"], ["4", "Block the way in"]]},
   "Four tricks|How bacteria resist", "CDC, Munita 2016")
ln("Some make enzymes that break the antibiotic down.", {"type": "tags", "tags": ["Enzyme", "breaks", "the drug"]}, "Trick 1|Enzymes destroy the drug", "CDC, Munita 2016")
ln("Some pump it straight back out, or change the target so the drug no longer fits.", {"type": "tags", "tags": ["Pump it out", "Change the target"]}, "Tricks 2 and 3|Pumps and new targets", "CDC, Munita 2016")
ln("And some close the doors it uses to get in.", IMG(GUT, "right"), "Trick 4|Restricted entry", "CDC, Munita 2016")
ln("Worse, bacteria can share resistance with other bacteria that have never even seen the drug.", {"type": "two_hats", "a": "Resistant bacterium", "b": "Gets the gene too", "join": "↓"}, "Shared genes|Resistance spreads between bacteria", "CDC, Munita 2016")
ln("They pass it on through mobile pieces of DNA, which is why resistance can spread so fast.", IMG(GUT3, "in"), "Mobile genetic elements|Fast spread", "CDC, Munita 2016")
ln("Medical students, this is classic exam material. Enzymes, efflux pumps, target changes and reduced entry.",
   {"type": "mnemonic", "title": "THE FOUR MECHANISMS", "items": [["1", "Enzymatic destruction"], ["2", "Efflux pumps"], ["3", "Target modification"], ["4", "Reduced permeability"]]},
   "For the exam|The four mechanisms", "CDC, Munita 2016")

# ── chapter 3 ───────────────────────────────────────────────────────────────────────────────────
ln("Chapter three. The scale of the problem.", {"type": "chapter", "n": 3, "title": "The scale of the problem", "sub": "What the numbers say", "bg": BG(WHOB)}, nofact=True)
ln("In twenty twenty three, about one in six lab-confirmed bacterial infections worldwide were resistant to antibiotics.",
   {"type": "stat", "text": "1 in 6", "count": False, "label": "INFECTIONS RESISTANT, 2023", "sub": "Lab-confirmed, worldwide", "color": "red"},
   "WHO surveillance, 2025|1 in 6 infections resistant", "WHO GLASS 2025, WHO")
ln("Between twenty eighteen and twenty twenty three, resistance rose in over forty percent of the drug and bug pairs WHO tracks.",
   IMG(LAB, "left"), "2018 to 2023|Rising in over 40% of combinations", "WHO GLASS 2025, WHO")
ln("Two gut bacteria keep topping these lists: E. coli and Klebsiella.", IMG(GUT2, "in"), "The leaders|E. coli and K. pneumoniae", "WHO GLASS 2025, Lancet 2022")
ln("Globally, more than forty percent of E. coli and over fifty five percent of Klebsiella resist the first-choice antibiotics for these infections.",
   {"type": "trial", "label": "RESISTANT TO 3RD-GEN CEPHALOSPORINS", "arms": [{"name": "K. pneumoniae", "value": 55, "text": "over 55%", "color": "red"}, {"name": "E. coli", "value": 40, "text": "over 40%"}], "sub": "WHO GLASS report, 2025"},
   "First-choice drugs|Failing more often", "WHO GLASS 2025, WHO")
ln("Even powerful drugs like carbapenems are losing effectiveness against Klebsiella and Acinetobacter.", IMG(SAMPLES, "in"), "Carbapenems|Losing ground", "WHO GLASS 2025, Lancet 2024")
ln("And M R S A, a resistant staph, caused over a hundred thousand deaths in a single year on its own.", IMG(MRSA, "out"), "MRSA|Over 100,000 deaths a year", "Lancet 2022, Lancet 2024")

# ── chapter 4 ───────────────────────────────────────────────────────────────────────────────────
ln("Older people are hit hardest. Since nineteen ninety, resistance deaths in people over seventy have risen by more than eighty percent.",
   {"type": "stat", "text": "+80%", "count": False, "label": "AMR DEATHS, AGE 70+, 1990-2021", "sub": "While deaths in under-5s more than halved", "color": "red"},
   "Older adults|The fastest-growing toll", "Lancet 2024, WHO")
ln("Chapter four. Why it matters for South Asia.", {"type": "chapter", "n": 4, "title": "Why South Asia should care", "sub": "Where resistance is highest", "bg": BG(MUKT)}, nofact=True)
ln("WHO estimates resistance is highest in its South-East Asia and Eastern Mediterranean regions, where one in three reported infections were resistant.",
   {"type": "stat", "text": "1 in 3", "count": False, "label": "SOUTH-EAST ASIA REGION", "sub": "Reported infections resistant", "color": "red"},
   "WHO South-East Asia|1 in 3 infections resistant", "WHO GLASS 2025, WHO")
ln("And forecasts in The Lancet put South Asia among the regions with the highest death rates from resistance by twenty fifty.", IMG(CALC, "right"),
   "Forecast to 2050|South Asia among the hardest hit", "Lancet 2024, WHO GLASS 2025")
ln("Resistant germs spread in hospitals, in the community, through food and the environment, and between people and animals.",
   IMG(POULTRY, "right"), "One Health|People, animals, food, environment", "CDC, WHO")

# ── chapter 5 ───────────────────────────────────────────────────────────────────────────────────
ln("Chapter five. What actually works.", {"type": "chapter", "n": 5, "title": "What actually works", "sub": "For doctors, students and everyone else", "bg": BG(HANDS)}, nofact=True)
ln("First, use antibiotics only when they're needed. Ask your doctor whether you really need one.", IMG(PILLS, "in"), "Use them wisely|Only when needed", "CDC, WHO")
ln("Colds are viral, and trials show antibiotics don't help them.", {"type": "versus", "sides": [{"name": "BACTERIA", "big": "Yes", "mark": "check", "lines": ["antibiotics", "can work"], "color": "green"}, {"name": "VIRUSES", "big": "No", "mark": "x", "lines": ["colds:", "no benefit"], "color": "red"}]},
   "Colds are viral|Antibiotics don't help", "Cochrane 2025, CDC")
ln("Antibiotics also have side effects. In cold trials, adults given antibiotics had more of them than those on placebo.", IMG(PILLS, "left"), "Not harmless|More side effects", "Cochrane 2025, CDC")
ln("Second, prevent infections. Clean hands are one of the best ways to stop germs spreading.", IMG(HANDS, "in"), "Prevention|Clean hands", "CDC, WHO")
ln("Vaccines prevent infections too, including resistant ones.", {"type": "tags", "tags": ["Vaccines", "Prevent infections", "Including resistant ones"]}, "Vaccines|Fewer infections", "CDC, WHO")
ln("For clinicians: prescribe only when the benefits outweigh the risks, and pick the right drug.",
   {"type": "mnemonic", "title": "STEWARDSHIP", "items": [["1", "Right patient"], ["2", "Right drug"], ["3", "Right time"]]}, "Stewardship|Every prescription counts", "CDC, WHO")
ln("So, to recap. Resistance is caused by germs adapting under antibiotic pressure, and it spreads between bacteria, people and animals.", IMG(GUT, "out"), "Recap|Adaptation and spread", "CDC, Munita 2016")
ln("It already causes over a million deaths a year, and it's highest in regions like ours.", IMG(MUKT, "in"), "Recap|Over a million deaths a year", "Lancet 2024, WHO GLASS 2025")
ln("Antimicrobial resistance is a major global health threat. But it isn't a lost battle.", IMG(MRSA, "left"), "A major threat|Not a lost battle", "WHO, CDC")
ln("Every antibiotic we don't need to use keeps the ones we have working longer.", IMG(RESEARCH, "in"), "", nofact=True)
ln("If this helped, subscribe to Paravion Med. Sources are in the description.", {"type": "end", "bg": BG(MRSA)}, nofact=True)

script = {
 "slug": SLUG, "series": "Deep Dive", "format": "long",
 "kickers": {}, "cover": {"kicker": "DEEP DIVE", "head": ["When", "antibiotics", "stop working"], "sub": "Antimicrobial resistance, explained.", "visual": {"type": "tags", "tags": ["AMR"]}},
 "lines": L,
 "meta": {
  "titles": ["When Antibiotics Stop Working: The Superbug Crisis Explained", "Antibiotic Resistance Explained (Deep Dive)", "How Bacteria Beat Antibiotics, and What Still Works"],
  "summary": "Drug-resistant bacteria directly caused 1.14 million deaths in 2021 and were linked to about 4.7 million. This deep dive covers how penicillin changed medicine, the four ways bacteria resist antibiotics, what WHO's 2025 surveillance found (1 in 6 infections resistant worldwide, 1 in 3 in WHO's South-East Asia region), and what actually works: using antibiotics only when needed, preventing infections, vaccines and stewardship.",
  "hashtags": ["#AntibioticResistance", "#AMR", "#Superbugs", "#Medicine", "#PublicHealth"],
  "ig_tags": "#amr #antibioticresistance #superbugs #medicine #publichealth #medstudent #paravionmed",
  "pinned": "Doctors and students: what's the biggest driver of antibiotic misuse where you work? 👇",
  "poll": ["Heard of AMR before?", "Yes 🩺", "First time 😮"],
  "sources": [
   ["Antimicrobial Resistance Collaborators. Global burden of bacterial AMR 1990-2021 with forecasts to 2050. Lancet 2024", "https://pubmed.ncbi.nlm.nih.gov/39299261/"],
   ["Antimicrobial Resistance Collaborators. Global burden of bacterial AMR in 2019. Lancet 2022", "https://pubmed.ncbi.nlm.nih.gov/35065702/"],
   ["WHO fact sheet: Antimicrobial resistance (updated July 2026)", "https://www.who.int/news-room/fact-sheets/detail/antimicrobial-resistance"],
   ["WHO news release: WHO warns of widespread resistance to common antibiotics worldwide (GLASS 2025)", "https://www.who.int/news/item/13-10-2025-who-warns-of-widespread-resistance-to-common-antibiotics-worldwide"],
   ["CDC: About antimicrobial resistance", "https://www.cdc.gov/antimicrobial-resistance/about/index.html"],
   ["CDC: Causes of antimicrobial resistance", "https://www.cdc.gov/antimicrobial-resistance/causes/index.html"],
   ["CDC: Preventing antimicrobial resistance", "https://www.cdc.gov/antimicrobial-resistance/prevention/index.html"],
   ["Munita JM, Arias CA. Mechanisms of antibiotic resistance. Microbiol Spectr 2016", "https://pubmed.ncbi.nlm.nih.gov/27227291/"],
   ["Chhabra S et al. The penicillin pioneer: Alexander Fleming. Cureus 2024", "https://pubmed.ncbi.nlm.nih.gov/39176366/"],
   ["Geddes A. 80th anniversary of the discovery of penicillin. Int J Antimicrob Agents 2008", "https://pubmed.ncbi.nlm.nih.gov/18715766/"],
   ["Kenealy T, Arroll B. Antibiotics for the common cold. Cochrane 2025", "https://pubmed.ncbi.nlm.nih.gov/41277585/"]],
  "removed": ["India 'Red Line' campaign: official page could not be verified (MoHFW/PIB blocked); cut.",
              "2050 death forecast numbers (e.g. '39 million'): not confirmed by a second trusted source; kept only the qualitative South Asia forecast.",
              "Fleming's Nobel lecture warning about underdosing: Nobel site blocked; cut.",
              "'Finish the course' advice: evidence is debated (BMJ 2017); not stated either way."],
  "notes": "The GLASS figures (1 in 6, 1 in 3, E. coli / Klebsiella resistance) are WHO's own surveillance data, cited from the report's release and the fact sheet. Evergreen deep dive. Re-check WHO/CDC pages and any newer GRAM estimates before posting.",
  "schedule": "2026-11-29T18:00:00+05:30",
  "checked_on": "2026-11-23",
  "verdict": "AMR directly caused 1.14 million deaths in 2021; resistance is rising; prudent use, prevention and vaccines work.",
  "thumbnail": {"image": MRSA, "lines": ["WHEN", "ANTIBIOTICS", "STOP WORKING"], "tag": "1 IN 6 INFECTIONS"}
 }
}

if __name__ == "__main__":
    os.makedirs(f"episodes/{SLUG}", exist_ok=True)
    json.dump(script, open(f"episodes/{SLUG}/script.json", "w"), indent=1, ensure_ascii=False)
    print(SLUG, sum(len(l["text"].split()) for l in L), "words,", len(L), "scenes")
