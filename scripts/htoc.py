#!/usr/bin/env python3
"""Table of contents for the hymnal.

  htoc                  the whole table of contents (pipe to less)
  htoc -c               just the 32 categories, with hymn counts
  htoc church           one category, by number (20) or name fragment
  htoc 20.11            one subcategory
  htoc -n 837           where hymn #837 sits (category / subcategory)
  htoc -a               alphabetical index of first lines
  htoc search "table"   category names, subheadings and first lines
                        containing a word (same as -s; regex ok)

Category data lives in hymn_toc.json next to this script; titles are read
from ~/Bible/hymns/<n>/title.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import bible_books as bb

USAGE = "Usage: htoc [-c | -a | -n <hymn> | search <word> | <category> | <cat.sub>]"
TOC_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "hymn_toc.json")

with open(TOC_PATH) as _f:
    CATS = json.load(_f)


def title(hno):
    try:
        with open(bb.HYMNS_DIR + str(hno) + "/title") as fp:
            return fp.readline().strip()
    except OSError:
        return "(not in your collection)"


def count(cat):
    return sum(len(s["hymns"]) for s in cat["subs"])


def hymn_line(h):
    return "    #%-5d %s" % (h, title(h))


def print_sub(sub):
    print("  " + sub["num"] + " " + sub["name"])
    for h in sub["hymns"]:
        print(hymn_line(h))


def print_cat(cat, with_hymns=True):
    print(bb.bold("%d. %s [%d]" % (cat["num"], cat["name"], count(cat))))
    if with_hymns:
        for sub in cat["subs"]:
            print_sub(sub)
        print()


def find_cat(query):
    q = query.lower()
    if q.isdigit():
        for c in CATS:
            if c["num"] == int(q):
                return c
        return None
    hits = [c for c in CATS if q in c["name"].lower()]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        # Prefer a match at the start of the name ("church" -> The Church still ok).
        starts = [c for c in hits if c["name"].lower().startswith(q)]
        if len(starts) == 1:
            return starts[0]
        print("Ambiguous: " + ", ".join("%d %s" % (c["num"], c["name"]) for c in hits))
        sys.exit(1)
    return None


def find_sub(code):
    for c in CATS:
        for s in c["subs"]:
            if s["num"] == code:
                return c, s
    return None, None


def locate(hno):
    for c in CATS:
        for s in c["subs"]:
            if hno in s["hymns"]:
                return c, s
    return None, None


def main():
    args = sys.argv[1:]
    if not args:
        for c in CATS:
            print_cat(c)
        return

    flag = args[0]
    if flag == "-c":
        for c in CATS:
            print_cat(c, with_hymns=False)
    elif flag == "-a":
        rows = []
        for c in CATS:
            for s in c["subs"]:
                for h in s["hymns"]:
                    t = title(h)
                    if not t.startswith("("):
                        rows.append((t.lstrip("\"'‘“(’").lower(), t, h))
        for _, t, h in sorted(rows):
            print("%-60s #%d" % (t[:60], h))
    elif flag == "-n":
        if len(args) < 2 or not args[1].isdigit():
            print(USAGE)
            sys.exit(1)
        h = int(args[1])
        c, s = locate(h)
        if c is None:
            print("Hymn #%d is not in the table of contents." % h)
            sys.exit(1)
        print("#%d  %s" % (h, title(h)))
        print("  %d. %s" % (c["num"], c["name"]))
        print("  %s %s" % (s["num"], s["name"]))
    elif flag in ("-s", "search"):
        if len(args) < 2:
            print(USAGE)
            sys.exit(1)
        pattern = bb.make_pattern(" ".join(args[1:]), False)
        for c in CATS:
            if pattern.search(c["name"]):
                print(bb.bold("%d. %s [%d]" % (c["num"], bb.highlight(pattern, c["name"]), count(c))))
            for s in c["subs"]:
                if pattern.search(s["name"]):
                    print("  %s %s   (%d. %s)   %s" % (
                        s["num"], bb.highlight(pattern, s["name"]), c["num"], c["name"],
                        ", ".join("#%d" % h for h in s["hymns"])))
                for h in s["hymns"]:
                    t = title(h)
                    if pattern.search(t):
                        print("    #%-5d %s   (%s %s)" % (h, bb.highlight(pattern, t), s["num"], s["name"]))
    elif flag.startswith("-"):
        print(USAGE)
        sys.exit(1)
    else:
        query = " ".join(args)
        if "." in query and query.replace(".", "").isdigit():
            c, s = find_sub(query)
            if s is None:
                print("No subcategory " + query)
                sys.exit(1)
            print(bb.bold("%d. %s" % (c["num"], c["name"])))
            print_sub(s)
            return
        c = find_cat(query)
        if c is None:
            print("No category matches '" + query + "'.")
            print("Categories: " + ", ".join("%d %s" % (x["num"], x["name"]) for x in CATS))
            sys.exit(1)
        print_cat(c)


if __name__ == "__main__":
    main()
