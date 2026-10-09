"""T1.9 empty and error states, drawn as the owner chose them (decision 17, 2026-10-09).

    python tools/screens/t19_page.py      docs/screens/t1/screens-t1-9.html, for the owner's approval

Once approved, section() goes into screens.html as T1.8's did.
"""
import html as H
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402
import tier_t1 as t  # noqa: E402
import empty_opt as E  # noqa: E402
import t18_page as P  # noqa: E402

E.SCREENS["Today"] = (t.TITLE, "Nothing here.", "Add a task", "Add anything…")   # owner: "nothing here", done or not


def today_done():
    body = ('<div class="cap" data-tap="Capture">+ <span>Add anything…</span></div>' + kit.zone("", '<div class="fold" data-tap="Done today"><span class="t">Done today · 3</span>▸</div>') +
            '<div class="empty-c"><span>Nothing here.</span><span class="btn fill" data-tap="Act">Add a task</span></div>')
    return E.doc(kit.phone(E.header(t.TITLE), body, kit.bar("Today")))


STATES = [
    ("Today, nothing planned: one sentence, one button, centred", lambda: E.doc(E.empty_phone("centred", "Today"))),
    ("Today, all done: the same sentence; Done today · n above it", today_done),
    ("Pages, empty", lambda: E.doc(E.empty_phone("centred", "Pages"))),
    ("Reminders, empty", lambda: E.doc(E.empty_phone("centred", "Reminders"))),
    ("A search that finds nothing names what was looked for; the field's ✕ clears it", lambda: E.doc(E.noresult_phones({"form": "centred", "words": "repeat", "action": "none"})[0])),
    ("A label filter that leaves nothing; the chip's ✕ clears it", lambda: E.doc(E.noresult_phones({"form": "centred", "words": "repeat", "action": "none"})[1])),
    ("A field's error: a line under the field", lambda: E.doc(E.field_phone({"form": "inline"}))),
    ("A failure: what happened, and Fix", lambda: E.doc(E.banner_phone({"words": "what"}))),
    ("First run: a tour of three cards (1 of 3)", lambda: E.doc(E.first_phone({"start": "tour"}))),
    ("Loading: what is on this device shows at once; newer rows slide in", lambda: E.doc(E.loading_phone({"show": "progressive"}))),
]
TABLE = [
    ("Empty screens", "One sentence and one button, centred (sum 26.5); the sentence names the screen's kind, the button adds one.", "empty"),
    ("Today with nothing to show", "\"Nothing here.\" whether all is done or nothing was planned; the Done today fold stays (decision 15).", "done"),
    ("Filtered to nothing", "Centred, naming what was looked for; the field's ✕ or the chip clears it (sum 31.5).", "noresult"),
    ("A field's error", "A line under the field, while it is wrong (sum 25).", "field"),
    ("A failure", "What happened, and Fix: \"Sync folder unreachable.\" (sum 19.5).", "banner"),
    ("First run", "Three cards before Today (3 taps).", "first"),
    ("Loading", "What is already on the device at once; nothing moves (sum 10).", "loading"),
]


def section(tag="approved"):
    figs = "".join('<figure><img src="%s" width="300" alt="%s"><figcaption>%s</figcaption></figure>' % (P.uri(f()), H.escape(c), H.escape(c)) for c, f in STATES)
    desk = '<figure><img src="%s" width="560" alt="Windows"><figcaption>Windows: an empty Today column</figcaption></figure>' % P.uri(E.empty_desk("centred"), 1100, 660, 560)
    rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % tuple(H.escape(x) for x in r) for r in TABLE)
    return ('<section id="t1-9"><h2>T1.9 Empty and error states <span class="tag">%s</span></h2>'
            '<p>Decision 17, 2026-10-09. The rule: one plain sentence and one action, no illustration, no cheer, no guilt (2026-10-07). '
            'Every part was scored with a control and its tone measured (<a href="empty-scores.html">the tables</a>, <a href="empty-options.html">every option drawn</a>).</p>'
            '<h3>Decided by</h3><table><tr><th>Part</th><th>Choice and its measure</th><th>Scored as</th></tr>%s</table>'
            '<h3>Phone</h3><div class="refs">%s</div><h3>Windows</h3><div class="refs">%s</div></section>') % (tag, rows, figs, desk)


if __name__ == "__main__":
    css = ("body{background:#f4f4f2;color:#1d1d1b;font:14px/1.45 system-ui,sans-serif;margin:0;padding:16px;max-width:1300px}"
           "table{border-collapse:collapse;font-size:13px}td,th{border-bottom:1px solid #ddd;padding:5px 8px;text-align:left;vertical-align:top}"
           ".refs{display:flex;gap:14px;flex-wrap:wrap;align-items:flex-start}figure{margin:0;max-width:300px}figcaption{font-size:12px;color:#6b6b66}"
           ".tag{font-size:12px;border:1px solid #6b6b66;border-radius:10px;padding:1px 8px}")
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Empty And Error States</title>'
            '<style>%s</style></head><body><p><a href="screens.html">‹ T1, the approved screens</a></p>%s</body></html>') % (css, section("decided, awaiting approval"))
    path = os.path.join(E.T.OUT, "screens-t1-9.html")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    print(path, len(page))
