"""Normalise script text and Whisper transcripts the same way, so '45' == 'forty-five', '10th' == 'tenth'."""
import re

_O = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
_T = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
_ORD = {"one": "first", "two": "second", "three": "third", "five": "fifth", "eight": "eighth", "nine": "ninth", "twelve": "twelfth"}


def words(n):
    if n < 20: return _O[n]
    if n < 100: return _T[n // 10] + ("" if n % 10 == 0 else " " + _O[n % 10])
    if n < 1000: return _O[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + words(n % 100))
    for div, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
        if n >= div:
            return words(n // div) + " " + name + ("" if n % div == 0 else " " + words(n % div))


def ordinal(n):
    w = words(n).split(); last = w[-1]
    w[-1] = _ORD.get(last, last[:-1] + "ieth" if last.endswith("y") else last + "th")
    return " ".join(w)


def norm(t):
    t = t.lower()
    # British/American spelling and possessives, applied to script and transcript alike
    t = t.replace("’", "'").replace("'s", "s").replace("our", "or").replace("anaes", "anes").replace("paed", "ped").replace("oed", "ed")
    t = re.sub(r"(\w)tre(s?)\b", r"\1ter\2", t)
    t = t.replace("-", " ").replace("–", " ").replace("%", " percent ")
    t = re.sub(r"(\d),(\d)", r"\1\2", t)
    t = re.sub(r"\b(\d+)(st|nd|rd|th)\b", lambda m: ordinal(int(m.group(1))), t)
    t = re.sub(r"\b(1[0-9]|20)(\d\d)\b", lambda m: words(int(m.group(1))) + " " + words(int(m.group(2))) if len(m.group(0)) == 4 else m.group(0), t)  # years
    t = re.sub(r"\d+", lambda m: words(int(m.group(0))), t)
    t = re.sub(r"[^a-z ]", " ", t)
    drop = {"dollars", "dollar", "euros", "euro", "a", "the", "and"}
    return " ".join(w for w in t.split() if w not in drop)
