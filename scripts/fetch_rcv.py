#!/usr/bin/env python3
"""Download the Recovery Version text (all 66 books) and the New Testament
book backgrounds and outlines from text.recoveryversion.bible, the free
online edition published by Living Stream Ministry, onto this computer.

  fetch_rcv.py            download whatever is missing (safe to re-run)
  fetch_rcv.py --force    download everything again
  fetch_rcv.py --verses   only the Bible text
  fetch_rcv.py --books    only the NT backgrounds/outlines

The text stays on your own computer for your personal study; please don't
redistribute it. (c) Living Stream Ministry.
"""

import concurrent.futures
import html
import os
import re
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import bible_books as bb

SITE = "https://text.recoveryversion.bible/"
WORKERS = 4

# (directory name, chapters, page name on the site)
BOOKS = [
    ("Gen", 50, "01_Genesis"), ("Exo", 40, "02_Exodus"), ("Lev", 27, "03_Leviticus"),
    ("Num", 36, "04_Numbers"), ("Deut", 34, "05_Deuteronomy"), ("Josh", 24, "06_Joshua"),
    ("Judg", 21, "07_Judges"), ("Ruth", 4, "08_Ruth"), ("1Sam", 31, "09_1Samuel"),
    ("2Sam", 24, "10_2Samuel"), ("1Kings", 22, "11_1Kings"), ("2Kings", 25, "12_2Kings"),
    ("1Chron", 29, "13_1Chronicles"), ("2Chron", 36, "14_2Chronicles"), ("Ezra", 10, "15_Ezra"),
    ("Neh", 13, "16_Nehemiah"), ("Esther", 10, "17_Esther"), ("Job", 42, "18_Job"),
    ("Psa", 150, "19_Psalms"), ("Prov", 31, "20_Proverbs"), ("Eccl", 12, "21_Ecclesiastes"),
    ("SOS", 8, "22_SongofSongs"), ("Isa", 66, "23_Isaiah"), ("Jer", 52, "24_Jeremiah"),
    ("Lam", 5, "25_Lamentations"), ("Ezek", 48, "26_Ezekiel"), ("Dan", 12, "27_Daniel"),
    ("Hos", 14, "28_Hosea"), ("Joel", 3, "29_Joel"), ("Amos", 9, "30_Amos"),
    ("Obad", 1, "31_Obadiah"), ("Jonah", 4, "32_Jonah"), ("Micah", 7, "33_Micah"),
    ("Nahum", 3, "34_Nahum"), ("Hab", 3, "35_Habakkuk"), ("Zeph", 3, "36_Zephaniah"),
    ("Hag", 2, "37_Haggai"), ("Zech", 14, "38_Zechariah"), ("Mal", 4, "39_Malachi"),
    ("Matt", 28, "40_Matthew"), ("Mark", 16, "41_Mark"), ("Luke", 24, "42_Luke"),
    ("John", 21, "43_John"), ("Acts", 28, "44_Acts"), ("Rom", 16, "45_Romans"),
    ("1Cor", 16, "46_1Corinthians"), ("2Cor", 13, "47_2Corinthians"), ("Gal", 6, "48_Galatians"),
    ("Eph", 6, "49_Ephesians"), ("Phil", 4, "50_Philippians"), ("Col", 4, "51_Colossians"),
    ("1Thes", 5, "52_1Thessalonians"), ("2Thes", 3, "53_2Thessalonians"),
    ("1Tim", 6, "54_1Timothy"), ("2Tim", 4, "55_2Timothy"), ("Titus", 3, "56_Titus"),
    ("Philemon", 1, "57_Philemon"), ("Heb", 13, "58_Hebrews"), ("James", 5, "59_James"),
    ("1Pet", 5, "60_1Peter"), ("2Pet", 3, "61_2Peter"), ("1John", 5, "62_1John"),
    ("2John", 1, "63_2John"), ("3John", 1, "64_3John"), ("Jude", 1, "65_Jude"),
    ("Rev", 22, "66_Revelation"),
]
NT_START = 39   # index of Matthew

QUOTES = {"‘": "'", "’": "'", "“": '"', "”": '"', " ": " "}


# ---------------------------------------------------------------- download

def fetch(url, tries=4):
    """Return the page text. Uses Python's own HTTPS first and falls back to
    the system curl (some Mac Pythons lack web certificates)."""
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "bible-cli (personal study)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:      # noqa: BLE001 - network errors vary a lot
            last = e
            if "CERTIFICATE" in str(e).upper() or "SSL" in str(e).upper():
                try:
                    return subprocess.run(["curl", "-fsSL", "--max-time", "30", url],
                                          check=True, capture_output=True).stdout.decode("utf-8", "replace")
                except Exception as e2:     # noqa: BLE001
                    last = e2
            if "404" in str(e):
                break
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("could not download " + url + " (" + str(last) + ")")


# ---------------------------------------------------------------- parsing

