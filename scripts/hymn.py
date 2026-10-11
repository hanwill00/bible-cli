#!/usr/bin/env python3

import re
import sys
import os

def process_latex_newline(line):
    return line[:-1] + "\\newline\n"

def is_full_hymn(arg):
    return arg.isnumeric()

def is_verse(arg):
    if re.match("[0-9]+\.[0-9]+$", arg) is None:
        return False
    return True

def is_chorus(arg):
    if re.match("[0-9]+\.c", arg) is None:
        return False
    return True

def is_title(arg):
    if re.match("[0-9]+\.t", arg) is None:
        return False
    return True

def path(hymn_no):
    base = os.environ.get("BIBLE_DIR") or os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    return base + "/hymns/" + hymn_no + "/"

def get_hymn(hymn_no, latex):
    hymn = ""
    hymn_path = path(hymn_no)

    title = "Hymns, #" + hymn_no
    if latex:
        title = "\\textbf{Hymns, \\#" + hymn_no
    if os.path.exists(hymn_path + "title"):
        with open(hymn_path + "title") as f:
            title += " (" + f.readline().strip("\n") + ")"
    hymn += title
    if latex:
        hymn += "}\\newline"
    hymn += "\n\n"

    chorus = ""
    if os.path.exists(hymn_path + "chorus"):
        with open(hymn_path + "chorus") as f:
            for line in f:
                if latex:
                    line = re.sub("  ", "\\\\indent", line)
                chorus += line
        if latex:
            chorus = process_latex_newline(chorus)

    files = []
    for name in os.listdir(hymn_path):
        if name in ["chorus", "title", "full"]:
            continue
        files += [name]
    files.sort()

    for num in files:
        if len(files) > 1:
            if latex:
                hymn += "\\textbf{" + num + "}\n"
            else:
                hymn += num + "\n"
        verse = ""
        with open(hymn_path + num) as f:
            for line in f:
                verse += line
        if latex:
            verse = process_latex_newline(verse)
        hymn += verse + "\n"
        if num == "1" and chorus != "":
            hymn += chorus

    return hymn

def print_verse(hymn_no, verse_no, latex):
    try:
        with open(path(hymn_no) + verse_no) as fp:
            title = "Hymns, #" + hymn_no + " verse " + verse_no + ":\n"
            if latex:
                title = "\\textbf{Hymns, \\#" + hymn_no + " verse " + verse_no + ":}\n"
            print(title)
            verse = ""
            for i, line in enumerate(fp):
                verse += line
            if latex:
                verse = process_latex_newline(verse)
            print(verse, end="")
        return True
    except:
        return False

def print_chorus(hymn_no, latex):
    try:
        with open(path(hymn_no) + "chorus") as fp:
            title = "Hymns, #" + hymn_no + " chorus:\n"
            if latex:
                title = "\\textbf{Hymns, \\#" + hymn_no + " chorus:}\n"
            print(title)
            chorus = ""
            for i, line in enumerate(fp):
                if len(line) > 0 and line != "\n":
                    chorus += line
            if latex:
                chorus = process_latex_newline(chorus)
            print(chorus, end="")
        return True
    except:
        return False

def print_title(hymn_no):
    try:
        with open(path(hymn_no) + "title") as fp:
            for i, line in enumerate(fp):
                print(line, end="")
        return True
    except:
        return False

USAGE = """Usage: hymn [-l] <hymn>[.verse|.c|.t] ...
  hymn 395   h395   h 395   h#395    the whole hymn
  h395.2     verse 2        h395.c   the chorus      h395.t   the title
  h 395 1    several hymns at once"""


def normalize(code):
    """'h395', 'H395', '#395', 'h#395', 'hymn395' -> '395' (suffixes kept)."""
    code = code.strip().lower()
    code = re.sub(r"^(hymns?|h)", "", code)
    return code.lstrip("#")


latex = False
args = []
for arg in sys.argv[1:]:
    if arg == '-l':
        latex = True
    else:
        args += [arg]

# "h" or "hymn" typed as its own word: h 395
args = [a for a in args if a.lower() not in ("h", "hymn", "hymns", "#")]
if len(args) == 0:
    print(USAGE)
    sys.exit(1)

for n, raw in enumerate(args):
    hymn_code = normalize(raw)
    num = hymn_code.split(".")[0]
    if not num.isnumeric() or not os.path.isdir(path(num)):
        hd = os.path.dirname(path("x").rstrip("/"))
        if not os.path.isdir(hd) or not os.listdir(hd):
            print("The hymns are not installed yet. Run:  " + os.path.dirname(os.path.realpath(__file__)) + "/fetch_hymns.py")
            sys.exit(1)
        print("No such hymn: " + raw)
        continue
    if n:
        print()
    if is_full_hymn(hymn_code):
        print(get_hymn(hymn_code, latex), end="")
    elif is_verse(hymn_code):
        code = hymn_code.split(".")
        if not print_verse(code[0], code[1], latex):
            print("Hymn #" + code[0] + " has no verse " + code[1])
    elif is_chorus(hymn_code):
        if not print_chorus(num, latex):
            print("Hymn #" + num + " has no chorus")
    elif is_title(hymn_code):
        print_title(num)
    else:
        print(USAGE)
