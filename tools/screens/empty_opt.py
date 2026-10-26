"""T1.9 empty and error states (decision 17, owner's answers 2026-10-09), scored as T1.8 was, with a control per part.
The rule from 2026-10-07 stands: one plain sentence and one action, no illustration, no cheer, no guilt.

    python tools/screens/empty_opt.py empty done noresult field banner first loading   score parts (empty-<part>.json)
    python tools/screens/empty_opt.py page scores                                       empty-options.html, empty-scores.html

Tone is measured on every sentence the drawings show:
  words; reading grade (Flesch-Kincaid, syllables counted as vowel groups, an estimate); cheer (words that congratulate,
  exclamation marks, emoji); blame (words that put the fault on the user). The word lists are below and are the
  assumption: they come from the 2026-10-07 rule, not from a study.
References: docs/screens/t1/empty-references.json (16 phone apps), compared on "form".
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402
import actions_opt as A  # noqa: E402
import toast_opt as T  # noqa: E402

CHEER = ["great", "awesome", "well done", "nice", "yay", "congrat", "good job", "you did it", "enjoy", "all clear", "woo", "amazing", "oops"]
BLAME = ["you forgot", "you haven't", "you didn't", "you failed", "you must", "invalid", "wrong", "not allowed"]
EMOJI = re.compile("[\U0001F300-\U0001FAFF]")  # pictographs only: interface glyphs (⚙ ✎ ☰) sit in U+2600-27BF and are not cheer


def tone(text):
    """(words, grade, cheer, blame) of the sentences a state shows."""
    s = re.sub(r"<.*?>", " ", text)
    words = re.findall(r"[A-Za-z']+", s)
    if not words:
        return 0, 0.0, 0, 0
    sentences = max(1, len(re.findall(r"[.!?]", s)))
    syl = sum(max(1, len(re.findall(r"[aeiouy]+", w.lower())) - (1 if w.lower().endswith("e") and len(w) > 3 else 0)) for w in words)
    grade = 0.39 * len(words) / sentences + 11.8 * syl / len(words) - 15.59
    low = s.lower()
    cheer = sum(low.count(c) for c in CHEER) + s.count("!") + len(EMOJI.findall(s))
    blame = sum(low.count(b) for b in BLAME)
    return len(words), round(grade, 1), cheer, blame


CSS = """
.empty-c{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;text-align:center;color:var(--dim);font-size:15px;padding:0 24px}
.empty-i{min-height:48px;display:flex;align-items:center;padding:0 12px;color:var(--dim);font-size:15px}
.example{min-height:48px;display:flex;align-items:center;gap:10px;padding:0 12px;color:var(--dim);opacity:.55;border:1px dashed var(--dim);border-radius:10px;font-size:15px}
.illu{width:150px;height:150px;border-radius:50%;background:var(--zone2)}
.skel{height:14px;border-radius:7px;background:var(--zone2);margin:17px 12px}
.spin{width:40px;height:40px;border-radius:50%;border:4px solid var(--zone2);border-top-color:var(--ink)}
.field{min-height:48px;border-radius:12px;box-shadow:inset 0 0 0 1px var(--dim);display:flex;align-items:center;padding:0 12px;font-size:15px;color:var(--dim)}
.ferr{font-size:13px;color:var(--ink);padding:4px 12px 0}
"""
HEADER = '<div class="hdr"><span class="ttl">%s</span>%s%s%s</div>'


def header(title):
    return HEADER % (title, kit.icon_button("⌕", "Search"), kit.icon_button("✎", "Edit"), kit.icon_button("⚙", "Settings"))


def doc(html, theme="light"):
    return A.doc(html, theme).replace("</style>", CSS + "</style>", 1)


SCREENS = {  # title, the sentence, the action's word, the capture placeholder (T1.3's, by screen)
    "Today": (t.TITLE, "Nothing planned for today.", "Add a task", "Add anything…"),
    "Pages": ("Pages", "No pages yet.", "New page", "Write a page title…"),
    "Reminders": ("Reminders", "No reminders yet.", "New reminder", "Remind me to…"),
}


def empty_body(form, sentence, word, placeholder):
    cap = '<div class="cap" data-tap="Capture">+ <span>%s</span></div>' % placeholder
    if form == "centred":
        return cap + '<div class="empty-c"><span>%s</span><span class="btn fill" data-tap="Act">%s</span></div>' % (sentence, word)
    if form == "inline":
        return cap + kit.zone("", '<div class="empty-i">%s</div>' % sentence)
    if form == "placeholder":
        return cap
    if form == "example":
        return cap + kit.zone("", '<div class="empty-i">%s</div><div class="example">e.g. %s</div>' % (sentence, "Call the bank at 15:00"))
    return cap + ('<div class="empty-c"><div class="illu"></div><span style="font-size:18px;color:var(--ink)">All clear! 🎉 Enjoy your free day!</span>'
                  '<span class="btn fill" data-tap="Act">%s</span><span class="btn text" data-tap="Templates">Browse templates</span></div>' % word)


def empty_phone(form, screen):
    title, sentence, word, ph = SCREENS[screen]
    return kit.phone(header(title), empty_body(form, sentence, word, ph), kit.bar("Today" if screen == "Today" else ("Pages" if screen == "Pages" else "Hub")))


def empty_desk(form):
    title, sentence, word, ph = SCREENS["Today"]
    head = '<div class="hdr"><span class="ttl">%s</span><span class="srch" data-tap="Search" style="width:320px">⌕ Search everything <span class="kbd">Ctrl+K</span></span></div>' % title
    col = '<div class="dcol" style="display:flex;flex-direction:column">%s</div>' % empty_body(form, sentence, word, ph)
    return kit.document(kit.desk(kit.rail("Today"), head, col + '<div class="page"></div>'), "light", t.EXTRA + t.T12_CSS + A.CSS + CSS, True)


def shown_text(document):
    body = document[document.index("<body"):].split('<div class="bar">')[0]   # the bar and what follows it are not the state's words
    body = re.sub(r'<div class="(hdr|rail)".*?</div>', " ", body, flags=re.S)
    return re.sub(r"<[^>]+>", " ", body)


# ---- part: empty ------------------------------------------------------------------------------------------------------
"""
  form  centred (the sentence and a button in the middle), inline (the sentence where the first row would be; the capture
        line is the action), placeholder (the capture line's placeholder alone), example (the sentence and one greyed
        example row, dotted)
  Screens: Today, Pages, Reminders; Windows' Today too. Task: add the first item: one tap on the button or the capture
  line (then typing, the same for all). Measured: reach to the way in, the empty block's height, clutter, words, grade,
  cheer, blame.
  Control: an illustration, "All clear! 🎉 Enjoy your free day!", and two buttons.
