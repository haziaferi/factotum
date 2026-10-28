"""T3c.1 stage 3 groundwork: the 10-item placeholder set and the Comparability measure (owner, 2026-10-18; decision 19).

Not a part yet: stage 3 scores the overlap forms x the item sets with this measure leading. Run on its own:
    python tools/screens/t3_overlap.py table            Comparability per form, at 2 and 10 items, Month and 6 M
    python tools/screens/t3_overlap.py sheet OUT.html   the throwaway drawings (greys) the numbers are measured on
    python tools/screens/t3_overlap.py selftest         deterministic, and the control last at 2 and at 10 items

The items (placeholders, seeded like t3_review's year): the six kinds the item page knows, two of most, with differing
scales, a goal on four and none on six, sparse items (about a quarter to two fifths of days logged) and dense ones
(four fifths and more), so a form that only works for same-unit series is exposed. PAIR is the 2-item set: Reading
(minutes, a goal) and Mood (a rating, no goal), two units, one goal missing - the hard case.

Each bucket's value is the owner's pick (T3c.2): the mean of logged days; a yes/no's share of logged days done; a
choice's share of logged days on its named option (Lunch: "home"; PROVISIONAL, flagged: the picked split bar is four
stacked shares and cannot be overlaid, so stage 3 must say how a choice enters an overlaid form). Empty is not zero:
a bucket with no log draws nothing and breaks the line.

Comparability: "two items compared at a glance" (T3c.1), lower is better. For a pair of shown items, over the buckets
where both have a point, the sum of five parts, each 0 to 1:
  scale       Cleveland & McGill (1984): position on a common scale is judged best, then position on identical but
              nonaligned scales, then the rest. Read from the drawing: the same frame and the same mapping and the
              same unit of the plotted quantity = 1; separate frames of equal height, same unit, unfolded = 2 (aligned
              lanes); same unit but unequal frames or folded bands (a horizon's layers, Heer et al. 2009) = 3; the
              plotted quantities in different units (dual axes; percent of goal mixed with a fallback) = 4. Cost
              (rank - 1) / 3 (HAND-SET: the studies give an order, not distances).
  travel      the vertical distance the eye travels between the two compared marks, px over the chart's box height
              (Javed, McDonnel & Elmqvist 2010: shared space suits a small visual span, split space a large one; the
              span is what this measures, overlap is the next part).
  hidden      the share of each compared series' mark pixels lying under marks drawn after it, times the provisional
              opacity (owner: opacity reduces it, does not remove it; a series' identity is not counted, only its
              marks); the mean of the two.
  resolution  pixels for a tenth of the plotted scale against STEP_ENOUGH (Heer et al. 2009: estimates degrade as
              charts shrink); 0 when a tenth is plainly seen, up to 1.
  flips       the share of compared buckets whose drawn order (which of the two sits higher in its frame) reverses
              under an equally legitimate choice the form leaves free: dual axes from zero or fitted to the data
              (Isenberg et al. 2011 and the dual-axis critique: the apparent relation is an artefact of the axes);
              an own range over the span or over the year. Percent of goal and runs leave no such choice.
At 2 items the one pair; at 10 the mean over every pair that shares a bucket (any two may be the two compared). Each
size is the mean of Month (30 daily points) and 6 M (26 weekly means). Aigner et al. (2011) found indexing to a common
base cut comparison errors: the percent and own-range forms; it is a reason for the candidates, not a part here.

The control (T3c.1): dual y-axes on one chart, Oracle-like, up to four axes, every item overlaid on its unit's axis;
units past the fourth share the fourth axis.
"""
import datetime
import itertools
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t3_review as R  # noqa: E402  (the year, its days, the holiday and the 6 M buckets)

