"""The T1.8 section of docs/screens/t1/screens.html: toasts, dialogs and actions as the owner approved them (decision 17,
2026-10-09), images inlined as greyscale WebP. tier_t1.py builds the page.
"""
import base64
import html as H
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402
import kit  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402
import actions_opt as A  # noqa: E402
import toast_opt as T  # noqa: E402

HEADER = '<div class="hdr"><span class="ttl">%s</span>%s%s%s</div>' % (t.TITLE, kit.icon_button("⌕", "Search"), kit.icon_button("✎", "Edit"), kit.icon_button("⚙", "Settings"))


def today(overlay=""):
    return A.today(overlay, header=HEADER)


def decided(document):
    """An older part's Today drawn as decided: ⌕ ✎ ⚙ top right, and each row's label dot."""
    document = re.sub(r'<div class="hdr"><span class="ttl">' + re.escape(t.TITLE) + r'</span>.*?</div>', lambda m: HEADER, document, count=1, flags=re.S)
    return A.with_dots(document)


def empty_in_place():
    """Trash as decided (grouped), its Empty Trash turned into the held confirmation in place."""
    d = A.t_doc({"pages": "grouped"})
    return d.replace('<span class="act2 hold" data-tap="Empty">🗑 Empty</span>', '<span class="btn fill hold" data-tap="Go" style="font-size:13px;padding:0 12px">🗑 Hold to empty</span>', 1)


def failure():
    """Part F's banner, on Today as decided."""
    html = T.today_html().replace('<div class="cap"', '<div class="banner"><span class="t">%s</span><span class="btn text" data-tap="Fix">Fix</span></div><div class="cap"' % T.FAIL, 1)
    return decided(A.doc(html))


def trash_selected():
    rows = "".join('<div class="grp%s" data-tap="Group %s"><span class="ck3%s" style="margin-right:10px"></span><span class="t">%s</span><span class="n">%d with it</span>▸</div>' % (
        " sel" if i < 2 else "", p, " on" if i < 2 else "", kit.ud(p), len(c)) for i, (p, c) in enumerate(A.TRASHED))
    head = A.sel_header(2, [("Restore", "↺ 2"), ("Delete forever", "🗑 2")]).replace('data-tap="A Delete forever"', 'data-tap="A Delete forever" style="box-shadow:inset 0 -3px 0 var(--dim)"')
    return A.doc(kit.phone(head, '<div class="c2"><div class="trsec">PAGES · 18</div>%s</div>' % rows, kit.bar("Hub")))


def edit_menu():
    menu = '<div class="menu3" style="top:52px">%s</div>' % "".join('<div class="mi2" data-tap="%s"><span class="t">%s</span></div>' % (a, l) for a, l in (
        ("Select", "☐ Select"), ("Sort", "⇅ Sort: by hand"), ("Sort name", "    by name"), ("Sort edited", "    by last edited")))
    html = A.n_screen("Pages", "overflow")
    html = re.sub(r'<div class="hdr">.*?</div>', '<div class="hdr"><span class="ttl">Pages</span>%s%s%s</div>' % (kit.icon_button("⌕", "Search"), kit.icon_button("✎", "Edit"), kit.icon_button("⚙", "Settings")), html, count=1, flags=re.S)
    return A.doc(html[:-len("</div>")] + menu + "</div>")


