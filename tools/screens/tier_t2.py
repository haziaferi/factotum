"""T2 items, calendar and alarms: the approved screens (decision 18), drawn into docs/screens/t2/screens.html.

    python tools/screens/tier_t2.py

Every drawing comes from t2_opt's own functions with the owner's picks, so the page shows what was scored. Each
screen in light and dark on the phone, and on Windows where it has a Windows form (the alarm rings on the phone only).
Images are greyscale WebP, inlined; the page is kept under 512 KiB as T1's is (tier_t1.fit_size).
"""
import base64
import html as H
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import screen_score as ss  # noqa: E402
import t2_opt as M  # noqa: E402
import tier_t1 as t  # noqa: E402

PAGE = {"form": "inplace", "fields": "all", "save": "auto"}
CAL = ("week", "tabs")
DAY = {"layout": "hours", "show": "everything", "filter": "chips"}
REM = {"order": "next", "group": "days", "skip": "inplace"}
ALARM = {"form": "full", "dismiss": "slide", "snooze": "one", "skip": "upcoming"}


def img(d, w=360, h=740, show=240):
    from PIL import Image
    im = Image.open(ss.render(d, w, h)).convert("L")
    im = im.resize((show, round(im.height * show / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=60)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def fig(cap, d, w=360, h=740, show=240):
    return '<figure><img src="%s" width="%d" alt="%s"><figcaption>%s</figcaption></figure>' % (img(d, w, h, show), show, H.escape(cap), H.escape(cap))


def phone(cap, make):
    """A phone screen in light and dark; make(theme) returns the document."""
    return fig(cap, make("light")) + fig(cap + " (dark)", make("dark"))


def desk(cap, d):
    return fig(cap + " (Windows)", d, 1100, 660, 520)


def sections():
    out = []
    out.append(("Calendar: Week (the default)", "Tabs Week · Month · 3 days. Week is the planner: the days as cells, each listing its things with "
                "their start times; a tapped day opens the Day screen.",
                phone("Week", lambda th: M.doc(M.cal_phone(*CAL), th)) + desk("Week", M.cal_desk(*CAL))))
    out.append(("Calendar: Month", "A tapped date opens the Day screen.",
                phone("Month", lambda th: M.doc(M.cal_phone("month", "tabs"), th)) + desk("Month", M.cal_desk("month", "tabs"))))
    out.append(("Calendar: 3 days", "The time grid, titles wrapping in their blocks, clashes side by side, the line at the current time.",
                phone("3 days", lambda th: M.doc(M.cal_phone("3day", "tabs"), th)) + desk("3 days", M.cal_desk("3day", "tabs"))))
    out.append(("The Day screen", "Opened from a day in Week or Month: all the hours down the left, opened at the day's first thing, the "
                "line at the current time, every thing a block with its times, the untimed in a strip above; chips show one kind.",
                phone("Mon 5 Oct", lambda th: M.day_doc(DAY, th)) + desk("Mon 5 Oct", M.day_desk(DAY))))
    out.append(("An item's page", "The row grows in place, every field shown (an unset one reads \"Add a reminder\"), each change kept as "
                "made with Undo.",
                "".join(phone(k.capitalize(), (lambda kk: lambda th: M.doc(M.page_phone(kk, PAGE), th))(k)) for k in M.FIELDS) + desk("A task", M.page_desk(PAGE))))
    out.append(("The Reminders list", "Soonest first under day headers. A tap grows the row in place, as an item's page does; Skip for "
                "today sits under When, and the skipped row folds into \"Done today\".",
                phone("Reminders", lambda th: M.doc(M.rem_phone(REM), th)) + phone("A reminder open", lambda th: M.doc(M.rem_skip_doc(REM), th)) +
                desk("Reminders", M.rem_desk(REM))))
    out.append(("The alarm ringing", "Full screen over the lock screen and any app: the time, what it is, one large Snooze, and Slide to "
                "dismiss at the foot. Skip for today comes an hour before, in a quiet notification.",
                phone("Ringing", lambda th: M.doc(M.alarm_phone(ALARM), th)) + fig("An hour before: Skip for today", M.upcoming_doc())))
    return out


CSS = """
:root{--bg:#f4f4f2;--ink:#1d1d1b;--dim:#5f5f5b;--card:#ffffff;--line:#d9d9d5}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121211;--ink:#ecece8;--dim:#a3a39e;--card:#1c1c1a;--line:#33332f}}
:root[data-theme="dark"]{--bg:#121211;--ink:#ecece8;--dim:#a3a39e;--card:#1c1c1a;--line:#33332f}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:36px 0 4px}
p{margin:0 0 12px;color:var(--dim);max-width:72ch}
.figs{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start}
figure{margin:0;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:8px}
figure img{display:block;max-width:100%;height:auto;border-radius:6px}
figcaption{font-size:13px;color:var(--dim);margin-top:6px}
"""


def main():
    body = ['<h1>T2: items, calendar and alarms</h1><p>The approved screens (decision 18, owner, 2026-10-12 and 13), in greys, '
            'placeholder data in dotted outlines. The options not picked, their scores and the reasons are in t2-options.html, '
            't2-scores.html and decisions/18-screens-t2.md.</p>']
    for title, intro, figs in sections():
        body.append('<section><h2>%s</h2><p>%s</p><div class="figs">%s</div></section>' % (H.escape(title), H.escape(intro), figs))
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>T2 screens</title><style>%s</style></head><body><main>%s</main></body></html>') % (CSS, "".join(body))
    page = t.fit_size(page)
    out = os.path.join(M.T.OUT, "screens.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    print(out, len(page.encode("utf-8")))


if __name__ == "__main__":
    main()
