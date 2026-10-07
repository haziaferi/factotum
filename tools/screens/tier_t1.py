"""T1 shared parts (decision 17), one screen at a time. Writes docs/screens/t1/screens.html and
docs/screens/t1/scores.md. Each screen has options, a control that must lose (exit 2 otherwise), states, the
phone and Windows, real copy, and measured scores beside real apps' numbers.

    PYTHONUTF8=1 python tools/screens/tier_t1.py
"""
import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402
import screen_score as ss  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "screens", "t1")
e = html.escape
TARGETS = ["Search", "Capture", "Hub", "Settings"]
REFERENCE_SCREENS = ["bearable/00-main.png", "daylio/00-main.png", "howwefeel/00-main.png", "loop/00-main.png",
                     "tasks-org/00-main.png", "ticktick/00-main.png", "anytype/space.png", "obsidian/00-main.png"]

# ---- T1.1 header and bar ----------------------------------------------------------------------------------
TITLE = "Today · Mon 5 Oct"  # the date is the app's, not user data: no dotted outline
APPROVED_BUTTONS = (("⌕", "Search"), ("⚙", "Settings"))  # T1.1 approved: A, with Settings right of Search (owner, 2026-10-07)
SYNC_LINE = '<div class="note">Can\'t reach the sync folder. Changes stay on this phone until it\'s back.</div>'
EXTRA = """
.note{margin:0 12px;padding:10px 14px;border-radius:12px;background:var(--zone2);font-size:13px;color:var(--ink)}
.hdr.bottom{background:var(--zone)}
.bigdate{font-size:26px;font-weight:600;margin:10px 4px 2px}
.srchbar{flex:1;margin:0 8px 0 0}
"""


def desk_today(title_html, extra_buttons=()):
    head = ('<div class="hdr"><span class="ttl">%s</span><span class="srch" data-tap="Search" style="width:320px">⌕ Search everything '
            '<span class="kbd">Ctrl+K</span></span>%s</div>') % (title_html, "".join(kit.icon_button(*b) for b in extra_buttons))
    page = ('<div class="page"><div class="kbd">Pages › ' + kit.ud("Garden plan") + '</div><h3>' + kit.ud("Garden plan") +
            '</h3><p>' + kit.ud("Raised beds go along the south fence.") + '</p></div>')
    return kit.desk(kit.rail("Today"), head, '<div class="dcol">%s</div>%s' % (kit.today_body(), page))


OPTIONS_T11 = [
    {"id": "A", "name": "Quiet header", "how": "direct",
     "about": "The title, then one Search button. Everything else lives in the bar, or in the Hub (Settings is a card there).",
     "phone": lambda: kit.phone(kit.header(TITLE, (("⌕", "Search"),)), kit.today_body(), kit.bar("Today")),
     "desk": lambda: desk_today(TITLE), "declared": {"Settings": 2}},
    {"id": "A′", "name": "Approved: quiet header with Settings", "how": "approved",
     "about": "The owner's choice (2026-10-07): option A, with a Settings button right of Search.",
     "phone": lambda: kit.phone(kit.header(TITLE, APPROVED_BUTTONS), kit.today_body(), kit.bar("Today")),
     "desk": lambda: desk_today(TITLE), "declared": {}},
    {"id": "B", "name": "Search field as the header", "how": "direct",
     "about": "The header is the search field itself. Tapping it opens the keyboard. The date moves into the page as a large title.",
     "phone": lambda: kit.phone('<div class="hdr"><span class="cap srchbar" data-tap="Search">⌕ Search</span></div>',
                                '<div class="bigdate">%s</div>' % TITLE + kit.today_body(), kit.bar("Today")),
     "desk": lambda: desk_today(TITLE), "declared": {"Settings": 2}},
    {"id": "C", "name": "Header at the thumb (oblique: Peripheral Glance)", "how": "oblique",
     "about": "The header strip sits just above the bar, where the thumb already is, as Safari's address bar does. The top of the screen holds only content.",
     "phone": lambda: kit.phone("", kit.today_body() + '<div style="flex:1"></div>',
                                kit.header(TITLE, (("⌕", "Search"),)).replace('class="hdr"', 'class="hdr bottom"') + kit.bar("Today")),
     "desk": lambda: desk_today(TITLE), "declared": {"Settings": 2}},
    {"id": "X", "name": "Control: a busy header", "how": "control",
     "about": "Search, filter, sort, notifications and a profile in the header, plus a floating + button. It must lose.",
     "phone": lambda: kit.phone(kit.header(TITLE, (("⌕", "Search"), ("⚲", "Filter"), ("⇅", "Sort"), ("🔔", "Notifications"), ("◐", "Profile"))),
                                kit.today_body() + '<span class="ib" data-tap="Capture" style="position:absolute;right:16px;bottom:88px;background:var(--ink);color:var(--bg);width:56px;height:56px;font-size:26px">+</span>',
                                kit.bar("Today").replace('opacity:.65', '')),
     "desk": lambda: desk_today(TITLE, (("⚲", "Filter"), ("⇅", "Sort"), ("🔔", "Notifications"), ("◐", "Profile"))), "declared": {"Settings": 2}},
]
# X's receded bar items are made full strength on purpose: the control ignores depth coding.
CONTROL_CSS = ".bar .s{opacity:1;color:var(--ink)}"

