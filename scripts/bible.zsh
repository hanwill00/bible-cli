# Bible toolkit shell setup (zsh or bash). The installer adds one line to
# ~/.zshrc that sets BIBLE_HOME and sources this file.

: "${BIBLE_HOME:=$HOME/Bible}"
_B="$BIBLE_HOME/scripts"

# ---- commands --------------------------------------------------------------
alias verse="$_B/verse.py"            v="$_B/verse.py"
alias compare="$_B/compare.py"        vcomp="$_B/compare.py"
alias vsearch="$_B/vsearch.py"        vs="$_B/vsearch.py"
alias fsearch="$_B/fsearch.py"
alias hymn="$_B/hymn.py"              h="$_B/hymn.py"
alias hsearch="$_B/hsearch.py"        hs="$_B/hsearch.py"
alias htoc="$_B/htoc.py"
alias il="$_B/interlinear.py"         interlinear="$_B/interlinear.py"
alias book="$_B/book.py"              background="$_B/book.py"
alias xref="$_B/xref.py"              cf="$_B/xref.py"

# a version name as a command: kjv john 3:16
alias rcv="$_B/verse.py rcv"  kjv="$_B/verse.py kjv"  asv="$_B/verse.py asv"
alias darby="$_B/verse.py darby"  jnd="$_B/verse.py jnd"  esv="$_B/verse.py esv"

# ---- typing a book name or hymn number as a command --------------------------
#   john 3:16      1 cor 13      jude 20-21      h395      h395.2
_bible_cnf() {
  if [[ "$1" =~ ^[hH]#?[0-9]+(\.([0-9]+|c|t))?$ ]]; then
    "$_B/hymn.py" "$@"; return $?
  fi
  if "$_B/verse.py" --is-book "$1" 2>/dev/null || \
     { [ -n "$2" ] && "$_B/verse.py" --is-book "$1 $2" 2>/dev/null; }; then
    "$_B/verse.py" "$@"; return $?
  fi
  return 127
}

if [ -n "$ZSH_VERSION" ]; then
  if (( $+functions[command_not_found_handler] )) && (( ! $+functions[_bible_prev_cnf] )); then
    functions[_bible_prev_cnf]=$functions[command_not_found_handler]
  fi
  command_not_found_handler() {
    _bible_cnf "$@"; local rc=$?
    [ $rc -ne 127 ] && return $rc
    if (( $+functions[_bible_prev_cnf] )); then _bible_prev_cnf "$@"; return $?; fi
    print -u2 "zsh: command not found: $1"; return 127
  }
elif [ -n "$BASH_VERSION" ]; then
  command_not_found_handle() {
    _bible_cnf "$@"; local rc=$?
    [ $rc -ne 127 ] && return $rc
    echo "bash: $1: command not found" >&2; return 127
  }
fi

# ---- book abbreviations that are also built-in Mac commands -------------------
# "col 1:15" is Colossians; "col -b file" is still the normal command.
for _c in col rev ex ps; do
  eval "$_c() { if [[ \"\$1\" == [0-9]* ]]; then \"\$_B/verse.py\" $_c \"\$@\"; else command $_c \"\$@\"; fi; }"
done
unset _c
