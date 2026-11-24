"""Opening the full form from the capture sheet (owner, 2026-10-07): which list shape, scored on harmony, ease of
use and clutter, over all ten kinds and over the owner's three most used (task, event, tracker log), to compare.

Shapes, from the phone captures (_screens-sources/capture, gitignored):
  todoist   a pop-over anchored at the chip row's left, above the sheet (Todoist's + list: icon and label rows)
  ticktick  a pop-over anchored at the row's right, above ⋯ (TickTick's ⋯ list)
  anydo     an inline list that grows the sheet upward, the line and keyboard staying (Any.do's # and group lists)
  page      the control: a separate full-page form (Tasks.org), every field a row; it must lose
The typed line while the list is open (owner: score each):
  linked    the line as typed, with its chips
  title     the parse applied: the line keeps only the title, and the values move into the list's rows
  underline the parsed words underlined in the line, no chips
  highlight the parsed words highlighted, no chips
Each list holds the kind's fields with their current values (SPEC R46 to R106, and the ledger, R137), then Kind and Templates,
which ⋯ also carries (owner: ⋯ replaces Details).

Measures (all from the render, as capture_v2):
  H  heights (distinct drawn heights of controls and rows), edges (distinct left edges of text), sprawl (craftkit ui)
  U  hick (log2(rows + 1): Hick-Hyman choice time grows with the options shown), reach (mean Fitts' ID from the
     keyboard's centre to the rows), unseen (rows not wholly on screen), line_hidden (the typed line covered),
     taps (taps to change one field: open + row, or one on the page after opening it)
  C  clutter (edge density, light theme), covered (share of the screen the list hides), rows

    PYTHONUTF8=1 python tools/screens/form_opt.py
"""
import itertools
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_v2 as v2  # noqa: E402
import kit  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402

KINDS = {  # key: (kind label, typed line, parsed words, fields (name, value))
    "task": ("Task", "Call mum fri", ["fri"], [("Date", "Fri 9 Oct"), ("Time", "None"), ("Repeat", "Never"), ("Reminder", "None"), ("Label", "None"),
                                                ("Subtasks", "None"), ("Notes", "Empty"), ("Page", "None")]),
    "event": ("Event", "Dentist tomorrow 9am every 6 months", ["tomorrow 9am", "every 6 months"],
              [("Date", "Tue 6 Oct"), ("Time", "09:00 to 09:45"), ("Repeat", "Every 6 months"), ("Reminder", "10 min before"),
               ("Calendar", "Personal"), ("Label", "None"), ("Notes", "Empty")]),
    "reminder": ("Reminder", "Remind me to take meds at 21", ["at 21"], [("Date", "Today"), ("Time", "21:00"), ("Alert", "Notification"),
                                                                         ("Repeat", "Never"), ("Nag", "Off"), ("Sound", "Default")]),
    "log": ("Log", "water 2", ["water", "2"], [("Tracker", "Water"), ("Value", "2 glasses"), ("Time", "Now"), ("Note", "Empty")]),
    "habit": ("Log", "walked 30 min", ["walked", "30 min"], [("Habit", "Walk"), ("Amount", "30 min"), ("Time", "Now"), ("Note", "Empty")]),
    "journal": ("Journal", "slept badly, calmer after the walk", [], [("Day", "Today"), ("Label", "None")]),
    "timer": ("Timer", "start reading", ["start", "reading"], [("Activity", "Reading"), ("Starts", "Now"), ("Label", "None")]),
    "timelog": ("Time", "read 30 min", ["read", "30 min"], [("Activity", "Reading"), ("Duration", "30 min"), ("Ended", "Now"), ("Comment", "Empty")]),
    "checkin": ("Check-in", "energy 2", ["energy 2"], [("Mood", "Not set"), ("Energy", "2 of 5"), ("Pleasantness", "Not set"), ("About", "Today"),
                                                       ("Note", "Empty")]),
    "ledger": ("Ledger", "masking high", ["masking high"], [("Masking effort", "High"), ("Masking social", "Not set"), ("Masking recovery", "Not set"),
                                                            ("Sensory", "Not set"), ("Day", "Today")]),
}
TOP3 = ["task", "event", "log"]
SPACE = {"shape": ["todoist", "ticktick", "anydo", "short"], "line": ["linked", "title", "underline", "highlight"]}
H = 32
CSS = v2.CSS + """
.c2 .ul{text-decoration:underline;text-decoration-thickness:1.5px;text-underline-offset:3px}
.c2 .hl{background:var(--zone2);border-radius:4px;padding:0 2px}
.pop{position:absolute;bottom:100%;margin-bottom:6px;width:260px;background:var(--zone);border-radius:14px;box-shadow:0 8px 28px rgba(0,0,0,.22);padding:4px 0;max-height:430px;overflow:hidden}
.pop.l{left:12px}.pop.r{right:12px}
.fr{min-height:48px;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:0 14px;font-size:14px}
.fr .fv{color:var(--dim);font-size:13px;white-space:nowrap}
.inl{max-height:330px;overflow:hidden;border-bottom:1px solid var(--zone2);margin:0 -12px 4px}
.pageform .fr{border-bottom:1px solid var(--zone2)}
"""


