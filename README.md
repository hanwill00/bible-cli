# Bible toolkit for the Terminal

Read and search the Bible and the hymns right from your Mac's Terminal: fast, offline, no ads.

```
$ john 3:16
John 3:16 For God so loved the world that He gave His only begotten Son, that everyone who believes into Him would not perish, but would have eternal life.

$ vs -o eph "economy"
Eph. 1:10 Unto the economy of the fullness of the times, to head up all things in Christ, ...
Eph. 3:9 And to enlighten all that they may see what the economy of the mystery is, ...
Total verses: 2
Total occurrences: 2

$ h 395
Hymns, #395 (O Jesus Christ, grow Thou in me)
...
```

**What you get**

- **Recovery Version text:** all 66 books.
- **Other versions:** KJV, ASV, Darby, and the ESV (online, needs a free key).
- **Search:** any word or phrase, in any book, group of books or version.
- **Hymns:** the full hymnal, searchable, with a table of contents.
- **Greek/Hebrew interlinear:** with Strong's numbers and a lexicon.
- **Cross-references:** Treasury of Scripture Knowledge and OpenBible.info.
- **Book backgrounds and outlines:** for the New Testament books.

---

## Install (one line)

1. Open **Terminal** (press ⌘-Space, type `Terminal`, press Return).
2. Paste this line and press Return:

```
curl -fsSL https://raw.githubusercontent.com/GITHUB_USER/bible-cli/main/install.sh | bash
```

3. Wait about 10–15 minutes. The installer downloads the Recovery Version text and the hymns onto your computer.
4. **Close Terminal and open a new window.** Then try `john 3:16`.

**If a window pops up asking to install "command line developer tools":** click **Install**, wait for it to finish, then paste the line again. Your Mac needs these once, for Python.

**Already have a folder called `Bible` in your home folder?** The installer won't touch it. Install somewhere else instead:

```
curl -fsSL https://raw.githubusercontent.com/GITHUB_USER/bible-cli/main/install.sh | BIBLE_DIR=~/BibleTool bash
```

**Updating:** paste the same install line again. Your downloaded text and hymns are kept.

---

## Cheat sheet

| You type | You get |
|---|---|
| `john 3:16` | a verse (just type the book name) |
| `rom 8` | a whole chapter |
| `rom 8:28-30` | a range |
| `gen 43-44` | several chapters |
| `rom 8:28; psa 23:1` | several references |
| `1 cor 1:1, 5-8` | short forms carry over the book and chapter |
| `kjv john 3:16` | another version (`kjv`, `asv`, `darby`, `esv`) |
| `vcomp john 3:16` | the verse in every version, side by side |
| `vs "eternal life"` | search the whole Bible |
| `vs rom "grace"` | search one book |
| `vs nt "faith.*love"` | "faith", then later "love", in the New Testament |
| `vs "grace" or "mercy"` | either word |
| `h 395` or `h395` | a hymn |
| `hs "abide"` | search the hymns |
| `htoc -c` | hymnal categories |
| `il john 1:1` | Greek under the English |
| `book rom` | background and outline of Romans |
| `cf rom 8:28` | cross-references |

Every command shows its options when you type it on its own, for example just `vs`.

---

## Reading verses: `verse` / `v`, or just the book name

```
john 1:14              one verse
rom 8                  a chapter
rom 8:28-30            a range
gen 43:30-44:2         a range that crosses chapters
jude 19-21             one-chapter books work as you'd expect
rom 8:28; psa 23:1     several references (also , or +)
1 cor 1:1, 5-8         = 1 Cor. 1:1 and 1:5-8
v -p rom 8:28-30       paragraph form: text only, one reference at the end
```

Books can be written almost any way: `romans`, `rom`, `rm`, `1 cor`, `1cor`, `1 corinthians`, `ps`, `psa`, `sos`, `song of songs`... Capitals and periods don't matter.

**Versions:** put the version first.

```
kjv rom 8:28           King James
asv rom 8:28           American Standard
darby rom 8:28         Darby (also: jnd)
esv rom 8:28           ESV (needs a key, see below)
verse kjv asv rom 8:28 several versions, labeled
verse all rom 8:28     every installed version
vcomp rom 8:28         same as "verse all"
```

### Turning on the ESV (optional)

The ESV is fetched online each time, so it needs a free personal key from Crossway:

