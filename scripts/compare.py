#!/usr/bin/env python3
"""Show a passage in several versions side by side (one after another).

  compare [-p] <version> [<version> ...] <book> <ref>

  compare esv rcv kjv rom 8:28        those three, in the order given
  compare darby asv psa 23:1-3        a range
  compare rom 8:28                    no versions given: every installed one
  compare -p esv kjv rom 8:28-30      paragraph form

Versions: rcv (Recovery Version), kjv, asv, darby / jnd, esv.
Also callable as vcomp.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import bible_books as bb
import verse as vs

USAGE = "Usage: compare [-p] [<version> ...] <book> <chapter:verse[-verse]>"


def main():
    para = False
    args = []
    for a in sys.argv[1:]:
        if a == "-p":
            para = True
        else:
            args.append(a)
    if len(args) < 2:
        print(USAGE)
        sys.exit(1)

    # Peel off as many leading version names as there are.
    versions = []
    while True:
        v, rest = bb.parse_version(args)
        if rest is args:          # nothing recognised at the front
            break
        if v == "ALL":
            versions = bb.all_versions()
        elif v not in versions:
            versions.append(v)
        args = rest
    if not versions:
        versions = bb.all_versions()
    if len(args) < 2:
        print(USAGE)
        sys.exit(1)

    ref = args[-1]
    res = bb.resolve(" ".join(args[:-1]))
    if res is None or res[0] != "book":
        print("Unknown book: " + " ".join(args[:-1]))
        sys.exit(1)
    book = res[1][0]

    for v in versions:
        print(bb.bold(bb.version_label(v) + ":"))
        try:
            lines = vs.verses(v, book, ref)
        except RuntimeError as e:
            print(str(e))
            print()
            continue
        if lines is None:
            print("Invalid verse reference.")
            print()
            continue
        if para:
            print(bb.paragraph(lines))
        else:
            for line in lines:
                print(line)
        if v == "ESV":
            print("(ESV)")
        print()
    if "ESV" in versions:
        print(bb.ESV_COPYRIGHT)


if __name__ == "__main__":
    main()
