"""Shared mockup parts for the screen tiers (decision 15, "every screen, one at a time, before colour").

Greys only, with depth coding: tonal surfaces instead of rules, inactive navigation receded
(nav_glance's 'depth' coding, which cut measured clutter by about 40%). Module identity comes from labels
and glyphs, never hue. Type and icons are placeholders until Q5 and Q8 are scored.

Owner's frame (2026-10-07): the bar is Today · Calendar · Hub · Pages · [slot 5: check-in by default];
the Hub is a hexagon on a tonal circle, always on. User data is wrapped in a dotted outline (`ud()`), so
sample content is never mistaken for interface; the scorer hides that outline before it measures.

Elements a finger can hit carry data-tap; text the scorer must read carries its real size. Both are
measured from the rendered page by screen_score.py, never assumed here.
"""
import html
import math

e = html.escape

# ---- tokens -----------------------------------------------------------------------------------------------
GREYS = {
    "light": {"bg": "#F4F4F2", "zone": "#FBFBF9", "zone2": "#EBEBE7", "ink": "#1C1C1A", "dim": "#60605B"},
    "dark": {"bg": "#121315", "zone": "#1C1D1F", "zone2": "#26272A", "ink": "#E6E5E1", "dim": "#9C9A94"},
    "oled": {"bg": "#000000", "zone": "#0E0E0F", "zone2": "#18191A", "ink": "#DCDBD7", "dim": "#93918B"},
}
THEMES = list(GREYS)


def theme_css():
    blocks = []
    for t, g in GREYS.items():
        sel = ":root,[data-theme=light]" if t == "light" else "[data-theme=%s]" % t
        blocks.append("%s{%s}" % (sel, ";".join("--%s:%s" % kv for kv in g.items())))
    return "\n".join(blocks)


BASE_CSS = """
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,"Segoe UI",sans-serif}
.ud{outline:1.5px dotted var(--dim);outline-offset:2px;border-radius:4px}
.score .ud{outline:none}
/* phone */
.phone{position:relative;width:360px;height:740px;border-radius:22px;background:var(--bg);display:flex;flex-direction:column;overflow:hidden;flex:none;box-shadow:0 0 0 1px var(--zone2)}
.score .phone{border-radius:0;box-shadow:none}
.hdr{height:56px;display:flex;align-items:center;gap:4px;padding:0 4px 0 16px;flex:none}
.hdr .ttl{flex:1;font-size:18px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ib{width:48px;height:48px;display:grid;place-items:center;border-radius:999px;color:var(--dim);font-size:18px;flex:none}
.body{flex:1;overflow:hidden;padding:4px 12px 12px;display:flex;flex-direction:column;gap:8px}
.zone{background:var(--zone);border-radius:14px;padding:6px 12px}
.zone h4{margin:6px 0 2px;font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--dim);font-weight:600}
.row{display:flex;align-items:center;gap:12px;min-height:48px}
.row .t{flex:1;min-width:0;font-size:15px}
.row .tm{width:44px;color:var(--dim);font-size:13px;flex:none}
/* the circle is 22 px; its hit area is the full 48 px (screen_score caught the 22 px target) */
.ck{width:48px;height:48px;margin:0 -13px;display:grid;place-items:center;flex:none}.ck::before{content:"";width:22px;height:22px;border:2px solid var(--dim);border-radius:50%}
.cap{display:flex;align-items:center;gap:10px;background:var(--zone2);border-radius:14px;min-height:48px;padding:0 14px;color:var(--dim);font-size:15px}
/* bar */
.bar{height:72px;display:flex;background:var(--zone2);flex:none;padding:4px 0 8px}
/* inactive items recede by colour (dim, >= 4.5:1 on the bar), never by opacity: opacity .65 left labels at 2.4:1 (T1.1 critique) */
.bar .s{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;font-size:12px;color:var(--dim)}
.bar .s i{font-style:normal;font-size:18px;width:56px;height:30px;display:grid;place-items:center;border-radius:999px}
.bar .s.on{opacity:1;color:var(--ink);font-weight:600}.bar .s.on i{background:var(--zone)}
.bar .s.hub{opacity:1;color:var(--ink)}.bar .s.hub i{background:var(--zone);box-shadow:inset 0 0 0 1px var(--dim)}
/* desktop */
.desk{position:relative;width:1100px;height:660px;border-radius:10px;display:flex;overflow:hidden;background:var(--bg);flex:none;box-shadow:0 0 0 1px var(--zone2)}
.score .desk{border-radius:0;box-shadow:none}
.rail{width:88px;display:flex;flex-direction:column;align-items:center;padding:10px 0;gap:4px;background:var(--zone2);flex:none}
.rail .s{width:76px;min-height:56px;border-radius:12px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:12px;color:var(--dim)}
.rail .s i{font-style:normal;font-size:18px}.rail .s.on{opacity:1;color:var(--ink);font-weight:600;background:var(--zone)}
.rail .s.hub{opacity:1;color:var(--ink)}.rail .s.hub i{display:grid;place-items:center;width:44px;height:30px;border-radius:999px;background:var(--zone);box-shadow:inset 0 0 0 1px var(--dim)}
.rail .sp{flex:1}.kbd{font:11px ui-monospace,monospace;color:var(--dim)}
.dmain{flex:1;display:flex;flex-direction:column;min-width:0}
.dcols{flex:1;display:grid;grid-template-columns:380px 1fr;gap:16px;padding:4px 16px 16px;overflow:hidden}
.dcol{display:flex;flex-direction:column;gap:8px;min-width:0;overflow:hidden}
.page{background:var(--zone);border-radius:14px;padding:18px 28px;overflow:hidden}
.page h3{font-size:22px;margin:4px 0 10px}
.srch{display:flex;align-items:center;gap:10px;background:var(--zone2);border-radius:999px;height:40px;padding:0 16px;color:var(--dim);font-size:14px}
"""

