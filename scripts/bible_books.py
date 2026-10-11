#!/usr/bin/env python3
"""Shared book table, groupings and search helpers for vsearch / fsearch / hsearch."""

import os
import re
import signal
import sys

# Let `| head` / `| less` close the pipe quietly instead of a traceback.
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

# The data lives next to this scripts/ folder (override with $BIBLE_DIR).
BIBLE_DIR = (os.environ.get("BIBLE_DIR")
             or os.path.dirname(os.path.dirname(os.path.realpath(__file__)))).rstrip("/")
VERSES_DIR = BIBLE_DIR + "/verses/"
FOOTNOTES_DIR = BIBLE_DIR + "/footnotes/"
HYMNS_DIR = BIBLE_DIR + "/hymns/"

NO_FOOTNOTES = ("Recovery Version footnotes are not installed. They are not available from a\n"
                "public website, so this toolkit can't download them; if you have them, put\n"
                "them in " + BIBLE_DIR + "/footnotes/<Book>/<chapter>/<verse>/<note number>.")
NO_VERSES = ("The Recovery Version text is not installed yet. Run:  " + BIBLE_DIR
             + "/scripts/fetch_rcv.py\n(Other versions work now, e.g. 'verse kjv john 3:16'.)")
NO_HYMNS = ("The hymns are not installed yet. Run:  " + BIBLE_DIR + "/scripts/fetch_hymns.py")


def require_dir(path, message):
    """Exit with a friendly message if a data folder is missing or empty."""
    if not os.path.isdir(path) or not any(not n.startswith(".") for n in os.listdir(path)):
        print(message)
        sys.exit(1)

# Canonical order (directory names under verses/ and footnotes/).
BOOK_ORDER = [
    "Gen", "Exo", "Lev", "Num", "Deut",
    "Josh", "Judg", "Ruth", "1Sam", "2Sam", "1Kings", "2Kings",
    "1Chron", "2Chron", "Ezra", "Neh", "Esther",
    "Job", "Psa", "Prov", "Eccl", "SOS",
    "Isa", "Jer", "Lam", "Ezek", "Dan",
    "Hos", "Joel", "Amos", "Obad", "Jonah", "Micah", "Nahum",
    "Hab", "Zeph", "Hag", "Zech", "Mal",
    "Matt", "Mark", "Luke", "John", "Acts",
    "Rom", "1Cor", "2Cor", "Gal", "Eph", "Phil", "Col",
    "1Thes", "2Thes", "1Tim", "2Tim", "Titus", "Philemon",
    "Heb", "James", "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev",
]