def rows_html(key, line_mode, short=False):
    # short (owner, 2026-10-07): ⋯ opens only Kind, Templates and Full form; the full form is its own page
    fields = [("Kind", KINDS[key][0]), ("Templates", ""), ("Full form", "")] if short else KINDS[key][3] + [("Kind", KINDS[key][0]), ("Templates", "")]
    return "".join('<div class="fr" data-tap="Field %s"><span>%s</span><span class="fv">%s</span></div>' % (n, n, val) for n, val in fields)


def line_html(key, line_mode):
    kind, text, words, fields = KINDS[key]
    if line_mode == "title":
        title = text
        for w in words:
            title = title.replace(w, "")
        body = t.e(" ".join(title.split()) or text)
    elif line_mode in ("underline", "highlight"):
        body = t.e(text)
        for w in words:
            body = body.replace(w, '<span class="%s">%s</span>' % ("ul" if line_mode == "underline" else "hl", w), 1)
    else:
        body = t.e(text)
    return '<div class="line"><span class="in">%s<span class="caret"></span></span></div>' % kit.ud(body)


def sheet(shape, line_mode, key):
    kind, text, words, fields = KINDS[key]
    kind_chip = '<span class="tg kind" data-tap="Kind" style="justify-content:flex-start"><span class="vis" data-vis="kind" style="height:%dpx">%s</span></span>' % (H, kind)
    chips = "".join('<span class="tg pchip" data-tap="Fix %s"><span class="vis" data-vis="chip" style="height:%dpx">%s</span></span>' % (v, H, v)
                    for _, v in fields[:3]) if line_mode == "linked" else ""
    more = v2.control("More", "⋯", H, "ghost")
    plus = v2.control("Add details", "+", H, "tonal") if shape == "todoist" else ""
    row = '<div class="crow" style="position:relative"><div class="chips">%s%s%s</div><span style="margin-left:auto;display:flex;gap:6px">%s</span>%s</div>' % (
        plus, kind_chip, chips, "" if shape == "todoist" else more,
        '<div class="pop %s"%s>%s</div>' % ("l" if shape == "todoist" else "r", ' style="width:180px"' if shape == "short" else "",
                                           rows_html(key, line_mode, shape == "short")) if shape in ("todoist", "ticktick", "short") else "")
    inline = '<div class="inl">%s</div>' % rows_html(key, line_mode) if shape == "anydo" else ""
    return '<div class="sheet">%s%s%s</div>' % (inline, line_html(key, line_mode), row)