"""
EMPTY_SPACE = {"form": ["centred", "inline", "placeholder", "example"]}


def score_empty(v):
    f = "illustration" if v.get("control") else v["form"]
    reach, cl, block, txt = [], [], [], ""
    for sc in SCREENS:
        d = doc(empty_phone(f, sc))
        tp = {x["name"]: x for x in ss.measure(d, 360, 740)["taps"]}
        way = tp.get("Act") or tp.get("Capture")
        reach.append(T.fitts(T.THUMB, way))
        cl.append(sum(ss.edge_density(ss.render(doc(empty_phone(f, sc), th), 360, 740)) for th in ("light", "dark")) / 2)
        block.append(T.probe(d, "t19-block-%s-%s" % (f, sc), "(function(){var e=document.querySelector('.empty-c,.empty-i');if(!e)return 0;var z=e.closest('.zone')||e;return Math.round(z.getBoundingClientRect().height)})()"))
        txt += " " + shown_text(d)
    w, g, c, b = tone(txt.replace("+", ""))
    desk = empty_desk(f)
    dtp = {x["name"]: x for x in ss.measure(desk, 1100, 660)["taps"]}
    return {"reach": round(sum(reach) / len(reach), 3), "block_px": round(sum(block) / len(block)), "words": w, "grade": g, "cheer": c, "blame": b,
            "small": [], "clutter": round(sum(cl) / len(cl), 4), "desk_clutter": T.clutter_of(lambda th: desk.replace('data-theme="light"', 'data-theme="%s"' % th), 1100, 660),
            "desk_way": int(bool(dtp.get("Act") or dtp.get("Capture")))}


# ---- part: done --------------------------------------------------------------------------------------------------------
"""
  sentences  one ("Nothing for today." whether all is done or nothing was planned), two ("Nothing left for today." when
             all is done, "Nothing planned for today." when nothing was)
  fold       kept (the "Done today · n" fold stays under the sentence when things were done), hidden
  Measured: whether the screen says which of the two it is (two sentences, or the fold), words, cheer, rows used, clutter.
  Control: "Great job! You finished everything 🎉" with an illustration, the fold hidden.