# Alternate spellings -> directory name. (Lower case, no periods.)
books = {
    "genesis": "Gen", "gn": "Gen",
    "exodus": "Exo", "ex": "Exo",
    "leviticus": "Lev", "lv": "Lev",
    "numbers": "Num",
    "deuteronomy": "Deut", "dt": "Deut",
    "joshua": "Josh",
    "judges": "Judg",
    "1 samuel": "1Sam", "1 sam": "1Sam",
    "2 samuel": "2Sam", "2 sam": "2Sam",
    "1 kings": "1Kings", "2 kings": "2Kings",
    "1 chronicles": "1Chron", "1 chron": "1Chron",
    "2 chronicles": "2Chron", "2 chron": "2Chron",
    "ez": "Ezra",
    "nehemiah": "Neh",
    "esth": "Esther", "es": "Esther", "est": "Esther",
    "jb": "Job",
    "psalm": "Psa", "psalms": "Psa", "ps": "Psa",
    "proverbs": "Prov", "prv": "Prov",
    "ecclesiastes": "Eccl", "ecc": "Eccl",
    "song of songs": "SOS", "song of solomon": "SOS",
    "isaiah": "Isa", "is": "Isa",
    "jeremiah": "Jer",
    "lamentations": "Lam",
    "ezekiel": "Ezek", "ezk": "Ezek", "eze": "Ezek",
    "daniel": "Dan", "dn": "Dan",
    "hosea": "Hos",
    "obadiah": "Obad",
    "mic": "Micah",
    "nah": "Nahum",
    "habakkuk": "Hab",
    "zephaniah": "Zeph",
    "haggai": "Hag",
    "zechariah": "Zech",
    "malachi": "Mal",
    "matthew": "Matt", "mt": "Matt",
    "mk": "Mark",
    "luk": "Luke",
    "jn": "John",
    "ac": "Acts",
    "romans": "Rom", "rm": "Rom",
    "1 corinthians": "1Cor", "1 cor": "1Cor",
    "2 corinthians": "2Cor", "2 cor": "2Cor",
    "galatians": "Gal",
    "ephesians": "Eph",
    "philippians": "Phil",
    "colossians": "Col",
    "1 thessalonians": "1Thes", "1 thes": "1Thes",
    "2 thessalonians": "2Thes", "2 thes": "2Thes",
    "1 timothy": "1Tim", "1 tim": "1Tim",
    "2 timothy": "2Tim", "2 tim": "2Tim",
    "tit": "Titus", "tt": "Titus",
    "phm": "Philemon", "philem": "Philemon",
    "hebrews": "Heb",
    "jam": "James",
    "1 peter": "1Pet", "1 pet": "1Pet",
    "2 peter": "2Pet", "2 pet": "2Pet",
    "1 john": "1John", "1 jn": "1John",
    "2 john": "2John", "2 jn": "2John",
    "3 john": "3John", "3 jn": "3John",
    "jud": "Jude",
    "revelation": "Rev", "rv": "Rev",
}
# Every directory name maps to itself (lower case).
for _b in BOOK_ORDER:
    books[_b.lower()] = _b
# Short glued forms for the numbered books: 1co, 1th, 1jn ... (usable as a
# command name, unlike "1 cor").
books.update({
    "1sa": "1Sam", "2sa": "2Sam", "1ki": "1Kings", "2ki": "2Kings", "1kgs": "1Kings", "2kgs": "2Kings",
    "1ch": "1Chron", "2ch": "2Chron", "1chr": "1Chron", "2chr": "2Chron",
    "1co": "1Cor", "2co": "2Cor", "1th": "1Thes", "2th": "2Thes", "1thess": "1Thes", "2thess": "2Thes",
    "1ti": "1Tim", "2ti": "2Tim", "1pe": "1Pet", "2pe": "2Pet", "1pt": "1Pet", "2pt": "2Pet",
    "1jn": "1John", "2jn": "2John", "3jn": "3John", "1jo": "1John", "2jo": "2John", "3jo": "3John",
    "1samuel": "1Sam", "2samuel": "2Sam", "1corinthians": "1Cor", "2corinthians": "2Cor",
    "1thessalonians": "1Thes", "2thessalonians": "2Thes", "1timothy": "1Tim", "2timothy": "2Tim",
    "1peter": "1Pet", "2peter": "2Pet", "1chronicles": "1Chron", "2chronicles": "2Chron",
})


# ---------- versions ----------
# Text of the Recovery Version lives in verses/; other versions in
# versions/<Name>/ with the same layout and line format.
VERSIONS = {
    "rcv": None, "recovery": None, "recovery version": None,
    "kjv": "KJV", "king james": "KJV", "king james version": "KJV",
    "asv": "ASV", "american standard": "ASV", "american standard version": "ASV",
    "darby": "Darby", "jnd": "Darby", "jn darby": "Darby", "john nelson darby": "Darby",
    "esv": "ESV", "english standard": "ESV", "english standard version": "ESV",
    "all": "ALL", "all versions": "ALL", "every version": "ALL",
}

# Versions that are fetched from the web per passage rather than stored.
REMOTE_VERSIONS = {"ESV"}
ESV_KEY_PATH = BIBLE_DIR + "/esv_api_key"
ESV_COPYRIGHT = "Scripture quotations marked ESV are from the ESV Bible " \
                "(The Holy Bible, English Standard Version), copyright 2001 by Crossway. www.esv.org"

