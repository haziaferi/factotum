"""T1.6 Repeat builder (owner, 2026-10-08; decision 17). Opens from ⋯ › Repeat beside the line and from the full page's
Repeat row; the item here is "Sample", Fri 16 Oct at 09:00, so the builder starts on "every week on Fri".

The owner's answers: the builder reaches every rule group directly (everyday intervals, ordinals and month ends, within
a day, random and after-done); cron scored three ways; presets first or the builder straight away; the next dates with
and without; all four containers; axes harmony, ease, clutter, rule coverage, legibility, closeness to the references.

Space
  form      freq      Google Calendar's custom repeat: "Every [n] [unit ▾]", the unit's section under it, the times,
                      option chips (Random range, Random time, From when done), the end
            modes     a segmented row first (Repeat · Interval · Random · After done), each with its own short form;
                      units as chips, not a menu (MedTimer's reminder types)
            sentence  the rule as a sentence of tappable words, "Every [week] on [Fri] at [09:00], [forever]"; a tapped
                      word opens its chooser under the sentence (one at a time)
            typed     a field that reads the rule from words ("every 2 weeks tue thu"), as the capture line does, with
                      preset chips; it also takes cron
  start     presets   a short list first (Daily, Weekdays, Weekly on Fri, Monthly on the 16th, Yearly, Custom…)
            builder   the builder at once, the presets as its first row of chips
  cron      field     a cron row at the foot, always drawn, with its readout (the calculator)
            five      five small fields (min, hour, day, month, weekday), with the readout
            advanced  an "Advanced (cron)" row that opens the field and its readout
            (typed takes cron in its own field: only "field")
  preview   none · words (the rule in words, then its next three dates) · month (the words, and the next dates
            dotted on a small month)
  container sheet · page · keyboard (the builder in the keyboard's place) · popover (above the line, keyboard kept)

Tasks (each opened from ⋯ › Repeat, not counted; each ends on Done unless a preset closes it):
  T1 every weekday · T2 every 2 weeks on Tue and Thu · T3 monthly on the 2nd Tuesday · T4 the last day of every month,
  6 times · T5 08:30 and 20:30 every day · T6 every 90 minutes from 09:00 to 17:00 · T7 at random every 2 to 4 days ·
  T8 at a random time between 09:00 and 12:00 every day · T9 3 days after it was last done · T10 cron 0 9 1 * 1
  (the 1st or any Monday: crontab's OR rule, which no builder form reaches)
Defaults are the item's: weekly, Fri, 09:00; a time window defaults to 09:00-21:00; an end to never.

Ease is one count of actions (owner, 2026-10-08): taps + keystrokes, walked in order. A tapped field brings the
keyboard up (290 px); a later target the keyboard hides costs one more action (closing it). Typing assumes no
autocomplete. Visibility (owner: everything a task needs is drawn) is hit-tested per view, with and without the keyboard.

    PYTHONUTF8=1 python tools/screens/repeat_opt.py [--workers 4]
"""
import concurrent.futures
import itertools
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_v2 as v2  # noqa: E402
import kit  # noqa: E402
import picker_opt as P  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402

FORMS = ["freq", "modes", "sentence", "typed"]
SPACE = {"form": FORMS, "start": ["presets", "builder"], "cron": ["field", "five", "advanced"], "preview": ["none", "words", "month"],
         "container": ["sheet", "page", "keyboard", "popover"]}
PRESETS = [("Daily", "Daily"), ("Weekdays", "Weekdays"), ("Weekly", "Weekly on Fri"), ("Monthly", "Monthly on the 16th"), ("Yearly", "Yearly on 16 Oct")]
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
FIELDS = {"Rule field", "N field", "N2 field", "Time 1", "From", "To", "End field", "Cron field", "Cron min", "Typed field", "Add time"}
CSS = P.CSS + """
.pk .ttl{font-size:15px;font-weight:600}
.pk .lab{font-size:12px;color:var(--dim);font-weight:600;min-width:44px;display:inline-flex;align-items:center;min-height:48px}
.pk .wdg{display:grid;grid-template-columns:repeat(7,1fr);margin:0 -12px}.pk .wdg .tg{min-width:0}
.pk .nf{flex:none;width:56px;min-height:48px;display:inline-flex;align-items:center;justify-content:center;border-radius:10px;box-shadow:inset 0 0 0 1px var(--zone2);font-size:15px}
.pk .tf{flex:none;width:72px;min-height:48px;display:inline-flex;align-items:center;justify-content:center;border-radius:10px;box-shadow:inset 0 0 0 1px var(--zone2);font-size:15px}
.pk .txt{font-size:14px;padding:0 4px}
.pk .sent{font-size:17px;line-height:48px}.pk .sent .tok{display:inline-flex;min-height:48px;align-items:center;justify-content:center;padding:0 2px;min-width:48px}.pk .sent .tok b{font-weight:600;text-decoration:underline;text-decoration-color:var(--dim);text-underline-offset:4px}
.pk .seg{display:flex}.pk .seg .tg{flex:1;min-width:0}.pk .seg .vis{width:100%;padding:0 4px;font-size:13px}
.pk .mini{display:grid;grid-template-columns:repeat(7,1fr);font-size:11px;color:var(--dim);text-align:center;row-gap:2px;padding:2px 0 4px}
.pk .mini i{display:block;width:4px;height:4px;border-radius:50%;background:var(--ink);margin:0 auto}
.pk .plist .prow{min-height:48px;display:flex;align-items:center;font-size:15px;border-bottom:1px solid var(--zone2)}
.pk .menu{position:absolute;left:68px;top:96px;width:180px;background:var(--bg);border-radius:12px;box-shadow:0 8px 28px rgba(0,0,0,.22);padding:4px 8px}
.pk .menu .prow{min-height:48px;display:flex;align-items:center;font-size:15px}
.c2 .f-on .vis{background:var(--zone2);font-weight:600}
.c2 .f-off .vis{background:transparent;box-shadow:inset 0 0 0 1px var(--zone2)}
"""


