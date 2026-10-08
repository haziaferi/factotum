"""When sheet: how a repeat's start date is changed (owner, 2026-10-08: "I don't know how to change it if it doesn't
show"; score all three).

  next    the readout's first Next date is a control: tapping it opens the month; once moved, "starting [date]" reads in
          the sentence
  row     a "Starting [date]" row in the interval's chooser
  always  "starting [date]" is always a word of the sentence

The prototype itself (docs/screens/t1/when-prototype.html) is measured: a script set each state, then
screen_score's render and hit-tested measure run on it, the phone alone at 360 x 740.
States: the sheet as ⋯ › Repeat opens it (the interval's chooser open), and closed on the default weekly rule.
Measures
  actions_open    taps to move the start from the opening state (the start control, then a day)
  actions_closed  the same from the closed sentence (a chooser to open first where the control is not drawn)
  seen_open, seen_closed   whether the start control is drawn and hit-testable in that state
  lines           the sentence's lines when closed (height spent on every rule)
  foot            the foot's height (sentence, cron and Undo row, readout), px
  clutter_open, clutter_closed   edge density, light and dark averaged
  controls        hit-testable controls in the sheet, closed

    PYTHONUTF8=1 python tools/screens/when_start_opt.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import screen_score as ss  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
PAGE = os.path.join(ROOT, "docs", "screens", "t1", "when-prototype.html")
OUT = os.path.join(ROOT, "docs", "screens", "t1", "when-start.json")
ONLY_PHONE = ("<style>body{padding:0!important}h1,.dim,.side{display:none!important}.wrap{display:block}"
              ".phone{border-radius:0;box-shadow:none}</style>")


def doc(variant, state, theme="light"):
    html = open(PAGE, encoding="utf-8").read()
    setup = ("S.v.start='%s';openFrom('repeat');%s"
             "document.getElementById('sheet').setAttribute('data-picker','1');"
             "document.documentElement.dataset.theme='%s';") % (variant, "S.open=null;render(true);" if state == "closed" else "", theme)
    return html.replace("</head>", ONLY_PHONE + "</head>").replace("</body>", "<script>%s</script></body>" % setup)


def measure(variant, state):
    m = ss.measure(doc(variant, state), 360, 740)
    taps = {t["name"]: t for t in m["taps"]}
    seen = bool(taps.get("Tok start", {}).get("seen")) or any(n.startswith("Chip ") and n[5:8] in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun") and t.get("seen") for n, t in taps.items())
    clutter = sum(ss.edge_density(ss.render(doc(variant, state, th), 360, 740)) for th in ("light", "dark")) / 2
    return m, seen, round(clutter, 4)


def lines_and_foot(variant):
    """The sentence's lines and the foot's height, read from the rendered page with a probe script."""
    probe = ("<script>(function(){var s=document.querySelector('.sent'),f=document.querySelector('.foot');"
             "document.body.insertAdjacentHTML('beforeend','<pre id=\"__pro'+'be\">'+JSON.stringify({lines:Math.round(s.getBoundingClientRect().height/48),"
             "foot:Math.round(f.getBoundingClientRect().height)})+'</pre>')})()</script>")
    d = doc(variant, "closed").replace("</body>", probe + "</body>")
    res = ss._edge(["--dump-dom"], True, "probe-" + variant + str(abs(hash(d)) % 10 ** 8), d, 660, 1040)
    import re
    return json.loads(re.search(r'<pre id="__probe">(.*?)</pre>', res.stdout, re.S).group(1).replace("&quot;", '"'))


def main():
    rows = []
    for v in ("next", "row", "always"):
        mo, seen_o, c_o = measure(v, "open")
        mc, seen_c, c_c = measure(v, "closed")
        lf = lines_and_foot(v)
        controls = len([t for t in mc["taps"] if t.get("seen")])
        rows.append({"variant": v, "seen_open": seen_o, "seen_closed": seen_c, "actions_open": 2 if seen_o else 3, "actions_closed": 2 if seen_c else 3,
                     "lines": lf["lines"], "foot": lf["foot"], "clutter_open": c_o, "clutter_closed": c_c, "controls": controls})
        print(rows[-1], flush=True)
    with open(OUT, "w", encoding="utf-8", newline=chr(10)) as fh:
        json.dump(rows, fh, indent=1)


if __name__ == "__main__":
    main()