FULL_NAMES = {
    "Gen": "Genesis", "Exo": "Exodus", "Lev": "Leviticus", "Num": "Numbers", "Deut": "Deuteronomy",
    "Josh": "Joshua", "Judg": "Judges", "Ruth": "Ruth", "1Sam": "1 Samuel", "2Sam": "2 Samuel",
    "1Kings": "1 Kings", "2Kings": "2 Kings", "1Chron": "1 Chronicles", "2Chron": "2 Chronicles",
    "Ezra": "Ezra", "Neh": "Nehemiah", "Esther": "Esther", "Job": "Job", "Psa": "Psalm",
    "Prov": "Proverbs", "Eccl": "Ecclesiastes", "SOS": "Song of Solomon", "Isa": "Isaiah",
    "Jer": "Jeremiah", "Lam": "Lamentations", "Ezek": "Ezekiel", "Dan": "Daniel", "Hos": "Hosea",
    "Joel": "Joel", "Amos": "Amos", "Obad": "Obadiah", "Jonah": "Jonah", "Micah": "Micah",
    "Nahum": "Nahum", "Hab": "Habakkuk", "Zeph": "Zephaniah", "Hag": "Haggai", "Zech": "Zechariah",
    "Mal": "Malachi", "Matt": "Matthew", "Mark": "Mark", "Luke": "Luke", "John": "John",
    "Acts": "Acts", "Rom": "Romans", "1Cor": "1 Corinthians", "2Cor": "2 Corinthians",
    "Gal": "Galatians", "Eph": "Ephesians", "Phil": "Philippians", "Col": "Colossians",
    "1Thes": "1 Thessalonians", "2Thes": "2 Thessalonians", "1Tim": "1 Timothy", "2Tim": "2 Timothy",
    "Titus": "Titus", "Philemon": "Philemon", "Heb": "Hebrews", "James": "James", "1Pet": "1 Peter",
    "2Pet": "2 Peter", "1John": "1 John", "2John": "2 John", "3John": "3 John", "Jude": "Jude",
    "Rev": "Revelation",
}
# Display prefixes, matching the Recovery Version files ("Rom. 8:28 ...").
PREFIXES = {
    "Gen": "Gen.", "Exo": "Exo.", "Lev": "Lev.", "Num": "Num.", "Deut": "Deut.", "Josh": "Josh.",
    "Judg": "Judg.", "Ruth": "Ruth", "1Sam": "1 Sam.", "2Sam": "2 Sam.", "1Kings": "1 Kings",
    "2Kings": "2 Kings", "1Chron": "1 Chron.", "2Chron": "2 Chron.", "Ezra": "Ezra", "Neh": "Neh.",
    "Esther": "Esth.", "Job": "Job", "Psa": "Psa.", "Prov": "Prov.", "Eccl": "Eccl.", "SOS": "SoS",
    "Isa": "Isa.", "Jer": "Jer.", "Lam": "Lam.", "Ezek": "Ezek.", "Dan": "Dan.", "Hos": "Hosea",
    "Joel": "Joel", "Amos": "Amos", "Obad": "Obad.", "Jonah": "Jonah", "Micah": "Micah",
    "Nahum": "Nahum", "Hab": "Hab.", "Zeph": "Zeph.", "Hag": "Hag.", "Zech": "Zech.", "Mal": "Mal.",
    "Matt": "Matt.", "Mark": "Mark", "Luke": "Luke", "John": "John", "Acts": "Acts", "Rom": "Rom.",
    "1Cor": "1 Cor.", "2Cor": "2 Cor.", "Gal": "Gal.", "Eph": "Eph.", "Phil": "Phil.", "Col": "Col.",
    "1Thes": "1 Thes.", "2Thes": "2 Thes.", "1Tim": "1 Tim.", "2Tim": "2 Tim.", "Titus": "Titus",
    "Philemon": "Philemon", "Heb": "Heb.", "James": "James", "1Pet": "1 Pet.", "2Pet": "2 Pet.",
    "1John": "1 John", "2John": "2 John", "3John": "3 John", "Jude": "Jude", "Rev": "Rev.",
}
SINGLE_CHAPTER = {"Obad", "Philemon", "2John", "3John", "Jude"}


