#!/usr/bin/env python3
"""Recovery Version book background and outline.

  book rom               background (author, time, place, recipients, subject) + outline
  book rom -b            background only
  book rom -o            outline only
  book rom 8:28          where a verse falls in the outline (and the background line)
  book rom 8             where a chapter's sections fall
  book nt                the subject line of every New Testament book
  book -s "Body"         search all outlines and backgrounds for a word (regex ok)

Source: the Recovery Version (Living Stream Ministry), New Testament books.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import bible_books as bb

INFO_DIR = bb.BIBLE_DIR + "/bookinfo/"
USAGE = "Usage: book [-b|-o] <book> [chapter[:verse]]   |   book nt   |   book -s <word>"
BOLD, DIM, CYAN, RESET = "\033[1m", "\033[2m", "\033[36m", "\033[0m"


def c(code, t):
    return code + t + RESET if bb.COLOR else t


def load(book):
    try:
        with open(INFO_DIR + book, encoding="utf-8") as fp:
            text = fp.read()
    except OSError:
        return None, None
    head, _, outline = text.partition("\nOUTLINE\n")
    intro = []
    for line in head.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            intro.append((k.strip(), v.strip()))
    return intro, [l.rstrip() for l in outline.splitlines() if l.strip()]


def show_intro(intro):
    w = max(len(k) for k, _ in intro) if intro else 0
    for k, v in intro:
        print(c(BOLD, (k + ":").ljust(w + 1)) + " " + v)


def color_outline_line(line):
    m = re.match(r"^(\s*)(\S+\.)\s(.*?)(\s—\s(?:vv?\.\s)?[\d:].*)?$", line)
    if not m:
        return line
    ind, num, text, ref = m.groups()
    out = ind + c(BOLD if not ind else "", num) + " " + text
    if ref:
        out += c(CYAN, ref)
    return out


# ---------------------------------------------------------------- verse location

def _ref_spans(ref, ctx_chap, single):
    """'1:18 — 3:20' -> [((1,18),(3,20))]; 'vv. 3-4' -> [((ctx,3),(ctx,4))];
    'vv. 1-2, 7-8, 13' -> three spans. Verse letters (17-18a) are ignored."""
    ref = ref.strip()
    spans = []
    rel = re.match(r"^vv?\.\s*(.*)$", ref)
    if rel or single:
        body = rel.group(1) if rel else ref
        chap = 1 if single else ctx_chap
        for piece in body.split(","):
            nums = [int(x) for x in re.findall(r"\d+", piece)]
            if not nums or chap is None:
                continue
            spans.append(((chap, nums[0]), (chap, nums[-1])))
        return spans
    parts = re.split(r"\s*—\s*", ref)
    if len(parts) == 2:                                   # 1:18 — 3:20
        a = re.match(r"(\d+):(\d+)", parts[0])
        b = re.match(r"(\d+):(\d+)", parts[1])
        if a and b:
            spans.append(((int(a.group(1)), int(a.group(2))), (int(b.group(1)), int(b.group(2)))))
        return spans
    m = re.match(r"^(\d+):(\d+)(?:-(\d+))?(?::(\d+))?", ref)
    if m:
        ch, v1, x, y = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
        if y:                                             # 3:21-5:11
            spans.append(((ch, v1), (int(x), int(y))))
        else:
            spans.append(((ch, v1), (ch, int(x) if x else v1)))
        return spans
    m = re.match(r"^(\d+)(?:-(\d+))?$", ref)              # whole chapters: 5-7
    if m:
        spans.append(((int(m.group(1)), 1), (int(m.group(2) or m.group(1)), 999)))
    return spans


def outline_entries(outline, single):
    """[(depth, line, spans)] with chapter context carried from parents."""
    entries = []
    stack = []    # (depth, chapter)
    for line in outline:
        depth = (len(line) - len(line.lstrip())) // 2
        m = re.search(r"\s—\s((?:vv?\.\s*)?[\d:][\d:,\-\s—ab]*)$", line)
        while stack and stack[-1][0] >= depth:
            stack.pop()
        ctx = stack[-1][1] if stack else None
        spans = _ref_spans(m.group(1), ctx, single) if m else []
        chap = spans[0][0][0] if spans else ctx
        stack.append((depth, chap))
        entries.append((depth, line, spans))
    return entries


def locate(book, outline, chap, verse):
    single = book in bb.SINGLE_CHAPTER
    if single and verse is None:
        chap, verse = 1, chap
    lo = (chap, verse if verse is not None else 1)
    hi = (chap, verse if verse is not None else 999)
    hits = []
    for depth, line, spans in outline_entries(outline, single):
        if any(not (b < lo or a > hi) for a, b in spans):
            hits.append((depth, line))
    if not hits:
        print("Not found in the outline.")
        return
    if verse is not None:
        # the chain from the top-level point down to the deepest one
        chain = []
        for depth, line in hits:
            while chain and chain[-1][0] >= depth:
                chain.pop()
            chain.append((depth, line))
        hits = chain
    for depth, line in hits:
        print(color_outline_line(line))


# ---------------------------------------------------------------- main

def main():
    args = sys.argv[1:]
    mode = "all"
    if "-b" in args:
        mode = "intro"
        args.remove("-b")
    if "-o" in args:
        mode = "outline"
        args.remove("-o")
    if not args:
        print(USAGE)
        sys.exit(1)

    if args[0] == "-s":
        pat = bb.make_pattern(" ".join(args[1:]), False)
        for b in bb.BOOK_ORDER:
            intro, outline = load(b)
            if intro is None:
                continue
            hits = [k + ": " + v for k, v in intro if pat.search(v)] + [l for l in outline if pat.search(l)]
            if hits:
                print(c(BOLD, bb.FULL_NAMES.get(b, b)))
                for h in hits:
                    print("  " + bb.highlight(pat, h.strip()))
        return

    # optional trailing chapter / verse
    chap = verse = None
    if re.match(r"^\d+(:\d+)?$", args[-1]) and len(args) > 1:
        m = re.match(r"^(\d+)(?::(\d+))?$", args[-1])
        chap, verse = int(m.group(1)), (int(m.group(2)) if m.group(2) else None)
        args = args[:-1]

    res = bb.resolve(" ".join(args))
    if res is None:
        print("Unknown book: " + " ".join(args))
        sys.exit(1)
    kind, books = res
    if kind == "group":                       # subject lines for a group of books
        for b in books:
            intro, _ = load(b)
            subj = dict(intro).get("Subject", "") if intro else "(not available)"
            print(c(BOLD, bb.FULL_NAMES.get(b, b).ljust(16)) + subj)
        return
    book = books[0]
    intro, outline = load(book)
    if intro is None:
        print("No Recovery Version background/outline for " + bb.FULL_NAMES.get(book, book)
              + " (only the New Testament books are available).")
        sys.exit(1)

    print(c(BOLD, bb.FULL_NAMES.get(book, book).upper()))
    if chap is not None:
        subj = dict(intro).get("Subject")
        if subj:
            print(c(DIM, "Subject: " + subj))
        print()
        locate(book, outline, chap, verse)
        return
    print()
    if mode in ("all", "intro"):
        show_intro(intro)
        print()
    if mode in ("all", "outline"):
        print(c(BOLD, "OUTLINE"))
        for line in outline:
            print(color_outline_line(line))


if __name__ == "__main__":
    main()
