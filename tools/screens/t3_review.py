"""T3c.1 stage 2: how each kind becomes one point per bucket, scored on the graph alone (owner, 2026-10-18; decision 19).

Registered into t3_opt's parts by t3_opt itself (register(globals()) at its end):
    python tools/screens/t3_opt.py rv_count rv_rating rv_yesno rv_choice rv_add rv_level rv_midnight page_html scores

The owner's rules (T3c.1): spans Today, Week, Month, 6 M, Year, rolling and ending today; a point per day in Week and
Month, per week in 6 M, per month in Year; empty is not zero (a day with no log is left out of every average); a
bucket resting on few logs is drawn like any other. Week and Month draw the days themselves, so the rules differ only
at 6 M and Year: each option is a rule, drawn at both (26 weeks and 12 months, one 312 x 130 plot each).

The rules, per kind (owner: "score them"):
  count  Water, glasses   mean of logged days / the bucket's total / days the goal was met (share of logged days) /
                          a 7-day moving mean (Track & Graph's way; plotted per day)
  add    Reading, min     the same four
  rating Mood, 1-5        mean of entries / the bucket's low-high band with its mean / a 7-day moving mean
  level  Weight, kg       mean of entries / the bucket's last entry / the low-high band with its mean / moving mean
  yesno  Walk             share of logged days done / a count of days done / runs (a bar per run of days done)
  choice Lunch            a split bar per bucket (each option's share of logged days) / the most frequent option /
                          runs (a lane per option, a bar per run)
  The control of each: empty counted as zero (or "no"), the error the owner ruled out; for choices, the options'
  codes averaged as numbers.
rv_midnight: a session over midnight (Sleep 23:10-07:00, Reading 23:30-00:20) counted on the day it starts / the day
  it ends / split at midnight, drawn per day at Week and Month.

Axes (owner, T3c.1; Comparability and Taps belong to the whole screen, stage 3 and 5): Fit, Readability, Calm,
Mental load, Honesty of averages, Consistency (2). No lead in this stage (Comparability leads where it can be
measured). Measured from the drawing's geometry and the data: Fit (empty drawn as zero; a sum of values that do not add
up; a choice averaged), Honesty (a total resting on a partial bucket reads low: the share of buckets drawn more than
10% under their logged days' rate; a bucket resting on under half its days is drawn as any other: half a count each,
the owner's "show as is" kept and its cost shown), Readability (the smallest mark, pixels for one meaningful step),
Calm (the median bucket-to-bucket jump in px; ink left out, as it follows the values), Mental load (HAND-SET costs of each kind's three
long-span questions, flagged, and the numbers printed / 10, series, a legend), Consistency (how many other kinds use the
same family of rule: mean, total, share, band, last, mode, runs, moving).
"""
import datetime
import math

W, PH, TOP, BOT = 312, 130, 12, 16
END = datetime.date(2026, 10, 16)
DAYS = 365
START = END - datetime.timedelta(days=DAYS - 1)
GAP = (datetime.date(2026, 7, 6), datetime.date(2026, 7, 26))   # a holiday: nothing logged for three weeks


def _rng(seed):
    s = [seed]

    def r():
        s[0] = (s[0] * 1103515245 + 12345) % 2147483648
        return s[0] / 2147483648.0
    return r


def _days():
    return [START + datetime.timedelta(days=i) for i in range(DAYS)]


def make_data():
    """A year of placeholder logs, a day with no log None; deterministic."""
    days = _days()
    out = {}
    r = _rng(7)

    def logged(d, p):
        return not (GAP[0] <= d <= GAP[1]) and r() < p
    out["count"] = [round(4 + 5 * r() + (1 if d.month in (6, 7, 8) else 0)) if logged(d, 0.86) else None for d in days]   # the goal (8) met on about a quarter of days
    out["add"] = [(0 if r() < 0.18 else 5 * round((15 + 35 * r()) / 5)) if logged(d, 0.8) else None for d in days]
    out["rating"] = [max(1, min(5, round(3 + (r() - 0.45) * 3 - (0.6 if d.month in (1, 2) else 0)))) if logged(d, 0.82) else None for d in days]
    w, lv = 76.0, []
    for i, d in enumerate(days):
        w += -0.012 + (r() - 0.5) * 0.25
        lv.append(round(w, 1) if logged(d, 0.45) else None)
    out["level"] = lv
    out["yesno"] = [(1 if r() < (0.75 if d.month in (4, 5, 6, 7, 8, 9) else 0.5) else 0) if logged(d, 0.9) else None for d in days]
    opts = ("home", "packed", "out", "skipped")
    out["choice"] = [opts[min(3, int(r() * r() * 4 + (0.8 if d.month >= 9 and r() < 0.4 else 0)))] if logged(d, 0.85) else None for d in days]
    return out