def esv_key():
    try:
        with open(ESV_KEY_PATH) as fp:
            return fp.read().strip()
    except OSError:
        return None


def esv_verses(book, chapter, lo=None, hi=None):
    """Fetch a chapter, verse or range from api.esv.org and return lines in
    the usual 'Rom. 8:28 text' format. Raises RuntimeError with a message."""
    import json
    import urllib.parse
    import urllib.request
    key = esv_key()
    if not key:
        raise RuntimeError("No ESV API key. Get a free key at https://api.esv.org/ and save it in " +
                           ESV_KEY_PATH)
    q = FULL_NAMES[book] + " " + chapter
    if lo is not None:
        q += ":" + str(lo) + ("-" + str(hi) if hi and hi != lo else "")
    params = {
        "q": q,
        "include-passage-references": "false", "include-verse-numbers": "true",
        "include-first-verse-numbers": "true", "include-footnotes": "false",
        "include-headings": "false", "include-short-copyright": "false",
        "include-selahs": "true", "indent-poetry": "false", "indent-paragraphs": "0",
        "indent-declares": "0", "indent-psalm-doxology": "0", "line-length": "0",
    }
    url = "https://api.esv.org/v3/passage/text/?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": "Token " + key})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except Exception as e:  # network, 401, 429 ...
        raise RuntimeError("ESV API request failed: " + str(e))
    passages = data.get("passages") or []
    if not passages:
        raise RuntimeError("ESV: no text returned for '" + q + "'")
    text = re.sub(r"\s+", " ", " ".join(passages)).strip()
    # Split "[28] And we know ... [29] For those ..." into verse lines.
    parts = re.split(r"\[(\d+)\]", text)
    lines = []
    prefix = PREFIXES[book]
    for i in range(1, len(parts) - 1, 2):
        vno, body = parts[i], parts[i + 1].strip()
        ref = prefix + " " + vno if book in SINGLE_CHAPTER else prefix + " " + chapter + ":" + vno
        lines.append(ref + " " + body)
    if not lines:
        lines = [prefix + " " + chapter + " " + text]
    return lines


def parse_version(args):
    """Peel an optional leading version name off args.
    Returns (version, remaining_args); version is None for the Recovery
    Version, a directory name under versions/, or 'ALL'."""
    for n in (3, 2, 1):
        key = " ".join(args[:n]).lower().replace(".", "")
        if len(args) >= n and key in VERSIONS:
            return VERSIONS[key], args[n:]
    return None, args


def parse_versions(args):
    """Peel any number of leading version names off args.
    'kjv esv rom 8:28' -> (['KJV', 'ESV'], ['rom', '8:28']);
    no version -> ([None], args)."""
    versions = []
    while True:
        v, rest = parse_version(args)
        if rest is args:
            break
        if v == "ALL":
            for x in all_versions():
                if x not in versions:
                    versions.append(x)
        elif v not in versions:
            versions.append(v)
        args = rest
    return versions or [None], args


def verses_dir(version):
    if version is None:
        return VERSES_DIR
    return BIBLE_DIR + "/versions/" + version + "/"


def version_label(version):
    return "RcV" if version is None else version


def all_versions():
    """[None, 'ASV', 'Darby', 'KJV', ...] - whatever is installed."""
    vdir = BIBLE_DIR + "/versions/"
    out = [None]
    if os.path.isdir(vdir):
        out += sorted(d for d in os.listdir(vdir) if not d.startswith("."))
    if esv_key():
        out.append("ESV")
    return out


def expand_versions(version):
    return all_versions() if version == "ALL" else [version]


# "Rom. 8:28 text" / "1 Cor. 1:1 text" / "Jude 3 text" -> (ref, text)
_REF_RE = re.compile(r"^((?:\d )?[A-Za-z]+\.? (?:\d+:)?\d+) (.*)$")