# ==== the 10 items ==============================================================================================================
# HAND-SET (placeholders): names generic; p = the share of days logged outside the holiday (density)
ITEMS = [
    dict(key="water", name="Water", kind="count", unit="glasses", goal=8, p=0.86),
    dict(key="pushups", name="Push-ups", kind="count", unit="reps", goal=None, p=0.30),
    dict(key="reading", name="Reading", kind="minutes", unit="min", goal=30, p=0.80),
    dict(key="practice", name="Practice", kind="minutes", unit="min", goal=None, p=0.25),
    dict(key="walk", name="Walk", kind="yes/no", unit="share of days", goal=None, p=0.90),
    dict(key="stretch", name="Stretch", kind="yes/no", unit="share of days", goal=5 / 7, p=0.40),   # 5 days a week
    dict(key="lunch", name="Lunch", kind="choices", unit="share of days", goal=None, p=0.85, option="home"),
    dict(key="weight", name="Weight", kind="weight", unit="kg", goal=70, p=0.45),
    dict(key="mood", name="Mood", kind="ratings", unit="1-5", goal=None, p=0.82),
    dict(key="focus", name="Focus", kind="ratings", unit="1-10", goal=None, p=0.30),
]
BY = {it["key"]: it for it in ITEMS}
PAIR = ("reading", "mood")   # the 2-item set: minutes with a goal, a rating without one
SETS = {2: list(PAIR), 10: [it["key"] for it in ITEMS]}
DENSE, SPARSE = 0.8, 0.4   # what the record calls dense and sparse (share of the year's days logged)


def make_items():
    """A year of placeholder logs per item (a day with no log None), seeded per item; the holiday logs nothing."""
    days = R._days()
    out = {}
    for n, it in enumerate(ITEMS):
        r = R._rng(101 + n)

        def logged(d):
            return not (R.GAP[0] <= d <= R.GAP[1]) and r() < it["p"]
        k, vals = it["key"], []
        w = 76.0
        for d in days:
            if k == "weight":   # a slow fall, logged on some days
                w += -0.012 + (r() - 0.5) * 0.25
            if not logged(d):
                vals.append(None)
                continue
            if k == "water":
                vals.append(round(4 + 5 * r() + (1 if d.month in (6, 7, 8) else 0)))
            elif k == "pushups":
                vals.append(round(10 + 25 * r()))
            elif k == "reading":
                vals.append(0 if r() < 0.18 else 5 * round((15 + 35 * r()) / 5))
            elif k == "practice":
                vals.append(15 * round((20 + 70 * r()) / 15))
            elif k == "walk":
                vals.append(1 if r() < (0.75 if d.month in (4, 5, 6, 7, 8, 9) else 0.5) else 0)
            elif k == "stretch":
                vals.append(1 if r() < 0.65 else 0)
            elif k == "lunch":
                vals.append(("home", "packed", "out", "skipped")[min(3, int(r() * r() * 4))])
            elif k == "weight":
                vals.append(round(w, 1))
            elif k == "mood":
                vals.append(max(1, min(5, round(3 + (r() - 0.45) * 3 - (0.6 if d.month in (1, 2) else 0)))))
            else:   # focus, 1 to 10
                vals.append(max(1, min(10, round(4 + 5 * r()))))
        out[k] = vals
    return out


DATA = make_items()


def density(k):
    return sum(1 for v in DATA[k] if v is not None) / R.DAYS


def bucket_days(span):
    """[[day indices]]: Month a day each (30), 6 M a week each (26, t3_review's buckets)."""
    if span == "month":
        return [[i] for i in range(R.DAYS - 30, R.DAYS)]
    return [d for _, d in R.buckets("6m")]


def year_buckets(span):
    """The same bucket length over the whole year: the other legitimate range for an own range."""
    if span == "month":
        return [[i] for i in range(R.DAYS)]
    return [list(range(e - 7, e)) for e in range(R.DAYS, 6, -7)]


def value(k, days):
    """The bucket's value by the picked rule (T3c.2), or None when nothing was logged."""
    it = BY[k]
    logged = [DATA[k][i] for i in days if DATA[k][i] is not None]
    if not logged:
        return None
    if it["kind"] == "choices":
        return sum(1 for v in logged if v == it["option"]) / len(logged)
    return sum(logged) / len(logged)


