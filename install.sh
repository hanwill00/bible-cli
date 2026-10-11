#!/bin/bash
# Bible toolkit installer / updater for macOS (also works on Linux).
#
#   curl -fsSL https://raw.githubusercontent.com/GITHUB_USER/bible-cli/main/install.sh | bash
#
# Installs into ~/Bible (or $BIBLE_DIR), adds one line to ~/.zshrc, then
# downloads the Recovery Version text and the hymns onto this computer.
# Re-run the same line any time to update; your downloaded text is kept.
#
# Options (put them after "bash -s --"):
#   --no-download   install the commands only; fetch the text/hymns later
#   --no-hymns      skip the hymns
set -e

REPO="${BIBLE_CLI_REPO:-GITHUB_USER/bible-cli}"
BRANCH="${BIBLE_CLI_BRANCH:-main}"
DEST="${BIBLE_DIR:-$HOME/Bible}"
DOWNLOAD=1; HYMNS=1
for a in "$@"; do
  case "$a" in
    --no-download) DOWNLOAD=0 ;;
    --no-hymns) HYMNS=0 ;;
  esac
done

say()  { printf '\033[1m%s\033[0m\n' "$*"; }
fail() { printf '\033[31m%s\033[0m\n' "$*" >&2; exit 1; }

# ---- 1. Python ---------------------------------------------------------------
if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 6))' >/dev/null 2>&1; then
  if [ "$(uname)" = "Darwin" ]; then
    xcode-select --install >/dev/null 2>&1 || true
    fail "Python 3 is needed. A window should have opened to install Apple's
Command Line Tools - click Install, wait for it to finish, then run this
installer again."
  fi
  fail "Python 3.6 or newer is needed (python3 was not found)."
fi

# ---- 2. Don't overwrite someone's own ~/Bible folder ---------------------------
if [ -d "$DEST" ] && [ ! -f "$DEST/.bible-cli" ] && [ -n "$(ls -A "$DEST" 2>/dev/null)" ]; then
  fail "$DEST already exists and wasn't made by this installer.
Pick another folder, e.g.:
  curl -fsSL https://raw.githubusercontent.com/$REPO/$BRANCH/install.sh | BIBLE_DIR=~/BibleTool bash"
fi

# ---- 3. Get the files ----------------------------------------------------------
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
if [ -n "$BIBLE_CLI_SRC" ]; then            # local copy (for testing)
  SRC="$BIBLE_CLI_SRC"
else
  say "Downloading the toolkit..."
  curl -fsSL "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz" | tar -xz -C "$TMP" \
    || fail "Couldn't download https://github.com/$REPO - check your internet connection."
  SRC="$(ls -d "$TMP"/*/ | head -1)"
fi

say "Installing into $DEST ..."
mkdir -p "$DEST"
touch "$DEST/.bible-cli"
cp -R "$SRC/scripts" "$DEST/"
cp "$SRC/README.md" "$SRC/CREDITS.md" "$DEST/" 2>/dev/null || true
chmod +x "$DEST"/scripts/*.py
for t in "$SRC"/data/*.tar.gz; do
  tar -xzf "$t" -C "$DEST"                   # KJV/ASV/Darby, interlinear, cross-references
done

# ---- 4. Shell setup --------------------------------------------------------------
LINE="export BIBLE_HOME=\"$DEST\"; source \"\$BIBLE_HOME/scripts/bible.zsh\"   # bible-cli"
add_line() {
  local rc="$1"
  [ -f "$rc" ] || touch "$rc"
  if grep -q '# bible-cli' "$rc"; then
    grep -v '# bible-cli' "$rc" > "$rc.bible-cli.tmp" && cat "$rc.bible-cli.tmp" > "$rc" && rm -f "$rc.bible-cli.tmp"
  fi
  printf '\n%s\n' "$LINE" >> "$rc"
}
add_line "$HOME/.zshrc"
case "$SHELL" in */bash) add_line "$HOME/.bash_profile" ;; esac

# ---- 5. Recovery Version text and hymns ----------------------------------------------
if [ "$DOWNLOAD" = 1 ]; then
  say "Downloading the Recovery Version text (about 5 minutes)..."
  python3 "$DEST/scripts/fetch_rcv.py" || say "Some chapters didn't download - run $DEST/scripts/fetch_rcv.py again later."
  if [ "$HYMNS" = 1 ]; then
    say "Downloading the hymns (about 5-10 minutes)..."
    python3 "$DEST/scripts/fetch_hymns.py" || say "Some hymns didn't download - run $DEST/scripts/fetch_hymns.py again later."
  fi
fi

echo
say "Done! Open a NEW Terminal window and try:"
echo "  john 3:16"
echo "  vs \"eternal life\""
echo "  h 395"
echo
echo "Guide: $DEST/README.md  (or the project page on GitHub)"
