#!/usr/bin/env python3
"""Greek / Hebrew interlinear, parsing and Strong's lookup.

  il heb 11:6            interlinear: RcV text, then each Greek/Hebrew word with its
                         transliteration, English gloss, Strong's number and parsing
  il psa 103:7-8         ranges, chapters and comma lists work as in `verse`
  il john 1:1, 14
  il -w heb 11:6         word list: one word per line, parsing spelled out,
                         dictionary form and meaning
  il -c heb 11:6         compact: word, transliteration and gloss only
  il -t psa 103:7        leave out the Hebrew/Greek script (transliteration only),
                         useful if a terminal mangles right-to-left text

  il G2100               lexicon entry for a Strong's number, then every occurrence
  il H1870 psa           ... limited to a book, group or chapter (same scopes as vs)
  il -o G2100            ... just the count per book
  il -b H1870 psa        ... brief: without the RcV verse under each occurrence

  il G2222 G0166         phrase: verses where the words occur together (within 3
                         words of each other, any order) -- e.g. "eternal life"
  il -n 6 G2222 G0166    ... within 6 words;   il -a G2222 G0166  anywhere in the verse
  il -f eternal          find Strong's numbers by English gloss, transliteration or
                         Greek/Hebrew word:  il -f zoe,  il -f derek,  il -f πίστις

Greek: the NA27/28 text.  Hebrew: the Leningrad codex (verse numbers follow the
English Bible; psalm titles are verse 0).  Data: STEP Bible (www.STEPBible.org),
Tyndale House, CC BY 4.0 -- see ~/Bible/interlinear/CREDITS.txt.
"""

import os
import re
import shutil
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import bible_books as bb
import verse as vs

IL_DIR = bb.BIBLE_DIR + "/interlinear/"
TEXT_DIR = IL_DIR + "text/"
USAGE = ("Usage: il [-w|-c|-t] <book> <ref>          interlinear\n"
         "       il [-o|-b] <Strong's #> [scope]     lexicon + occurrences\n"
         "       il [-n N|-a] <#> <#> ... [scope]    words occurring together\n"
         "       il -f <word>                        find Strong's numbers")

DIM, CYAN, BOLD, RESET = "\033[2m", "\033[36m", "\033[1m", "\033[0m"
LRM = "‎"          # keeps right-to-left words in left-to-right column order


def c(code, text):
    return code + text + RESET if bb.COLOR else text


# ---------------------------------------------------------------- data access

def read_words(book, chap):
    """{verse(int): [(orig, translit, gloss, strongs, morph, lemma), ...]}"""
    out = {}
    try:
        with open(TEXT_DIR + book + "/" + str(chap), encoding="utf-8") as fp:
            for line in fp:
                f = line.rstrip("\n").split("\t")
                f += [""] * (7 - len(f))
                out.setdefault(int(f[0]), []).append(tuple(f[1:7]))
    except OSError:
        return None
    return out


def rcv_line(book, chap, verse):
    lines = vs.read_chapter(None, book, str(chap))
    if lines and 1 <= verse <= len(lines):
        return lines[verse - 1]
    return None


def label(book, chap, verse):
    p = bb.PREFIXES.get(book, book)
    if verse == 0:
        return p + " " + str(chap) + " (title)"
    if book in bb.SINGLE_CHAPTER:
        return p + " " + str(verse)
    return p + " " + str(chap) + ":" + str(verse)


_LEX = None


def lexicon():
    global _LEX
    if _LEX is None:
        _LEX = {}
        try:
            with open(IL_DIR + "lexicon.tsv", encoding="utf-8") as fp:
                for line in fp:
                    f = line.rstrip("\n").split("\t")
                    if len(f) >= 6:
                        _LEX[f[0]] = f[1:]
        except OSError:
            pass
    return _LEX


def base_strongs(s):
    m = re.match(r"^([GH])0*(\d+)", s)
    return (m.group(1) + m.group(2).zfill(4)) if m else s


# ---------------------------------------------------------------- display width

def width(s):
    w = 0
    for ch in s:
        if unicodedata.combining(ch) or unicodedata.category(ch) in ("Mn", "Me", "Cf"):
            continue
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


def pad(s, n):
    return s + " " * max(0, n - width(s))


def is_hebrew(s):
    return any("֐" <= ch <= "׿" for ch in s)


# ---------------------------------------------------------------- parsing codes