DATA = make_data()
GOALS = {"count": 8, "add": 30, "level": 70}
KINDS = {"count": "Water, glasses a day", "add": "Reading, minutes a day", "rating": "Mood, 1 to 5", "level": "Weight, kg",
         "yesno": "Walk, done or not", "choice": "Lunch: home, packed, out, skipped"}
RULES = {"count": ["mean", "total", "goal_days", "moving"], "add": ["mean", "total", "goal_days", "moving"],
         "rating": ["mean", "band", "moving"], "level": ["mean", "last", "band", "moving"],
         "yesno": ["share", "count_days", "runs"], "choice": ["split", "mode", "runs"]}
FAMILY = {"mean": "mean", "total": "total", "goal_days": "share", "moving": "moving", "band": "band", "last": "last",
          "share": "share", "count_days": "total", "runs": "runs", "split": "share", "mode": "mode"}
# HAND-SET (flagged): each kind's three long-span questions, and what each rule costs to answer them (0 read off, 1 a
# visual comparison, 2 a sum or a count, 3 not answerable)
QUESTIONS = {"count": ("a usual day lately", "more or less than before", "how often the goal was met"),
             "add": ("a usual day lately", "more or less than before", "how often the goal was met"),
             "rating": ("a usual day lately", "better or worse than before", "how often it was low"),
             "level": ("now", "the trend", "the distance to the goal"),
             "yesno": ("how often lately", "more or less than before", "the longest gap"),
             "choice": ("the most often lately", "how it changed", "a given week's mix")}
COSTS = {"count": {"mean": (0, 0, 2), "total": (1, 0, 3), "goal_days": (2, 1, 0), "moving": (0, 0, 2), "zeros": (0, 1, 2)},
         "add": {"mean": (0, 0, 2), "total": (1, 0, 3), "goal_days": (2, 1, 0), "moving": (0, 0, 2), "zeros": (0, 1, 2)},
         "rating": {"mean": (0, 0, 2), "band": (1, 0, 1), "moving": (0, 0, 2), "zeros": (1, 1, 2)},
         "level": {"mean": (1, 0, 1), "last": (0, 0, 1), "band": (1, 0, 1), "moving": (1, 0, 1), "zeros": (3, 3, 3)},
         "yesno": {"share": (0, 0, 3), "count_days": (1, 0, 3), "runs": (1, 1, 0), "zeros": (0, 1, 3)},
         "choice": {"split": (1, 0, 0), "mode": (0, 1, 3), "runs": (1, 1, 1), "zeros": (3, 3, 3)}}


def buckets(span):
    """[(label, [day indices])] for 6 M (26 weeks back from the end) or Year (12 calendar-length months back)."""
    idx = list(range(DAYS))
    if span == "6m":
        out = []
        end = DAYS
        for k in range(26):
            out.insert(0, ("", idx[end - 7:end]))
            end -= 7
        return out
    days = _days()
    out, cur = [], None
    for i, d in enumerate(days[-365:]):
        key = (d.year, d.month)
        if cur is None or cur[0] != key:
            cur = (key, [])
            out.append(cur)
        cur[1].append(DAYS - 365 + i)
    return [("%d" % k[1], v) for k, v in out[-12:]]


def value(kind, rule, days):
    """The bucket's point(s): (value or None, extra) - extra holds a band's low/high, a split's shares."""
    vals = [DATA[kind][i] for i in days]
    logged = [v for v in vals if v is not None]
    n, full = len(logged), len(days)
    if rule == "zeros":
        if kind == "choice":
            code = {"home": 1, "packed": 2, "out": 3, "skipped": 4}
            return (sum(code[v] for v in logged) / full if full else None), None
        return sum((v or 0) for v in vals) / full, None
    if not logged:
        return None, None
    if kind == "choice":
        shares = {o: sum(1 for v in logged if v == o) / n for o in ("home", "packed", "out", "skipped")}
        if rule == "mode":
            return max(shares, key=shares.get), shares
        return shares, shares
    if rule in ("mean", "share"):
        return sum(logged) / n, None
    if rule == "total":
        return float(sum(logged)), None
    if rule == "count_days":
        return float(sum(logged)), None
    if rule == "goal_days":
        return sum(1 for v in logged if v >= GOALS[kind]) / n, None
    if rule == "last":
        return logged[-1], None
    if rule == "band":
        return sum(logged) / n, (min(logged), max(logged))
    return sum(logged) / n, None