def ch(name, label, on=False):
    return v2.control(name, label, 32, "on" if on else "off", square=False)


def b(name, label):
    return P.btn(name, label)


def field(name, val, cls="nf"):
    return '<span class="%s" data-tap="%s">%s</span>' % (cls, name, val)


def row(*parts, label=None):
    return '<div class="row">%s%s</div>' % ('<span class="lab">%s</span>' % label if label else "", "".join(parts))


def weekdays(sel, prefix="Wd"):
    return '<div class="wdg">%s</div>' % "".join(ch("%s %s" % (prefix, d), d[:2], d in sel) for d in WD)


def month_sec(mode="day"):
    return (row(ch("Month day", "On day 16", mode == "day"), ch("Month weekday", "On a weekday", mode == "wd"), ch("Month last", "Last day", mode == "last"))
            + row(*[ch("Ord %s" % o, o, o == "3rd") for o in ("1st", "2nd", "3rd", "4th", "Last")]) + weekdays({"Fri"}, "Ow"))


def times_sec(random_time=False):
    if random_time:
        return row(field("From", "09:00", "tf"), '<span class="txt">to</span>', field("To", "21:00", "tf"), label="Between")
    return row(field("Time 1", "09:00", "tf"), b("Add time", "+ time"), label="At")


def window_sec():
    return row(field("From", "09:00", "tf"), '<span class="txt">to</span>', field("To", "21:00", "tf"), label="From")


def ends_sec():
    return row(ch("End never", "Never", True), ch("End after", "After"), field("End field", "6"), ch("End on", "On date"), label="Ends")


def presets_row():
    return '<div class="row">%s</div>' % "".join(ch("Preset %s" % k, k) for k, _ in PRESETS)


def preset_list():
    return '<div class="plist">%s<div class="prow" data-tap="Custom">Custom…</div></div>' % "".join(
        '<div class="prow" data-tap="Preset %s">%s</div>' % (k, lab) for k, lab in PRESETS)


def cron_sec(kind):
    readout = '<div class="calc">Cron, read back: <b>0 9 1 * 1</b> is "09:00 on the 1st, or on any Monday"; next Mon 19, Mon 26 Oct, Sun 1 Nov</div>'
    if kind == "field":
        return row(field("Cron field", "min hour day month weekday", "field"), label="Cron") + readout
    if kind == "five":
        return row(*[field("Cron min" if i == 0 else "Cron %s" % n, n) for i, n in enumerate(("min", "hour", "day", "mon", "wday"))], label="Cron") + readout
    return '<div class="row">%s</div>' % b("Advanced", "Advanced (cron) ›")


def preview_sec(kind, words="Every week on Fri at 09:00"):
    if kind == "none":
        return ""
    line = '<div class="calc" data-tap="Readout">%s · next Fri 16, Fri 23, Fri 30 Oct</div>' % words if words != "Next" else '<div class="calc" data-tap="Readout">Next: Fri 16, Fri 23, Fri 30 Oct</div>'
    if kind == "words":
        return line
    cells = "".join("<div>%s</div>" % d for d in "MTWTFSS") + "<div></div>" * 3 + "".join(
        "<div>%d%s</div>" % (d, "<i></i>" if d in (16, 23, 30) else "") for d in range(1, 32))
    return line + '<div class="mini" data-tap="Readout dates">%s</div>' % cells


def header(v, back=False):
    if v["container"] == "page":
        return ""
    return '<div class="row" style="justify-content:space-between">%s<span class="ttl">Repeat</span>%s</div>' % (b("Back", "‹") if back else "<span></span>", b("Done", "Done"))


# ---- the forms, one state at a time ----------------------------------------------------------------------------
def freq(v, state):
    unit = {"base": "week", "menu": "week", "month": "month", "day": "day", "dayrand": "day", "dayrt": "day", "minutes": "minutes"}[state]
    interval = row('<span class="txt">Every</span>', field("N field", "1"),
                   ('<span class="txt">to</span>' + field("N2 field", "4")) if state == "dayrand" else "",
                   b("Unit", "%s ▾" % {"week": "week", "month": "month", "day": "day", "minutes": "minutes"}[unit]))
    sec = {"week": weekdays({"Fri"}), "month": month_sec(), "day": "", "minutes": window_sec()}[unit]
    opts = row(ch("Opt Random", "Random range", state == "dayrand"), ch("Opt Random time", "Random time", state == "dayrt"), ch("Opt Done", "From when done"))
    body = interval + sec + (times_sec(state == "dayrt") if unit != "minutes" else "") + opts + ends_sec()
    if state == "menu":
        body += '<div class="menu">%s</div>' % "".join('<div class="prow" data-tap="Unit %s">%s</div>' % (u, u.lower()) for u in ("Minutes", "Hours", "Days", "Weeks", "Months", "Years"))
    return body