G_CASE = {"N": "nominative", "G": "genitive", "D": "dative", "A": "accusative", "V": "vocative"}
G_NUM = {"S": "singular", "P": "plural"}
G_GEN = {"M": "masculine", "F": "feminine", "N": "neuter"}
G_TENSE = {"P": "present", "I": "imperfect", "F": "future", "A": "aorist", "R": "perfect",
           "L": "pluperfect", "X": "no tense"}
G_VOICE = {"A": "active", "M": "middle", "P": "passive", "E": "middle or passive",
           "D": "middle deponent", "O": "passive deponent", "N": "middle/passive deponent",
           "Q": "impersonal active", "X": "no voice"}
G_MOOD = {"I": "indicative", "S": "subjunctive", "O": "optative", "M": "imperative",
          "N": "infinitive", "P": "participle", "R": "imperative participle"}
G_POS = {"N": "noun", "V": "verb", "A": "adjective", "T": "article", "P": "personal pronoun",
         "R": "relative pronoun", "C": "reciprocal pronoun", "D": "demonstrative pronoun",
         "K": "correlative pronoun", "I": "interrogative pronoun", "X": "indefinite pronoun",
         "Q": "correlative/interrogative pronoun", "F": "reflexive pronoun",
         "S": "possessive pronoun", "ADV": "adverb", "CONJ": "conjunction",
         "COND": "conditional particle", "PRT": "particle", "PREP": "preposition",
         "INJ": "interjection", "ARAM": "Aramaic word", "HEB": "Hebrew word"}
G_EXTRA = {"T": "title", "P": "person", "L": "place", "C": "comparative", "S": "superlative",
           "PRI": "proper, indeclinable", "NUI": "numeral, indeclinable", "LI": "letter",
           "OI": "indeclinable", "ATT": "Attic form", "ABB": "abbreviated", "I": "interrogative",
           "N": "negative", "K": "crasis", "APO": "apocopated"}


def _cng(s):
    """'GSF' -> genitive singular feminine; '1GS' -> 1st person genitive singular."""
    out = []
    if s[:1] in "123":
        out.append({"1": "1st", "2": "2nd", "3": "3rd"}[s[0]] + " person")
        s = s[1:]
    for ch, table in zip(s, (G_CASE, G_NUM, G_GEN)):
        if ch in table:
            out.append(table[ch])
    return " ".join(out)


def greek_morph(code):
    parts = code.split("-")
    pos = parts[0]
    if pos not in G_POS:
        return code
    out = [G_POS[pos]]
    rest = parts[1:]
    if pos == "V" and rest:
        t = rest[0]
        second = t.startswith("2")
        if second:
            t = t[1:]
        if len(t) >= 3:
            tense = ("second " if second else "") + G_TENSE.get(t[0], t[0])
            out.append(tense + " " + G_VOICE.get(t[1], t[1]) + " " + G_MOOD.get(t[2], t[2]))
        rest = rest[1:]
        if rest and re.match(r"^[123][SP]$", rest[0]):
            out.append({"1": "1st", "2": "2nd", "3": "3rd"}[rest[0][0]] + " person " + G_NUM[rest[0][1]])
            rest = rest[1:]
        elif rest and re.match(r"^[NGDAV][SP][MFN]?$", rest[0]):
            out.append(_cng(rest[0]))
            rest = rest[1:]
    elif rest and re.match(r"^[123]?[NGDAV][SP][MFN]?$", rest[0]):
        out.append(_cng(rest[0]))
        rest = rest[1:]
    for r in rest:
        out.append(G_EXTRA.get(r, r))
    return ", ".join(x for x in out if x)


H_POS = {"A": "adjective", "C": "conjunction", "D": "adverb", "N": "noun", "P": "pronoun",
         "R": "preposition", "S": "suffix", "T": "particle", "V": "verb"}
H_STEM = {"q": "qal", "N": "niphal", "p": "piel", "P": "pual", "h": "hiphil", "H": "hophal",
          "t": "hithpael", "o": "polel", "O": "polal", "r": "hithpolel", "m": "poel", "M": "poal",
          "k": "palel", "K": "pulal", "Q": "qal passive", "l": "pilpel", "L": "polpal",
          "f": "hithpalpel", "D": "nithpael", "j": "pealal", "i": "pilel", "u": "hothpaal",
          "c": "tiphil", "v": "hishtaphel", "w": "nithpalel", "y": "nithpoel", "z": "hithpoel"}