def moving(kind):
    """A 7-day moving mean over logged days, one point a day (None where the window holds no log)."""
    v = DATA[kind]
    out = []
    for i in range(DAYS):
        w = [x for x in v[max(0, i - 6):i + 1] if x is not None]
        out.append(sum(w) / len(w) if w else None)
    return out


class Plot:
    def __init__(self):
        self.parts, self.ink, self.marks, self.ys, self.numbers, self.legend, self.series = [], 0.0, [], [], 0, 0, 1

    def rect(self, x, y, w, h, fill="var(--ink)", stroke=False):
        h = max(h, 0)
        self.parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="1.5" fill="%s"%s/>' % (
            x, y, w, h, fill, ' stroke="var(--dim)" stroke-width="1"' if stroke else ""))
        self.ink += w * h
        if h > 0:
            self.marks.append(min(w, h))

    def dot(self, x, y, r=3):
        self.parts.append('<circle cx="%.1f" cy="%.1f" r="%g" fill="var(--ink)"/>' % (x, y, r))
        self.ink += math.pi * r * r
        self.marks.append(2 * r)

    def line(self, pts, w=2, colour="var(--ink)", dash="", mark=True):
        self.parts.append('<polyline points="%s" style="fill:none;stroke:%s;stroke-width:%g"%s/>' % (
            " ".join("%.1f,%.1f" % p for p in pts), colour, w, ' stroke-dasharray="%s"' % dash if dash else ""))
        if not mark:   # a reference line (the goal) is not a data mark (found 2026-10-18: it read as the smallest mark)
            return
        self.ink += sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) * w
        self.marks.append(w)

    def text(self, x, y, t, size=12, anchor="start", dim=True):
        self.parts.append('<text x="%.1f" y="%.1f" font-size="%g" fill="var(--%s)" text-anchor="%s">%s</text>' % (
            x, y, size, "dim" if dim else "ink", anchor, t))
        if any(c.isdigit() for c in t):
            self.numbers += 1

    def svg(self, title):
        return ('<div style="font-size:12px;color:var(--dim);margin:6px 0 2px">%s</div><svg width="%d" height="%d" viewBox="0 0 %d %d">%s</svg>' % (
            title, W, TOP + PH + BOT, W, TOP + PH + BOT, "".join(self.parts)))


def scale(kind, rule):
    """(lo, hi, one meaningful step) of the plotted value."""
    if rule in ("share", "goal_days") or (kind == "choice"):
        return 0, 1, 0.1
    if rule == "zeros" and kind == "choice":
        return 1, 4, 1
    if rule == "total" or rule == "count_days":
        return None
    return {"count": (0, 10, 1), "add": (0, 60, 5), "rating": (1, 5, 1), "level": (69, 77, 0.5), "yesno": (0, 1, 0.1)}[kind]


