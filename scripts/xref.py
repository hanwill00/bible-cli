#!/usr/bin/env python3
"""Cross-references.

  xref rom 8:28              Recovery Version cross-references (default source;
                             falls back to OpenBible until RcV data is installed)
  xref tsk rom 8:28          Treasury of Scripture Knowledge: references grouped
                             under the word or phrase of the verse they explain
  xref obi rom 8:28          OpenBible.info: ranked by how many people found each
                             one helpful (top 20; -a for all)
  xref rom 8                 a whole chapter (references only, no verse text)
  xref tsk rom 8:28, 9:11    lists and ranges work as in `verse`

  -r   references only (no verse text)        -v   with verse text (for chapters)
  -a   all OpenBible references (not just the top 20)
  -n N show the top N OpenBible references

Sources: tsk = treasury, obi = openbible, rcv = recovery (default).
Verse text shown is the Recovery Version.  See ~/Bible/xref/CREDITS.txt.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import bible_books as bb
import verse as vs

XREF_DIR = bb.BIBLE_DIR + "/xref/"
SOURCES = {"rcv": "rcv", "recovery": "rcv", "tsk": "tsk", "treasury": "tsk",
           "obi": "obi", "openbible": "obi", "openbibleinfo": "obi"}
NAMES = {"rcv": "Recovery Version", "tsk": "Treasury of Scripture Knowledge",
         "obi": "OpenBible.info"}
USAGE = "Usage: xref [rcv|tsk|obi] [-r|-v|-a|-n N] <book> <chapter[:verse]>"
BOLD, DIM, CYAN, RESET = "\033[1m", "\033[2m", "\033[36m", "\033[0m"
MAX_RANGE = 4          # verses of text shown per referenced range


def c(code, t):
    return code + t + RESET if bb.COLOR else t


def pretty(ref):
    """'2Cor 4:15-17' -> '2 Cor. 4:15-17' (Recovery Version abbreviations)."""
    book, _, rest = ref.partition(" ")
    p = bb.PREFIXES.get(book, book)
    if book in bb.SINGLE_CHAPTER and rest.startswith("1:"):
        rest = rest[2:]
    return p + " " + rest


def ref_lines(ref):
    """Recovery Version text for a reference like 'Psa 33:6,9' or 'Rom 9:11,23-24'
    or 'Gen 1:1-2:3'. Returns (lines, truncated)."""
    book, _, rest = ref.partition(" ")
    m = re.match(r"^(\d+):(.*)$", rest)
    if not m:
        return [], False
    chap, verses = m.group(1), m.group(2)
    out, cut = [], False
    for piece in verses.split(","):
        if re.match(r"^\d+(-\d+)?$", piece) or re.match(r"^\d+-\d+:\d+$", piece):
            r = chap + ":" + piece          # '6', '23-24', '1-2:3' (crosses a chapter)
        else:
            r = piece                       # already 'ch:v...'
        chap = r.split(":")[0]
        lines = vs.verses(None, book, r) or []
        if len(lines) > MAX_RANGE:
            lines, cut = lines[:MAX_RANGE], True
        out += lines
    return out, cut


def load(src, book, chap):
    rows = []
    try:
        with open(XREF_DIR + src + "/" + book + "/" + str(chap), encoding="utf-8") as fp:
            for line in fp:
                rows.append(line.rstrip("\n").split("\t"))
    except OSError:
        return None
    return rows


def show_refs(refs, with_text, indent="    "):
    if not with_text:
        print(indent + "; ".join(pretty(r) for r in refs))
        return
    for r in refs:
        lines, cut = ref_lines(r)
        if not lines:
            print(indent + c(CYAN, pretty(r)))
            continue
        for l in lines:
            print(indent + l)
        if cut:
            print(indent + c(DIM, "  ... (" + pretty(r) + ")"))


def tsk_verse(book, chap, verse, rows, with_text):
    groups = [(r[1], r[2].split("|")) for r in rows if r[0] == str(verse) and len(r) >= 3]
    if not groups:
        print(c(DIM, "  (no references)"))
        return
    for anchor, refs in groups:
        print("  " + c(BOLD, anchor) + c(DIM, "  (" + str(len(refs)) + ")"))
        show_refs(refs, with_text)
        if with_text:
            print()


def obi_verse(book, chap, verse, rows, with_text, top):
    hits = [(int(r[1]), r[2]) for r in rows if r[0] == str(verse) and len(r) >= 3]
    hits.sort(key=lambda h: -h[0])
    total = len(hits)
    if top is not None:
        hits = hits[:top]
    if not hits:
        print(c(DIM, "  (no references)"))
        return
    if not with_text:
        print("    " + "; ".join(pretty(t) for _, t in hits))
    else:
        for votes, t in hits:
            lines, cut = ref_lines(t)
            tag = c(DIM, "[%d] " % votes)
            if not lines:
                print("  " + tag + c(CYAN, pretty(t)))
                continue
            print("  " + tag + lines[0])
            for l in lines[1:]:
                print("        " + l)
            if cut:
                print("        " + c(DIM, "... (" + pretty(t) + ")"))
    if top is not None and total > len(hits):
        print(c(DIM, "  ... %d more (xref obi -a for all)" % (total - len(hits))))


def main():
    args = sys.argv[1:]
    src = "rcv"
    refs_only = verbose = False
    top = 20
    rest = []
    i = 0
    while i < len(args):
        a = args[i]
        key = a.lower().replace(".", "")
        if not rest and key in SOURCES:
            src = SOURCES[key]
        elif a == "-r":
            refs_only = True
        elif a == "-v":
            verbose = True
        elif a == "-a":
            top = None
        elif a == "-n" and i + 1 < len(args) and args[i + 1].isdigit():
            top = int(args[i + 1])
            i += 1
        else:
            rest.append(a)
        i += 1
    if not rest:
        print(USAGE)
        sys.exit(1)

    if src == "rcv" and not os.path.isdir(XREF_DIR + "rcv"):
        print(c(DIM, "(Recovery Version cross-references are not installed yet - showing "
                     "OpenBible.info. Use 'xref tsk' for the Treasury.)"))
        src = "obi"

    for book_words, ref in vs.expand_refs(" ".join(rest)):
        if book_words is None:
            print("Invalid query: " + ref)
            continue
        res = bb.resolve(" ".join(book_words))
        if res is None or res[0] != "book":
            print("Unknown book: " + " ".join(book_words))
            continue
        book = res[1][0]
        if re.match(r"^\d+(-\d+)?$", ref) and book in bb.SINGLE_CHAPTER:
            ref = "1:" + ref
        parsed = vs.parse_ref(ref)
        if parsed is None:
            print("Invalid reference: " + ref)
            continue
        c1, v1, c2, v2 = parsed
        whole_chapter = v1 is None
        with_text = (verbose or not whole_chapter) and not refs_only
        for chap in range(c1, c2 + 1):
            rows = load(src, book, chap)
            if rows is None:
                print("No " + NAMES[src] + " cross-references for " + book + " " + str(chap))
                continue
            text = vs.read_chapter(None, book, str(chap)) or []
            lo = v1 if (chap == c1 and v1) else 1
            hi = v2 if (chap == c2 and v2) else len(text)
            for verse in range(lo, hi + 1):
                head = text[verse - 1] if 0 < verse <= len(text) else (book + " " + str(chap) + ":" + str(verse))
                print(c(BOLD, head))
                if src == "tsk":
                    tsk_verse(book, chap, verse, rows, with_text)
                else:
                    obi_verse(book, chap, verse, rows, with_text, top)
                print()


if __name__ == "__main__":
    main()
