# Credits and sources

## Included in this repository (openly licensed)

| Data | Source | License |
|---|---|---|
| King James Version, American Standard Version, Darby | [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases) | Public domain |
| Greek & Hebrew interlinear, Strong's lexicons (TAGNT, TAHOT, TBESG, TBESH) | [STEP Bible](https://www.stepbible.org), Tyndale House Cambridge, via [STEPBible-Data](https://github.com/STEPBible/STEPBible-Data) | CC BY 4.0 |
| Treasury of Scripture Knowledge cross-references | [CrossReferences-org/bible-cross-references](https://github.com/CrossReferences-org/bible-cross-references) | CC BY 4.0 |
| OpenBible.info cross-references | [OpenBible.info](https://www.openbible.info), via scrollmapper/bible_databases | CC BY |

These are packed in `data/*.tar.gz`. More detail is in the `CREDITS.txt` files inside them.

**Changes made to the data:**

- **Interlinear:** split into one file per chapter. Hebrew cantillation marks, LXX-only rows and non-NA Greek variants were removed.
- **Darby:** "God" had been run into the previous word throughout; this was fixed.

## Downloaded onto your own computer by the installer (not redistributed)

| Data | Source | Notes |
|---|---|---|
| Holy Bible Recovery Version text; New Testament book backgrounds and outlines | [text.recoveryversion.bible](https://text.recoveryversion.bible) | © Living Stream Ministry. For personal study; please don't redistribute. |
| Hymns (Living Stream Ministry hymnal numbering) | [songbase.life](https://songbase.life) | For personal use; please don't redistribute. |
| ESV (optional, fetched live each time) | [api.esv.org](https://api.esv.org) | Needs your own free key. Scripture quotations marked ESV are from the ESV Bible, copyright 2001 by Crossway. |

## Not included

The Recovery Version **footnotes** aren't available from any public website, so the toolkit can't download them. If you have them, put them in `footnotes/<Book>/<chapter>/<verse>/<note number>`, one note per file. `fsearch` and footnote references like `rom 8:28.1` will then work.
