"""The capture line's placeholder (owner, 2026-10-07): shorter options, scored. The text box always spans its full
width and stays one line high until typed text wraps, so a placeholder must fit one line beside ⋯ (a constraint,
measured from the render: the line's height with the placeholder against its one-line height).

  U  kinds     how many of the owner's most typed kinds it names (task, event, log; journal also counted)
     verb      starts with a verb: a prompt says what to do (ux-copy: verb-first actions)
     context   names what the screen it opens from will make (context sets the default kind, owner)
  C  chars, words: less text to read past
The hint line below already lists the shorthands, so naming kinds here repeats part of it; that is the trade.

    PYTHONUTF8=1 python tools/screens/placeholder_opt.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_v2 as v2  # noqa: E402
import kit  # noqa: E402
import legend_opt as L  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402

KINDS = ("task", "event", "log", "journal")
VERBS = ("add", "type", "write", "log", "start", "note", "capture")
# text, opened from (for the context-aware option), context-aware?
OPTIONS = [
    ("Add anything…", False), ("Type anything…", False), ("Add a task, event, log…", False), ("Task, event, log, journal…", False),
    ("Add a task or event…", False), ("What's next?", False),
    ("context", True),  # Today: "Add anything…"; Journal: "Write a line…"; a tracker: "Log water…"; Calendar: "Add an event…"
    ("Add a task, event, log or journal line…", False),  # the control: the current one, which wraps
]
CONTEXT = {"Today": "Add anything…", "Journal": "Write a line…", "Water tracker": "Log water…", "Calendar": "Add an event…"}


def doc(text):
    body = L.phone("both", "empty").replace("Add a task, event, log or journal line…", t.e(text))
    return kit.document(body, "light", t.EXTRA + t.T12_CSS + t.T13_CSS + L.CSS, True)


def measure(text):
    m = ss.measure(doc(text), 360, 740)
    return round(m["boxes"]["line"][3]), m["sheet_h"]


def main():
    one_line = measure("Add")[0]
    rows = []
    for text, ctx in OPTIONS:
        texts = list(CONTEXT.values()) if ctx else [text]
        hs = [measure(x) for x in texts]
        fits = all(h == one_line for h, _ in hs)
        words = [w.strip("…?,.'").lower() for x in texts for w in x.split()]
        r = {"text": " / ".join("%s: %s" % kv for kv in CONTEXT.items()) if ctx else text, "fits": fits,
             "kinds": len({k for k in KINDS if k in words}) if not ctx else 1, "verb": int(all(x.split()[0].lower() in VERBS for x in texts)),
             "context": int(ctx), "chars": max(len(x) for x in texts), "words": max(len(x.split()) for x in texts),
             "sheet": max(s for _, s in hs)}
        rows.append(r)
    ok = [r for r in rows if r["fits"]]
    axes = {"U": (("kinds", -1), ("verb", -1), ("context", -1)), "C": (("chars", 1), ("words", 1))}
    for a, parts in axes.items():
        rk = [v2.ranks(ok, k, s) for k, s in parts]
        for i, r in enumerate(ok):
            r[a] = sum(c[i] for c in rk)
    front = [r for r in ok if not any(all(o[a] <= r[a] for a in "UC") and any(o[a] < r[a] for a in "UC") for o in ok if o is not r)]
    for r in rows:
        print("%s %-75s fits %-5s kinds %d verb %d context %d chars %2d words %d sheet %d %s" % (
            "*" if r in front else " ", r["text"][:75], r["fits"], r["kinds"], r["verb"], r["context"], r["chars"], r["words"], r["sheet"],
            "U %.1f C %.1f" % (r["U"], r["C"]) if "U" in r else "(wraps: fails the one-line rule)"))
    with open(os.path.join(v2.OUT, "placeholder-opt.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"rows": rows, "front": [r["text"] for r in front], "one_line_px": one_line}, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