def modes(v, state):
    mode = {"base": "Repeat", "month": "Repeat", "day": "Repeat", "interval": "Interval", "random": "Random", "randtime": "Random", "done": "After done"}[state]
    seg = '<div class="seg">%s</div>' % "".join(ch("Mode %s" % m, m, m == mode) for m in ("Repeat", "Interval", "Random", "After done"))
    if mode == "Repeat":
        unit = {"base": "Week", "month": "Month", "day": "Day"}[state]
        body = row(*[ch("Unit %ss" % u, u, u == unit) for u in ("Day", "Week", "Month", "Year")]) + row('<span class="txt">Every</span>', field("N field", "1"), '<span class="txt">%ss</span>' % unit.lower())
        body += {"Week": weekdays({"Fri"}), "Month": month_sec(), "Day": ""}[unit] + times_sec() + ends_sec()
    elif mode == "Interval":
        body = row('<span class="txt">Every</span>', field("N field", "30"), ch("Unit min", "min", True), ch("Unit h", "h")) + window_sec() + row(ch("Wdays all", "Every day", True), ch("Wdays pick", "Some days")) + ends_sec()
    elif mode == "Random":
        body = row(ch("Rand days", "Random days", state == "random"), ch("Rand time", "Random time", state == "randtime"))
        body += (row('<span class="txt">Every</span>', field("N field", "1"), '<span class="txt">to</span>', field("N2 field", "3"), '<span class="txt">days</span>') if state == "random"
                 else row(field("From", "09:00", "tf"), '<span class="txt">to</span>', field("To", "21:00", "tf"), label="Between")) + ends_sec()
    else:
        body = row(field("N field", "1"), ch("Unit d", "days", True), ch("Unit w", "weeks"), '<span class="txt">after it is done</span>') + times_sec() + ends_sec()
    return seg + body


def sentence(v, state):
    unit = {"base": "week", "unit": "week", "unitm": "month", "onm": "month", "endm": "month", "unitd": "day", "atd": "day", "unitmin": "minutes", "atmin": "minutes", "end": "week", "atrt": "day"}[state]
    on = {"week": "Fri", "month": "day 16", "day": "", "minutes": ""}[unit]
    words = '<div class="sent">Every <span class="tok" data-tap="Tok unit"><b>%s</b></span>%s <span class="tok" data-tap="Tok at"><b>%s</b></span>, <span class="tok" data-tap="Tok end"><b>forever</b></span></div>' % (
        unit, ' on <span class="tok" data-tap="Tok on"><b>%s</b></span>' % on if on else "", "from 09:00 to 21:00" if unit == "minutes" else "at 09:00")
    chooser = ""
    if state in ("unit", "unitm", "unitd", "unitmin"):
        chooser = (row(*[ch("Unit %s" % u, u.lower(), u.lower().rstrip("s") == unit.rstrip("s")) for u in ("Minutes", "Hours", "Days", "Weeks", "Months", "Years")])
                   + row('<span class="txt">every</span>', field("N field", "1"), ch("Opt Random", "random"), field("N2 field", "–"), ch("Opt Done", "after done")))
    elif state == "onm":
        chooser = month_sec()
    elif state in ("atd", "atrt"):
        chooser = times_sec(state == "atrt") + row(ch("Opt Random time", "Random time", state == "atrt"))
    elif state == "atmin":
        chooser = window_sec()
    elif state in ("end", "endm"):
        chooser = ends_sec()
    elif state == "base":
        chooser = ""
    return words + chooser


def typed(v, state):
    return (row(field("Typed field", "every week on fri", "field"))
            + '<div class="row">%s</div>' % "".join(ch("Preset %s" % k, k) for k, _ in PRESETS[:4]))


FORM = {"freq": freq, "modes": modes, "sentence": sentence, "typed": typed}


WORDS = {"month": "Every month on day 16 at 09:00", "onm": "Every month on day 16 at 09:00", "unitm": "Every month on day 16 at 09:00",
         "interval": "Every 30 min, 09:00 to 21:00, every day", "random": "Every 1 to 3 days, at random, at 09:00",
         "randtime": "Every day at a random time, 09:00 to 21:00", "done": "1 day after it is done, at 09:00",
         "day": "Every day at 09:00", "minutes": "Every 30 min, 09:00 to 21:00"}


def everything(v):
    """The control: every section of every form drawn at once, units as chips, the menu inline."""
    return (header(v) + presets_row() + '<div class="seg">%s</div>' % "".join(ch("Mode %s" % m, m) for m in ("Repeat", "Interval", "Random", "After done"))
            + row('<span class="txt">Every</span>', field("N field", "1"), '<span class="txt">to</span>', field("N2 field", "4"))
            + row(*[ch("Unit %s" % u, u.lower()) for u in ("Minutes", "Hours", "Days", "Weeks", "Months", "Years")])
            + weekdays({"Fri"}) + month_sec() + times_sec() + window_sec()
            + row(ch("Opt Random", "Random range"), ch("Opt Random time", "Random time"), ch("Opt Done", "From when done"))
            + ends_sec() + preview_sec("month") + cron_sec("five"))