def draw_span(kind, rule, span):
    p = Plot()
    bks = buckets(span)
    nb = len(bks)
    bw = W / nb
    y0 = TOP + PH
    p.parts.append('<line x1="0" x2="%d" y1="%d" y2="%d" stroke="var(--dim)" stroke-width="1"/>' % (W, y0, y0))
    under = thin = 0
    pts = []
    if rule == "moving":
        lo, hi, step = scale(kind, "mean")
        mv = moving(kind)
        first = DAYS - (26 * 7 if span == "6m" else 365)
        xs = W / (DAYS - first)
        seg = []
        for i in range(first, DAYS):
            if mv[i] is None:
                if len(seg) > 1:
                    p.line(seg, 2)
                seg = []
                continue
            y = y0 - (mv[i] - lo) / (hi - lo) * PH
            seg.append(((i - first) * xs, y))
            p.ys.append(y)
        if len(seg) > 1:
            p.line(seg, 2)
        if kind in GOALS:
            gy = y0 - (GOALS[kind] - lo) / (hi - lo) * PH
            if TOP <= gy <= y0:
                p.line([(0, gy), (W, gy)], 1, "var(--dim)", "4 4", mark=False)
        # a window resting on under half its days, drawn as any other: counted per bucket-length of days (2026-10-18:
        # the moving mean escaped the owner's "show as is" cost)
        per = 7 if span == "6m" else 30
        thin_days = sum(1 for i in range(first, DAYS) if 0 < sum(1 for x in DATA[kind][max(0, i - 6):i + 1] if x is not None) < 4)
        thin = round(thin_days / per, 2)
        return p, step / (hi - lo) * PH, under, thin
    sc = scale(kind, rule)
    if sc is None:   # totals: from zero to the largest bucket
        mx = max((value(kind, rule, d)[0] or 0) for _, d in bks)
        lo, hi, step = 0, mx * 1.1, (1 if kind == "count" else 5) if rule == "total" else 1
    else:
        lo, hi, step = sc
    for j, (lab, days) in enumerate(bks):
        x = j * bw
        v, extra = value(kind, rule, days)
        logged = sum(1 for i in days if DATA[kind][i] is not None)
        cov = logged / len(days)
        if 0 < cov < 0.5:
            thin += 1
        if rule in ("total", "count_days") and logged:
            rate_total = value(kind, "mean", days)[0] * len(days)
            if v < 0.9 * rate_total:
                under += 1
        if rule == "zeros" and logged and kind != "choice":
            if v < 0.9 * value(kind, "mean", days)[0]:
                under += 1
        if v is None:
            continue
        if kind == "choice" and rule in ("split", "runs"):
            if rule == "split":
                acc = 0
                fills = {"home": "var(--ink)", "packed": "var(--dim)", "out": "var(--zone2)", "skipped": "var(--bg)"}
                for o in ("home", "packed", "out", "skipped"):
                    h = extra[o] * PH
                    p.rect(x + 1, y0 - acc - h, bw - 2, h, fills[o], o == "skipped")
                    acc += h
            continue
        if kind == "choice" and rule == "mode":
            row = {"home": 0, "packed": 1, "out": 2, "skipped": 3}[v]
            p.dot(x + bw / 2, TOP + 10 + row * (PH - 20) / 3, 4)
            p.ys.append(TOP + row * PH / 3)
            continue
        if rule == "runs":
            continue
        y = y0 - (v - lo) / ((hi - lo) or 1) * PH
        if rule in ("mean", "last", "zeros") and kind in ("rating", "level"):
            p.dot(x + bw / 2, y, 3)
        elif rule == "band":
            l_, h_ = extra
            yl, yh = y0 - (l_ - lo) / (hi - lo) * PH, y0 - (h_ - lo) / (hi - lo) * PH
            p.rect(x + bw * 0.3, yh, bw * 0.4, max(2, yl - yh), "var(--zone2)")
            p.dot(x + bw / 2, y, 2.5)
        else:
            p.rect(x + 1, y, bw - 2, y0 - y)
        pts.append(y)
        p.ys.append(y)
    if rule == "runs":   # a lane (yes/no) or a lane per option (choice), a bar per run of days, over the span
        first = DAYS - (26 * 7 if span == "6m" else 365)
        xs = W / (DAYS - first)
        lanes = ["yes"] if kind == "yesno" else ["home", "packed", "out", "skipped"]
        lh = PH / len(lanes)
        for li, lane in enumerate(lanes):
            yy = TOP + li * lh + lh * 0.2
            i = first
            while i < DAYS:
                hit = (DATA[kind][i] == 1) if kind == "yesno" else (DATA[kind][i] == lane)
                if hit:
                    j = i
                    while j < DAYS and ((DATA[kind][j] == 1) if kind == "yesno" else (DATA[kind][j] == lane)):
                        j += 1
                    p.rect((i - first) * xs, yy, max(1, (j - i) * xs - 0.5), lh * 0.6)
                    i = j
                else:
                    i += 1
            if kind == "choice":
                p.text(0, yy + lh * 0.45, lane, 11)
        if kind == "choice":
            p.legend = 0
        step = xs   # a day's width
        return p, step, under, thin
    if kind == "choice" and rule == "split":
        p.legend, p.series = 1, 4
    if kind == "choice" and rule == "mode":
        for row, o in enumerate(("home", "packed", "out", "skipped")):
            p.text(0, TOP + 14 + row * (PH - 20) / 3, o, 11)
    if rule == "band":
        p.series = 2
    if kind in GOALS and rule in ("mean", "zeros", "band", "last"):
        gy = y0 - (GOALS[kind] - lo) / (hi - lo) * PH
        if TOP <= gy <= y0:
            p.line([(0, gy), (W, gy)], 1, "var(--dim)", "4 4", mark=False)
    return p, step / ((hi - lo) or 1) * PH, under, thin


