"""Writes docs/screens/t0/compare.html: the four source apps side by side on each T0 element
(palette, type, shapes, density, icons, navigation, dark mode, wording), from
docs/screens/t0/tokens.json and the screenshots in _screens-sources/ (gitignored; the page links them
relatively, so they show only on a machine that has them).

Contrast is computed here (WCAG 2.x relative luminance) from the token hex values; a value the
token file marks "computed" is a port of the app's own derivation and is shown with ~.

    python tools/screens/t0_compare.py
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "screens", "t0", "compare.html")
SHOTS = "../../../_screens-sources/"   # relative to OUT

tokens = json.load(open(os.path.join(ROOT, "docs", "screens", "t0", "tokens.json"), encoding="utf-8"))
apps = tokens["apps"]
FOLDER = {"Tendril": "tendril", "Chronicle": "chronicle", "Mnemo": "mnemo", "Equipoise": "equipoise"}

# What each app says when there is nothing yet, or when it asks something: the wording register.
# Read off the screenshots named beside each line.
WORDING = {
    "Tendril": [("Choose a page from the tree — or press Ctrl+K to find one.", "00-first-open"),
                ("Nothing unscheduled", "11-calendar-800px"),
                ("No key — nothing is sent anywhere", "04-settings"),
                ("Drag a task onto a day, or onto an hour. Drop a block here to clear its When.", "11-calendar-800px")],
    "Chronicle": [("Ready when you are. Add an activity with the + button, then tap play to start a timer.", "00-first-open"),
                  ("Add a tracker with the + button — a number, a yes/no, a rating, or a set of choices.", "01-Data-empty"),
                  ("No checklists yet — a resettable template list, like a morning routine.", "08-data-one-tracker"),
                  ("no time yet / no entries yet", "05-track-one-activity")],
    "Mnemo": [("Nothing in Ease. Tap + to add one.", "01-home-empty"),
              ("Keep reminders reliable", "00-first-open"),
              ("Notifications are on. Mnemo can alert you when a reminder is due.", "02-settings"),
              ("Colours, corner shapes and lettering for the app itself …", "03-settings-theme")],
    "Equipoise": [("How are you right now?", "01-checkin"),
                  ("Nothing to fix right now. This looks like a state worth staying in. Come back when it shifts.", "03-after-checkin"),
                  ("How much of today was masking?", "04-ledger"),
                  ("Everything lives on this phone.", "05-settings")],
}

# Screens that exist in no capture, so nobody reads the sheet as complete.
OMISSIONS = [
    "Tendril's phone layout (bottom bar below 840dp): the desktop window will not size below about 800 px and Tendril's Android build was not installed; the bar is described from ShellLayout.kt only.",
    "Typed text in a Tendril page: keystrokes sent to the window do not reach Compose's text field, so 08-page-blocks shows an empty block.",
    "Light theme on Mnemo and Equipoise: the phone runs in dark mode and neither app has its own light setting; Chronicle and Tendril were captured in both.",
    "Populated screens beyond one activity, one tracker reading, one reminder (January 2027) and one check-in.",
    "Every non-default palette of Tendril (10 registers) and Chronicle (6 palettes) as live screens: they are named on the settings captures, and only the default's values are in the token rows.",
]


def hexes(value):
    m = re.search(r"#([0-9A-Fa-f]{6})", str(value))
    return ("#" + m.group(1).upper()) if m else None


def lum(hx):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hx[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


PAIRS = [("onSurface", "background", 4.5), ("onSurfaceVariant", "background", 4.5),
         ("primary", "background", 3.0), ("onPrimary", "primary", 4.5), ("outline", "background", 3.0)]


def esc(s):
    return html.escape(str(s))


def swatches(colors):
    out = []
    for role in ("background", "surface", "onSurface", "onSurfaceVariant", "primary", "onPrimary", "outline", "error"):
        v = colors.get(role)
        hx = hexes(v)
        approx = "~" if "computed" in str(v) else ""
        if hx:
            out.append('<span class="sw"><i style="background:%s"></i>%s <code>%s%s</code></span>' % (hx, role, approx, hx))
        else:
            out.append('<span class="sw none">%s: %s</span>' % (role, esc(v)))
    return "".join(out)


def contrast(colors):
    rows = []
    for fg, bg, need in PAIRS:
        a, b = hexes(colors.get(fg)), hexes(colors.get(bg))
        if not (a and b):
            rows.append("<li>%s on %s: not set</li>" % (fg, bg))
            continue
        r = ratio(a, b)
        approx = "~" if "computed" in str(colors.get(fg)) + str(colors.get(bg)) else ""
        cls = "ok" if r >= need else "low"
        rows.append('<li class="%s">%s on %s: %s%.1f:1 <small>(needs %.1f)</small></li>' % (cls, fg, bg, approx, r, need))
    return "<ul class=c>%s</ul>" % "".join(rows)


def fonts(a):
    return "<br>".join("%s <small>%s</small>" % (esc(f["family"]), esc(f.get("weights", ""))) for f in a["fonts"])


def shapes(a):
    s = a.get("shapes_dp")
    if isinstance(s, dict):
        return "<br>".join("%s: %s" % (esc(k), esc(v)) for k, v in s.items() if not k.startswith("_"))
    return esc(s)


def gallery(app):
    folder = os.path.join(ROOT, "_screens-sources", FOLDER[app])
    names = sorted(f for f in os.listdir(folder) if f.endswith(".png")) if os.path.isdir(folder) else []
    return "".join('<a href="%s%s/%s"><img loading=lazy src="%s%s/%s" alt="%s"><span>%s</span></a>'
                   % (SHOTS, FOLDER[app], n, SHOTS, FOLDER[app], n, esc(n), esc(n[:-4])) for n in names)


def row(title, cell):
    return "<tr><th>%s</th>%s</tr>" % (title, "".join("<td>%s</td>" % cell(a) for a in apps))


nav = lambda a: "%s<br><b>%s</b><br><small>breakpoint: %s</small>" % (
    esc(a["navigation"]["pattern"]), " · ".join(esc(d) for d in a["navigation"]["destinations"]),
    esc(a["navigation"].get("breakpoint_dp")))
table = "".join([
    row("Default", lambda a: "<b>%s</b><br><small>%d variants: %s</small>" % (
        esc(a["default_variant"]), len(a.get("variants", [])), esc(", ".join(map(str, a.get("variants", [])))))),
    row("Palette, light", lambda a: swatches(a["colors"]["light"])),
    row("Contrast, light", lambda a: contrast(a["colors"]["light"])),
    row("Palette, dark", lambda a: swatches(a["colors"]["dark"])),
    row("Contrast, dark", lambda a: contrast(a["colors"]["dark"])),
    row("Dark mode", lambda a: esc(a["dark_mode"])),
    row("Type", fonts),
    row("Shapes (dp)", shapes),
    row("Density", lambda a: esc(json.dumps(a["density"], ensure_ascii=False))[:600]),
    row("Icons", lambda a: esc(a["icons"])),
    row("Navigation", nav),
    row("Wording", lambda a: "<ul>%s</ul>" % "".join(
        '<li>“%s” <small>%s</small></li>' % (esc(t), esc(s)) for t, s in WORDING[a["app"]])),
])

page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Factotum T0 comparison</title>
<style>
:root{--bg:#fbfaf8;--fg:#1d1d1b;--dim:#5f5f5a;--line:#dedbd5;--ok:#2f6b3a;--low:#a3341f;--card:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#18191b;--fg:#e8e6e1;--dim:#a8a59e;--line:#34353a;--ok:#8fcf98;--low:#f0a08f;--card:#202125}}
body{margin:0;padding:24px 16px;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 8px}p,li{max-width:80ch}small,.dim{color:var(--dim)}
.wrap{overflow-x:auto}table{border-collapse:collapse;min-width:960px;width:100%%}
th,td{border-top:1px solid var(--line);padding:10px 8px;vertical-align:top;text-align:left}
thead th{position:sticky;top:0;background:var(--bg)}tbody th{width:110px;color:var(--dim);font-weight:600}
.sw{display:flex;align-items:center;gap:6px;font-size:13px}.sw i{width:18px;height:18px;border-radius:4px;border:1px solid var(--line);flex:none}
.sw.none{color:var(--dim)}code{font-size:12px}ul{margin:0;padding-left:18px}.c{list-style:none;padding:0;font-size:13px}
.ok{color:var(--ok)}.low{color:var(--low);font-weight:600}
.gal{display:flex;gap:10px;overflow-x:auto;padding-bottom:8px}.gal a{flex:none;text-decoration:none;color:var(--dim);font-size:12px;text-align:center}
.gal img{display:block;height:300px;border:1px solid var(--line);border-radius:6px;background:var(--card)}
</style></head><body>
<h1>Factotum T0: the four apps, element by element</h1>
<p class=dim>For the owner's per-element choice (decision 2026-10-05). Tokens: <code>docs/screens/t0/tokens.json</code>, every value with a file:line there; ~ marks a colour the token file worked out by porting the app's own derivation, not one copied from source. Contrast is WCAG 2 relative luminance, computed by <code>tools/screens/t0_compare.py</code>. Screenshots are debug builds on empty or seed data, kept out of git in <code>_screens-sources/</code>.</p>
<div class=wrap><table><thead><tr><th></th>%s</tr></thead><tbody>%s</tbody></table></div>
<h2>Screenshots</h2>%s
<h2>Not shown on this sheet</h2><ul>%s</ul>
</body></html>
""" % ("".join("<th>%s</th>" % esc(a["app"]) for a in apps), table,
       "".join("<h3>%s</h3><div class=gal>%s</div>" % (esc(a["app"]), gallery(a["app"])) for a in apps),
       "".join("<li>%s</li>" % esc(o) for o in OMISSIONS))

with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(page)
print(OUT)