def split_ref(line):
    m = _REF_RE.match(line.rstrip("\n"))
    if m:
        return m.group(1), m.group(2)
    return "", line.rstrip("\n")


def paragraph(lines):
    """Join verse lines into one paragraph with a single reference at the end,
    e.g. 'text text text (Rom. 8:28-30)'."""
    refs = [split_ref(l)[0] for l in lines]
    texts = [split_ref(l)[1] for l in lines]
    first, last = refs[0], refs[-1]
    if first == last or not first:
        ref = first
    else:
        # "Rom. 8:28" .. "Rom. 8:30" -> "Rom. 8:28-30"; across chapters keep both.
        a, b = first.rsplit(" ", 1)[1], last.rsplit(" ", 1)[1]
        if ":" in a and ":" in b and a.split(":")[0] == b.split(":")[0]:
            ref = first + "-" + b.split(":")[1]
        else:
            ref = first + "-" + b
    body = " ".join(t.strip() for t in texts)
    return body + (" (" + ref + ")" if ref else "")


def _span(first, last):
    i, j = BOOK_ORDER.index(first), BOOK_ORDER.index(last)
    return BOOK_ORDER[i:j + 1]


# Named groups of books -> list of directory names, in canonical order.
groups = {
    "ot":            _span("Gen", "Mal"),
    "nt":            _span("Matt", "Rev"),
    "law":           _span("Gen", "Deut"),
    "history":       _span("Gen", "Neh"),     # Genesis through Nehemiah
    "poetry":        _span("Job", "SOS"),
    "prophets":      _span("Isa", "Mal"),
    "major":         _span("Isa", "Dan"),
    "minor":         _span("Hos", "Mal"),
    "gospels":       _span("Matt", "John"),
    "epistles":      _span("Rom", "Jude"),
    "pauline":       _span("Rom", "Philemon"),
    "heart":         ["Gal", "Eph", "Phil", "Col"],
    "pastoral":      ["1Tim", "2Tim", "Titus"],
    "general":       _span("Heb", "Jude"),
    # authors and paired books
    "peter":         ["1Pet", "2Pet"],
    "johns writings": ["John", "1John", "2John", "3John", "Rev"],
    "johns epistles": ["1John", "2John", "3John"],
    "pauls writings": _span("Rom", "Philemon"),
    "corinthians":   ["1Cor", "2Cor"],
    "thessalonians": ["1Thes", "2Thes"],
    "timothy":       ["1Tim", "2Tim"],
    "samuel":        ["1Sam", "2Sam"],
    "kings":         ["1Kings", "2Kings"],
    "chronicles":    ["1Chron", "2Chron"],
    "moses":         _span("Gen", "Deut"),
}
group_aliases = {
    "old testament": "ot", "old": "ot",
    "new testament": "nt", "new": "nt",
    "pentateuch": "law", "torah": "law",
    "historical": "history",
    "wisdom": "poetry", "poetic": "poetry", "poetical": "poetry",
    "major prophets": "major",
    "minor prophets": "minor",
    "gospel": "gospels",
    "epistle": "epistles", "letters": "epistles",
    "paul": "pauline", "pauline epistles": "pauline",
    "heart of the bible": "heart",
    "pastoral epistles": "pastoral",
    "general epistles": "general", "catholic": "general",
    "peters": "peter", "peters epistles": "peter", "peters writings": "peter", "pet": "peter",
    "johns writing": "johns writings", "johns": "johns writings", "johannine": "johns writings",
    "johns letters": "johns epistles", "johns epistle": "johns epistles",
    "pauls writing": "pauls writings", "pauls": "pauls writings", "pauls epistles": "pauls writings",
    "pauls letters": "pauls writings",
    "cor": "corinthians", "thes": "thessalonians", "thess": "thessalonians", "tim": "timothy",
    "sam": "samuel", "chron": "chronicles", "books of moses": "moses",
    "tims": "timothy", "timothys": "timothy", "timothies": "timothy", "timothy's": "timothy",
    "1 and 2 timothy": "timothy", "1&2 tim": "timothy",
    "cors": "corinthians", "1 and 2 corinthians": "corinthians",
    "thesses": "thessalonians", "1 and 2 thessalonians": "thessalonians",
    "pets": "peter", "peters": "peter", "1 and 2 peter": "peter",
    "sams": "samuel", "samuels": "samuel", "1 and 2 samuel": "samuel",
    "kgs": "kings", "1 and 2 kings": "kings",
    "chrons": "chronicles", "1 and 2 chronicles": "chronicles",
    "johns epistles": "johns epistles", "1 2 3 john": "johns epistles", "1-3 john": "johns epistles",
}


