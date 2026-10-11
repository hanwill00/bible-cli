#!/usr/bin/env python3
"""Print verses, chapters and footnotes.

  verse [-p] [version] <book> <ref> [; <book> <ref> ...]

  verse rom 8              a chapter
  verse rom 8:28           a verse
  verse rom 8:28-30        a range;  gen 43-44  two chapters;  gen 43:30-44:2  across chapters
  verse jude 3             a verse of a one-chapter book
  verse rom 3:2.1          footnote 1 on Rom. 3:2;  rom 3:24.1-3  notes 1-3
  verse rom 3:2.all        every note on that verse (also 3:2.)
  verse rom 3:2-5.all      every note on verses 2-5;  rom 3.all  every note in ch. 3
  verse rom 8:28; psa 23:1 several references (also , or +)
  verse 1 cor 1:1, 5-8     short forms carry over the book/chapter: 1 Cor. 1:1 and 1:5-8
  verse rom 3:24.1, 3      ... or the verse, for footnotes: notes 1 and 3 on Rom. 3:24

  verse kjv rom 8:28       another version (kjv, asv, darby / jnd, rcv)
  verse kjv esv rom 8:28   several versions, labelled, in the order given
  verse esv rom 8:28       ESV, fetched live from api.esv.org (needs a free
                           key saved in ~/Bible/esv_api_key)
  verse all rom 8:28       the same verse in every installed version
  -p                       paragraph form: text only, one reference at the end
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import bible_books as bb

USAGE = "Usage: verse [-p] [version ...] <book> <chapter[-chapter] | chapter:verse[-[chapter:]verse] | chapter:verse.note | chapter:verse.all | chapter.all>"


def read_chapter(version, book, chapter):
    try:
        with open(bb.verses_dir(version) + book + "/" + chapter) as fp:
            return fp.read().splitlines()
    except OSError:
        return None


def is_single_chapter(version, book):
    d = bb.verses_dir(version) + book + "/"
    return os.path.isdir(d) and bb.numeric_sort(os.listdir(d)) == ["1"]


def parse_ref(ref):
    """'8' -> (8,None,8,None); '8-10' -> (8,None,10,None);
    '8:28' -> (8,28,8,28); '8:28-30' -> (8,28,8,30); '43:30-44:2' -> (43,30,44,2).
    None if the reference is malformed."""
    m = re.match(r"^(\d+)(?::(\d+))?(?:-(\d+)(?::(\d+))?)?$", ref)
    if not m:
        return None
    c1, v1, x, y = m.groups()
    c1 = int(c1)
    v1 = int(v1) if v1 else None
    if x is None:                       # single chapter or verse
        return (c1, v1, c1, v1)
    if y is not None:                   # 43:30-44:2
        if v1 is None:
            return None
        return (c1, v1, int(x), int(y))
    if v1 is None:                      # 43-44  (chapter range)
        return (c1, None, int(x), None)
    return (c1, v1, c1, int(x))         # 8:28-30


def chapter_slice(version, book, chap, lo, hi):
    """Verses lo..hi of a chapter (None = to the end). Raises ValueError."""
    if version in bb.REMOTE_VERSIONS:
        return bb.esv_verses(book, str(chap), lo, hi)
    lines = read_chapter(version, book, str(chap))
    if lines is None:
        raise ValueError
    lo = lo or 1
    hi = hi or len(lines)
    if lo < 1 or hi < lo or lo > len(lines):
        raise ValueError
    return lines[lo - 1:hi]


def verses(version, book, ref):
    """Return the list of verse lines for a chapter, chapter range, verse or
    verse range (within or across chapters), or None if the reference is bad."""
    if re.match(r"^\d+(-\d+)?$", ref) and (book in bb.SINGLE_CHAPTER or is_single_chapter(version, book)):
        ref = "1:" + ref                              # 'jude 3' / 'jude 19-21' -> verses
    parsed = parse_ref(ref)
    if parsed is None:
        return None
    c1, v1, c2, v2 = parsed
    if c2 < c1 or (c1 == c2 and v1 is not None and v2 is not None and v2 < v1):
        return None
    out = []
    try:
        for chap in range(c1, c2 + 1):
            lo = v1 if chap == c1 else None
            hi = v2 if chap == c2 else None
            out += chapter_slice(version, book, chap, lo, hi)
    except ValueError:
        return None
    return out


def _notes_in(v_dir):
    names = [n for n in os.listdir(v_dir) if not n.startswith(".")]
    names.sort(key=lambda n: (int(n) if n.isdigit() else 10 ** 6, n))
    out = []
    for n in names:
        with open(v_dir + n) as fp:
            out.append(fp.read().rstrip("\n"))
    return out


def footnotes(book, ref):
    """Footnote references:
         3:2.1      one note          3:2.all / 3:2.* / 3:2.   every note on the verse
         3:2-5.all  every note on verses 2-5      3.all / 3.   every note in chapter 3
    Returns a list of note texts, or None if the reference is bad."""
    if book in bb.SINGLE_CHAPTER and ":" not in ref and not ref.startswith("."):
        ref = "1:" + ref                           # 'jude 20.1' -> 1:20.1
    m = re.match(r"^(\d+)(?::(\d+)(?:-(\d+))?)?\.(\d+-\d+|\d+|all|\*|)$", ref)
    if not m:
        return None
    chap, v1, v2, which = m.group(1), m.group(2), m.group(3), m.group(4)
    if re.match(r"^\d+-\d+$", which):              # note range: 3:24.1-3
        if v1 is None or v2:
            return None
        a, b = (int(x) for x in which.split("-"))
        if b < a:
            return None
        out = []
        for n in range(a, b + 1):
            path = bb.FOOTNOTES_DIR + book + "/" + chap + "/" + v1 + "/" + str(n)
            try:
                with open(path) as fp:
                    out.append(fp.read().rstrip("\n"))
            except OSError:
                pass
        return out or None
    if which == "":
        which = "all"
    ch_dir = bb.FOOTNOTES_DIR + book + "/" + chap + "/"
    if not os.path.isdir(ch_dir):
        return None
    if v1 is None:                                  # whole chapter
        if which != "all" and which != "*":
            return None
        out = []
        for v in bb.numeric_sort(os.listdir(ch_dir)):
            out += _notes_in(ch_dir + v + "/")
        return out
    lo, hi = int(v1), int(v2) if v2 else int(v1)
    if hi < lo:
        return None
    if which not in ("all", "*"):                   # one specific note
        if v2:
            return None
        path = ch_dir + v1 + "/" + which
        try:
            with open(path) as fp:
                return [fp.read().rstrip("\n")]
        except OSError:
            return None
    out = []
    for v in bb.numeric_sort(os.listdir(ch_dir)):
        if lo <= int(v) <= hi:
            out += _notes_in(ch_dir + v + "/")
    return out if out else None


def one(versions, book_words, ref, para):
    res = bb.resolve(" ".join(book_words))
    if res is None or res[0] != "book":
        print("Invalid query: " + " ".join(book_words) + " " + ref)
        return
    book = res[1][0]

    if "." in ref:                                  # footnote(s)
        bb.require_dir(bb.FOOTNOTES_DIR, bb.NO_FOOTNOTES)
        notes = footnotes(book, ref)
        if notes is None:
            print("Invalid footnote reference.")
            return
        for n in notes:
            print(n)
            print()
        return

    labelled = len(versions) > 1
    for v in versions:
        try:
            lines = verses(v, book, ref)
        except RuntimeError as e:
            print(str(e))
            continue
        if lines is None:
            print("Invalid verse reference.")
            return
        if labelled:
            print(bb.bold(bb.version_label(v) + ":"))
        if para:
            print(bb.paragraph(lines))
        else:
            for line in lines:
                print(line)
        if v == "ESV":
            print("(ESV)" if labelled else bb.ESV_COPYRIGHT)
        if labelled:
            print()
    if labelled and "ESV" in versions:
        print(bb.ESV_COPYRIGHT)


_BARE_RE = re.compile(r"^[\d:.\-]+$")


def expand_refs(text):
    """Split a line of references on ; , + and fill in what a short reference
    leaves out, the way printed citations do:
        1 cor 1:1, 5-8          -> 1 cor 1:1 ; 1 cor 1:5-8
        rom 8:28, 9:1           -> rom 8:28 ; rom 9:1
        rom 3:24.1, 3           -> rom 3:24.1 ; rom 3:24.3
        rom 3:24.1, 25.2        -> rom 3:24.1 ; rom 3:25.2
        gen 1, 3                -> gen 1 ; gen 3        (chapters)
    Yields (book_words, ref); book_words is None for an unusable piece."""
    text = text.replace("+", ";").replace(",", ";")
    book = None          # list of words
    chap = None          # chapter of the last chapter:verse reference
    verse = None         # verse of the last footnote reference
    for piece in text.split(";"):
        words = piece.split()
        if not words:
            continue
        if len(words) == 1 and _BARE_RE.match(words[0]) and book:
            ref = words[0]
            if ":" not in ref and "." not in ref and chap is not None and verse is None:
                ref = chap + ":" + ref                       # 5-8 after 1:1
            elif ":" not in ref and "." not in ref and verse is not None:
                ref = chap + ":" + verse + "." + ref         # 3 after 3:24.1
            elif ":" not in ref and "." in ref and chap is not None:
                ref = chap + ":" + ref                       # 25.2 after 3:24.1
        elif len(words) >= 2:
            book, ref = words[:-1], words[-1]
        else:
            yield None, piece.strip()
            continue
        m = re.match(r"^(\d+):(\d+)", ref)
        chap = m.group(1) if m else None
        mf = re.match(r"^\d+:(\d+)\.", ref)
        verse = mf.group(1) if mf else None
        yield book, ref


def main():
    # "verse --is-book john" exits 0 if 'john' names a book (used by the zsh
    # hook that lets you type "john 1:14" without the word verse).
    if len(sys.argv) >= 3 and sys.argv[1] == "--is-book":
        res = bb.resolve(" ".join(sys.argv[2:]))
        sys.exit(0 if res and res[0] == "book" else 1)
    para = False
    args = []
    for a in sys.argv[1:]:
        if a == "-p":
            para = True
        else:
            args.append(a)
    if not args:
        print(USAGE)
        sys.exit(1)
    versions, args = bb.parse_versions(args)
    if None in versions:
        bb.require_dir(bb.VERSES_DIR, bb.NO_VERSES)
    for book_words, ref in expand_refs(" ".join(args)):
        if book_words is None:
            print("Invalid query: " + ref)
            continue
        one(versions, book_words, ref, para)


if __name__ == "__main__":
    main()