def clean(fragment):
    """HTML fragment -> plain text in the style of the rest of the toolkit."""
    s = fragment.replace("<br />", " /").replace("<br/>", " /")
    s = s.replace("&nbsp;&mdash;", " -")
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    for a, b in QUOTES.items():
        s = s.replace(a, b)
    s = s.replace("\t", " ")
    return re.sub(r" {2,}", " ", s).strip()


VERSE_RE = re.compile(r'<p id="[^"]*" class="verse"><b>(.*?)</b>(.*?)</p>', re.S)


def parse_chapter(page):
    """'Rom. 8:28 And we know ...' lines for one chapter page."""
    out = []
    for ref, text in VERSE_RE.findall(page):
        line = clean(ref) + " " + clean(text)
        out.append(line.strip())
    return out


def parse_info(page):
    """Author / Time / Place / Recipients / Subject lines from a book's first page."""
    lines = []
    m = re.search(r'<div id="book-info">(.*?)</div>', page, re.S | re.I)
    if m:
        for p in re.findall(r"<p[^>]*>(.*?)</p>", m.group(1), re.S | re.I):
            t = clean(p.replace("&nbsp;&mdash;", " \u2014")).rstrip(".")
            if ":" in t:
                lines.append(t)
    m = re.search(r'<p class="subject">(.*?)</p>', page, re.S)
    if m:
        t = clean(m.group(1).replace("<br />", " ").replace("<br/>", " ")
                  .replace("&nbsp;&mdash;", " \u2014"))
        t = re.sub(r"\s*\u2014\s*", " \u2014 ", t)
        t = re.sub(r"^Subject:\s*", "", t)
        lines.append("Subject: " + t)
    return lines


LI_RE = re.compile(r'<li id="l(\d+)_[^"]*">(.*?)(?=<li id="l\d+_|</ol>|$)', re.S)


def parse_outline(page):
    """Indented outline lines ('I. Introduction - ... - 1:1-17')."""
    out = []
    start = page.find('<ol class="otl1"')
    if start < 0:
        return out
    body = page[start:]
    for depth, text in LI_RE.findall(body):
        text = text.split("<ol", 1)[0]
        t = clean(text.replace("&nbsp;&mdash;", " —"))
        t = re.sub(r"^(\S+\.)\s+", r"\1 ", t)
        t = re.sub(r"\s*—\s*", " — ", t)
        out.append("  " * (int(depth) - 1) + t)
    return out


# ---------------------------------------------------------------- main

def write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    os.replace(tmp, path)


def do_chapter(job):
    book, page, ch, dest = job
    lines = parse_chapter(fetch(SITE + page + "_" + str(ch) + ".htm"))
    if not lines:
        raise RuntimeError("no verses found in " + page + " " + str(ch))
    write(dest, lines)
    return book, ch


def do_book(job):
    book, page, dest = job
    info = parse_info(fetch(SITE + page + "_1.htm"))
    outline = parse_outline(fetch(SITE + page + "_o.htm"))
    if not info and not outline:
        raise RuntimeError("no background/outline found for " + book)
    write(dest, info + ["", "OUTLINE"] + outline)
    return book, 0


def run(jobs, worker, label):
    if not jobs:
        print(label + ": already downloaded.")
        return 0
    done = failed = 0
    total = len(jobs)
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as ex:
        futures = {ex.submit(worker, j): j for j in jobs}
        for f in concurrent.futures.as_completed(futures):
            try:
                f.result()
                done += 1
            except Exception as e:     # noqa: BLE001
                failed += 1
                print("\n  " + str(e))
            sys.stdout.write("\r" + label + ": %d / %d" % (done + failed, total))
            sys.stdout.flush()
    print()
    if failed:
        print("  %d failed - run this again later to fill them in." % failed)
    return failed


def main():
    args = set(sys.argv[1:])
    if args & {"-h", "--help"}:
        print(__doc__)
        return
    force = "--force" in args
    want_verses = "--books" not in args
    want_books = "--verses" not in args

    failed = 0
    if want_verses:
        jobs = []
        for book, chapters, page in BOOKS:
            for ch in range(1, chapters + 1):
                dest = bb.VERSES_DIR + book + "/" + str(ch)
                if force or not os.path.exists(dest):
                    jobs.append((book, page, ch, dest))
        failed += run(jobs, do_chapter, "Recovery Version chapters")
    if want_books:
        jobs = []
        for book, _, page in BOOKS[NT_START:]:
            dest = bb.BIBLE_DIR + "/bookinfo/" + book
            if force or not os.path.exists(dest):
                jobs.append((book, page, dest))
        failed += run(jobs, do_book, "New Testament backgrounds and outlines")
        src = bb.BIBLE_DIR + "/bookinfo/SOURCE.txt"
        if not os.path.exists(src):
            write(src, ["Recovery Version book backgrounds and outlines (New Testament), from "
                        "text.recoveryversion.bible", "(c) Living Stream Ministry. For personal use."])
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