A_STEM = {"q": "peal", "Q": "peil", "u": "hithpeel", "p": "pael", "P": "ithpaal", "M": "hithpaal",
          "a": "aphel", "h": "haphel", "s": "saphel", "e": "shaphel", "H": "hophal", "i": "ithpeel",
          "t": "hishtaphel", "v": "ishtaphel", "w": "hithaphel", "o": "polel", "z": "ithpoel",
          "r": "hithpolel", "f": "hithpalpel", "b": "hephal", "c": "tiphel", "m": "poel",
          "l": "palpel", "L": "ithpalpel", "O": "ithpolel", "G": "ittaphal"}
H_CONJ = {"p": "perfect", "q": "sequential perfect", "i": "imperfect", "w": "sequential imperfect",
          "h": "cohortative", "j": "jussive", "v": "imperative", "r": "participle (active)",
          "s": "participle (passive)", "a": "infinitive absolute", "c": "infinitive construct"}
H_PERS = {"1": "1st", "2": "2nd", "3": "3rd"}
H_GEN = {"m": "masculine", "f": "feminine", "c": "common", "b": "both"}
H_NUM = {"s": "singular", "p": "plural", "d": "dual"}
H_STATE = {"a": "absolute", "c": "construct", "d": "determined"}
H_NTYPE = {"c": "", "g": "gentilic", "p": "proper name"}
H_PROPER = {"m": "person", "f": "person (f)", "l": "place", "t": "title", "g": "people"}
H_PTYPE = {"d": "demonstrative", "f": "indefinite", "i": "interrogative", "p": "personal",
           "r": "relative"}
H_STYPE = {"d": "directional he", "h": "paragogic he", "n": "paragogic nun", "p": "pronominal"}
H_TTYPE = {"a": "affirmation", "d": "definite article", "e": "exhortation", "i": "interrogative",
           "j": "interjection", "m": "demonstrative", "n": "negative", "o": "object marker",
           "r": "relative"}
H_ATYPE = {"a": "", "c": "cardinal number", "g": "gentilic", "o": "ordinal number"}


def _pgn(s):
    out = []
    if s[:1] in H_PERS:
        out.append(H_PERS[s[0]] + " person")
        s = s[1:]
    if s[:1] in H_GEN:
        out.append(H_GEN[s[0]])
        s = s[1:]
    if s[:1] in H_NUM:
        out.append(H_NUM[s[0]])
        s = s[1:]
    if s[:1] in H_STATE:
        out.append(H_STATE[s[0]])
    return " ".join(out)


def hebrew_segment(seg, aramaic):
    if not seg:
        return ""
    pos, rest = seg[0], seg[1:]
    name = H_POS.get(pos, seg)
    if pos == "V" and len(rest) >= 2:
        stem = (A_STEM if aramaic else H_STEM).get(rest[0], rest[0])
        return "verb " + stem + " " + H_CONJ.get(rest[1], rest[1]) + (" " + _pgn(rest[2:]) if rest[2:] else "")
    if pos == "N" and rest:
        if rest[0] == "p":
            return "proper name" + (" (" + H_PROPER.get(rest[1], rest[1]) + ")" if rest[1:] else "")
        kind = H_NTYPE.get(rest[0], rest[0])
        return ("noun " + kind).strip() + " " + _pgn(rest[1:])
    if pos == "A" and rest:
        kind = H_ATYPE.get(rest[0], rest[0])
        return ("adjective " + kind).strip() + " " + _pgn(rest[1:])
    if pos == "P" and rest:
        return H_PTYPE.get(rest[0], rest[0]) + " pronoun " + _pgn(rest[1:])
    if pos == "S" and rest:
        return H_STYPE.get(rest[0], rest[0]) + " suffix " + _pgn(rest[1:])
    if pos == "T" and rest:
        return H_TTYPE.get(rest[0], rest[0]) + " particle"
    if pos == "R" and rest[:1] == "d":
        return "preposition + article"
    return name


def hebrew_morph(code):
    if not code or code[0] not in "HA":
        return code
    aramaic = code[0] == "A"
    segs = [hebrew_segment(s, aramaic) for s in code[1:].split("/")]
    return ("Aramaic: " if aramaic else "") + " + ".join(s.strip() for s in segs if s.strip())


def decode(code):
    if re.match(r"^[HA][A-Z]", code):
        return hebrew_morph(code)
    return greek_morph(code)


