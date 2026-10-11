#!/usr/bin/env python3
"""Download the hymns (Hymns, Living Stream Ministry numbering) from
songbase.life onto this computer, for `hymn`, `hsearch` and `htoc`.

  fetch_hymns.py            download whatever is missing (safe to re-run)
  fetch_hymns.py --force    download everything again
  fetch_hymns.py 395 1349   only these hymns

Each hymn is saved as hymns/<n>/ with: title, full, 1 2 3 ... (verses), chorus.
The lyrics stay on your own computer for personal use; please don't
redistribute them.
"""

import concurrent.futures
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import bible_books as bb
from fetch_rcv import fetch

SITE = "https://songbase.life/english_hymnal/"
LAST = 1360          # a little past the last hymn; missing numbers are skipped
WORKERS = 4

PROPS_RE = re.compile(r'data-react-props="([^"]*)"')


def parse(page):
    """Return (title, lyrics) from a songbase page, or None if no song."""
    for raw in PROPS_RE.findall(page):
        if "preloaded_song" not in raw:
            continue
        try:
            data = json.loads(html.unescape(raw))
        except ValueError:
            continue
        song = data.get("preloaded_song")
        if song and song.get("lyrics"):
            return song.get("title", "").strip(), song["lyrics"]
    return None


def split_hymn(lyrics):
    """Lyrics with [chords] -> (full, [verses], chorus). Chorus lines are the
    indented ones; verse numbers sit alone on a line."""
    text = re.sub(r"\[[^\]]*\]", "", lyrics)
    lines = [l.rstrip() for l in text.splitlines()]
    lines = [l for l in lines if l.strip() and "Capo " not in l]
    verses, verse, chorus = [], "", ""
    for line in lines:
        if line.startswith("  "):
            if verse:
                verses.append(verse)
                verse = ""
            chorus += line + "\n"
            continue
        if line.strip().isdigit():
            if verse:
                verses.append(verse)
            verse = ""
        else:
            verse += line + "\n"
    if verse:
        verses.append(verse)
    return "\n".join(lines), verses, chorus


def save(num, title, lyrics):
    full, verses, chorus = split_hymn(lyrics)
    if not verses:
        return False
    d = bb.HYMNS_DIR + str(num) + "/"
    os.makedirs(d, exist_ok=True)
    with open(d + "title", "w", encoding="utf-8") as fp:
        fp.write(title + "\n")
    if chorus:
        with open(d + "chorus", "w", encoding="utf-8") as fp:
            fp.write(chorus + "\n")
    for i, v in enumerate(verses, 1):
        with open(d + str(i), "w", encoding="utf-8") as fp:
            fp.write(v)
    with open(d + "full", "w", encoding="utf-8") as fp:      # written last = complete
        fp.write(full)
    return True


def one(num):
    got = parse(fetch(SITE + str(num)))
    if got is None:
        return num, "missing"
    return num, ("ok" if save(num, *got) else "empty")


def main():
    args = sys.argv[1:]
    if {"-h", "--help"} & set(args):
        print(__doc__)
        return
    force = "--force" in args
    nums = [int(a) for a in args if a.isdigit()]
    if not nums:
        nums = list(range(1, LAST + 1))
    todo = [n for n in nums if force or not os.path.exists(bb.HYMNS_DIR + str(n) + "/full")]
    if not todo:
        print("Hymns: already downloaded.")
        return
    os.makedirs(bb.HYMNS_DIR, exist_ok=True)
    done = failed = 0
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as ex:
        for f in concurrent.futures.as_completed([ex.submit(one, n) for n in todo]):
            try:
                f.result()
            except Exception as e:     # noqa: BLE001
                failed += 1
                print("\n  " + str(e))
            done += 1
            sys.stdout.write("\rHymns: %d / %d" % (done, len(todo)))
            sys.stdout.flush()
    print()
    print("Hymns installed: %d" % sum(1 for n in os.listdir(bb.HYMNS_DIR) if n.isdigit()))
    if failed:
        print("  %d failed - run this again later to fill them in." % failed)
        sys.exit(1)


if __name__ == "__main__":
    main()