"""
DONE_SPACE = {"sentences": ["one", "two"], "fold": ["kept", "hidden"]}


def done_phone(v):
    if v.get("control"):
        body = '<div class="cap" data-tap="Capture">+ <span>Add anything…</span></div><div class="empty-c"><div class="illu"></div><span style="font-size:18px;color:var(--ink)">Great job! You finished everything 🎉</span></div>'
    else:
        s = "Nothing for today." if v["sentences"] == "one" else "Nothing left for today."
        fold = '<div class="fold" data-tap="Done today"><span class="t">Done today · 3</span>▸</div>' if v["fold"] == "kept" else ""
        body = '<div class="cap" data-tap="Capture">+ <span>Add anything…</span></div>' + kit.zone("", '<div class="empty-i">%s</div>%s' % (s, fold))
    return kit.phone(header(t.TITLE), body, kit.bar("Today"))


def score_done(v):
    d = doc(done_phone(v))
    w, g, c, b = tone(shown_text(d).replace("+", ""))
    tells = 1 if (not v.get("control") and (v["sentences"] == "two" or v["fold"] == "kept")) else 0
    rows = 2 if (not v.get("control") and v["fold"] == "kept") else 1
    return {"tells_which": tells, "words": w, "cheer": c, "blame": b, "rows": rows, "small": [], "clutter": T.clutter_of(lambda th: doc(done_phone(v), th))}


# ---- part: noresult ----------------------------------------------------------------------------------------------------
"""
  form    centred, inline (where the first result would be)
  words   repeat ('No pages match "zqxjw".' / 'Nothing labelled Calm today.'), plain ("No results.")
  action  clear (a "Clear search" / "Clear filter" button), none (the search field's ✕ or the filter chip, as always)
  Contexts: a Pages search for "zqxjw"; Today filtered by the label Calm. Task: back to everything: the button (1) or
  the field's ✕ / the chip (1); measured reach to it. Measured also: whether it names what was looked for, tone, clutter.
  Control: an illustration, "Oops! Nothing here 😕", and two buttons.
"""
NORESULT_SPACE = {"form": ["centred", "inline"], "words": ["repeat", "plain"], "action": ["clear", "none"]}


def noresult_phones(v):
    out = []
    for ctx in ("search", "filter"):
        if v.get("control"):
            msg = '<div class="empty-c"><div class="illu"></div><span style="font-size:18px;color:var(--ink)">Oops! Nothing here 😕</span><span class="btn fill" data-tap="Clear">Try again</span><span class="btn text">Help</span></div>'
            inner = msg
        else:
            s = ('No pages match “zqxjw”.' if ctx == "search" else "Nothing labelled Calm today.") if v["words"] == "repeat" else "No results."
            btn = '<span class="btn text" data-tap="Clear">%s</span>' % ("Clear search" if ctx == "search" else "Clear filter") if v["action"] == "clear" else ""
            inner = ('<div class="empty-c"><span>%s</span>%s</div>' % (s, btn)) if v["form"] == "centred" else kit.zone("", '<div class="empty-i">%s</div>%s' % (s, btn))
        if ctx == "search":
            top = '<div class="field" style="margin:4px 0"><span style="flex:1">%s</span><span class="ib" data-tap="X">✕</span></div>' % kit.ud("zqxjw")
            out.append(kit.phone(kit.header("Search", (), ("‹", "Back")), top + inner, kit.bar("Pages")))
        else:
            chips = '<div class="c2"><div class="fbar">%s</div></div>' % R_chip()
            out.append(kit.phone(header(t.TITLE), chips + inner, kit.bar("Today")))
    return out


def R_chip():
    import repeat_opt as R
    return R.ch("Chip Calm", '<span class="dots"><i></i></span>&nbsp;Calm', True) + R.ch("Clear chip", "✕")


def score_noresult(v):
    reach, txt, cl = [], "", []
    for h in noresult_phones(v):
        d = doc(h)
        tp = {x["name"]: x for x in ss.measure(d, 360, 740)["taps"]}
        way = tp.get("Clear") or tp.get("X") or tp.get("Clear chip")
        reach.append(T.fitts(T.THUMB, way))
        txt += " " + shown_text(d)
        cl.append(sum(ss.edge_density(ss.render(doc(h, th), 360, 740)) for th in ("light", "dark")) / 2)
    w, g, c, b = tone(txt)
    names = 0 if v.get("control") else int(v["words"] == "repeat")
    return {"reach": round(sum(reach) / len(reach), 3), "names_it": names, "words": w, "grade": g, "cheer": c, "blame": b, "small": [], "clutter": round(sum(cl) / len(cl), 4)}


# ---- part: field --------------------------------------------------------------------------------------------------------
"""
  form  inline (a line under the field: "A label needs a name."), toast ("A label needs a name." at the foot for 4 s),
        disabled (Save greyed until there is a name; a tap on it shows the line), silent (Save closes and keeps nothing)
  Case: a new label with no name, Save tapped. Counted: whether it is noticed, whether it says how to fix it, whether
  what was typed is lost; measured: reach to the field to fix it, clutter.
  Control: a dialog, "Error: invalid input", OK.
"""
FIELD_SPACE = {"form": ["inline", "toast", "disabled", "silent"]}


def field_phone(v):
    f = "control" if v.get("control") else v["form"]
    save_cls = "btn fill" + (" dim" if f == "disabled" else "")
    body = '<div class="page2"><div class="field" data-tap="Name">Name</div>%s<div style="display:flex;gap:8px">%s</div></div>' % (
        '<div class="ferr">A label needs a name.</div>' if f == "inline" else "", R_swatches())
    html = kit.phone(kit.header("New label", (("✓", "Save"),), ("‹", "Back")), body, "")
    if f == "toast":
        html = T.with_overlay(html, T.toast("A label needs a name.", "bottom:24px;top:auto").replace('<span class="u" data-tap="Undo">Undo</span>', ""))
    if f == "control":
        html = T.with_overlay(html, '<div class="scrim"></div><div class="dlg" style="top:260px"><h4>Error</h4><p>Invalid input.</p><div class="btns"><span class="btn fill" data-tap="OK">OK</span></div></div>')
    if f == "disabled":
        html = html.replace('data-tap="Save"', 'data-tap="Save" style="opacity:.35"')
    return html


def R_swatches():
    import repeat_opt as R
    return "".join(R.ch("Swatch %d" % i, "●") for i in range(5))


def score_field(v):
    f = "control" if v.get("control") else v["form"]
    d = doc(field_phone(v))
    tp = {x["name"]: x for x in ss.measure(d, 360, 740)["taps"]}
    w, g, c, b = tone(shown_text(d))
    noticed = {"inline": 1, "toast": 1, "disabled": 1, "silent": 0, "control": 1}[f]
    says_fix = {"inline": 1, "toast": 1, "disabled": 1, "silent": 0, "control": 0}[f]
    lost = 1 if f == "silent" else 0
    extra = 1 if f == "control" else 0                   # OK before the field can be reached
    lasts = 0 if f in ("toast",) else 1                 # still readable while fixing
    return {"noticed": noticed, "says_fix": says_fix, "stays": lasts, "lost": lost, "extra_actions": extra, "reach": round(T.fitts(T.THUMB, tp["Name"]), 3),
            "words": w, "blame": b, "small": [], "clutter": T.clutter_of(lambda th: doc(field_phone(v), th))}


# ---- part: banner -----------------------------------------------------------------------------------------------------
"""
  words  whatfix ("Sync folder unreachable. Changes are kept on this phone." + Fix), what ("Sync folder unreachable." +
         Fix), plain ("Sync failed.", no Fix)
  The banner sits under the header (T1.8 F). Counted: says what happened, says the data is safe, has a fix. Measured:
  words, grade, blame, the banner's height, clutter.
  Control: "Error 0x80070005: sync exception" with OK.
"""
BANNER_SPACE = {"words": ["whatfix", "what", "plain"]}
BANNER_TEXT = {"whatfix": ("Sync folder unreachable. Changes are kept on this phone.", "Fix"), "what": ("Sync folder unreachable.", "Fix"),
               "plain": ("Sync failed.", None), "control": ("Error 0x80070005: sync exception", "OK")}


def banner_phone(v):
    text, act = BANNER_TEXT["control" if v.get("control") else v["words"]]
    btn = '<span class="btn text" data-tap="Fix">%s</span>' % act if act else ""
    return A.today().replace('<div class="cap"', '<div class="banner"><span class="t">%s</span>%s</div><div class="cap"' % (text, btn), 1).replace(
        re.search(r'<div class="hdr">.*?</div>', A.today(), re.S).group(0), header(t.TITLE), 1)


def score_banner(v):
    k = "control" if v.get("control") else v["words"]
    d = doc(banner_phone(v))
    w, g, c, b = tone(BANNER_TEXT[k][0])
    h = T.probe(d, "t19-banner-" + k, "(function(){var e=document.querySelector('.banner');return e?Math.round(e.getBoundingClientRect().height):0})()")
    return {"says_what": 0 if k == "control" else 1, "says_safe": 1 if k == "whatfix" else 0, "has_fix": 1 if k in ("whatfix", "what") else 0,
            "words": w, "grade": g, "blame": b, "banner_px": h, "small": [], "clutter": T.clutter_of(lambda th: doc(banner_phone(v), th))}


# ---- part: first -------------------------------------------------------------------------------------------------------
"""
  start  straight (the first open is Today, empty, as part "empty" decides), intro (one sheet: what Factotum keeps, and
         Start), tour (three cards before Today)
  Counted: taps before the app is usable, sentences read before it. Measured on the first screen: clutter, cover.
  Control: five onboarding screens, an account prompt, and every permission asked at once.
"""
FIRST_SPACE = {"start": ["straight", "intro", "tour"]}
FIRST_TEXT = {"straight": "", "intro": "Factotum keeps your tasks, events, habits and pages in one place, on this device.",
              "tour": "Capture anything from the line at the top. Your day is on Today. Everything else is in the Hub.",
              "control": "Welcome to Factotum! Let's get you set up. Create an account to sync. Allow notifications. Allow alarms. Allow battery use."}


def first_phone(v):
    k = "control" if v.get("control") else v["start"]
    base = kit.phone(header(t.TITLE), empty_body("inline", *SCREENS["Today"][1:]), kit.bar("Today"))
    if k == "straight":
        return base
    sheet = ('<div class="scrim"></div><div class="bsheet"><h4>%s</h4><p>%s</p><div class="col"><span class="btn fill wide" data-tap="Start">%s</span></div>%s</div>' % (
        "Welcome" if k != "tour" else "1 of 3", FIRST_TEXT[k], "Start" if k == "intro" else "Next",
        '<p style="text-align:center;margin:8px 0 0">● ○ ○</p>' if k == "tour" else ('<p style="text-align:center;margin:8px 0 0">1 of 5 · Skip</p>' if k == "control" else "")))
    return T.with_overlay(base, sheet)


def score_first(v):
    k = "control" if v.get("control") else v["start"]
    taps = {"straight": 0, "intro": 1, "tour": 3, "control": 5 + 1 + 7}[k]
    w, g, c, b = tone(FIRST_TEXT[k])
    return {"taps_before_use": taps, "words_before_use": w * (3 if k == "tour" else 1), "cheer": c, "small": [], "clutter": T.clutter_of(lambda th: doc(first_phone(v), th))}


# ---- part: loading -----------------------------------------------------------------------------------------------------
"""
  show  skeleton (grey bars where the rows will be), spinner (a ring in the middle), progressive (what is already on this
        device at once; newer rows slide in), blank (nothing until ready)
  Case: a large page or a first sync. Counted: rows that move when the content arrives (layout shift), something to read
  meanwhile. Measured: clutter of the waiting state.
  Control: a full-screen shade with "Loading, please wait…" and a percentage, blocking the screen.
"""
LOADING_SPACE = {"show": ["skeleton", "spinner", "progressive", "blank"]}


def loading_phone(v):
    k = "control" if v.get("control") else v["show"]
    if k == "progressive":
        return A.today()
    body = '<div class="cap" data-tap="Capture">+ <span>Add anything…</span></div>'
    if k == "skeleton":
        body += kit.zone("Agenda", "".join('<div class="skel" style="width:%d%%"></div>' % w for w in (70, 55, 80, 60)))
    elif k == "spinner":
        body += '<div class="empty-c"><div class="spin"></div></div>'
    html = kit.phone(header(t.TITLE), body, kit.bar("Today"))
    if k == "control":
        html = T.with_overlay(html, '<div class="scrim" style="background:rgba(0,0,0,.6)"></div><div class="dlg" style="top:300px;text-align:center"><div class="spin" style="margin:0 auto 12px"></div><p>Loading, please wait… 42%</p></div>')
    return html


def score_loading(v):
    k = "control" if v.get("control") else v["show"]
    shift = {"skeleton": 0, "spinner": 1, "progressive": 0, "blank": 1, "control": 1}[k]
    readable = 1 if k == "progressive" else 0
    blocks = 1 if k == "control" else 0
    return {"layout_shift": shift, "something_to_read": readable, "blocks": blocks, "small": [], "clutter": T.clutter_of(lambda th: doc(loading_phone(v), th))}


# ==== the T1.9 tables and pages through toast_opt's machinery ==========================================================
T.PREFIX, T.REFS, T.NAME = "empty", "empty-references.json", "T1.9 empty and error states"
T.SPACES = {"empty": EMPTY_SPACE, "done": DONE_SPACE, "noresult": NORESULT_SPACE, "field": FIELD_SPACE, "banner": BANNER_SPACE, "first": FIRST_SPACE, "loading": LOADING_SPACE}
T.SCORERS = {"empty": score_empty, "done": score_done, "noresult": score_noresult, "field": score_field, "banner": score_banner, "first": score_first, "loading": score_loading}
T.CONTROLS = {
    "empty": ({"form": "illustration", "control": True}, "an illustration, \"All clear! 🎉 Enjoy your free day!\" and two buttons"),
    "done": ({"sentences": "praise", "fold": "hidden", "control": True}, "\"Great job! You finished everything 🎉\" with an illustration, the fold hidden"),
    "noresult": ({"form": "illustration", "words": "oops", "action": "two", "control": True}, "an illustration, \"Oops! Nothing here 😕\" and two buttons"),
    "field": ({"form": "dialog", "control": True}, "a dialog: \"Error. Invalid input.\" and OK"),
    "banner": ({"words": "code", "control": True}, "\"Error 0x80070005: sync exception\" with OK"),
    "first": ({"start": "onboarding", "control": True}, "five onboarding screens, an account prompt, every permission at once"),
    "loading": ({"show": "blocking", "control": True}, "a dark shade with \"Loading, please wait… 42%\", blocking the screen"),
}
TONE_AXIS = ("words", "cheer", "blame")
T.AXES = {
    "empty": {"Ease": ("reach",), "Calm": ("block_px", "clutter", "desk_clutter"), "Tone": TONE_AXIS + ("grade",)},
    "done": {"Clarity": ("-tells_which",), "Calm": ("rows", "clutter"), "Tone": TONE_AXIS},
    "noresult": {"Ease": ("reach",), "Clarity": ("-names_it",), "Calm": ("clutter",), "Tone": TONE_AXIS},
    "field": {"Clarity": ("-noticed", "-says_fix", "-stays"), "Safety": ("lost",), "Ease": ("extra_actions", "reach"), "Calm": ("clutter",), "Tone": ("words", "blame")},
    "banner": {"Clarity": ("-says_what", "-says_safe", "-has_fix"), "Calm": ("banner_px", "clutter"), "Tone": ("words", "grade", "blame")},
    "first": {"Ease": ("taps_before_use", "words_before_use"), "Calm": ("clutter",), "Tone": ("cheer",)},
    "loading": {"Stability": ("layout_shift", "blocks"), "Clarity": ("-something_to_read",), "Calm": ("clutter",)},
}
T.TITLES = {"empty": "Empty screens", "done": "Today: all done, or nothing planned", "noresult": "Filtered to nothing", "field": "A field's error",
            "banner": "A failure banner's words", "first": "First run", "loading": "Loading"}
T.DRAW = {"empty": lambda v: [doc(empty_phone("illustration" if v.get("control") else v["form"], sc)) for sc in SCREENS] + [empty_desk("illustration" if v.get("control") else v["form"])],
          "done": lambda v: [doc(done_phone(v))], "noresult": lambda v: [doc(h) for h in noresult_phones(v)], "field": lambda v: [doc(field_phone(v))],
          "banner": lambda v: [doc(banner_phone(v))], "first": lambda v: [doc(first_phone(v))], "loading": lambda v: [doc(loading_phone(v))]}
# T1.9 decided (owner, 2026-10-09; decision 17): the pages draw the picks only (owner, 2026-10-26)
T.PICKED = {"banner": [{"words": "what"}], "done": [{"sentences": "one", "fold": "kept"}], "empty": [{"form": "centred"}],
            "field": [{"form": "inline"}], "first": [{"start": "tour"}], "loading": [{"show": "progressive"}],
            "noresult": [{"form": "centred", "words": "repeat", "action": "none"}]}


if __name__ == "__main__":
    for p in T.SPACES:
        if p in sys.argv[1:]:
            T.run_part(p)
    if "page" in sys.argv[1:]:
        T.options_page()
    if "scores" in sys.argv[1:]:
        T.scores_page()