def body(v, state):
    if v.get("control"):
        return everything(v)
    if state == "presets":
        return header(v) + preset_list()
    if state == "advanced":
        return header(v, back=True) + row(field("Cron field", "min hour day month weekday", "field"), label="Cron") + cron_sec("field").split("</div>", 1)[1]
    inner = FORM[v["form"]](v, state)
    # the readout follows the state drawn (the same length either way, so the measures do not move)
    words = WORDS.get(state, "Every week on Fri at 09:00")
    if v["form"] in ("sentence", "sentmodes"):
        words = "Next"  # the sentence is the rule in words; its readout adds only the dates
    show_preview = v["preview"]
    pre = presets_row() if v["start"] == "builder" else ""
    cron = cron_sec(v["cron"]) if v["form"] != "typed" and v.get("words", "none") == "none" else ""
    if v.get("words") == "field":
        pre += rule_field()
    if v["form"] == "typed" and v["preview"] == "none":
        show_preview = "none"
    return header(v, back=v["start"] == "presets") + pre + inner + preview_sec(show_preview, words) + cron


def phone(v, state, kb=False):
    c = v["container"]
    cls = {"keyboard": "pk", "sheet": "pk sheet", "popover": "pk pop", "page": "pk page"}[c]
    style = {"keyboard": ' style="height:290px"', "sheet": ' style="max-height:704px"', "popover": ' style="max-height:440px"', "page": ""}[c]
    if c == "page" and kb:
        style = ' style="bottom:290px"'
    pk = '<div class="%s"%s data-picker="1">%s</div>' % (cls, style, body(v, state))
    kbd = '<div class="kb" style="height:290px">keyboard</div>'
    if c == "page":
        head = kit.header("Repeat", (("✓", "Done"),), ("‹", "Back"))
        return kit.phone(head, '<div class="c2" style="position:relative;height:100%%">%s</div>' % pk, kbd.replace('class="kb"', 'class="kb" style="position:absolute;left:0;right:0;bottom:0;height:290px"') if kb else "")
    today = kit.phone(kit.header(t.TITLE, t.APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' + t.rows_today(t.row_d), kit.bar("Today"))
    today = today.replace("data-tap=", "data-behind=")
    if c == "keyboard":  # the builder takes the keyboard's place; a tapped field brings the keyboard back over it
        overlay = '<div class="sheet c2" style="position:relative">%s</div>%s' % (P.line_html(), kbd if kb else pk)
    elif c == "popover":  # above the line, the keyboard kept
        overlay = '<div class="sheet c2" style="position:relative">%s%s</div>%s' % (pk, P.line_html(), kbd)
    else:
        overlay = '<div class="c2">%s</div>%s' % (pk, kbd if kb else "")
    overlay = '<div class="scrim" style="background:rgba(0,0,0,.16)"></div><div class="c2" style="position:absolute;left:0;right:0;bottom:0">%s</div>' % overlay
    return today[:-len("</div>")] + overlay + "</div>"


def doc(v, state, kb=False, theme="light", score=True):
    return kit.document(phone(v, state, kb), theme, t.EXTRA + t.T12_CSS + t.T13_CSS + CSS, score)


# ---- the tasks, as each form walks them: (state, "tap", name) or (state, "type", keystrokes) ------------------------
def tap(state, *names):
    return [(state, "tap", n) for n in names]


def typ(state, n):
    return [(state, "type", n)]


def walk(v):
    f, start = v["form"], v["start"]
    base = "base"
    if f == "freq":
        T = {
            2: tap(base, "N field") + typ(base, 1) + tap(base, "Wd Tue", "Wd Thu", "Wd Fri", "Done"),
            3: tap(base, "Unit") + tap("menu", "Unit Months") + tap("month", "Month weekday", "Ord 2nd", "Ow Tue", "Done"),
            4: tap(base, "Unit") + tap("menu", "Unit Months") + tap("month", "Month last", "End after", "End field") + typ("month", 1) + tap("month", "Done"),
            5: tap(base, "Unit") + tap("menu", "Unit Days") + tap("day", "Time 1") + typ("day", 4) + tap("day", "Add time") + typ("day", 4) + tap("day", "Done"),
            6: tap(base, "Unit") + tap("menu", "Unit Minutes") + tap("minutes", "N field") + typ("minutes", 2) + tap("minutes", "To") + typ("minutes", 4) + tap("minutes", "Done"),
            7: tap(base, "Unit") + tap("menu", "Unit Days") + tap("day", "Opt Random") + tap("dayrand", "N field") + typ("dayrand", 1) + tap("dayrand", "N2 field") + typ("dayrand", 1) + tap("dayrand", "Done"),
            8: tap(base, "Unit") + tap("menu", "Unit Days") + tap("day", "Opt Random time") + tap("dayrt", "To") + typ("dayrt", 4) + tap("dayrt", "Done"),
            9: tap(base, "Unit") + tap("menu", "Unit Days") + tap("day", "N field") + typ("day", 1) + tap("day", "Opt Done", "Done"),
        }
    elif f == "modes":
        T = {
            2: tap(base, "N field") + typ(base, 1) + tap(base, "Wd Tue", "Wd Thu", "Wd Fri", "Done"),
            3: tap(base, "Unit Months") + tap("month", "Month weekday", "Ord 2nd", "Ow Tue", "Done"),
            4: tap(base, "Unit Months") + tap("month", "Month last", "End after", "End field") + typ("month", 1) + tap("month", "Done"),
            5: tap(base, "Unit Days") + tap("day", "Time 1") + typ("day", 4) + tap("day", "Add time") + typ("day", 4) + tap("day", "Done"),
            6: tap(base, "Mode Interval") + tap("interval", "N field") + typ("interval", 2) + tap("interval", "To") + typ("interval", 4) + tap("interval", "Done"),
            7: tap(base, "Mode Random") + tap("random", "N field") + typ("random", 1) + tap("random", "N2 field") + typ("random", 1) + tap("random", "Done"),
            8: tap(base, "Mode Random") + tap("random", "Rand time") + tap("randtime", "To") + typ("randtime", 4) + tap("randtime", "Done"),
            9: tap(base, "Mode After done") + tap("done", "N field") + typ("done", 1) + tap("done", "Done"),
        }
    elif f == "sentence":
        T = {
            2: tap(base, "Tok unit") + tap("unit", "N field") + typ("unit", 1) + tap("unit", "Tok on") + tap("base", "Wd Tue", "Wd Thu", "Wd Fri", "Done"),
            3: tap(base, "Tok unit") + tap("unit", "Unit Months") + tap("unitm", "Tok on") + tap("onm", "Month weekday", "Ord 2nd", "Ow Tue", "Done"),
            4: tap(base, "Tok unit") + tap("unit", "Unit Months") + tap("unitm", "Tok end") + tap("endm", "End after", "End field") + typ("endm", 1) + tap("endm", "Done"),
            5: tap(base, "Tok unit") + tap("unit", "Unit Days") + tap("unitd", "Tok at") + tap("atd", "Time 1") + typ("atd", 4) + tap("atd", "Add time") + typ("atd", 4) + tap("atd", "Done"),
            6: tap(base, "Tok unit") + tap("unit", "Unit Minutes") + tap("unitmin", "N field") + typ("unitmin", 2) + tap("unitmin", "Tok at") + tap("atmin", "To") + typ("atmin", 4) + tap("atmin", "Done"),
            7: tap(base, "Tok unit") + tap("unit", "Unit Days") + tap("unitd", "Opt Random", "N field") + typ("unitd", 1) + tap("unitd", "N2 field") + typ("unitd", 1) + tap("unitd", "Done"),
            8: tap(base, "Tok unit") + tap("unit", "Unit Days") + tap("unitd", "Tok at") + tap("atd", "Opt Random time") + tap("atrt", "To") + typ("atrt", 4) + tap("atrt", "Done"),
            9: tap(base, "Tok unit") + tap("unit", "Opt Done", "N field") + typ("unit", 1) + tap("unit", "Done"),
        }
        # sentence T2: the weekday chooser opens from "on Fri"; its chips are drawn in a "week on" state
        T[2] = tap(base, "Tok unit") + tap("unit", "N field") + typ("unit", 1) + tap("unit", "Tok on") + tap("onw", "Wd Tue", "Wd Thu", "Wd Fri", "Done")
    elif f == "slim":
        cron4 = tap(base, "Rule field") + typ(base, len(CRON_CHARS[4])) + tap(base, "End after", "End field") + typ(base, 1) + tap(base, "Done")
        T = {2: tap(base, "Mode Every") + tap("everyn", "N field") + typ("everyn", 1) + tap("everyn", "Wd Tue", "Wd Thu", "Wd Fri", "Done"),
             4: cron4,
             7: tap(base, "Mode Random") + tap("random", "N field") + typ("random", 1) + tap("random", "N2 field") + typ("random", 1) + tap("random", "Done"),
             8: tap(base, "Mode Random") + tap("random", "Rand time") + tap("randtime", "To") + typ("randtime", 4) + tap("randtime", "Done"),
             9: tap(base, "Mode After done") + tap("done", "N field") + typ("done", 1) + tap("done", "Done")}
        # T3, T5, T6 and T10 go through the field (walk_field), the quicker of words and cron
    elif f == "sentmodes":
        S = walk(dict(v, form="sentence", start="builder", words="none"))
        M = walk(dict(v, form="modes", start="builder", words="none"))
        T = {k: (S[k] if k <= 5 else M[k]) for k in range(2, 10)}
    else:  # typed: words, no autocomplete counted
        T = {k: tap(base, "Typed field") + typ(base, n) + tap(base, "Done") for k, n in
             ((2, len("every 2 weeks tue thu")), (3, len("2nd tue monthly")), (4, len("last day monthly 6 times")), (5, len("daily 8:30 20:30")),
              (6, len("every 90 min 9-17")), (7, len("random 2-4 days")), (8, len("daily random 9-12")), (9, len("3 days after done")))}
    # T1, a preset
    T[1] = tap("presets", "Preset Weekdays") if start == "presets" else tap(base, "Preset Weekdays", "Done")
    # T10, cron
    if f == "typed" or v.get("words") == "field":
        T[10] = tap(base, "Typed field" if f == "typed" else "Rule field") + typ(base, 9) + tap(base, "Done")
    elif f == "typed":
        T[10] = tap(base, "Typed field") + typ(base, 9) + tap(base, "Done")
    elif v["cron"] == "field":
        T[10] = tap(base, "Cron field") + typ(base, 9) + tap(base, "Done")
    elif v["cron"] == "five":
        T[10] = sum((tap(base, n) + typ(base, 1) for n in ("Cron min", "Cron hour", "Cron day", "Cron mon", "Cron wday")), []) + tap(base, "Done")
    else:
        T[10] = tap(base, "Advanced") + tap("advanced", "Cron field") + typ("advanced", 9) + tap("advanced", "Done")
    if start == "presets":
        for k in T:
            if k != 1:
                T[k] = tap("presets", "Custom") + T[k]
    return T


TYPED_CHARS = {2: "every 2 weeks tue thu", 3: "2nd tue monthly", 4: "last day monthly 6 times", 5: "daily 8:30 20:30",
               6: "every 90 min 9-17", 7: "random 2-4 days", 8: "daily random 9-12", 9: "3 days after done", 10: "0 9 1 * 1"}


CRON_CHARS = {3: "0 9 * * TUE#2", 4: "0 9 L * *", 5: "30 8,20 * * *", 6: "0 9,12,15 * * *" + chr(10) + "30 10,13,16 * * *", 10: "0 9 1 * 1"}


def walk_field(v):
    """The field's path for each task: the shorter of words and cron (with L, #, names and several lines), no
    autocomplete counted. T4's count is not cron: the field path types the words."""
    T = {k: tap("base", "Rule field") + typ("base", min(len(w), len(CRON_CHARS.get(k, w)) if k != 4 else len(w))) + tap("base", "Done") for k, w in TYPED_CHARS.items()}
    if v["start"] == "presets":
        T = {k: tap("presets", "Custom") + x for k, x in T.items()}
    return T


def walk_control(v):
    T = walk(dict(v, form="freq", start="builder"))
    out = {}
    for k, task in T.items():
        out[k] = [("base", kind, x) for s, kind, x in task if x not in ("Unit", "Advanced")]
    return out


def states_of(v):
    out = {s for task in (walk_control(v) if v.get("control") else walk(v)).values() for s, _, _ in task}
    if v.get("words") == "field":
        out |= {s for task in walk_field(v).values() for s, _, _ in task}
    return sorted(out | {"base"})


def sentence_onw(v, state):  # the weekday chooser of the sentence form
    return sentence(v, "base") + weekdays({"Fri"})


_orig_sentence = sentence


def sentence(v, state):  # noqa: F811
    return sentence_onw(v, state) if state == "onw" else _orig_sentence(v, state)


FORM["sentence"] = sentence

SENT_STATES = {"base", "unit", "unitm", "onm", "endm", "unitd", "atd", "onw"}


def seg_html(mode):
    return '<div class="seg">%s</div>' % "".join(ch("Mode %s" % m, m, m == mode) for m in ("Repeat", "Interval", "Random", "After done"))


def sentmodes(v, state):
    """Merge (owner, 2026-10-08): the schedule types as the first chooser, the sentence under them; Repeat edits
    the sentence's words, the other types show their own short form under the sentence."""
    if state in SENT_STATES:
        return seg_html("Repeat") + sentence(v, state)
    mode = {"interval": "Interval", "random": "Random", "randtime": "Random", "done": "After done"}[state]
    return seg_html(mode) + '<div class="sent">%s</div>' % WORDS[state] + modes(v, state).split("</div>", 1)[1]


FORM["sentmodes"] = sentmodes


def slim(v, state):
    """Owner, 2026-10-08: cron (with L, #, names and several lines) shown in the sheet, not behind Advanced, takes
    the tasks it can express; the builder keeps only what cron cannot: every n days or weeks, random, after done,
    and the end. The field and its calculator come from rule_field (words or cron)."""
    mode = {"base": None, "everyn": "Every", "random": "Random", "randtime": "Random", "done": "After done"}[state]
    seg = '<div class="seg">%s</div>' % "".join(ch("Mode %s" % m, lab, m == mode) for m, lab in (("Every", "Every n…"), ("Random", "Random"), ("After done", "After done")))
    if state == "base":
        return seg + ends_sec()
    if state == "everyn":
        return seg + row('<span class="txt">Every</span>', field("N field", "1"), ch("Unit d", "days"), ch("Unit w", "weeks", True), ch("Unit m", "months")) + weekdays({"Fri"}) + ends_sec()
    return seg + modes(v, state).split("</div>", 1)[1]


FORM["slim"] = slim


def rule_field():
    """Merge (owner, 2026-10-08): one field that takes the rule in words or as cron lines, with the calculator's
    cron line under it (shown when cron can express the rule)."""
    return row(field("Rule field", "Type a rule or cron", "field")) + '<div class="calc">As cron: 0 9 * * 5</div>'


def measure_view(v, state, kb):
    m = ss.measure(doc(v, state, kb), 360, 740)
    return {x["name"]: x for x in m["taps"]}, m


def score(v):
    views, base_m = {}, None
    T = walk_control(v) if v.get("control") else walk(v)
    for s in states_of(v):
        for kb in (False, True):
            views[(s, kb)] = measure_view(v, s, kb)
    base_m = views[("base", False)][1]
    typed_kb = v["form"] == "typed"  # its field is focused when it opens

    def sim(k, task):
        kb = typed_kb and task[0][0] == "base"
        n, miss, tids = 0, set(), []
        for state, kind, x in task:
            if kind == "type":
                n += x
                continue
            seen = lambda kbv: views[(state, kbv)][0].get(x, {}).get("seen")
            if kb and not seen(True):
                if seen(False):
                    n += 1  # close the keyboard first
                    kb = False
                else:
                    miss.add("T%d %s: %s" % (k, state, x))
            elif not kb and not seen(False):
                miss.add("T%d %s: %s" % (k, state, x))
            tp = views[(state, kb)][0].get(x)
            if tp and tp.get("seen"):
                tids.append(math.log2(math.hypot(P.THUMB[0] - tp["x"], P.THUMB[1] - tp["y"]) / min(tp["w"], tp["h"]) + 1))
            n += 1
            if x in FIELDS or x.startswith("Cron "):
                kb = True
            if x == "Done" or x.startswith("Preset"):
                kb = False
        return n, miss, tids

    alt = walk_field(v) if v.get("words") == "field" else {}
    actions, ids, unseen, per_task, path = 0, [], set(), {}, {}
    for k in sorted(set(T) | set(alt)):
        runs = ([(sim(k, T[k]), "builder")] if k in T else []) + ([(sim(k, alt[k]), "field")] if k in alt else [])
        (n, miss, tids), which = min(runs, key=lambda r: (len(r[0][1]), r[0][0]))  # the quicker of the drawn paths
        unseen |= miss
        ids += tids
        per_task[k], path[k] = n, which
        actions += n
    pk = base_m["boxes"].get("picker")
    in_pk = [x for x in base_m["taps"] if pk and x["box"][1] >= pk[1] - 1 and x.get("seen") and not x["name"].startswith("Readout")]
    small = sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for (st, kbv), (tp, m) in views.items() if not kbv for x in tp.values()
                    if x.get("seen") and not x["name"].startswith("Readout") and (x["w"] < 48 or x["h"] < 48)})
    readout = views[("base", False)][0]
    words_seen = bool(readout.get("Readout", {}).get("seen")) or v["form"] in ("sentence", "sentmodes")
    dates_seen = bool(readout.get("Readout", {}).get("seen"))
    clutter = sum(ss.edge_density(ss.render(doc(v, "base", False, th), 360, 740)) for th in ("light", "dark")) / 2
    # T2-T9 without free text: typed reaches them only by words; slim leaves T3-T6 to the field (cron or words)
    coverage = {"typed": 0, "slim": 4}.get(v["form"], 8)
    return {"actions": actions, "per_task": per_task, "path": path, "reach": round(sum(ids) / max(1, len(ids)), 3), "unseen": len(unseen), "unseen_names": sorted(unseen),
            "small": small, "heights": max(1, len({x[4] for x in base_m["vis"]})), "clutter": round(clutter, 4),
            "covered": 1.0 if v["container"] == "page" else round(min(1.0, (pk[3] if pk else 0) / 740), 3),
            "controls": len(in_pk), "uncovered_rules": 8 - coverage, "unread": 2 - int(words_seen) - int(dates_seen)}