STATES = [
    ("Today: ⌕ ✎ ⚙ top right; each row's label dot under its time", lambda: A.doc(today())),
    ("Done, with Undo for 7 s; a swipe sideways clears it", lambda: A.doc(today(T.toast("Done: " + kit.ud("Pay the fine"), "bottom:84px;top:auto")))),
    ("Added from the capture sheet: the toast sits above it; Undo reopens it with what was typed", lambda: decided(T.a_docs({"place": "anchored"})["capture"])),
    ("Three deleted in a row: one toast, ▸ to pick one", lambda: A.doc(today(T.b_toasts({"stack": "merge"})[0]))),
    ("A long press selects; each action says how many it touches", lambda: A.m_doc({"offer": "each"})),
    ("✎ on Pages: Select, and the screen's own edits (Sort)", edit_menu),
    ("Trash: Pages grouped per page; Empty Trash held, top right", lambda: A.t_doc({"pages": "grouped"})),
    ("Trash, two groups selected: Restore, or Delete forever (held)", trash_selected),
    ("Empty Trash: confirmed in place, by holding", empty_in_place),
    ("Changed on two devices: a card on Today", lambda: decided(A.doc(T.d_today({"form": "card", "answer": "stacked", "words": "words"})))),
    ("…its answer: the versions stacked, in words", lambda: T.doc(T.d_page({"form": "card", "answer": "stacked", "words": "words"}))),
    ("A failure: a banner under the header until fixed", failure),
    ("A permission, asked when first needed", lambda: T.e_doc({"when": "need"})),
    ("The capture sheet closed with text not added: Undo for 7 s", lambda: decided(A.doc(T.with_overlay(T.today_html(), T.toast("Draft discarded", "bottom:84px;top:auto"))))),
]
TABLE = [
    ("Where the toast sits", "Anchored: above the capture sheet when it is open, otherwise above the bar. Hides nothing; reach 2.40.", "A"),
    ("Undo", "7 s; several in a row merge into one (▸ to pick one); a sideways swipe clears it. After it, Trash and \"Done today\". Undo after Add reopens the sheet with what was typed.", "B"),
    ("Destructive confirmation", "Only Delete forever and Empty Trash ask: in place, near the thumb, held. Empty Trash stays top right.", "C"),
    ("Sync clash", "A card on Today; the versions stacked; Keep this / Keep both in words.", "D"),
    ("Permissions", "Asked when a feature first needs them, after a sheet that says why.", "E"),
    ("Failures", "A banner under the header until fixed.", "F"),
    ("Text not added", "Discarded, with Undo for 7 s.", "H"),
    ("An element's actions; selecting", "A long press selects; one selected shows its actions in the header; more taps add. Select is also under ✎. Pairing score 60 (no clash, one model).", "I, S, X"),
    ("A mixed selection", "Each action where it applies, saying how many it touches.", "M"),
    ("A screen's actions", "Top right: ⌕ Search, ✎ Edit (Select, Sort, Edit home), ⚙ Settings.", "N"),
    ("Trash's Pages section", "One group per page, with what went with it: 7 actions, 4 rows read, against 9 and 10.", "T"),
]


def uri(doc, w=360, h=740, show=300):
    im = Image.open(ss.render(doc, w, h)).convert("L")
    im = im.resize((show, round(im.height * show / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=55)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def section():
    """The approved T1.8 section, for screens.html (owner, 2026-10-09: "add this in the screens HTML file")."""
    figs = "".join('<figure><img src="%s" width="300" alt="%s"><figcaption>%s</figcaption></figure>' % (uri(f()), H.escape(c), H.escape(c)) for c, f in STATES)
    desk = '<figure><img src="%s" width="560" alt="Windows"><figcaption>Windows: the toast at the foot of the column the action was in</figcaption></figure>' % uri(T.a_desk({"place": "anchored"}), 1100, 660, 560)
    rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % tuple(H.escape(x) for x in r) for r in TABLE)
    return ('<section id="t1-8"><h2>T1.8 Toasts, dialogs and actions <span class="tag">approved</span></h2>'
            '<p>Decision 17, approved 2026-10-09. Every part was scored with a control (<a href="toasts-scores.html">the tables</a>, '
            '<a href="toasts-options.html">every option drawn</a>); the words follow <a href="actions-inventory.md">the actions inventory</a>: '
            'Delete moves to Trash, Restore and Delete forever live in Trash, and only Delete forever and Empty Trash are held.</p>'
            '<h3>Decided by</h3><table><tr><th>Part</th><th>Choice and its measure</th><th>Scored as</th></tr>%s</table>'
            '<h3>Phone</h3><div class="refs">%s</div><h3>Windows</h3><div class="refs">%s</div></section>') % (rows, figs, desk)


if __name__ == "__main__":
    print(len(section()))
