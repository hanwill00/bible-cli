#!/usr/bin/env python3
"""Search Bible verses.

  vsearch [options] [version] [<book or group> [<chapter>] [+ ...]] <term>

  vsearch "righteousness"            everything (Recovery Version)
  vsearch romans "righteousness"     one book
  vsearch rom 3 "righteousness"      one chapter
  vsearch rom 3-5 "righteousness"    a chapter range;  rom 3:21-31  a verse range
  vsearch nt "righteousness"         a group: ot, nt, law, history, poetry,
                                     prophets, major, minor, gospels,
                                     epistles, pauline, heart, pastoral, general
  vsearch rom + sos "glory"          several books/groups: join with + , or 'and'
  vsearch rom 8 + poetry "glory"     (a part may have a chapter)
  vsearch psa "arrows.*quiver"       the term is a regular expression

  vsearch kjv rom "charity"          another version: kjv, asv, darby (jnd),
  vsearch kjv asv rom "glory"        several versions, labelled
  vsearch all rom 8 "purpose"        'all' / 'all versions': every installed one

  vsearch m 3 psa "arrows.*quiver"   match across up to 3 consecutive verses
                                     (order matters; each hit is printed as a
                                     block).  Same as -m 3.
  vsearch syn "compassions"          also search synonyms (from
                                     bible_synonyms.txt and WordNet).  Same as -s.

  -o  also print totals        -w  whole words only
  -p  paragraph form: text first, reference at the end
  -f  search footnotes instead (same as fsearch)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import bible_books as bb

USAGE = "Usage: vsearch [-o] [-w] [-p] [syn] [m <N>] [version] " \
        "[<book or group> [<chapter>] [+ ...]] <search term>"


def chapters_of(version, book, chapter, verse_range=None):
    book_dir = bb.verses_dir(version) + book + "/"
    if not os.path.isdir(book_dir):
        return
    names = [chapter] if chapter else bb.numeric_sort(os.listdir(book_dir))
    for ch in names:
        try:
            with open(book_dir + ch) as fp:
                lines = fp.read().splitlines()
        except OSError:
            print("No such chapter: " + book + " " + ch)
            continue
        if verse_range:
            lo, hi = verse_range
            lines = lines[lo - 1:hi]
        yield ch, lines


def show(lines, pattern, para):
    if para:
        print(bb.highlight(pattern, bb.paragraph(lines)))
    else:
        for line in bb.highlight_block(pattern, lines):
            print(line)


def search_verses(version, scope, pattern, show_totals, para):
    verses = occurrences = 0
    for book, chapter, vr in scope:
        for _, lines in chapters_of(version, book, chapter, vr):
            for line in lines:
                hits = pattern.findall(line)
                if hits:
                    verses += 1
                    occurrences += len(hits)
                    show([line], pattern, para)
    if show_totals:
        print("Total verses: " + str(verses))
        print("Total occurrences: " + str(occurrences))


def search_windows(version, scope, pattern, width, show_totals, para):
    """Report every minimal run of <= width consecutive verses (within a
    chapter) whose joined text matches the pattern."""
    blocks = 0
    for book, chapter, vr in scope:
        for _, lines in chapters_of(version, book, chapter, vr):
            n = len(lines)

            def matches(i, j):  # verses i..j inclusive
                return pattern.search(" ".join(lines[i:j + 1])) is not None

            for i in range(n):
                for j in range(i, min(i + width, n)):
                    if matches(i, j):
                        # Minimal on the left too: verse i must be needed.
                        if j == i or not matches(i + 1, j):
                            blocks += 1
                            show(lines[i:j + 1], pattern, para)
                            print()
                        break
    if show_totals:
        print("Total matches: " + str(blocks))


def main():
    flags, args = bb.parse_args(sys.argv[1:], USAGE)
    versions, args = bb.parse_versions(args)
    if None in versions:
        bb.require_dir(bb.VERSES_DIR, bb.NO_VERSES)
    if flags["f"]:
        import fsearch
        fsearch.run(flags, args, versions[0] if len(versions) == 1 else "ALL")
        return
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

    versions = [v for v in versions if v not in bb.REMOTE_VERSIONS]
    if not versions:
        print("The ESV is fetched from api.esv.org one passage at a time and its terms don't "
              "allow keeping a searchable copy. Use 'verse esv <ref>' to read it.")
        sys.exit(1)
    for v in versions:
        if len(versions) > 1:
            print(bb.bold("== " + bb.version_label(v) + " =="))
        if flags["m"]:
            search_windows(v, scope, pattern, flags["m"], flags["o"], flags["p"])
        else:
            search_verses(v, scope, pattern, flags["o"], flags["p"])
        if len(versions) > 1:
            print()


if __name__ == "__main__":
    main()
