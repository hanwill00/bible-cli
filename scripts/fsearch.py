#!/usr/bin/env python3
"""Search Recovery Version footnotes.

  fsearch [-o] [-w] [<book or group> [<chapter>]] <term>

  fsearch "economy"                 everything
  fsearch romans "economy"          one book
  fsearch rom 8 "economy"           one chapter
  fsearch rom 8-10 "economy"        a chapter range;  rom 8:1-17  a verse range
  fsearch heart "economy"           a group (same groups as vsearch)
  fsearch rom + eph "economy"       several books/groups, joined with +
  fsearch syn "compassion"          include synonyms
  -o  also print totals (notes / occurrences)
  -w  match whole words only

Each matching footnote is printed in full, followed by a blank line.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import bible_books as bb

USAGE = "Usage: fsearch [-o] [-w] [syn] [<book or group> [<chapter>] [+ ...]] <search term>"


def note_files(scope):
    """Yield footnote file paths in canonical order."""
    for book, chapter, vr in scope:
        book_dir = bb.FOOTNOTES_DIR + book + "/"
        if not os.path.isdir(book_dir):
            continue
        chapters = [chapter] if chapter else bb.numeric_sort(os.listdir(book_dir))
        for ch in chapters:
            ch_dir = book_dir + ch + "/"
            if not os.path.isdir(ch_dir):
                if chapter:
                    print("No footnotes for " + book + " " + ch)
                continue
            for v in bb.numeric_sort(os.listdir(ch_dir)):
                if vr and not (vr[0] <= int(v) <= vr[1]):
                    continue
                v_dir = ch_dir + v + "/"
                notes = [n for n in os.listdir(v_dir) if not n.startswith(".")]
                # Notes are usually numeric but may be e.g. "1a"; sort sensibly.
                notes.sort(key=lambda n: (int(n) if n.isdigit() else 10 ** 6, n))
                for n in notes:
                    yield v_dir + n


def search_footnotes(scope, pattern, show_totals):
    bb.require_dir(bb.FOOTNOTES_DIR, bb.NO_FOOTNOTES)
    notes = occurrences = 0
    for path in note_files(scope):
        try:
            with open(path) as fp:
                text = fp.read()
        except OSError:
            continue
        hits = pattern.findall(text)
        if hits:
            notes += 1
            occurrences += len(hits)
            print(bb.highlight(pattern, text.rstrip("\n")))
            print()
    if show_totals:
        print("Total notes: " + str(notes))
        print("Total occurrences: " + str(occurrences))


def run(flags, args, version=None):
    if version is not None:
        print("Footnotes exist only for the Recovery Version.")
        sys.exit(1)
    if not args:
        print(USAGE)
        sys.exit(1)
    args, term = bb.split_or(args)
    scope = bb.parse_scope(args, USAGE)
    if flags["s"]:
        pattern, words, note = bb.synonym_patterns(term, flags["w"])
        print("Searching: " + ", ".join(words) + ("  " + note if note else ""))
        print()
    else:
        pattern = bb.make_pattern(term, flags["w"])
    search_footnotes(scope, pattern, flags["o"])


def main():
    flags, args = bb.parse_args(sys.argv[1:], USAGE)
    version, args = bb.parse_version(args)
    run(flags, args, version)


if __name__ == "__main__":
    main()