# ==== the drawings: one box, every form ==========================================================================================
W = R.W                 # 312, the chart's width (as stage 2)
H_BOX = 260             # HAND-SET: the chart's box on Review, the same for every form and size (stage 5 settles it)
LANE_GAP = 4            # HAND-SET: px between lanes
ALPHA = 0.6             # HAND-SET, PROVISIONAL (owner's note): overlaid series drawn at this opacity until the palette pass
STEP_ENOUGH = 12        # HAND-SET (t3_graphs): a step this size is plainly seen; more pixels read no better
BANDS = 2               # HAND-SET: a horizon row's layers (Heer et al. 2009 tested two to four; two kept it readable)
MAX_AXES = 4            # the control's cap (T3c.1: Oracle-like, up to four)
SCALE_COST = {1: 0.0, 2: 1 / 3, 3: 2 / 3, 4: 1.0}   # HAND-SET spacing of the Cleveland & McGill order
DASH = ("", "6 3", "2 3", "8 3 2 3", "1 2", "10 4", "4 4", "6 2 2 2", "3 6", "12 2")   # PROVISIONAL: series told apart


def nice_up(x):
    """1, 2, 2.5, 5 x 10^k at or above x (the usual axis rule)."""
    if x <= 0:
        return 1.0
    e = 10 ** math.floor(math.log10(x))
    for m in (1, 2, 2.5, 5, 10):
        if m * e >= x - 1e-9:
            return m * e
    return 10 * e


def nice_down(x, step_of):
    s = nice_up(step_of) / 5
    return math.floor(x / s) * s


