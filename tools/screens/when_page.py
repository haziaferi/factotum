"""The approved When sheet (T1.5 + T1.6 merged, decision 17) for screens.html: its states rendered from the interactive
prototype itself (docs/screens/t1/when-prototype.html), so the page shows exactly what was tried and measured.

Each state is the prototype with a script that sets it; screen_score renders it (headless Edge). Phone at 360 x 740;
Windows as the same sheet in a panel under the quick-add window, 1100 x 660. PNGs go to docs/screens/t1/when/.

    PYTHONUTF8=1 python tools/screens/when_page.py      (tier_t1.py calls section())
"""
import html
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import screen_score as ss  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
T1 = os.path.join(ROOT, "docs", "screens", "t1")
PAGE = os.path.join(T1, "when-prototype.html")
IMG = os.path.join(T1, "when")
ONLY_PHONE = ("<style>body{padding:0!important}h1,.dim,.side{display:none!important}.wrap{display:block}"
              ".phone{border-radius:0;box-shadow:none}</style>")
# Windows: the window instead of the phone, the sheet as a panel over it (opened from the quick-add window's ⋯)
DESK = ("<style>body{padding:0!important}h1,.dim,.side{display:none!important}.wrap{display:block}"
        ".phone{width:1100px!important;height:660px;border-radius:10px;max-width:none}"
        ".today{width:520px;margin:24px auto 0}.gesture{display:none}"
        ".sheet{left:340px;right:auto;width:420px;bottom:auto;top:96px;max-height:540px;border-radius:14px;padding-bottom:10px;box-shadow:0 12px 40px rgba(0,0,0,.28)}</style>")

STATES = [
    ("date", "⋯ › Date: Once, the month showing (day load under the busy days)", "openFrom('date')"),
    ("time", "The time tapped: the 24-hour dial (hours, then minutes) and a typed field", "openFrom('date');S.open='time';E.slot='t0';E.stage='h';render(true)"),
    ("repeat", "⋯ › Repeat: Every, the interval's chooser with the Starting row", "openFrom('repeat')"),
    ("on", "Weekly, \"on\" tapped: the weekdays, Weekdays and Weekends as shortcuts", "openFrom('repeat');S.n=2;S.days=new Set([1,3]);S.open='on';render(true)"),
    ("month", "Monthly, \"on\" tapped: the day of the month or the weekday of the month, one at a time",
     "openFrom('repeat');setUnit('month');S.mmode='wom';S.ord=2;S.owd=1;S.open='on';render(true)"),
    ("window", "Every 30 minutes on weekdays: the window", "openFrom('repeat');setUnit('minute');S.n=30;S.days=new Set([0,1,2,3,4]);S.open='time';E.slot='a';E.stage='h';render(true)"),
    ("random", "Every 2–4 days at random, bounded by a window", "openFrom('repeat');setUnit('day');S.random=true;S.time.kind='window';S.time.a='09:00';S.time.b='12:00';S.open='interval';render(true)"),
    ("until", "\"forever\" tapped, Until: the start plus 3 months, or a date", "openFrom('repeat');S.end.kind='until';S.open='end';render(true)"),
    ("closed", "Closed: the rule, its cron line, Undo and Redo, the next dates", "openFrom('repeat');S.n=2;S.days=new Set([1,3]);S.open=null;render(true);past=['x'];render(true)"),
]


def doc(setup, css):
    page = open(PAGE, encoding="utf-8").read()
    return page.replace("</head>", css + "</head>").replace("</body>", "<script>%s</script></body>" % setup)


def render_all():
    os.makedirs(IMG, exist_ok=True)
    out = []
    for name, cap, setup in STATES:
        png = ss.render(doc(setup, ONLY_PHONE), 360, 740)
        shutil.copy(png, os.path.join(IMG, name + ".png"))
        out.append((name, cap))
    png = ss.render(doc("openFrom('repeat')", DESK), 1100, 660)
    shutil.copy(png, os.path.join(IMG, "desk-repeat.png"))
    png = ss.render(doc("openFrom('date')", DESK), 1100, 660)
    shutil.copy(png, os.path.join(IMG, "desk-date.png"))
    return out


TABLE = [
    ("Time entry", "the dial with a typed field (T1.5's measure: 13 actions against 27 for wheels)", "picker3-actions.json"),
    ("Dial size", "24-hour, two rings; inner hours 32 dp apart, 250 dp across (owner's exception to 48 dp for the inner ring)", "decision 17"),
    ("Changing a repeat's start", "a Starting row in the interval's chooser: the shortest foot (121 px) and calmest (clutter 0.029); +1 tap from a closed sentence", "when-start.json"),
    ("Entries", "⋯ › Date and ⋯ › Repeat into one sheet: 14–27 fewer taps over T1.5's and T1.6's 14 tasks than one ⋯ › When", "decision 17"),
    ("Rules", "minutes and hours take a window; at random needs a bound; a random time takes a count per day; after it's done hides \"on\"; impossible options are not drawn", "decision 17"),
]


def section():
    states = render_all()
    imgs = "".join('<figure><img src="when/%s.png" width="300" alt="%s"><figcaption>%s</figcaption></figure>' % (n, html.escape(c), html.escape(c)) for n, c in states)
    rows = "".join("<tr><td>%s</td><td>%s</td><td><code>%s</code></td></tr>" % (html.escape(a), html.escape(b), c) for a, b, c in TABLE)
    return ('<section id="t1-5"><h2>T1.5 + T1.6 When: dates, times and repeats <span class="tag">approved</span></h2>'
            '<p>One sentence replaces the date and time picker and the repeat builder (owner\'s workshop, 2026-10-08): '
            '<b>Once</b> on [date] [time], or <b>Every</b> [interval] [on days] [time], [end]. Tapping a word opens its one chooser '
            'above the sentence; the sheet grows upward only, so the sentence stays put; Undo and Redo sit under it; impossible '
            'combinations are not drawn. Typing on the capture line sets dates and repeats without opening it; tapping a highlighted '
            'date offers only "Keep as text". <a href="when-prototype.html">Open the interactive prototype</a>.</p>'
            '<h3>Decided by</h3><table><tr><th>Part</th><th>Choice and its measure</th><th>Record</th></tr>%s</table>'
            '<h3>Phone</h3><div class="refs">%s</div>'
            '<h3>Windows</h3><p class="dim">The same sheet as a panel over the window, opened from the quick-add window'"'"'s ⋯.</p>'
            '<div class="refs"><figure><img src="when/desk-repeat.png" width="560" alt="Windows, Repeat"><figcaption>⋯ › Repeat</figcaption></figure>'
            '<figure><img src="when/desk-date.png" width="560" alt="Windows, Date"><figcaption>⋯ › Date</figcaption></figure></div></section>') % (rows, imgs)


if __name__ == "__main__":
    print(len(section()))