def draw(kind, rule):
    """Both spans, and their measures."""
    out, m = [], {"ink": 0, "mark": 99, "step": 99, "under": 0, "thin": 0, "noise": 0, "numbers": 0, "legend": 0, "series": 1}
    for span, title in (("6m", "6 M · a point per week"), ("year", "Year · a point per month")):
        p, step, under, thin = draw_span(kind, rule, span)
        out.append(p.svg(title))
        jumps = sorted(abs(p.ys[i + 1] - p.ys[i]) for i in range(len(p.ys) - 1)) or [0]
        m["ink"] += p.ink / (W * PH) / 2
        m["mark"] = min(m["mark"], min(p.marks) if p.marks else 0)
        m["step"] = min(m["step"], step)
        m["under"] += under
        m["thin"] += thin
        m["noise"] += jumps[len(jumps) // 2] / 2
        m["numbers"] += p.numbers
        m["legend"] = max(m["legend"], p.legend)
        m["series"] = max(m["series"], p.series)
    return "".join(out), m


# ==== midnight ==================================================================================================================
def sessions(item):
    """A month of sessions (start day index, start minute, minutes); Sleep nightly 23:10-07:00 (a few missed),
    Reading some evenings 21:00-21:40 and some late 23:30-00:20."""
    r = _rng(11 if item == "sleep" else 13)
    out = []
    for d in range(DAYS - 30, DAYS):
        if item == "sleep":
            if r() < 0.9:
                out.append((d, 23 * 60 + 10 + int(r() * 30), 7 * 60 + int(r() * 60)))
        else:
            if r() < 0.6:
                late = r() < 0.35
                out.append((d, (23 * 60 + 30) if late else 21 * 60, 50 if late else 40))
    return out


def per_day(item, rule):
    tot = {d: 0.0 for d in range(DAYS - 30, DAYS + 1)}
    frag = 0
    for d, s, m in sessions(item):
        end = s + m
        if end <= 1440:
            tot[d] += m
            continue
        if rule == "drop":
            continue
        if rule == "start":
            tot[d] += m
        elif rule == "end":
            tot[d + 1] += m
        else:
            tot[d] += 1440 - s
            tot[d + 1] += end - 1440
            frag += 1
    return tot, frag


def draw_midnight(item, rule, span):
    tot, frag = per_day(item, rule)
    days = list(range(DAYS - (7 if span == "week" else 30) + 1, DAYS + 1))
    p = Plot()
    hi = 600 if item == "sleep" else 60
    bw = W / len(days)
    y0 = TOP + PH
    p.parts.append('<line x1="0" x2="%d" y1="%d" y2="%d" stroke="var(--dim)" stroke-width="1"/>' % (W, y0, y0))
    vals = [tot.get(d, 0) for d in days]
    for j, v in enumerate(vals):
        if v:
            h = min(v, hi) / hi * PH
            p.rect(j * bw + 1, y0 - h, bw - 2, h)
            p.ys.append(y0 - h)
    logged = [v for v in vals if v]
    med = sorted(logged)[len(logged) // 2] if logged else 0
    short = sum(1 for v in logged if v < 0.5 * med)
    return p, frag, short, (60 if item == "sleep" else 5) / hi * PH


def register(ns):
    T, kit, ipdoc = ns["T"], ns["kit"], ns["ipdoc"]

    def page(title, body):
        return ipdoc(kit.phone(kit.header(title, (), ("‹", "Back")), '<div class="zone" style="padding-bottom:8px">%s</div>' % body, kit.bar("Hub")))

    def make(kind):
        part = "rv_" + kind

        def score(v):
            rule = "zeros" if v.get("control") else v["rule"]
            _, m = draw(kind, rule)
            fit = 0.0
            if rule == "zeros":
                fit += 1   # empty drawn as zero (or no), or a choice averaged as a number
            if rule == "total" and kind in ("rating", "level"):
                fit += 1
            costs = COSTS[kind][rule]
            # "show as is" (owner): a bucket resting on under half its days drawn like any other - half a count each
            honesty = m["under"] + 0.5 * m["thin"]
            load = sum(costs) + m["numbers"] / 10 + (m["series"] - 1) * 0.5 + m["legend"]
            fam = FAMILY.get(rule, "zeros")
            cons = sum(1 for k, rs in RULES.items() if k != kind and any(FAMILY[x] == fam for x in rs))
            return {"fit": fit, "honesty": round(honesty, 2), "under": m["under"], "thin": m["thin"],
                    "mark_seen": round(min(m["mark"], 6), 2), "step_seen": round(min(m["step"], 12), 2), "ink": round(m["ink"], 4),
                    "noise_seen": round(max(m["noise"], 3), 2),
                    # the median jump in meaningful steps above the flat floor: a pixel or two is not calmer (2026-10-18: zeros
                    # compressed the share's jumps by 1 px and kept the control on Walk's front)
                    "jumps": round(max(m["noise"] - 3, 0) / max(m["step"], 6)), "load": round(load, 2), "costs": list(costs), "shared": cons, "small": []}

        def drawing(v):
            rule = "zeros" if v.get("control") else v["rule"]
            html, _ = draw(kind, rule)
            return [page(KINDS[kind].split(",")[0].split(":")[0], '<div class="iph">%s · %s</div>%s' % (KINDS[kind], rule.replace("_", " "), html))]

        T.SPACES[part] = {"rule": RULES[kind]}
        T.SCORERS[part] = score
        T.VALID[part] = lambda v: True
        T.CONTROLS[part] = [({"rule": "zeros", "control": True}, "empty counted as zero (no, for yes/no; the codes averaged, for choices): the error the owner ruled out")]
        T.TITLES[part] = "T3c.2 Review's long spans, %s: one point per week (6 M) and per month (Year) (%s)" % (KINDS[kind], "; ".join(QUESTIONS[kind]))
        T.DRAW[part] = drawing
        T.POOL[part] = lambda ok: [r for r in ok]
        T.DRAW_MAX[part] = 8
        T.AXES[part] = {"Fit": ("fit",), "Honesty": ("honesty",), "Readability": ("-mark_seen", "-step_seen"), "Calm": ("jumps",),
                        "Mental load": ("load",), "Consistency": ("-shared",)}
        # Calm without ink here (2026-10-18): each rule's marks are fixed, so ink follows the values - empty counted as zero
        # drew shorter bars and read "calmer", which put the control on two fronts
        T.WEIGHTS[part] = {"Consistency": 2}
        T.REFS_INFO.add(part)

    for kind in KINDS:
        make(kind)

    # ---- midnight ----
    part = "rv_midnight"

    def mscore(v):
        rule = v["rule"] if not v.get("control") else "drop"
        frag = short = 0
        steps = []
        for item in ("sleep", "reading"):
            for span in ("week", "month"):
                p, f, s, st = draw_midnight(item, rule, span)
                frag += f
                short += s
                steps.append(st)
        # consistency with the item's History, which lists a session at its start (T3b.7f): the start day agrees
        hist = 0 if rule == "start" else 1
        return {"fragments": frag, "short_days": short, "history_mismatch": hist, "fit": 1 if rule == "drop" else 0,
                "step_seen": round(min(min(steps), 12), 2), "small": []}

    def mdraw(v):
        rule = v["rule"] if not v.get("control") else "drop"
        body = ""
        for item, name in (("sleep", "Sleep, a night 23:10-07:00"), ("reading", "Reading, some sessions 23:30-00:20")):
            for span in ("week", "month"):
                p, *_ = draw_midnight(item, rule, span)
                body += p.svg("%s · %s" % (name, "Week" if span == "week" else "Month"))
        return [page("Midnight", '<div class="iph">a session over midnight: %s</div>%s' % (rule, body))]

    T.SPACES[part] = {"rule": ["start", "end", "split"]}
    T.SCORERS[part] = mscore
    T.VALID[part] = lambda v: True
    T.CONTROLS[part] = [({"rule": "drop", "control": True}, "a session over midnight not counted on any day (a day's bucket that only takes sessions wholly inside it)")]
    T.TITLES[part] = "T3c.2 Review: which day a session over midnight belongs to (the day it starts, ends, or split)"
    T.DRAW[part] = mdraw
    T.POOL[part] = lambda ok: [r for r in ok]
    T.DRAW_MAX[part] = 4
    T.AXES[part] = {"Fit": ("fit", "short_days"), "Fragments": ("fragments",), "Consistency": ("history_mismatch",), "Readability": ("-step_seen",)}
    T.WEIGHTS[part] = {"Consistency": 2}
    T.REFS_INFO.add(part)