def phone(shape, line_mode, key):
    if shape == "page":
        kind, text, words, fields = KINDS[key]
        body = '<div class="zone pageform">%s%s</div>' % (line_html(key, "title"), rows_html(key, "title"))
        return kit.phone(kit.header("New %s" % kind.lower(), (("✓", "Save"),), ("‹", "Back")), '<div class="c2">%s</div>' % body, "")
    today = kit.phone(kit.header(t.TITLE, t.APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' + t.rows_today(t.row_d), kit.bar("Today"))
    today = today.replace("data-tap=", "data-behind=")
    overlay = ('<div class="scrim" style="background:rgba(0,0,0,.16)"></div><div class="c2" style="position:absolute;left:0;right:0;bottom:0">%s'
               '<div class="kb">keyboard</div></div>') % sheet(shape, line_mode, key)
    return today[:-len("</div>")] + overlay + "</div>"


def doc(shape, line_mode, key, theme="light", score=True):
    return kit.document(phone(shape, line_mode, key), theme, t.EXTRA + t.T12_CSS + t.T13_CSS + CSS, score)


def sprawl(shape, line_mode, key):
    path = os.path.join(ss.CACHE, "form-%s-%s-%s.html" % (shape, line_mode, key))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc(shape, line_mode, key))
    res = subprocess.run([sys.executable, os.path.join(v2.CRAFT, "craftkit_cli.py"), "ui", "--json", path], capture_output=True, text=True,
                         env=dict(os.environ, PYTHONUTF8="1"))
    found = json.loads(res.stdout).get("findings", [])
    return sum(1 for f in found if not f.get("code", "").startswith(("colour", "contrast"))
               and (f.get("severity") in ("warn", "warning", "error") or f.get("code") == "spacing-off-grid"))


def measure_one(shape, line_mode, key):
    d = doc(shape, line_mode, key)
    m = ss.measure(d, 360, 740)
    png = ss.render(d, 360, 740)
    rows = [x for x in m["taps"] if x["name"].startswith("Field ")]
    on = [x for x in rows if x["box"][1] >= 0 and x["box"][1] + x["box"][3] <= 740]
    reach = sum(math.log2(math.hypot(v2.KB_MID[0] - x["x"], v2.KB_MID[1] - x["y"]) / min(x["w"], x["h"]) + 1) for x in on) / max(1, len(on))
    line = m["boxes"].get("line")
    # the typed line covered by the list, and rows clipped or off screen: what is actually drawn at each point
    # (a clipped row keeps its box, so boxes alone counted it as seen and as covering the line)
    hidden = int(bool(m.get("line_covered")))
    on = [x for x in rows if x.get("seen")]
    reach = sum(math.log2(math.hypot(v2.KB_MID[0] - x["x"], v2.KB_MID[1] - x["y"]) / min(x["w"], x["h"]) + 1) for x in on) / max(1, len(on))
    tops = [x["box"][1] for x in rows]
    covered = 0.0
    if rows:
        if shape == "page":
            covered = 1.0
        else:
            y0, y1 = min(tops), max(x["box"][1] + x["box"][3] for x in rows)
            covered = round(max(0, y1 - max(0, y0)) * (260 if shape != "anydo" else 360) / (360 * 740), 3)
    if shape == "short":  # two steps: the short list over the sheet, then the page; ease adds both choices
        page = measure_one("page", "title", key)
        first_hick = math.log2(len(rows) + 1)
        return {"heights": max(1, len({x[4] for x in m["vis"]})), "edges": len({round(x["box"][0] + 14) for x in rows} | ({round(line[0])} if line else set())),
                "sprawl": sprawl(shape, line_mode, key), "hick": first_hick + page["hick"], "reach": (reach + page["reach"]) / 2,
                "unseen": len(rows) - len(on) + page["unseen"], "line_hidden": hidden, "taps": 3, "clutter": ss.edge_density(png),
                "covered": round(sum(x["box"][2] * x["box"][3] for x in rows) / (360 * 740), 3), "rows": len(rows),
                "small": sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for x in m["taps"] if x["w"] < 48 or x["h"] < 48})}
    return {"heights": max(1, len({x[4] for x in m["vis"]})),  # no drawn control is not better than one height
             "edges": len({round(x["box"][0] + 14) for x in rows} | ({round(line[0])} if line else set())),
            "sprawl": sprawl(shape, line_mode, key), "hick": math.log2(len(rows) + 1), "reach": reach, "unseen": len(rows) - len(on),
            "line_hidden": hidden, "taps": 2 if shape != "page" else 2, "clutter": ss.edge_density(png), "covered": covered, "rows": len(rows),
            "small": sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for x in m["taps"] if x["w"] < 48 or x["h"] < 48})}


AXES = {"H": (("heights", 1), ("edges", 1), ("sprawl", 1)),
        "U": (("hick", 1), ("reach", 1), ("unseen", 1), ("line_hidden", 1), ("taps", 1)),
        "C": (("clutter", 1), ("covered", 1), ("rows", 1))}


def aggregate(per, keys):
    out = {}
    for k in ("heights", "edges", "sprawl", "unseen", "line_hidden", "taps", "rows"):
        out[k] = max(per[x][k] for x in keys)
    for k in ("hick", "reach", "clutter", "covered"):
        out[k] = round(sum(per[x][k] for x in keys) / len(keys), 4)
    out["small"] = sorted({s for x in keys for s in per[x]["small"]})
    return out


def front_of(rows):
    for axis, parts in AXES.items():
        rk = [v2.ranks(rows, k, s) for k, s in parts]
        for i, r in enumerate(rows):
            r[axis] = sum(col[i] for col in rk)
    return [r for r in rows if not any(all(o[a] <= r[a] for a in "HUC") and any(o[a] < r[a] for a in "HUC") for o in rows if o is not r)]


def main():
    variants = [dict(zip(SPACE, c)) for c in itertools.product(*SPACE.values())] + [{"shape": "page", "line": "title"}]
    per = []
    for v in variants:
        per.append({k: measure_one(v["shape"], v["line"], k) for k in KINDS})
        print(v, flush=True)
    result = {}
    for name, keys in (("all ten", list(KINDS)), ("top three", TOP3)):
        rows = [dict(v=v, control=v["shape"] == "page", **aggregate(p, keys)) for v, p in zip(variants, per)]
        rows = [r for r in rows if not r["small"]] + [r for r in rows if r["small"]]
        ok = [r for r in rows if not r["small"]]
        fr = front_of(ok)
        ctrl = next(r for r in rows if r["control"])
        result[name] = {"rows": rows, "front": [rows.index(r) for r in fr], "control_beaten": ctrl not in fr}
        print("==", name, "front", len(fr), "control beaten", ctrl not in fr)
        for r in sorted(fr, key=lambda r: r["H"] + r["U"] + r["C"]):
            print("  ", r["v"], "H %.1f U %.1f C %.1f" % (r["H"], r["U"], r["C"]), {k: r[k] for k in ("heights", "edges", "sprawl", "hick", "reach", "unseen", "clutter", "covered", "rows")})
    with open(os.path.join(v2.OUT, "form-opt.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, indent=1, ensure_ascii=False)
    if not all(r["control_beaten"] for r in result.values()):
        sys.exit(2)


if __name__ == "__main__":
    main()
