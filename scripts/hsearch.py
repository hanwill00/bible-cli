#!/usr/bin/env python3
"""Search hymn lyrics and titles.

  hsearch [-o] [-w] [-t] [<hymn number>] <term>

  hsearch "abide"           all hymns
  hsearch 1 "glory"         one hymn  (also h1, h 1, #1)
  -o  also print totals (hymns / occurrences)
  -w  match whole words only
  -t  search titles only

Prints "Hymn #N (title):" followed by each matching line.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import bible_books as bb

USAGE = "Usage: hsearch [-o] [-w] [-t] [<hymn number>] <search term>"


def read(path):
    try:
        with open(path) as fp:
            return fp.read()
    except OSError:
        return ""


def search_hymn(hno, pattern, titles_only):
    """Print matches for one hymn; return number of occurrences."""
    hdir = bb.HYMNS_DIR + hno + "/"
    title = read(hdir + "title").strip()
    text = title if titles_only else read(hdir + "full")
    hits = pattern.findall(text)
    if not hits and not titles_only:
        hits = pattern.findall(title)
        if not hits:
            return 0
    elif not hits:
        return 0
    header = "Hymn #" + hno
    if title:
        header += " (" + bb.highlight(pattern, title) + ")"
    print(header + ":")
    if not titles_only:
        for line in text.splitlines():
            if pattern.search(line):
                print("  " + bb.highlight(pattern, line))
    print()
    return len(hits)


def main():
    flags = {"o": False, "w": False, "t": False}
    args = []
    argv = sys.argv[1:]
    # allow "hsearch h 395 term" and "hsearch h395 term" / "#395"
    if len(argv) >= 3 and argv[0].lower() == "h" and argv[1].isdigit():
        argv = argv[1:]
    argv = [re.sub(r"^(?:[hH]#?|#)(\d+)$", r"\1", a) for a in argv]
    for a in argv:
        if a.startswith("-") and len(a) > 1 and not a[1:].isdigit():
            for ch in a[1:]:
                if ch not in flags:
                    print("Unknown option -" + ch)
                    print(USAGE)
                    sys.exit(1)
                flags[ch] = True
        else:
            args.append(a)
    args, term = bb.split_or(args)
    args = args + [term]          # keep the old "[hymn] term" shape
    if len(args) == 0 or len(args) > 2:
        print(USAGE)
        sys.exit(1)

    term = args[-1]
    pattern = bb.make_pattern(term, flags["w"])

    if len(args) == 2:
        if not args[0].isdigit():
            print(USAGE)
            sys.exit(1)
        hymns = [args[0]]
    else:
        bb.require_dir(bb.HYMNS_DIR, bb.NO_HYMNS)
        hymns = bb.numeric_sort(os.listdir(bb.HYMNS_DIR))

    matched = occurrences = 0
    for hno in hymns:
        n = search_hymn(hno, pattern, flags["t"])
        if n:
            matched += 1
            occurrences += n
    if flags["o"]:
        print("Total hymns: " + str(matched))
        print("Total occurrences: " + str(occurrences))


if __name__ == "__main__":
    main()