STATES_T11 = [
    ("Normal", lambda: kit.phone(kit.header(TITLE, APPROVED_BUTTONS), kit.today_body(), kit.bar("Today"))),
    ("Hub open (the centre slot active)", lambda: kit.phone(kit.header(TITLE, APPROVED_BUTTONS), kit.today_body(),
                                                            kit.bar("Hub").replace('class="s hub"', 'class="s on hub"'))),
    ("Slot 5 re-pinned to the ledger", lambda: kit.phone(kit.header(TITLE, APPROVED_BUTTONS), kit.today_body(),
                                                       kit.bar("Today", kit.BAR[:4] + [("◇", "Ledger")]))),
    ("Long title", lambda: kit.phone(kit.header("Pages · " + kit.ud("Garden plan for the allotment, spring and summer"), (("⌕", "Search"), ("⋯", "More"))),
                                     kit.today_body(), kit.bar("Pages"))),
    ("Error: sync folder unreachable", lambda: kit.phone(kit.header(TITLE, APPROVED_BUTTONS), SYNC_LINE + kit.today_body(), kit.bar("Today"))),
]


def make(fn, css=""):
    return lambda theme, score: kit.document(fn(), theme, EXTRA + css, score)


def score_screen(options):
    rows = []
    for o in options:
        css = CONTROL_CSS if o["how"] == "control" else ""
        r = ss.score_option(make(o["phone"], css), 360, 740, TARGETS, o["declared"])
        rd = ss.score_option(make(o["desk"], css), 1100, 660, TARGETS, o["declared"])
        r["desk_clutter"] = rd["clutter"]
        r["small"] = len(r["small_taps"]) + len(rd["small_taps"])
        r["faint_n"] = len(r["faint"]) + len(rd["faint"])
        r["min_text_short"] = max(0, 14 - r["min_text"])  # px below a 14 px floor
        r["steps_sum"] = sum(v[0] for v in r["steps"].values())
        rows.append(r)
    low = ("clutter", "desk_clutter", "strong_nav", "far_nav", "faint_n", "small", "min_text_short", "steps_sum")
    fr = ss.front(rows, low)
    return rows, fr, low


def frame(inner, theme_toggle=True):
    return inner


def section_t11(refs):
    rows, fr, low = score_screen(OPTIONS_T11)
    ctrl = [i for i, o in enumerate(OPTIONS_T11) if o["how"] == "control"]
    beaten = all(i not in fr for i in ctrl)
    head = "<tr><th>Option</th><th>Clutter (phone)</th><th>Clutter (Windows)</th><th>Strong nav items</th><th>Nav in the top quarter</th><th>Faint labels</th><th>Taps under 48 dp</th><th>Smallest text</th><th>Steps to Search · Capture · Hub · Settings</th><th></th></tr>"
    body = ""
    for o, r, i in zip(OPTIONS_T11, rows, range(len(rows))):
        steps = " · ".join("%s%s" % (v[0], "*" if v[1] == "declared" else "") for v in r["steps"].values())
        tag = "control" if o["how"] == "control" else ("front" if i in fr else "dominated")
        body += "<tr><td><b>%s</b> %s</td><td>%.3f</td><td>%.3f</td><td>%d</td><td>%d</td><td>%d</td><td>%s</td><td>%g px</td><td>%s</td><td>%s</td></tr>" % (
            o["id"], e(o["name"]), r["clutter"], r["desk_clutter"], r["strong_nav"], r["far_nav"], r["faint_n"], e(", ".join(r["small_taps"]) or "none"), r["min_text"], steps, tag)
    refrow = " · ".join("%s %.3f" % (k.split("/")[0], v) for k, v in refs.items())
    opts = "".join('<div class="opt"><h3>%s · %s <span class="tag">%s</span></h3><p class="dim">%s</p><div class="pair">%s<div class="dwrap">%s</div></div></div>' % (
        o["id"], e(o["name"]), o["how"], e(o["about"]), o["phone"](), o["desk"]()) for o in OPTIONS_T11)
    states = "".join('<div><div class="cap2">%s</div>%s</div>' % (e(n), f()) for n, f in STATES_T11)
    refimgs = "".join('<figure><img src="../../../_screens-sources/reference/%s" alt=""><figcaption>%s · %.3f</figcaption></figure>' % (k, k.split("/")[0], v) for k, v in refs.items())
    html_ = ('<section id="t1-1"><h2>T1.1 Header and bar <span class="tag">approved 2026-10-07: A′</span></h2>'
             '<p>The chrome every screen shares: the header (title, Search) and the bar of Today · Calendar · Hub · Pages · [check-in]. '
             'Data the person would type is in a <span class="ud">dotted outline</span>. Steps marked * go through the Hub.</p>'
             '<h3>Scores</h3><table>%s%s</table><p class="dim">Clutter of the real apps\' main screens, measured the same way: %s. '
             'Lower is calmer. %s</p>'
             '<h3>Options</h3>%s<h3>States (approved: A′)</h3><div class="states">%s</div>'
             '<details><summary>Real apps compared (local screenshots, not in the public repo)</summary><div class="refs">%s</div></details></section>') % (
        head, body, refrow, "The control loses, as it must." if beaten else "<b>The control is on the front: the measures are not discriminating.</b>",
        opts, states, refimgs)
    return html_, rows, fr, beaten