1. Make an account and an API key at **https://api.esv.org**.
2. Save the key (replace `YOUR_KEY`, and use your install folder if it isn't `~/Bible`):

```
echo "YOUR_KEY" > ~/Bible/esv_api_key
```

---

## Searching: `vsearch` / `vs`

```
vs [options] [version] [books] "search term"
```

Put the search term in quotes. Capitals don't matter.

```
vs "righteousness"                whole Bible
vs romans "righteousness"         one book
vs rom 3 "righteousness"          one chapter
vs nt "righteousness"             a group of books (see below)
vs rom + gal "justified"          several books (also: rom, gal  or  rom and gal)
vs kjv rom "charity"              another version
vs "grace" or "truth"             either one
```

**Options** (they can be combined, e.g. `vs -o -w nt "mercy"`)

| Option | What it does |
|---|---|
| `-o` | show totals at the end (verses and occurrences) |
| `-w` | whole words only: `vs -w "sin"` won't match "since" |
| `-p` | paragraph form: text first, reference at the end |
| `m 3` | search across up to 3 verses in a row: `vs m 3 psa "arrows.*quiver"` |
| `syn` | include synonyms: `vs syn "compassion"` also finds mercy, pity... |

**Search patterns.** A few special characters make searches more powerful:

| Pattern | Means | Example |
|---|---|---|
| `.*` | anything in between | `vs "faith.*hope.*love"` |
| `\|` | or (inside one term) | `vs "Jehovah\|Lord"` |
| `\b` | word edge | `vs "\bsin\b"` (or just use `-w`) |

**Groups of books** work anywhere a book does:

| Group | Books |
|---|---|
| `ot` / `nt` | Old / New Testament |
| `law` | Genesis–Deuteronomy |
| `history` | Genesis–Nehemiah |
| `poetry` | Job–Song of Songs |
| `prophets`, `major`, `minor` | Isaiah–Malachi, Isaiah–Daniel, Hosea–Malachi |
| `gospels` | Matthew–John |
| `epistles`, `pauline`, `general` | Romans–Jude, Romans–Philemon, Hebrews–Jude |
| `heart` | Galatians, Ephesians, Philippians, Colossians |
| `pastoral` | 1 & 2 Timothy, Titus |
| `peter`, `johns writings`, `johns epistles`, `corinthians`, `samuel`, `kings`, `chronicles`, `moses`... | what they say |

---

## Hymns: `hymn` / `h`, `hsearch` / `hs`, `htoc`

```
h 395           the whole hymn (also h395, h#395, hymn 395)
h395.2          verse 2
h395.c          the chorus
h395.t          the title
h 395 1         two hymns at once

hs "abide"              search every hymn
hs "abide" or "dwell"   either word
hs h395 "daily"         search inside one hymn
hs -t "Father"          titles only
hs -o -w "glory"        totals, whole words

htoc -c                 the 32 categories, with hymn counts
htoc church             one category (by name or number: htoc 20)
htoc -n 837             where hymn 837 sits in the hymnal
htoc search "table"     search category names and first lines
htoc -a                 alphabetical index of first lines
```

---

## Greek and Hebrew: `il`

Shows each original-language word under the verse, with its transliteration, English meaning, Strong's number and grammar.

```
il john 1:1             interlinear
il -c john 1:1          compact: word, transliteration, meaning only
il -w psa 103:7         word list with the grammar spelled out
il -t psa 103:7         transliteration instead of Hebrew/Greek letters

il G2222                dictionary entry for a Strong's number + every verse it's in
il H1870 psa            ... only in Psalms
il -o H1870             ... counts per book only
il G2222 G0166          verses where both words occur together ("eternal life")
il -f eternal           find Strong's numbers by English word
```

---

## Book background and outline: `book` / `background`

New Testament books only (that's what the online Recovery Version publishes).

```
book rom                author, time, place, recipients, subject, and the outline
book rom -b             background only
book rom -o             outline only
book rom 8:28           where a verse falls in the outline
book pauline            the subject of each book in a group
book -s "Body"          search every outline and background
```

---

## Cross-references: `xref` / `cf`

```
cf rom 8:28             cross-references with their verse text
cf tsk rom 8:28         Treasury of Scripture Knowledge, grouped by word
cf obi rom 8:28         OpenBible.info, most helpful first (top 20)
cf rom 8                a whole chapter (references only)
cf -r rom 8:28          references only, no verse text
cf obi -a rom 8:28      all of them, not just the top 20
```

---

## Tips

- **Long output?** Add `| less` to scroll (press `q` to quit): `vs "love" | less`.
- **Copy results:** add `| pbcopy` and paste anywhere: `rom 8:28-30 | pbcopy`.
- **Four abbreviations clash with built-in Mac commands:** `col`, `rev`, `ex` and `ps`. The toolkit handles this: `col 1:15` gives Colossians, while `col -b` still runs the Mac command.
- **Footnotes:** `fsearch` and footnote references like `rom 8:28.1` only work if you have the Recovery Version footnotes. They aren't on a public website, so the installer can't download them.

---

## Troubleshooting

**"command not found" right after installing.** Open a new Terminal window. The commands load when a window opens.

**"The Recovery Version text is not installed yet."** The download was interrupted. Run this again; it picks up where it stopped:

```
~/Bible/scripts/fetch_rcv.py
```

The hymns work the same way, with `~/Bible/scripts/fetch_hymns.py`.

**Uninstall.** Delete the `Bible` folder in your home folder (or wherever you installed it). Then open `~/.zshrc` and delete the line ending in `# bible-cli`:

```
open -e ~/.zshrc
```

---

## Where things come from

See [CREDITS.md](CREDITS.md). In short:

- **Recovery Version text and New Testament outlines:** downloaded by your own computer from the free online edition at text.recoveryversion.bible. They are © Living Stream Ministry, for your personal use.
- **Hymns:** downloaded from songbase.life, for personal use.
- **Openly licensed data that comes with the toolkit:** KJV, ASV and Darby; the STEP Bible interlinear (CC BY 4.0); the cross-references.

None of the copyrighted text is stored in this repository.