def normalize(name):
    return " ".join(name.lower().replace(".", "").replace("'", "").replace("\u2019", "").split())


def resolve(name):
    """Return (kind, list_of_books) for a book or group name, or None."""
    key = normalize(name)
    if key in books:
        return "book", [books[key]]
    key = group_aliases.get(key, key)
    if key in groups:
        return "group", groups[key]
    return None


def usage_scopes():
    return "Scopes: a book (rom, 1 cor, song of songs ...) or a group: " + \
        ", ".join(sorted(groups)) + "."


def numeric_sort(names):
    """Sort directory entries numerically, ignoring junk like .DS_Store."""
    return sorted((n for n in names if n.isdigit()), key=int)


# ---------- output helpers ----------

COLOR = sys.stdout.isatty() or os.environ.get("BIBLE_COLOR") == "1"
RED, BOLD, RESET = "\033[1;31m", "\033[1m", "\033[0m"


OR_WORDS = {"or", "OR", "|"}


def split_or(args):
    """['rom', 'a', 'or', 'b'] -> (['rom'], ['a', 'b']).
    Several search terms joined by 'or' match a verse containing any of them."""
    args = list(args)
    if not args:
        return args, []
    terms = [args.pop()]
    while len(args) >= 2 and args[-1] in OR_WORDS:
        args.pop()
        terms.insert(0, args.pop())
    return args, terms


def make_pattern(term, whole_word):
    """The term is a regular expression (like grep); fall back to a literal
    match if it is not a valid one. A list of terms matches any of them."""
    if isinstance(term, (list, tuple)):
        if len(term) == 1:
            return make_pattern(term[0], whole_word)
        alts = "|".join("(?:" + make_pattern(t, whole_word).pattern + ")" for t in term)
        return re.compile(alts, re.IGNORECASE)
    try:
        re.compile(term)
        # ".*" stops at the nearest match, so "arrows.*quiver" runs from the
        # first "arrows" to the next "quiver" rather than the last one.
        pat = re.sub(r"\.\*(?![?+])", ".*?", term)
    except re.error:
        pat = re.escape(term)
    if whole_word:
        pat = r"\b(?:" + pat + r")\b"
    return re.compile(pat, re.IGNORECASE)


# ---------- synonyms ----------

SYNONYMS_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "bible_synonyms.txt")