def variants():
    for c in itertools.product(*SPACE.values()):
        v = dict(zip(SPACE, c))
        if v["form"] == "typed" and (v["cron"] != "field" or v["container"] == "keyboard"):
            continue  # typed takes cron in its own field; in the keyboard's place it would have no keyboard
        yield v


def control():
    """Everything at once in a sheet: every section of every form, all drawn. It must lose."""
    return {"form": "freq", "start": "builder", "cron": "five", "preview": "month", "container": "sheet", "control": True}


def main():
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    vs = list(variants()) + [control()]
    out = os.path.join(v2.OUT, "repeat-opt.json")
    if "--only" in sys.argv:  # rescore one form and merge it into the last run
        form = sys.argv[sys.argv.index("--only") + 1]
        with open(out, encoding="utf-8") as fh:
            old = json.load(fh)["rows"]
        redo = [v for v in vs if v["form"] == form and not v.get("control")]
        with concurrent.futures.ProcessPoolExecutor(workers) as ex:
            new = dict((json.dumps(v, sort_keys=True), dict(v=v, **r)) for v, r in zip(redo, ex.map(score, redo)))
        rows = [new.get(json.dumps(r["v"], sort_keys=True), r) for r in old]
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"rows": rows}, fh, indent=1, ensure_ascii=False)
        print("rescored", len(new), form)
        return
    rows = []
    with concurrent.futures.ProcessPoolExecutor(workers) as ex:
        for v, r in zip(vs, ex.map(score, vs)):
            rows.append(dict(v=v, **r))
            print(len(rows), v, {k: r[k] for k in ("actions", "reach", "unseen", "small", "clutter", "covered", "unread")}, flush=True)
    with open(os.path.join(v2.OUT, "repeat-opt.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"rows": rows}, fh, indent=1, ensure_ascii=False)


# ---- ranking: six axes (owner, 2026-10-08) ---------------------------------------------------------------------
REFS = os.path.join(v2.OUT, "repeat-references.json")  # measured on the phone (geometry and labels only)
FEATURES = ("presets_first", "unit_control", "weekday_chips", "page", "readout", "next_dates", "modes")


def features(r):
    v = r["v"]
    return {"presets_first": v["start"] == "presets", "unit_control": {"freq": "menu", "modes": "chips", "sentence": "words", "sentmodes": "words", "slim": "text", "typed": "text"}[v["form"]],
            "weekday_chips": v["form"] != "typed", "page": v["container"] == "page", "readout": r["unread"] < 2, "next_dates": r["unread"] == 0,
            "modes": v["form"] in ("modes", "sentmodes", "slim")}


def ref_distance(r, refs):
    f = features(r)
    return round(sum(sum(f[k] != ref[k] for k in FEATURES) / len(FEATURES) for ref in refs) / len(refs), 3)


def harmony(r):
    """picker_opt's harmony parts on the opening view: sprawl (craftkit ui) and the heaviest element's share of mass."""
    v = dict(r["v"])
    d = doc(v, "base")
    m = ss.measure(d, 360, 740)
    png = ss.render(d, 360, 740)
    path = os.path.join(ss.CACHE, "rp-%s.html" % "-".join(str(v.get(k)) for k in list(SPACE) + ["words"]))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(d)
    import subprocess
    res = subprocess.run([sys.executable, os.path.join(v2.CRAFT, "craftkit_cli.py"), "ui", "--json", path], capture_output=True, text=True, env=dict(os.environ, PYTHONUTF8="1"))
    found = json.loads(res.stdout).get("findings", [])
    sprawl = sum(1 for f in found if not f.get("code", "").startswith(("colour", "contrast")) and (f.get("severity") in ("warn", "warning", "error") or f.get("code") == "spacing-off-grid"))
    return {"sprawl": sprawl, "heavy": P.masses(png, m)}


AXES = {"H": ("heights", "sprawl", "heavy"), "U": ("actions", "reach"), "C": ("clutter", "covered", "controls"),
        "Rules": ("uncovered_rules",), "Legible": ("unread",), "Refs": ("ref_distance",)}


SPACE_MERGE = {"form": ["freq", "modes", "sentence", "sentmodes", "slim"], "words": ["none", "field"], "start": ["presets", "builder"],
               "preview": ["none", "words"], "container": ["sheet", "page"]}


def merge_run(workers=4):
    """Owner, 2026-10-08: score a merge. The sentence with the schedule types as its first chooser, and each form with
    a field that takes words or cron (the calculator under it), the quicker path counted per task. Containers and
    preview narrowed by the first run (the keyboard's place and the pop-over fail the visibility rule; the month
    preview loses to words on every measure; cron behind Advanced beats the other cron forms)."""
    vs = [dict(dict(zip(SPACE_MERGE, c)), cron="advanced") for c in itertools.product(*SPACE_MERGE.values())]
    vs = [v for v in vs if not (v["form"] == "slim" and v["words"] == "none")] + [control()]  # slim is the field
    rows = []
    with concurrent.futures.ProcessPoolExecutor(workers) as ex:
        for v, r in zip(vs, ex.map(score, vs)):
            rows.append(dict(v=v, **r))
            print(len(rows), v, {k: r[k] for k in ("actions", "reach", "unseen", "small", "clutter", "covered", "unread")}, flush=True)
    with open(os.path.join(v2.OUT, "repeat-merge.json"), "w", encoding="utf-8", newline=chr(10)) as fh:
        json.dump({"rows": rows}, fh, indent=1, ensure_ascii=False)


def rank(src="repeat-opt.json", dst="repeat-rank.json"):
    with open(os.path.join(v2.OUT, src), encoding="utf-8") as fh:
        rows = json.load(fh)["rows"]
    with open(REFS, encoding="utf-8") as fh:
        refs = json.load(fh)["apps"]
    ok = [r for r in rows if not r["small"] and r["unseen"] == 0 or r["v"].get("control")]
    with concurrent.futures.ProcessPoolExecutor(4) as ex:
        for r, h in zip(ok, ex.map(harmony, ok)):
            r.update(h)
    for r in ok:
        r["ref_distance"] = ref_distance(r, refs) if not r["v"].get("control") else 1.0
    for axis, keys in AXES.items():
        cols = [v2.ranks(ok, k, 1) for k in keys]
        for i, r in enumerate(ok):
            r[axis] = sum(c[i] for c in cols)
    ax = list(AXES)
    front = [r for r in ok if not any(all(o[a] <= r[a] for a in ax) and any(o[a] < r[a] for a in ax) for o in ok if o is not r)]
    ctrl = [r for r in ok if r["v"].get("control")]
    beaten = not any(r in front for r in ctrl)
    with open(os.path.join(v2.OUT, dst), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"passed": len(ok) - len(ctrl), "of": len(rows) - len(ctrl), "front": front, "control_beaten": beaten,
                   "all": [{k: r.get(k) for k in ("v", "actions", "reach", "clutter", "covered", "controls", "heights", "sprawl", "heavy", "uncovered_rules", "unread", "ref_distance") + tuple(ax)} for r in ok]},
                  fh, indent=1, ensure_ascii=False)
    print("passed", len(ok) - len(ctrl), "front", len(front), "control beaten", beaten)
    for r in sorted(front, key=lambda r: sum(r[a] for a in ax)):
        print(r["v"], " ".join("%s %.0f" % (a, r[a]) for a in ax), {k: r[k] for k in ("actions", "reach", "clutter", "covered", "unread", "ref_distance")})
    if not beaten:
        sys.exit(2)


if __name__ == "__main__":
    if "--merge" in sys.argv:
        merge_run()
        rank("repeat-merge.json", "repeat-merge-rank.json")
    elif "--rank" in sys.argv:
        rank()
    else:
        main()