# ---------------------------------------------------------------- interlinear view

def show_interlinear(words, compact, no_script):
    cols = []
    for orig, tr, gloss, strongs, morph, _ in words:
        rows = []
        if not no_script:
            rows.append(orig + (LRM if is_hebrew(orig) else ""))
        rows += [tr, gloss]
        if not compact:
            rows += [base_strongs(strongs), morph]
        cols.append(rows)
    styles = ([BOLD] if not no_script else []) + [DIM, ""] + ([] if compact else [CYAN, CYAN])
    term = shutil.get_terminal_size((100, 24)).columns
    line = []
    used = 0
    blocks = []
    for col in cols:
        w = max(width(x) for x in col) + 2
        if line and used + w > term:
            blocks.append(line)
            line, used = [], 0
        line.append((col, w))
        used += w
    if line:
        blocks.append(line)
    for block in blocks:
        for r in range(len(block[0][0])):
            text = "".join(pad(col[r], w) for col, w in block).rstrip()
            print(c(styles[r], text) if styles[r] else text)
        print()


def show_wordlist(words, no_script):
    rows = []
    for orig, tr, gloss, strongs, morph, lemma in words:
        lem = lemma.split("=", 1)
        head = lem[0] if lem else ""
        mean = lem[1] if len(lem) > 1 else ""
        rows.append(("" if no_script else orig + (LRM if is_hebrew(orig) else ""), tr, gloss,
                     base_strongs(strongs), decode(morph),
                     (head + (LRM if is_hebrew(head) else "") + "  " + mean).strip()))
    widths = [max(width(r[i]) for r in rows) for i in range(4)]
    for r in rows:
        first = ""
        if not no_script:
            first = c(BOLD, pad(r[0], widths[0])) + "  "
        print(first + c(DIM, pad(r[1], widths[1])) + "  " + pad(r[2], widths[2]) + "  "
              + c(CYAN, pad(r[3], widths[3])) + "  " + r[4]
              + ("   " + c(DIM, "< " + r[5]) if r[5] else ""))
    print()


def interlinear(args, mode, no_script):
    for book_words, ref in vs.expand_refs(" ".join(args)):
        if book_words is None:
            print("Invalid query: " + ref)
            continue
        res = bb.resolve(" ".join(book_words))
        if res is None or res[0] != "book":
            print("Unknown book: " + " ".join(book_words))
            continue
        book = res[1][0]
        if "." in ref:
            print("Footnote references aren't part of the interlinear: " + ref)
            continue
        if re.match(r"^\d+(-\d+)?$", ref) and book in bb.SINGLE_CHAPTER:
            ref = "1:" + ref
        parsed = vs.parse_ref(ref)
        if parsed is None:
            print("Invalid reference: " + ref)
            continue
        c1, v1, c2, v2 = parsed
        for chap in range(c1, c2 + 1):
            data = read_words(book, chap)
            if data is None:
                print("No interlinear data for " + label(book, chap, 1).rsplit(":", 1)[0])
                break
            lo = v1 if chap == c1 and v1 is not None else min(data)
            hi = v2 if chap == c2 and v2 is not None else max(data)
            for verse in sorted(data):
                if not lo <= verse <= hi:
                    continue
                rcv = rcv_line(book, chap, verse) if verse else None
                print(c(BOLD, rcv if rcv else label(book, chap, verse)))
                if mode == "words":
                    show_wordlist(data[verse], no_script)
                else:
                    show_interlinear(data[verse], mode == "compact", no_script)


# ---------------------------------------------------------------- Strong's lookup

def strongs_lookup(query, scope_args, counts_only, brief):
    q = query.upper()
    if re.match(r"^\d+[A-Z]?$", q):
        candidates = ["G" + q, "H" + q]
    else:
        candidates = [q]
    lex = lexicon()
    exact = bool(re.match(r"^[GH]\d+[A-Z]$", q))
    shown = False
    for cand in candidates:
        key_base = base_strongs(cand)
        entries = [k for k in lex if (k == cand if exact else base_strongs(k) == key_base)]
        # prefer the plain / first sense entries for the header
        entries.sort()
        if not entries:
            continue
        shown = True
        e = lex[entries[0]]
        lemma, tr, typ, gloss, defn = e[0], e[1], e[2], e[3], e[4]
        print(c(BOLD, lemma + (LRM if is_hebrew(lemma) else "")) + "  " + c(DIM, tr) + "  "
              + c(CYAN, key_base) + "  " + gloss)
        senses = [lex[k][3] for k in entries[1:] if lex[k][3] and lex[k][3] != gloss]
        if senses:
            print(c(DIM, "senses: " + "; ".join(dict.fromkeys(senses))))
        if not counts_only:
            print()
            for dl in defn.split("\\n"):
                print("  " + dl)
        print()
        concordance(key_base if not exact else cand, exact, scope_args, counts_only, brief)
    if not shown:
        print("No lexicon entry for " + query)