def _stem(word):
    """Crude stem so 'compassions' also finds 'compassion', 'mercies' -> 'merci'."""
    w = word.lower()
    for suf in ("ies", "es", "s", "ed", "ing"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            w = w[: -len(suf)]
            if suf == "ies":
                w += "i"
            break
    return w


def synonyms(term):
    """Return (words, note): the term plus its synonyms from bible_synonyms.txt
    and, when the nltk WordNet corpus is installed, from WordNet."""
    key = _stem(term)
    words = {term.lower()}
    # 1. curated groups: one group per line, comma separated; '#' comments.
    try:
        with open(SYNONYMS_PATH) as fp:
            for line in fp:
                line = line.split("#")[0].strip()
                if not line:
                    continue
                group = [w.strip().lower() for w in line.split(",") if w.strip()]
                if any(_stem(w) == key for w in group):
                    words.update(group)
    except OSError:
        pass
    # 2. WordNet, if available.
    note = ""
    try:
        from nltk.corpus import wordnet
        for syn in wordnet.synsets(term):
            for lemma in syn.lemma_names():
                if "_" not in lemma:
                    words.add(lemma.lower())
    except ImportError:
        note = "(WordNet not installed; using bible_synonyms.txt only. " \
               "For more: pip3 install nltk && python3 -c \"import nltk; nltk.download('wordnet')\")"
    except LookupError:
        note = "(WordNet corpus missing; using bible_synonyms.txt only. " \
               "Run: python3 -c \"import nltk; nltk.download('wordnet')\")"
    return sorted(words), note


def synonym_pattern(term, whole_word):
    words, note = synonyms(term)
    stems = set()
    for w in words:
        s = _stem(w)
        stems.add(s)
        if s.endswith("y"):          # mercy -> merci(es), glory -> glori(ous)
            stems.add(s[:-1] + "i")
    alts = "|".join(re.escape(s) + r"\w*" for s in sorted(stems))
    pat = r"\b(?:" + alts + r")"
    if whole_word:
        pat += r"\b"
    return re.compile(pat, re.IGNORECASE), words, note


def highlight(pattern, text):
    if not COLOR:
        return text
    return pattern.sub(lambda m: RED + m.group(0) + RESET, text)


def highlight_block(pattern, lines):
    """Highlight matches of pattern in the text formed by joining lines with
    spaces, so a match that spans several verses is coloured from its first
    word to its last, across the line breaks."""
    if not COLOR:
        return list(lines)
    joined = " ".join(lines)
    spans = [m.span() for m in pattern.finditer(joined) if m.end() > m.start()]
    out = []
    pos = 0
    for line in lines:
        start, end = pos, pos + len(line)
        pieces = []
        cur = start
        ref_end = start + len(split_ref(line)[0]) + 1   # keep "Psa. 127:5" uncoloured
        for a, b in spans:
            a2, b2 = max(a, start), min(b, end)
            if a2 == start and a < start:                # match continues from the line above
                a2 = min(ref_end, b2)
            if a2 >= b2:
                continue
            pieces.append(joined[cur:a2])
            pieces.append(RED + joined[a2:b2] + RESET)
            cur = b2
        pieces.append(joined[cur:end])
        out.append("".join(pieces))
        pos = end + 1
    return out


def bold(text):
    return BOLD + text + RESET if COLOR else text


def parse_args(argv, usage):
    """Split argv into (flags, positional).
    Flags: -o counts, -w whole word, -f footnotes, -s / 'syn' synonyms,
    -m N / 'm N' match across up to N consecutive verses."""
    flags = {"o": False, "w": False, "f": False, "s": False, "p": False, "m": None}
    args = []
    argv = list(argv)
    i = 0
    while i < len(argv):
        a = argv[i]
        nxt = argv[i + 1] if i + 1 < len(argv) else None
        if a in ("syn", "-syn", "--syn"):
            flags["s"] = True
        elif a == "m" and nxt is not None and nxt.isdigit():
            flags["m"] = int(nxt)
            i += 1
        elif a == "-m" and nxt is not None and nxt.isdigit():
            flags["m"] = int(nxt)
            i += 1
        elif a.startswith("-") and len(a) > 1 and not a[1:].isdigit():
            for ch in a[1:]:
                if ch == "m":
                    print("-m needs a number, e.g. -m 3")
                    sys.exit(1)
                if ch in flags:
                    flags[ch] = True
                else:
                    print("Unknown option -" + ch)
                    print(usage)
                    sys.exit(1)
        else:
            args.append(a)
        i += 1
    if not args:
        print(usage)
        sys.exit(1)
    if flags["m"] is not None and flags["m"] < 1:
        print("-m needs a number of verses of at least 1")
        sys.exit(1)
    return flags, args


SEPARATORS = {"+", ",", "&", "and"}


def _split_parts(ref_args):
    """Split ['rom', '8', '+', 'poetry', ',', 'sos'] into
    [['rom', '8'], ['poetry'], ['sos']]. Separators may also be glued on:
    'rom,sos' or 'rom+sos'."""
    parts, cur = [], []
    for a in ref_args:
        tokens = [a]
        if a not in SEPARATORS and ("," in a or "+" in a or "&" in a):
            tokens = [t for t in re.split(r"([,+&])", a) if t != ""]
        for t in tokens:
            if t in SEPARATORS:
                if cur:
                    parts.append(cur)
                cur = []
            else:
                cur.append(t)
    if cur:
        parts.append(cur)
    return parts


_CHAP_RE = re.compile(r"^(\d+)(?:-(\d+))?$")            # 8 or 8-10
_VERSE_RE = re.compile(r"^(\d+):(\d+)(?:-(\d+))?$")     # 8:28 or 8:28-39


def parse_scope(ref_args, usage):
    """ref_args: everything before the search term.
    Returns a list of (book, chapter, verse_range) in canonical order, where
    chapter is a string or None (whole book) and verse_range is (lo, hi) or
    None.  'rom 8-10 + psa 23:1-3 + poetry' ->
    [(Job,None,None), ..., (Psa,'23',(1,3)), ..., (Rom,'8',None), (Rom,'9',None), (Rom,'10',None)]."""
    if not ref_args:
        return [(b, None, None) for b in BOOK_ORDER]
    scope = {}  # book -> list of (chapter, verse_range); [] means whole book
    prev_book = None
    prev_chap = None
    for part in _split_parts(ref_args):
        # "1 cor 1:1, 5-8" -> the 5-8 part inherits "1 cor" (and chapter 1)
        if len(part) == 1 and prev_book and re.match(r"^[\d:\-]+$", part[0]):
            ref = part[0]
            if ":" not in ref and prev_chap is not None:
                ref = prev_chap + ":" + ref
            part = prev_book + [ref]
        chapters = []          # list of (chapter, verse_range)
        last = part[-1]
        m = _CHAP_RE.match(last)
        mv = _VERSE_RE.match(last)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
            if hi < lo:
                print("Bad chapter range: " + last)
                sys.exit(1)
            chapters = [(str(c), None) for c in range(lo, hi + 1)]
            part = part[:-1]
        elif mv:
            lo, hi = int(mv.group(2)), int(mv.group(3) or mv.group(2))
            if hi < lo:
                print("Bad verse range: " + last)
                sys.exit(1)
            chapters = [(mv.group(1), (lo, hi))]
            part = part[:-1]
        if chapters and not part:
            print("A chapter or verse range needs a book in front of it.")
            sys.exit(1)
        prev_book = part if part else prev_book
        prev_chap = mv.group(1) if (not m and mv) else None
        res = resolve(" ".join(part))
        if res is None:
            print("Unknown book or group: '" + " ".join(part) + "'.")
            print(usage)
            print(usage_scopes())
            sys.exit(1)
        kind, book_list = res
        if chapters and kind == "group":
            print("A chapter only makes sense with a single book ('" +
                  " ".join(part) + " " + last + "').")
            sys.exit(1)
        for b in book_list:
            lst = scope.setdefault(b, [])
            if chapters:
                if lst != "ALL":
                    lst.extend(chapters)
            else:
                scope[b] = "ALL"
    out = []
    for b in BOOK_ORDER:
        if b not in scope:
            continue
        if scope[b] == "ALL":
            out.append((b, None, None))
        else:
            seen = set()
            for ch, vr in sorted(scope[b], key=lambda x: (int(x[0]), x[1] or (0, 0))):
                if (ch, vr) not in seen:
                    seen.add((ch, vr))
                    out.append((b, ch, vr))
    return out


def synonym_patterns(terms, whole_word):
    """synonym_pattern for one or more 'or' terms."""
    if not isinstance(terms, (list, tuple)):
        terms = [terms]
    pats, words, notes = [], [], []
    for t in terms:
        p, w, n = synonym_pattern(t, whole_word)
        pats.append("(?:" + p.pattern + ")")
        words += w
        if n:
            notes.append(n)
    return re.compile("|".join(pats), re.IGNORECASE), words, "  ".join(notes)