PAGE_CSS = """
body{padding:20px 16px 48px}h1{font-size:21px;margin:0 0 4px}h2{font-size:18px;margin:28px 0 6px}h3{font-size:15px;margin:18px 0 6px}
p{max-width:95ch}.dim{color:var(--dim)}
table{border-collapse:collapse;font-size:13px}td,th{padding:5px 10px;text-align:left;border-top:1px solid var(--zone2);vertical-align:top}th{color:var(--dim);font-weight:600}
.opt{background:var(--zone);border-radius:16px;padding:12px 16px;margin:12px 0}
.opt .phone,.states .phone{box-shadow:0 0 0 1px var(--zone2)}
.pair{display:flex;gap:16px;align-items:flex-start;overflow-x:auto;padding-bottom:6px}.dwrap{flex:none}
.tag{font-size:11px;font-weight:500;padding:2px 8px;border-radius:999px;background:var(--zone2);color:var(--dim)}
.states{display:flex;gap:16px;overflow-x:auto;padding-bottom:6px}.cap2{font-size:12px;color:var(--dim);margin:0 0 6px;max-width:360px}
.refs{display:flex;gap:12px;flex-wrap:wrap}.refs img{width:180px;border-radius:12px}figure{margin:0}figcaption{font-size:12px;color:var(--dim)}
.sw{display:flex;gap:6px;margin:10px 0}.sw button{font:inherit;color:var(--ink);background:var(--zone);border:1px solid var(--zone2);border-radius:999px;padding:4px 14px;cursor:pointer}
"""


def main():
    os.makedirs(OUT, exist_ok=True)
    refs = ss.reference_clutter(REFERENCE_SCREENS)
    s11, rows, fr, beaten = section_t11(refs)
    page = ['<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>Factotum T1 shared parts</title><style>%s\n%s\n%s\n%s</style></head><body>' % (kit.theme_css(), kit.BASE_CSS, EXTRA, PAGE_CSS),
            '<h1>T1 · Shared parts</h1><p class="dim">Decision 17. Greys only; colour comes after every screen is settled. '
            'Type and icons are placeholders. One screen at a time: each waits for the owner\'s approval.</p>',
            '<div class="sw"><button onclick="document.documentElement.dataset.theme=\'light\'">Light</button>'
            '<button onclick="document.documentElement.dataset.theme=\'dark\'">Dark</button><button onclick="document.documentElement.dataset.theme=\'oled\'">OLED</button></div>',
            s11, "</body></html>"]
    with open(os.path.join(OUT, "screens.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(page))
    md = ["# T1 scores", "", "Generated by `tools/screens/tier_t1.py`.", "", "## T1.1 Header and bar", "",
          "| Option | Clutter phone | Clutter Windows | Strong nav | Nav in top quarter | Faint labels | Taps < 48 dp | Smallest text | Steps (Search, Capture, Hub, Settings) | Status |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for o, r, i in zip(OPTIONS_T11, rows, range(len(rows))):
        md.append("| %s %s | %.3f | %.3f | %d | %d | %d | %s | %g px | %s | %s |" % (o["id"], o["name"], r["clutter"], r["desk_clutter"], r["strong_nav"], r["far_nav"], r["faint_n"],
                  ", ".join(r["small_taps"]) or "none", r["min_text"], " · ".join(str(v[0]) for v in r["steps"].values()),
                  "control" if o["how"] == "control" else ("front" if i in fr else "dominated")))
    md += ["", "Reference main screens: " + ", ".join("%s %.3f" % kv for kv in refs.items())]
    with open(os.path.join(OUT, "scores.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(md) + "\n")
    print("\n".join(md))
    if not beaten:
        sys.exit(2)


if __name__ == "__main__":
    main()