class Series:
    """One item as drawn: its frame (top, bottom), axis, the unit of what is plotted, its points and the cells it inks."""

    def __init__(self, key, top, bottom, axis, unit, bands=1):
        self.key, self.top, self.bottom, self.axis, self.unit, self.bands = key, top, bottom, axis, unit, bands
        self.ys, self.pos, self.alt = [], [], []   # per bucket: y px, position in the frame 0..1, the same under the free choice
        self.cells, self.parts, self.step = set(), [], 0.0

    def stamp_line(self, pts, width=2):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.ceil(math.dist((x0, y0), (x1, y1)) / 0.5)))
            for s in range(n + 1):
                x, y = x0 + (x1 - x0) * s / n, y0 + (y1 - y0) * s / n
                for dx in range(width):
                    for dy in range(width):
                        self.cells.add((int(x) - width // 2 + dx, int(y) - width // 2 + dy))

    def stamp_dot(self, x, y, r=2.5):
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx * dx + dy * dy <= r * r:
                    self.cells.add((int(x) + dx, int(y) + dy))

    def stamp_rect(self, x, y, w, h):
        for cx in range(int(x), int(math.ceil(x + w))):
            for cy in range(int(y), int(math.ceil(y + h))):
                self.cells.add((cx, cy))


def _q(it, v, how, rng=None):
    """The plotted quantity and its unit: percent of goal, a share of the own range, or the raw value."""
    if how == "pct" and it["goal"]:
        return v / it["goal"] * 100, "% of goal"
    if how in ("pct", "own"):
        lo, hi = rng
        return (v - lo) / ((hi - lo) or 1), "own range"
    return v, it["unit"]


def _range(k, bks):
    vs = [x for x in (value(k, d) for d in bks) if x is not None]
    return (min(vs), max(vs)) if vs else (0, 1)


def _line(s, xs, opacity, dash):
    """Ink a series' points as a broken line (empty breaks it), a lone point as a dot; and its SVG."""
    seg = []
    for x, y in list(zip(xs, s.ys)) + [(None, None)]:
        if y is None:
            if len(seg) > 1:
                s.stamp_line(seg)
                s.parts.append('<polyline points="%s" style="fill:none;stroke:var(--ink);stroke-width:2;opacity:%g"%s/>' % (
                    " ".join("%.1f,%.1f" % p for p in seg), opacity, ' stroke-dasharray="%s"' % dash if dash else ""))
            elif len(seg) == 1:
                s.stamp_dot(*seg[0])
                s.parts.append('<circle cx="%.1f" cy="%.1f" r="2.5" fill="var(--ink)" opacity="%g"/>' % (seg[0][0], seg[0][1], opacity))
            seg = []
        else:
            seg.append((x, y))


def draw(form, keys, span):
    """The form drawn for these items at this span: [Series] in drawing order (later ones lie on top)."""
    bks, yb = bucket_days(span), year_buckets(span)
    nb, n = len(bks), len(keys)
    xs = [(j + 0.5) * W / nb for j in range(nb)]
    out = []
    if form in ("dual", "pct", "own"):   # shared space: one frame, every item overlaid
        top, bot = 0, H_BOX
        if form == "dual":
            units = []
            for k in keys:
                if BY[k]["unit"] not in units:
                    units.append(BY[k]["unit"])
            axis_of = {u: min(i, MAX_AXES - 1) for i, u in enumerate(units)}
            span_of = {}
            for a in range(min(len(units), MAX_AXES)):
                vs = [value(k, d) for k in keys if axis_of[BY[k]["unit"]] == a for d in bks]
                vs = [v for v in vs if v is not None] or [0, 1]
                hi = nice_up(max(vs))
                # from zero (the usual default), or fitted to the data: the choice the form leaves free
                span_of[a] = ((0, hi), (nice_down(min(vs), hi - min(vs)), nice_up(max(vs))))
        if form == "pct":
            pmax = max([value(k, d) / BY[k]["goal"] * 100 for k in keys if BY[k]["goal"] for d in bks if value(k, d) is not None] or [100])
            pmax = nice_up(pmax)
        for i, k in enumerate(keys):
            it = BY[k]
            rs, ry = _range(k, bks), _range(k, yb)
            if form == "dual":
                a = axis_of[it["unit"]]
                s = Series(k, top, bot, "axis%d" % a, it["unit"])
                (lo, hi), (lo2, hi2) = span_of[a]
                s.step = (bot - top) / 10
            else:
                q0, unit = _q(it, 1, form, rs)
                s = Series(k, top, bot, unit, unit)
                lo, hi = (0, pmax) if unit == "% of goal" else (0, 1)
                s.step = (bot - top) / 10
            for d in bks:
                v = value(k, d)
                if v is None:
                    s.ys.append(None), s.pos.append(None), s.alt.append(None)
                    continue
                if form == "dual":
                    p, p2 = (v - lo) / ((hi - lo) or 1), (v - lo2) / ((hi2 - lo2) or 1)
                else:
                    q, unit = _q(it, v, form, rs)
                    p = (q - lo) / ((hi - lo) or 1)
                    p2 = _q(it, v, form, ry)[0] if unit == "own range" else p   # the year's range instead of the span's
                s.pos.append(p), s.alt.append(p2), s.ys.append(bot - p * (bot - top))
            _line(s, xs, ALPHA, DASH[i % len(DASH)])
            out.append(s)
        return out
    # split space: a lane per item, one time axis
    h = H_BOX / n
    for i, k in enumerate(keys):
        it = BY[k]
        top, bot = i * h, (i + 1) * h - LANE_GAP
        rs, ry = _range(k, bks), _range(k, yb)
        lh = bot - top
        if form == "runs":   # a bar per run of days the goal was met (with a goal), or done / logged / on its option (without)
            # a day is a hit: yes/no done (a weekly goal has no daily meaning); a choice on its option; an amount at its
            # goal, or merely logged when it has none
            unit = {"yes/no": "done", "choices": it.get("option", "")}.get(it["kind"], "goal met" if it["goal"] else "logged")
            s = Series(k, top, bot, "lane", unit)
            first = bks[0][0]
            dx = W / (R.DAYS - first)
            hits = []
            for i2 in range(first, R.DAYS):
                v = DATA[k][i2]
                if v is None:
                    hits.append(None)
                elif it["kind"] == "yes/no":
                    hits.append(1 if v == 1 else 0)
                elif it["kind"] == "choices":
                    hits.append(1 if v == it["option"] else 0)
                else:
                    hits.append(1 if (not it["goal"] or v >= it["goal"]) else 0)
            # compared per bucket: the share of the bucket's logged days that hit, its bar's y the lane's middle
            for d in bks:
                hs = [hits[i2 - first] for i2 in d if hits[i2 - first] is not None]
                if not hs:
                    s.ys.append(None), s.pos.append(None), s.alt.append(None)
                    continue
                p = sum(hs) / len(hs)
                s.pos.append(p), s.alt.append(p), s.ys.append(top + lh / 2)
            j = 0
            while j < len(hits):
                if hits[j] == 1:
                    e = j
                    while e < len(hits) and hits[e] == 1:
                        e += 1
                    s.stamp_rect(j * dx, top + lh * 0.2, max(1, (e - j) * dx - 0.5), lh * 0.6)
                    s.parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="var(--ink)"/>' % (
                        j * dx, top + lh * 0.2, max(1, (e - j) * dx - 0.5), lh * 0.6))
                    j = e
                else:
                    j += 1
            s.step = lh * 0.6   # on or off: the bar is the step
            out.append(s)
            continue
        bands = BANDS if form == "horizon" else 1
        s = Series(k, top, bot, "lane", "own range", bands)
        s.step = lh * bands / 10
        for j, d in enumerate(bks):
            v = value(k, d)
            if v is None:
                s.ys.append(None), s.pos.append(None), s.alt.append(None)
                continue
            p, p2 = _q(it, v, "own", rs)[0], _q(it, v, "own", ry)[0]
            s.pos.append(p), s.alt.append(p2)
            if form == "horizon":   # folded: the lower half a light band, the upper half laid over it darker
                f = min(p * bands, bands - 1e-9)
                layer, part = int(f), f - int(f)
                y = bot - part * lh
                bw = W / nb
                for L in range(layer + 1):
                    hh = lh if L < layer else part * lh
                    s.stamp_rect(j * bw, bot - hh, bw - 0.5, hh)
                    s.parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="var(--%s)"/>' % (
                        j * bw, bot - hh, bw - 0.5, hh, "dim" if L == 0 else "ink"))
                s.ys.append(y)
            else:
                s.ys.append(bot - p * lh)
        if form == "lanes":
            _line(s, xs, 1, "")
        out.append(s)
    return out