# ---- glyphs -----------------------------------------------------------------------------------------------
def hub_svg(size=20):
    pts = " ".join("%.2f,%.2f" % (12 + 9 * math.cos(math.radians(a - 90)), 12 + 9 * math.sin(math.radians(a - 90)))
                   for a in range(0, 360, 60))
    return ('<svg viewBox="0 0 24 24" width="%d" height="%d" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linejoin="round"><polygon points="%s"/><circle cx="12" cy="12" r="2.4" fill="currentColor"/></svg>') % (size, size, pts)


BAR = [("◷", "Today"), ("▦", "Calendar"), ("HUB", "Hub"), ("☰", "Pages"), ("◎", "check-in")]
RAIL = [("◷", "Today"), ("▦", "Calendar"), ("HUB", "Hub"), ("☰", "Pages"), ("◎", "check-in")]


def bar(on="Today", items=BAR):
    cells = []
    for glyph, label in items:
        cls = "s" + (" on" if label == on else "") + (" hub" if glyph == "HUB" else "")
        g = hub_svg() if glyph == "HUB" else glyph
        cells.append('<div class="%s" data-tap="%s"><i>%s</i>%s</div>' % (cls, e(label), g, e(label)))
    return '<div class="bar">%s</div>' % "".join(cells)


def rail(on="Today", items=RAIL):
    cells = []
    for i, (glyph, label) in enumerate(items):
        cls = "s" + (" on" if label == on else "") + (" hub" if glyph == "HUB" else "")
        g = hub_svg() if glyph == "HUB" else glyph
        cells.append('<div class="%s" data-tap="%s"><i>%s</i>%s<span class="kbd">Ctrl+%d</span></div>' % (cls, e(label), g, e(label), i + 1))
    return '<div class="rail">%s<div class="sp"></div><div class="s" data-tap="Settings"><i>⚙</i>Settings</div></div>' % "".join(cells)


# ---- parts ------------------------------------------------------------------------------------------------
def ud(content, tag="span"):
    """User data: sample content the person would have typed, drawn inside a dotted outline."""
    return '<%s class="ud">%s</%s>' % (tag, content, tag)


def icon_button(glyph, name):
    return '<span class="ib" data-tap="%s" aria-label="%s">%s</span>' % (e(name), e(name), glyph)


def header(title, buttons=(("⌕", "Search"),), lead=None):
    left = icon_button(*lead) if lead else ""
    return '<div class="hdr">%s<span class="ttl">%s</span>%s</div>' % (left, title, "".join(icon_button(*b) for b in buttons))


def row(title, time="", check=True):
    tm = '<span class="tm">%s</span>' % e(time) if time else ""
    ck = '<span class="ck" data-tap="Finish"></span>' if check else ""
    return '<div class="row" data-tap="Open item">%s%s<span class="t">%s</span></div>' % (tm, ck, ud(e(title)))


def zone(title, inner):
    return '<div class="zone"><h4>%s</h4>%s</div>' % (e(title), inner)


def phone(head, body, bottom):
    return '<div class="phone">%s<div class="body">%s</div>%s</div>' % (head, body, bottom)


def desk(rail_html, head, cols):
    return '<div class="desk">%s<div class="dmain">%s<div class="dcols">%s</div></div></div>' % (rail_html, head, cols)


# A Today screen with title-only rows (decision 17), used as the content behind chrome options.
AGENDA = [("Dentist", "09:00", False), ("Pay the fine", "", True), ("Call the bank", "15:00", False), ("Return library books", "", True)]
ROUTINES = ["Walk", "Water", "Morning routine", "Sleep reading"]


def today_body(capture=True):
    parts = ['<div class="cap" data-tap="Capture">+ <span>Add…</span></div>'] if capture else []
    parts.append(zone("Agenda", "".join(row(t, tm, ck) for t, tm, ck in AGENDA)))
    parts.append(zone("Routines", "".join(row(t, check=False) for t in ROUTINES)))  # habits are Logged, not finished: rows come in T1.2
    return "".join(parts)


def document(body, theme="light", extra_css="", score=False):
    return ('<!doctype html><html lang="en" data-theme="%s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>%s\n%s\n%s</style></head>'
            '<body class="%s">%s</body></html>') % (theme, theme_css(), BASE_CSS, extra_css, "score" if score else "", body)