def concordance(key, exact, scope_args, counts_only, brief):
    testament = "OT" if key.startswith("H") else "NT"
    if scope_args:
        scope = bb.parse_scope(scope_args, USAGE)
    else:
        books = bb.groups["ot"] if testament == "OT" else bb.groups["nt"]
        scope = [(b, None, None) for b in books]
    per_book = {}
    hits = []
    for book, chapter, vr in scope:
        bdir = TEXT_DIR + book + "/"
        if not os.path.isdir(bdir):
            continue
        chapters = [chapter] if chapter else bb.numeric_sort(os.listdir(bdir))
        for ch in chapters:
            data = read_words(book, ch)
            if not data:
                continue
            for verse in sorted(data):
                if vr and not vr[0] <= verse <= vr[1]:
                    continue
                for orig, tr, gloss, strongs, morph, lemma in data[verse]:
                    s = strongs if exact else base_strongs(strongs)
                    if s == key:
                        per_book[book] = per_book.get(book, 0) + 1
                        hits.append((book, int(ch), verse, orig, tr, gloss, morph))
    total = len(hits)
    where = " ".join(scope_args) if scope_args else testament
    print(c(BOLD, "%d occurrence%s in %s" % (total, "" if total == 1 else "s", where)))
    if counts_only or total == 0:
        print("  " + ", ".join("%s %d" % (bb.PREFIXES.get(b, b).rstrip("."), n) for b, n in per_book.items()))
        return
    print()
    for book, ch, verse, orig, tr, gloss, morph in hits:
        print(c(CYAN, pad(label(book, ch, verse), 14)) + "  " + c(BOLD, orig + (LRM if is_hebrew(orig) else ""))
              + "  " + c(DIM, tr) + "  " + gloss)
        if not brief and verse:
            rcv = rcv_line(book, ch, verse)
            if rcv:
                print("    " + rcv.split(" ", 2)[-1] if rcv.count(" ") >= 2 else "    " + rcv)
    print()


# ---------------------------------------------------------------- finding numbers

def plain(s):
    """Lower-case, strip accents/breathings/vowel points: 'zōē' -> 'zoe'."""
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(ch for ch in s if not unicodedata.combining(ch)).replace(".", "").replace("'", "")


def find_numbers(word):
    q = plain(word)
    lex = lexicon()
    seen = set()
    exact, partial = [], []
    for key in sorted(lex):
        lemma, tr, typ, gloss = lex[key][0], lex[key][1], lex[key][2], lex[key][3]
        b = base_strongs(key)
        fields = [plain(lemma), plain(tr), plain(gloss)]
        words = set(re.findall(r"\w+", " ".join(fields)))
        if q in (fields[0], fields[1]) or q in words:
            bucket = exact
        elif any(q in f for f in fields):
            bucket = partial
        else:
            continue
        if (b, gloss) in seen:
            continue
        seen.add((b, gloss))
        bucket.append((b, lemma, tr, gloss))
    rows = exact + partial
    if not rows:
        print("Nothing found for " + word)
        return
    for b, lemma, tr, gloss in rows[:60]:
        print(c(CYAN, b.ljust(6)) + "  " + c(BOLD, lemma + (LRM if is_hebrew(lemma) else "")) + "  "
              + c(DIM, tr) + "  " + gloss)
    if len(rows) > 60:
        print(c(DIM, "... %d more; be more specific" % (len(rows) - 60)))


# ---------------------------------------------------------------- phrase search

