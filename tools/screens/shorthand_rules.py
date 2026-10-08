"""Capture shorthands: when a token counts (owner, 2026-10-07: accepted, "making sure they're safe for text that
includes those letters in a word"). A reference matcher for the rules, and the cases it must pass; the app's parser
(with the screens' build) takes these cases as its acceptance test. Evidence for whole-token matching: Vikunja's
partial-word bug (a date read out of "Renovation"), in _screens-sources/nl-capture-research.md.

Rules
  1. A kind shorthand counts only as the line's whole first token (td ev rm lg j t ck ld, any case), followed by a
     space and more text. "tdah", "event", "ldap", "j." and a line that is only "td" stay text.
  2. A field marker counts only at a token's start (the line's start or after a space), and only when the value
     after it parses; otherwise the text stays as typed:
       #  a letter follows          #health          (not "C#", "#1", "# heading")
       @  a letter follows          @personal        (not "a@b.com", "@ 5pm")
       ^  a letter follows          ^garden          (not "2^8")
       ~  a duration follows        ~30m ~1h ~1h30m  (not "~approx", "~5")
       !  a time or offset follows  !10m !2h !9:00   (not "Wow!", "!!!", "! now")
       *  a repeat word follows     *daily *weekly *every ...  (not "2*3", "*important*")
  3. Whatever counted is highlighted; tapping a highlight offers "Keep as text", which undoes rules 1-2 for it.
     Dates and times read from the words are highlighted and offer it too (owner, 2026-10-08: in a Journal line
     "tomorrow" may be only a word, not the item's date); to change a date, the words are edited.

    PYTHONUTF8=1 python tools/screens/shorthand_rules.py      (exits 1 on any failing case)
"""
import json
import os
import re
import sys

KINDS = {"td": "task", "ev": "event", "rm": "reminder", "lg": "log", "j": "journal", "t": "timer", "ck": "check-in", "ld": "ledger"}
DUR = r"\d+(?:m|h|d)(?:\d+m)?"
MARKERS = {
    "#": r"[^\W\d_][\w-]*",
    "@": r"[^\W\d_][\w-]*",
    "^": r"[^\W\d_][\w-]*",
    "~": DUR + r"\b",
    "!": r"(?:" + DUR + r"|\d{1,2}:\d{2})\b",
    "*": r"(?:daily|weekly|monthly|yearly|weekdays|every)\b",
}
TOKEN_START = r"(?:(?<=\s)|^)"


def parse(line):
    """Returns (kind or None, [(marker, value)]), by the rules above."""
    kind = None
    m = re.match(r"^(\S+)\s+\S", line)
    if m and m.group(1).lower() in KINDS:
        kind = KINDS[m.group(1).lower()]
    found = []
    for mk, val in MARKERS.items():
        for mm in re.finditer(TOKEN_START + re.escape(mk) + "(" + val + ")", line):
            found.append((mk, mm.group(1)))
    return kind, sorted(found)


# (line, expected kind, expected markers)
CASES = [
    # rule 1: kinds
    ("td call mum fri", "task", []), ("ev dentist tomorrow 9am", "event", []), ("rm take meds !21:00", "reminder", [("!", "21:00")]),
    ("lg water 2", "log", []), ("j slept badly", "journal", []), ("t reading", "timer", []), ("T reading ~30m", "timer", [("~", "30m")]),
    ("ck energy 2", "check-in", []), ("ld masking high", "ledger", []),
    ("tdah meeting notes", None, []), ("event planning", None, []), ("ldap password reset", None, []), ("evening walk", None, []),
    ("rmdir old folder", None, []), ("lgbt+ book club", None, []), ("j.k. rowling book", None, []), ("t-shirt wash", None, []),
    ("ckd follow-up", None, []), ("td", None, []), ("call td bank", None, []), ("ci vediamo domani", None, []), ("log the bug", None, []),
    # rule 2: markers
    ("buy milk #home", None, [("#", "home")]), ("learn C# basics", None, []), ("fix issue #1", None, []), ("# heading", None, []),
    ("call @personal tomorrow", None, [("@", "personal")]), ("email a@b.com today", None, []), ("meet @ 5pm", None, []),
    ("plan ^garden layout", None, [("^", "garden")]), ("compute 2^8", None, []),
    ("ev yoga ~1h30m", "event", [("~", "1h30m")]), ("about ~approx", None, []), ("~5 apples", None, []),
    ("rm stretch !10m", "reminder", [("!", "10m")]), ("Wow! great day", None, []), ("!!! urgent", None, []), ("! now", None, []),
    ("water plants *weekly", None, [("*", "weekly")]), ("td gym *every monday", "task", [("*", "every")]), ("2*3 is six", None, []),
    ("*important* note", None, []),
    # a marker inside a word, with a value that would parse: rule 2's "at a token's start" is what keeps these text
    ("ping user@home later", None, []), ("abc#tag in code", None, []), ("solve x^y", None, []), ("foo*daily report", None, []),
    ("wow!10m left", None, []), ("a~30m wait", None, []),
]


def main():
    fails = []
    for line, kind, markers in CASES:
        got = parse(line)
        if got != (kind, sorted(markers)):
            fails.append((line, (kind, markers), got))
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "docs", "screens", "t1", "shorthand-cases.jsonl")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        for line, kind, markers in CASES:
            fh.write(json.dumps({"line": line, "kind": kind, "markers": markers}, ensure_ascii=False) + "\n")
    print("%d cases, %d failing" % (len(CASES), len(fails)))
    for f in fails:
        print("FAIL", f)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