# ==== Comparability ==============================================================================================================
def scale_rank(a, b):
    """Cleveland & McGill's order, read from the drawing (see the docstring)."""
    if a.unit != b.unit:
        return 4
    if (a.top, a.bottom) == (b.top, b.bottom) and a.axis == b.axis:
        return 1
    if abs((a.bottom - a.top) - (b.bottom - b.top)) < 0.5 and a.bands == b.bands == 1:
        return 2
    return 3


def hidden(series):
    """Per series: the share of its cells under cells of series drawn after it."""
    out, above = {}, set()
    for s in reversed(series):
        out[s.key] = len(s.cells & above) / len(s.cells) if s.cells else 0.0
        above |= s.cells
    return out


def pair_parts(a, b, hid):
    both = [j for j in range(len(a.ys)) if a.ys[j] is not None and b.ys[j] is not None]
    if not both:
        return None
    travel = sum(abs(a.ys[j] - b.ys[j]) for j in both) / len(both) / H_BOX
    sign = lambda x: (x > 1e-9) - (x < -1e-9)
    flips = sum(1 for j in both if sign(a.pos[j] - b.pos[j]) != sign(a.alt[j] - b.alt[j])) / len(both)
    res = (max(0.0, 1 - a.step / STEP_ENOUGH) + max(0.0, 1 - b.step / STEP_ENOUGH)) / 2
    return {"scale": SCALE_COST[scale_rank(a, b)], "travel": travel, "hidden": ALPHA * (hid[a.key] + hid[b.key]) / 2,
            "resolution": res, "flips": flips, "shared": len(both)}


PARTS = ("scale", "travel", "hidden", "resolution", "flips")


def comparability(form, size, spans=("month", "6m")):
    """{'comp': the cost, each part's mean, 'pairs': pairs compared} for a form at 2 or 10 items; lower is better."""
    keys = SETS[size]
    acc = {p: 0.0 for p in PARTS}
    pairs = 0
    for span in spans:
        ss = draw(form, keys, span)
        hid = hidden(ss)
        got = [pp for a, b in itertools.combinations(ss, 2) for pp in [pair_parts(a, b, hid)] if pp]
        pairs += len(got)
        for p in PARTS:
            acc[p] += sum(g[p] for g in got) / len(got) / len(spans)
    out = {p: round(acc[p], 4) for p in PARTS}
    out["comp"] = round(sum(acc.values()), 4)
    out["pairs"] = pairs
    return out