def phrase_search(keys, scope_args, window, counts_only, brief):
    keys = [k.upper() for k in keys]
    exact = [bool(re.match(r"^[GH]\d+[A-Z]$", k)) for k in keys]
    keys = [k if e else base_strongs(k) for k, e in zip(keys, exact)]
    testament = "OT" if keys[0].startswith("H") else "NT"
    lex = lexicon()
    names = []
    for k in keys:
        e = next((lex[x] for x in sorted(lex) if base_strongs(x) == base_strongs(k)), None)
        names.append((e[0] + " (" + k + ")") if e else k)
    print(c(BOLD, " + ".join(names)) + c(DIM, "   " + ("anywhere in the verse" if window is None
                                                       else "within %d words" % window)))
    print()
    if scope_args:
        scope = bb.parse_scope(scope_args, USAGE)
    else:
        scope = [(b, None, None) for b in bb.groups["ot" if testament == "OT" else "nt"]]
    total = 0
    per_book = {}
    for book, chapter, vr in scope:
        bdir = TEXT_DIR + book + "/"
        if not os.path.isdir(bdir):
            continue
        for ch in ([chapter] if chapter else bb.numeric_sort(os.listdir(bdir))):
            data = read_words(book, ch)
            if not data:
                continue
            for verse in sorted(data):
                if vr and not vr[0] <= verse <= vr[1]:
                    continue
                words = data[verse]
                pos = {}
                for i, w in enumerate(words):
                    for j, k in enumerate(keys):
                        s = w[3] if exact[j] else base_strongs(w[3])
                        if s == k:
                            pos.setdefault(j, []).append(i)
                if len(pos) < len(keys):
                    continue
                span = best_span(pos, len(keys), window)
                if span is None:
                    continue
                total += 1
                per_book[book] = per_book.get(book, 0) + 1
                if counts_only:
                    continue
                a, b = span
                seg = words[a:b + 1]
                greek = " ".join(w[0] for w in seg)
                gloss = " ".join(w[2] for w in seg)
                print(c(CYAN, pad(label(book, int(ch), verse), 14)) + "  " + c(BOLD, greek)
                      + "  " + gloss)
                if not brief and verse:
                    rcv = rcv_line(book, ch, verse)
                    if rcv:
                        print("    " + rcv.split(" ", 2)[-1])
    where = " ".join(scope_args) if scope_args else testament
    if not counts_only:
        print()
    print(c(BOLD, "%d verse%s in %s" % (total, "" if total == 1 else "s", where)))
    if counts_only and per_book:
        print("  " + ", ".join("%s %d" % (bb.PREFIXES.get(b, b).rstrip("."), n) for b, n in per_book.items()))


def best_span(pos, n, window):
    """Smallest (start, end) word span containing one position for each key;
    None if it is wider than the window (window None = any width)."""
    import itertools
    best = None
    for combo in itertools.product(*[pos[j] for j in range(n)]):
        a, b = min(combo), max(combo)
        if best is None or b - a < best[1] - best[0]:
            best = (a, b)
    if best is None:
        return None
    if window is not None and best[1] - best[0] > window:
        return None
    return best


# ---------------------------------------------------------------- main

def main():
    mode, no_script, counts_only, brief = "inter", False, False, False
    window, find = 3, None
    args = []
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "-n" and i + 1 < len(argv) and argv[i + 1].isdigit():
            window = int(argv[i + 1])
            i += 2
            continue
        if a == "-f" and i + 1 < len(argv):
            find = " ".join(argv[i + 1:])
            break
        if re.match(r"^-[wctoba]+$", a):
            for ch in a[1:]:
                if ch == "w": mode = "words"
                elif ch == "c": mode = "compact"
                elif ch == "t": no_script = True
                elif ch == "o": counts_only = True
                elif ch == "b": brief = True
                elif ch == "a": window = None
        else:
            args.append(a)
        i += 1
    if find:
        find_numbers(find)
        return
    if not args:
        print(USAGE)
        sys.exit(1)
    if not os.path.isdir(TEXT_DIR):
        print("Interlinear data not found in " + TEXT_DIR)
        sys.exit(1)
    nums = []
    for a in args:
        if re.match(r"^[GgHh]\d+[A-Za-z]?$", a):
            nums.append(a)
        else:
            break
    if len(nums) >= 2:
        phrase_search(nums, args[len(nums):], window, counts_only, brief)
    elif re.match(r"^[GgHh]?\d+[A-Za-z]?$", args[0]) and (args[0][0] in "GgHh" or len(args) == 1):
        strongs_lookup(args[0], args[1:], counts_only, brief)
    else:
        interlinear(args, mode, no_script)


if __name__ == "__main__":
    main()