FORMS = {"pct": "percent of goal, overlaid (own range where an item has no goal)", "own": "each item's own range, overlaid",
         "lanes": "stacked lanes, each its own range, one time axis", "horizon": "horizon rows, two layers, each its own range",
         "runs": "Gantt-like runs in a lane per item (goal met, done, or logged)",
         "dual": "CONTROL: dual y-axes, every item overlaid on its unit's axis (up to four)"}


def table():
    rows = {f: {n: comparability(f, n) for n in (2, 10)} for f in FORMS}
    return rows


# ==== the throwaway sheet ========================================================================================================
def sheet(path):
    css = (":root{--ink:#222;--dim:#999;--bg:#fff;--zone2:#ccc}body{background:var(--bg);color:var(--ink);font:13px sans-serif;margin:16px}"
           "svg{background:#f4f4f4;margin:2px 12px 12px 0}h3{font-size:13px;margin:10px 0 2px}")
    body = []
    for f, what in FORMS.items():
        for n in (2, 10):
            for span in ("month", "6m"):
                ss = draw(f, SETS[n], span)
                body.append('<h3>%s · %d items · %s</h3><svg width="%d" height="%d">%s</svg>' % (
                    what, n, "Month" if span == "month" else "6 M", W, H_BOX, "".join(p for s in ss for p in s.parts)))
    with open(path, "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write('<!doctype html><meta charset="utf-8"><title>Overlap forms</title><style>%s</style>%s' % (css, "".join(body)))


# ==== the self-check =============================================================================================================
def selftest():
    kinds = {it["kind"] for it in ITEMS}
    assert len(ITEMS) == 10 and kinds == {"count", "minutes", "yes/no", "choices", "weight", "ratings"}, kinds
    assert 0 < sum(1 for it in ITEMS if it["goal"]) < 10, "goals on some items, not all"
    dens = [density(it["key"]) for it in ITEMS]
    assert min(dens) < SPARSE * 0.9 and max(dens) > DENSE * 0.9, dens   # the holiday's three weeks shave the dense ones
    assert BY[PAIR[0]]["unit"] != BY[PAIR[1]]["unit"], "the pair is two units"
    assert make_items() == DATA, "the data is deterministic"
    first, second = table(), table()
    assert first == second, "the measure is deterministic"
    order = {n: sorted(FORMS, key=lambda f: first[f][n]["comp"]) for n in (2, 10)}
    assert order[2][-1] == "dual", order[2]   # at 2 items the control is last
    # at 10 items it is NOT last (2026-10-28, constants left as set): 22 px lanes give 2.2 px for a tenth of a range, and
    # lanes and horizon rows fall behind it on resolution. It still loses to at least two candidates at both sizes; the
    # exact set behind it is held here so a change to the data or the measure is seen, not absorbed
    for n in (2, 10):
        assert len(order[n][:order[n].index("dual")]) >= 2, (n, order[n])
    assert set(order[10][order[10].index("dual") + 1:]) == {"lanes", "horizon"}, order[10]
    print("NOT last at 10 items: behind the control", order[10][order[10].index("dual") + 1:])
    print("selftest ok:", {n: [(f, first[f][n]["comp"]) for f in sorted(FORMS, key=lambda f: first[f][n]["comp"])] for n in (2, 10)})


if __name__ == "__main__":
    if "selftest" in sys.argv[1:]:
        selftest()
    if "table" in sys.argv[1:]:
        for it in ITEMS:
            print("%-9s %-8s %-14s goal %-5s logged %.2f" % (it["name"], it["kind"], it["unit"], "yes" if it["goal"] else "no", density(it["key"])))
        t = table()
        for n in (2, 10):
            print("--- %d items" % n)
            for f in sorted(FORMS, key=lambda f: t[f][n]["comp"]):
                print("%-8s %s" % (f, t[f][n]))
    if "sheet" in sys.argv[1:]:
        sheet(sys.argv[sys.argv.index("sheet") + 1])
