"""T3b.7a the graphs, scored per kind of value before the item's page is re-scored (owner, 2026-10-16).

Registered into t3_opt's parts by t3_opt itself (register(globals()) at its end), so the usual run scores them:
    python tools/screens/t3_opt.py gk_count gk_rating gk_yesno gk_choice gk_add gk_level page_html scores

The kinds, each with 30 placeholder days ending Fri 16 Oct 2026 (a day with no entry is None):
  gk_count   Water, glasses a day, goal 8 (counts)
  gk_rating  Mood, 1 to 5 (ratings)
  gk_yesno   Walk, done or not (yes/no)
  gk_choice  Lunch: home, out, packed, skipped (choices)
  gk_add     Reading, minutes a day, goal 30 (an amount that adds up)
  gk_level   Weight, kg, goal 70, not every day (an amount that does not add up)

Forms come from the graph survey (_screens-sources/t3/goals/graphs/notes.md: openScale, Loop, Track & Graph, Chronicle,
Streak, aTimeLogger, Timety, drip). No heatmap (owner). Each option is a form x its y-axis (grid / the two ends / none) x
the values printed (none / the last / every one); a weight's y-range (fit to the data / a plausible band, drip's way /
from zero) is a fourth dimension. Each kind has two controls, the surveyed apps' own charts, which must lose.

Axes (owner): fit to the data, readability at phone size, calm, mental load; consistency the lowest weight (0.25, in the
total only).
  Fit (computed from the drawing and the data): a day with no entry drawn as zero; a line across days with no entry; bars
    not from zero; a sum implied of a value that does not add up (bars, area, a running total of a weight); a quantity
    implied of a rating (bars from zero); a line through whole counts; smoothing that invents values; the goal outside the
    range; two units on one axis or two axes.
  Readability (measured in headless Edge at 360x740, and the geometry): the smallest text, text overlapping text or cut at
    the edge, the smallest mark, pixels for one meaningful step (a glass, a rating step, 5 min, 0.5 kg; a day's cell for
    yes/no and choices).
  Calm: ink (the marks' area over the chart's), day-to-day jitter in pixels (a range fit to the data makes 0.3 kg look like
    a fall), comparative or gamified elements (percent scores, streaks).
  Mental load: the cost of answering each kind's three questions from the graph (0 read off, 1 a visual comparison or a
    count up to 7, 2 a sum or a count to 30, 3 not answerable) - HAND-SET per form, a reading of what each form shows,
    flagged; plus the numbers printed / 10, a second series, a legend to look up.
  Consistency: how many other kinds use the same form (one family of graphs across the app).
"""
import math
import threading

LOCK = threading.Lock()

# ==== the data ===================================================================================================================
DAYS = 30
X_LABELS = ((0, "17 Sep"), (14, "1 Oct"), (29, "16 Oct"))
WATER = [5, 7, 8, 4, 6, 8, 9, 3, 5, None, 8, 6, 5, 8, 7, 4, 6, 8, 5, 7, 9, None, 5, 8, 7, 6, 4, 8, 7, 5]
MOOD = [3, 4, 3, 2, 4, 4, 5, 3, None, 3, 2, 2, 3, 4, 4, 3, 5, 4, None, 3, 3, 4, 2, 3, 4, 4, None, 4, 5, 4]
WALK = [1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1]
LUNCH = ["home", "out", "home", "packed", "home", "out", "skipped", "home", "packed", "packed", "home", "out", "home", "skipped",
         "packed", "packed", "home", "home", "out", "packed", "home", "skipped", "packed", "packed", "home", "out", "home", "packed", "packed", None]
CHOICES = ("home", "packed", "out", "skipped")
READING = [20, 35, 0, 45, 30, 25, 0, 50, 30, 20, 40, 0, 35, 30, 25, 45, 0, 30, 20, 35, 40, 0, 25, 30, 45, 20, 0, 35, 30, 20]
WEIGHT = [73.8, None, 73.9, 73.4, None, 73.2, None, 73.0, 73.1, None, 73.2, 72.8, None, 72.9, 72.6, None, 72.5, 72.4, None, 72.3,
          72.5, None, 72.4, 72.1, None, 72.0, 72.2, None, 72.1, 72.4]

W, H, BOT = 312, 132, 16          # the chart's width, the plot's height, the date row under it
TOP = 10                          # room above the plot for a printed value
KINDS = {
    "count": dict(name="Water", vals=WATER, goal=8, lo=0, hi=10, ticks=(0, 2, 4, 6, 8, 10), step=1, unit="glasses"),
    "rating": dict(name="Mood", vals=MOOD, goal=None, lo=1, hi=5, ticks=(1, 2, 3, 4, 5), step=1, unit=""),
    "yesno": dict(name="Walk", vals=WALK, goal=None, lo=0, hi=7, ticks=(0, 7), step=None, unit="days"),
    "choice": dict(name="Lunch", vals=LUNCH, goal=None, lo=0, hi=1, ticks=(), step=None, unit=""),
    "add": dict(name="Reading", vals=READING, goal=30, lo=0, hi=60, ticks=(0, 20, 40, 60), step=5, unit="min"),
    "level": dict(name="Weight", vals=WEIGHT, goal=70, lo=None, hi=None, ticks=None, step=0.5, unit="kg"),
}
LEVEL_RANGE = {"fit": (71.8, 74.0, (72, 73, 74)), "plausible": (69, 75, (69, 70, 71, 72, 73, 74, 75)), "zero": (0, 80, (0, 20, 40, 60, 80))}

FORMS = {
    "count": ["bars", "stubs", "lollipop", "dots", "line", "weeks", "dist"],
    "rating": ["strip", "line", "bars", "band", "dist", "avg"],
    "yesno": ["ticks", "weeks", "tally", "runs", "cumul"],
    "choice": ["strip", "hbars", "stacked", "pie", "rows"],
    "add": ["bars", "stubs", "lollipop", "weeks", "cumul", "line", "bars_avg"],
    "level": ["line", "dots", "avg", "smooth", "band", "bars", "area", "spark"],
}
NO_AXIS = {"count": {"dist"}, "rating": {"dist"}, "yesno": {"ticks", "tally", "runs"}, "choice": set(FORMS["choice"]), "add": set(), "level": {"spark"}}   # no y-axis to draw
SAME = {"dist": ("last",), "tally": ("last", "every"), "spark": ("last", "every"), "pie": ("last",), "hbars": ("last",), "runs": ("last",)}   # values that draw nothing new
# the three questions per kind, and what each form costs to answer them (HAND-SET, a reading of the form; see the docstring)
QUESTIONS = {
    "count": ("today against the goal", "a usual day", "more or less than before"),
    "rating": ("a usual day", "the low days", "better or worse than before"),
    "yesno": ("days this week", "days this month", "when it was missed"),
    "choice": ("the most often", "how it changed", "a given day"),
    "add": ("today against the goal", "this week's total", "more or less than before"),
    "level": ("now", "the trend", "the distance to the goal"),
}
COSTS = {
    "count": {"bars": (0, 1, 1), "stubs": (0, 1, 1), "lollipop": (0, 1, 1), "dots": (0, 1, 1), "line": (0, 1, 0), "weeks": (3, 2, 0), "dist": (3, 0, 3)},
    "rating": {"strip": (1, 0, 1), "line": (1, 1, 0.5), "bars": (1, 0, 1), "band": (0, 1, 0), "dist": (0, 0, 3), "avg": (0, 0, 0)},
    "yesno": {"ticks": (1, 2, 0), "weeks": (0, 2, 3), "tally": (1, 0, 0), "runs": (2, 2, 0), "cumul": (1, 0, 1)},
    "choice": {"strip": (2, 1, 0), "hbars": (0, 3, 3), "stacked": (1, 0, 3), "pie": (1, 3, 3), "rows": (1, 1, 0)},
    "add": {"bars": (0, 2, 1), "stubs": (0, 2, 1), "lollipop": (0, 2, 1), "weeks": (3, 0, 0), "cumul": (1, 1, 0), "line": (0, 2, 0.5), "bars_avg": (0, 2, 0)},
    "level": {"line": (1, 0, 1), "dots": (1, 1, 1), "avg": (1, 0, 1), "smooth": (1, 0, 1), "band": (2, 0, 1), "bars": (1, 1, 1), "area": (1, 0, 1), "spark": (0, 0, 3)},
}
DAILY = {"bars", "stubs", "lollipop", "dots", "line", "strip", "avg", "smooth", "area", "bars_avg", "ticks", "tally", "cumul", "rows", "spark"}   # a mark per day


ENCODING = {"line": 0, "dots": 0, "strip": 0, "avg": 0, "smooth": 0, "cumul": 0, "lollipop": 0, "ticks": 0, "tally": 0, "rows": 0, "spark": 0,
            "area": 1, "bars": 1, "stubs": 1, "bars_avg": 1, "weeks": 1, "dist": 1, "hbars": 1, "runs": 1, "band": 1, "stacked": 2, "pie": 2,
            "chronicle": 1, "trackandgraph": 0, "loop": 0, "streak": 0, "atimelogger": 2, "timety": 0, "openscale": 0, "openscale_home": 0}
CTL_ENCODING = {("choice", "trackandgraph"): 2}
STEP_ENOUGH, MARK_ENOUGH = 12, 6   # HAND-SET: a step or a mark this size is plainly seen; more pixels read no better
NOISE_FLAT = 3   # HAND-SET: day-to-day jitter under 3 px reads as flat; less is no calmer (a range from zero bought calm with an unreadable trend)


def fmt(x):
    return ("%g" % round(x, 1)) if isinstance(x, float) else str(x)


def valid(kind):
    def ok(v):
        if v.get("control"):
            return True
        f = v["form"]
        if f in NO_AXIS[kind] and v["yaxis"] != "none":
            return False   # no axis to draw
        if v["values"] in SAME.get(f, ()):
            return False   # the same drawing as another option
        if kind == "choice" and f in ("strip", "rows") and v["values"] == "last":
            return False   # the last day's choice is its own mark already
        if kind == "choice" and f == "strip" and v["values"] == "every":
            return False   # every day's letter is the strip itself
        if kind in ("count", "add") and v["range"] == "fit" and f != "line":
            return False   # a length read from a cut baseline misleads; only a line may fit its range
        return True
    return ok


# ==== drawing ===================================================================================================================
class Chart:
    """One chart: the marks, and the geometry the scorer reads (ink, the smallest mark, pixels per step, jitter)."""

    def __init__(self, kind, v):
        self.k, self.v, self.cfg = kind, v, KINDS[kind]
        self.parts, self.ink, self.marks = [], 0.0, []
        self.misfit, self.series, self.legend, self.compare = {}, 1, 0, 0
        ya = v.get("yaxis", "none")
        self.g = 0 if ya == "none" else 26
        if kind == "level":
            lo, hi, ticks = LEVEL_RANGE[v.get("range", "fit")]
        elif v.get("range") == "fit":
            have = [x for x in self.cfg["vals"] if x is not None]
            lo, hi = min(have), max(have)
            ticks = tuple(round(lo + (hi - lo) * k / 3) for k in range(4))
        else:
            lo, hi, ticks = self.cfg["lo"], self.cfg["hi"], self.cfg["ticks"]
        self.lo, self.hi, self.ticks = lo, hi, ticks
        self.pw = W - self.g - 4
        self.sw = self.pw / DAYS
        self.ys = []   # y of every daily mark, for jitter

    def x(self, i):
        return self.g + i * self.sw + self.sw / 2

    def y(self, val, lo=None, hi=None):
        lo = self.lo if lo is None else lo
        hi = self.hi if hi is None else hi
        return TOP + H - (val - lo) / ((hi - lo) or 1) * H

    def add(self, svg, area=0.0, mark=None):
        self.parts.append(svg)
        self.ink += area
        if mark is not None:
            self.marks.append(mark)

    def text(self, x, y, t, size=11, anchor="middle", dim=True):
        self.parts.append('<text x="%.1f" y="%.1f" font-size="%g" fill="var(--%s)" text-anchor="%s">%s</text>' % (x, y, size, "dim" if dim else "ink", anchor, t))

    def rect(self, x, y, w, h, fill="var(--ink)", rx=2, mark=True):
        h = max(h, 0)
        self.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%g" fill="%s"/>' % (x, y, w, h, rx, fill), w * h, min(w, h) if (h > 0 and mark) else None)

    def dot(self, x, y, r=3, fill="var(--ink)"):
        self.add('<circle cx="%.1f" cy="%.1f" r="%g" fill="%s"/>' % (x, y, r, fill), math.pi * r * r, 2 * r)

    def poly(self, pts, width=2, colour="var(--ink)", dash=""):
        d = " ".join("%.1f,%.1f" % p for p in pts)
        length = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        self.add('<polyline points="%s" style="fill:none;stroke:%s;stroke-width:%g"%s/>' % (d, colour, width, ' stroke-dasharray="%s"' % dash if dash else ""), length * width, width)

    def axis(self):
        ya = self.v.get("yaxis", "none")
        self.parts.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="var(--dim)" stroke-width="1"/>' % (self.g, W - 4, TOP + H, TOP + H))
        if ya != "none" and self.ticks:
            shown = self.ticks if ya == "grid" else (self.ticks[0], self.ticks[-1])
            for t in shown:
                yy = self.y(t)
                if ya == "grid" and t != self.ticks[0]:
                    self.parts.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="var(--zone2)" stroke-width="1"/>' % (self.g, W - 4, yy, yy))
                self.text(self.g - 4, yy + 4, fmt(t), 12, "end")
        for i, t in X_LABELS:
            self.text(min(max(self.x(i), 20 + self.g), W - 24), TOP + H + 13, t, 12)

    def goal(self, val, label=None):
        if val is None:
            return
        if not (self.lo <= val <= self.hi):
            self.misfit["goal outside the range"] = 1
            return
        yy = self.y(val)
        self.parts.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="var(--dim)" stroke-width="1" stroke-dasharray="4 4"/>' % (self.g, W - 4, yy, yy))
        self.text(W - 6, yy - 3, label or "goal %s" % fmt(val), 12, "end")

    def values(self, pts, show):
        """The values printed: the last, or every one (pts: (x, y, text))."""
        if show == "last" and pts:
            x, y, t = pts[-1]
            self.text(min(x, W - 12), y - 5, t, 12, "middle", dim=False)
        elif show == "every":
            for x, y, t in pts:
                self.text(x, y - 4, t, 9, "middle")

    def svg(self):
        return ('<svg width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="chart">%s</svg>' % (W, TOP + H + BOT + 2, W, TOP + H + BOT + 2, "".join(self.parts)))


def daily_bars(c, vals, stubs, from_zero_lo=None):
    base = c.y(c.lo if from_zero_lo is None else from_zero_lo)
    pts = []
    for i, val in enumerate(vals):
        if val is None:
            if stubs:
                c.rect(c.x(i) - c.sw / 2 + 1.5, base - 2, c.sw - 3, 2, "var(--dim)", 0, mark=False)   # no entry, not a value
            else:
                c.misfit["no entry drawn as zero"] = 1
            continue
        yy = c.y(val)
        c.rect(c.x(i) - c.sw / 2 + 1.5, yy, c.sw - 3, base - yy)
        c.ys.append(yy)
        pts.append((c.x(i), yy, fmt(val)))
    return pts


def line_through(c, vals, dots=False, smooth=False, width=2):
    pts, seg, prev_none, out = [], [], False, []
    for i, val in enumerate(vals):
        if val is None:
            prev_none = True
            continue
        if prev_none and pts and not (c.k == "level" and dots):   # a weight's entries joined, each a dot: drip's and openScale's way
            c.misfit["a line across days with no entry"] = 0.5
        prev_none = False
        p = (c.x(i), c.y(val))
        pts.append(p)
        c.ys.append(p[1])
        out.append((p[0], p[1], fmt(val)))
    if smooth:   # openScale's spline: midpoints eased, values that were never entered drawn between entries
        c.misfit["smoothing invents values"] = 0.5
        sm = []
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            for t in (0, 0.25, 0.5, 0.75):
                e = t * t * (3 - 2 * t)
                sm.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * e))
        sm.append(pts[-1])
        c.poly(sm, width)
    else:
        c.poly(pts, width)
    if dots:
        for x, y in pts:
            c.dot(x, y, 3)
    return out


def weekly(vals):
    """Four full weeks back from today, then the two days before them: (first day, values)."""
    out, end = [], DAYS
    while end > 0:
        start = max(0, end - 7)
        out.insert(0, (start, vals[start:end]))
        end = start
    return out


def draw(kind, v):
    if v.get("control"):
        return draw_control(kind, v["control_app"])
    c = Chart(kind, v)
    cfg, f, show = c.cfg, v["form"], v.get("values", "none")
    vals = cfg["vals"]
    if kind in ("count", "add", "rating", "level"):
        if kind == "level" and f in ("bars", "area"):
            c.misfit["a sum implied of a weight"] = 1
        if kind == "rating" and f == "bars":
            c.misfit["a quantity implied of a rating"] = 0.5
        if kind in ("count", "rating") and f == "line":
            c.misfit["a line through whole values"] = 0.5
        if kind == "add" and f == "line":
            c.misfit["a line between daily totals"] = 0.5
        if f in ("bars", "stubs", "bars_avg"):
            if kind == "level" and c.lo > 0:
                c.misfit["bars not from zero"] = 1
            c.axis()
            pts = daily_bars(c, vals, f == "stubs" or kind == "level", c.lo)
            if f == "bars_avg":
                av = [sum(x for x in vals[max(0, i - 6):i + 1] if x is not None) / max(1, sum(1 for x in vals[max(0, i - 6):i + 1] if x is not None)) for i in range(DAYS)]
                c.poly([(c.x(i), c.y(a)) for i, a in enumerate(av)], 2, "var(--dim)")
                c.series = 2
            c.goal(cfg["goal"])
            c.values(pts, show)
        elif f == "lollipop":
            c.axis()
            pts = []
            for i, val in enumerate(vals):
                if val is None:
                    continue
                yy = c.y(val)
                c.add('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" stroke="var(--ink)" stroke-width="1.5"/>' % (c.x(i), c.x(i), c.y(c.lo), yy), 1.5 * (c.y(c.lo) - yy), 1.5)
                c.dot(c.x(i), yy, 3.5)
                c.ys.append(yy)
                pts.append((c.x(i), yy, fmt(val)))
            c.goal(cfg["goal"])
            c.values(pts, show)
        elif f == "dots" and kind == "count":   # a dot per glass, stacked (Loop's frequency dots, read as units)
            c.axis()
            pts = []
            for i, val in enumerate(vals):
                if val is None:
                    continue
                for k in range(val):
                    c.dot(c.x(i), c.y(k + 0.5), min(3.2, c.sw / 2 - 1))
                c.ys.append(c.y(val))
                pts.append((c.x(i), c.y(val), fmt(val)))
            c.goal(cfg["goal"])
            c.values(pts, show)
        elif f in ("line", "smooth", "area"):
            c.axis()
            if f == "area":
                pp = [(c.x(i), c.y(x)) for i, x in enumerate(vals) if x is not None]
                c.add('<polygon points="%s %.1f,%.1f %.1f,%.1f" fill="var(--zone2)"/>' % (" ".join("%.1f,%.1f" % p for p in pp), pp[-1][0], c.y(c.lo), pp[0][0], c.y(c.lo)),
                      sum(c.y(c.lo) - p[1] for p in pp) * c.sw * 0.4)
            pts = line_through(c, vals, dots=(kind == "level" and f == "line"), smooth=(f == "smooth"))
            c.goal(cfg["goal"])
            c.values(pts, show)
        elif f in ("strip", "dots", "avg"):   # a dot per day at its value; avg adds a 7-day mean (a second series)
            c.axis()
            pts = []
            for i, val in enumerate(vals):
                if val is None:
                    continue
                c.dot(c.x(i), c.y(val), 3.2, "var(--dim)" if f == "avg" else "var(--ink)")
                c.ys.append(c.y(val))
                pts.append((c.x(i), c.y(val), fmt(val)))
            if f == "avg":
                av = []
                for i in range(DAYS):
                    w = [x for x in vals[max(0, i - 6):i + 1] if x is not None]
                    av.append((c.x(i), c.y(sum(w) / len(w))) if w else None)
                c.poly([p for p in av if p], 2)
                c.series = 2
            c.goal(cfg["goal"])
            c.values(pts, show)
        elif f == "band":   # each week's lowest to highest, its mean a line
            c.axis()
            pts = []
            for start, wk in weekly(vals):
                w = [x for x in wk if x is not None]
                if not w:
                    continue
                x0, x1 = c.g + start * c.sw + 3, c.g + (start + len(wk)) * c.sw - 3
                c.rect(x0, c.y(max(w)), x1 - x0, max(2, c.y(min(w)) - c.y(max(w))), "var(--zone2)", 4)
                m = sum(w) / len(w)
                c.poly([(x0, c.y(m)), (x1, c.y(m))], 2)
                c.ys.append(c.y(m))
                pts.append(((x0 + x1) / 2, c.y(max(w)), fmt(round(m, 1))))
            c.series = 2
            c.goal(cfg["goal"])
            c.values(pts, show)
        elif f == "weeks":   # each week's total (the last a part week)
            wks = weekly(vals)
            tot = [sum(x for x in wk if x is not None) for _, wk in wks]
            c.lo, c.hi = 0, (80 if kind == "count" else 300)
            c.ticks = (0, 40, 80) if kind == "count" else (0, 100, 200, 300)
            c.axis()
            pts = []
            for (start, wk), t in zip(wks, tot):
                x0, x1 = c.g + start * c.sw + 3, c.g + (start + len(wk)) * c.sw - 3
                c.rect(x0, c.y(t), x1 - x0, c.y(0) - c.y(t))
                c.ys.append(c.y(t))
                pts.append(((x0 + x1) / 2, c.y(t), fmt(t)))
            c.goal(cfg["goal"] * 7, "a week's goal %s" % fmt(cfg["goal"] * 7))
            c.values(pts, show)
        elif f == "cumul":   # the month's running total against the goal's pace
            run, acc = [], 0
            for x in vals:
                acc += x or 0
                run.append(acc)
            c.lo, c.hi, c.ticks = 0, 1000, (0, 500, 1000)
            c.axis()
            c.poly([(c.x(i), c.y(r)) for i, r in enumerate(run)], 2)
            c.ys += [c.y(r) for r in run]
            c.parts.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" stroke="var(--dim)" stroke-width="1" stroke-dasharray="4 4"/>' % (c.x(0), c.x(DAYS - 1), c.y(cfg["goal"]), c.y(cfg["goal"] * DAYS)))
            c.text(W - 6, c.y(cfg["goal"] * DAYS) + 12, "goal's pace", 12, "end")
            c.values([(c.x(i), c.y(r), fmt(r)) for i, r in enumerate(run)], show)
        elif f == "dist":   # days at each value
            levels = list(range(0, 11)) if kind == "count" else [1, 2, 3, 4, 5]
            cnt = [sum(1 for x in vals if x == k) for k in levels]
            bw = W / len(levels)
            top = max(cnt)
            pts = []
            for j, (k, n) in enumerate(zip(levels, cnt)):
                hh = n / top * H
                c.rect(j * bw + 3, TOP + H - hh, bw - 6, hh)
                c.text(j * bw + bw / 2, TOP + H + 13, str(k), 11)
                pts.append((j * bw + bw / 2, TOP + H - hh, str(n)))
            c.parts.append('<line x1="0" x2="%d" y1="%.1f" y2="%.1f" stroke="var(--dim)" stroke-width="1"/>' % (W, TOP + H, TOP + H))
            c.values(pts, "every" if show == "every" else "none")
        elif f == "spark":   # today's value large, a sparkline beside it (no axis, no goal drawn)
            last = [x for x in vals if x is not None][-1]
            c.parts.append('<text x="0" y="40" font-size="26" fill="var(--ink)">%s</text><text x="0" y="58" font-size="12" fill="var(--dim)">kg today</text>' % fmt(last))
            c.g, c.pw = 100, W - 104
            c.sw = c.pw / DAYS
            pp = [(c.x(i), 8 + (c.hi - x) / ((c.hi - c.lo) or 1) * 50) for i, x in enumerate(vals) if x is not None]
            c.poly(pp, 2)
            c.ys += [p[1] for p in pp]
            if any(x is None for x in vals):
                c.misfit["a line across days with no entry"] = 0.5
            c.misfit["the goal not drawn"] = 1 if not (c.lo <= cfg["goal"] <= c.hi) else 0
        return finish(c)
    if kind == "yesno":
        if f == "ticks":
            for i, d in enumerate(vals):
                if d:
                    c.rect(c.x(i) - c.sw / 2 + 1, TOP + H - 26, c.sw - 2, 26, "var(--ink)", 3)
                else:
                    c.rect(c.x(i) - c.sw / 2 + 1, TOP + H - 26, c.sw - 2, 26, "var(--zone2)", 3)
                c.ys.append(0)
            c.axis()
            if show != "none":
                c.text(W - 4, TOP + H - 34, "%d of 30 days" % sum(vals) if show == "last" else "this week %d · 30 days %d" % (sum(vals[-7:]), sum(vals)), 12, "end", False)
        elif f == "tally":   # the month's number large, a tick per day under it
            c.parts.append('<text x="0" y="%d" font-size="26" fill="var(--ink)">%d</text><text x="40" y="%d" font-size="13" fill="var(--dim)">of 30 days · %d this week</text>' % (TOP + 60, sum(vals), TOP + 60, sum(vals[-7:])))
            for i, d in enumerate(vals):
                c.rect(c.x(i) - c.sw / 2 + 1, TOP + H - 26, c.sw - 2, 26, "var(--ink)" if d else "var(--zone2)", 3)
                c.ys.append(0)
            c.axis()
        elif f == "weeks":
            c.lo, c.hi, c.ticks = 0, 7, (0, 7)
            c.axis()
            pts = []
            for start, wk in weekly(vals):
                t = sum(wk)
                x0, x1 = c.g + start * c.sw + 3, c.g + (start + len(wk)) * c.sw - 3
                c.rect(x0, c.y(t), x1 - x0, c.y(0) - c.y(t))
                pts.append(((x0 + x1) / 2, c.y(t), "%d" % t))
            c.values(pts, show)
        elif f == "runs":   # each run of days in a row as a bar along time (Loop's best streaks, kept in time)
            i = 0
            pts = []
            while i < DAYS:
                if vals[i]:
                    j = i
                    while j < DAYS and vals[j]:
                        j += 1
                    c.rect(c.g + i * c.sw + 1, TOP + H - 30, (j - i) * c.sw - 2, 14, "var(--ink)", 7)
                    pts.append((c.g + (i + j) / 2 * c.sw, TOP + H - 30, "%d" % (j - i)))
                    i = j
                else:
                    i += 1
            c.axis()
            c.values(pts, show)
        elif f == "cumul":
            run, acc = [], 0
            for d in vals:
                acc += d
                run.append(acc)
            c.lo, c.hi, c.ticks = 0, 30, (0, 10, 20, 30)
            c.axis()
            c.poly([(c.x(i), c.y(r)) for i, r in enumerate(run)], 2)
            c.values([(c.x(i), c.y(r), "%d" % r) for i, r in enumerate(run)], show)
        return finish(c)
    # choices
    letters = {"home": "H", "packed": "P", "out": "O", "skipped": "–"}
    shade = {"home": "var(--ink)", "packed": "var(--dim)", "out": "var(--zone2)", "skipped": "none"}
    cnt = {k: sum(1 for x in vals if x == k) for k in CHOICES}
    if f == "strip":   # a letter per day
        for i, x in enumerate(vals):
            if x:
                c.text(c.x(i), TOP + H - 8, letters[x], 12, "middle", False)
                c.marks.append(7)
                c.ink += 30
        c.axis()
        c.parts.append('<text x="0" y="%d" font-size="12" fill="var(--dim)">H home · P packed · O out · – skipped</text>' % (TOP + H - 40))
        c.legend = 1
    elif f == "rows":   # a row per choice, a mark on its days (small multiples, labelled)
        rh = H / len(CHOICES)
        c.g = 56
        c.pw = W - c.g - 4
        c.sw = c.pw / DAYS
        for j, k in enumerate(CHOICES):
            yy = TOP + j * rh + rh / 2
            c.text(0, yy + 4, k, 11, "start")
            for i, x in enumerate(vals):
                if x == k:
                    c.rect(c.x(i) - c.sw / 2 + 1, yy - 8, c.sw - 2, 16, "var(--ink)", 3)
            if show == "every":
                c.text(W - 2, yy + 4, str(cnt[k]), 9, "end")
        c.axis()
    elif f == "hbars":   # days per choice, most first
        order = sorted(CHOICES, key=lambda k: -cnt[k])
        rh = H / len(order)
        top = max(cnt.values())
        for j, k in enumerate(order):
            yy = TOP + j * rh
            c.text(0, yy + rh / 2 + 4, k, 12, "start")
            c.rect(64, yy + rh / 2 - 7, (W - 100) * cnt[k] / top, 14)
            if show != "none":
                c.text(64 + (W - 100) * cnt[k] / top + 6, yy + rh / 2 + 4, str(cnt[k]), 12, "start", False)
    elif f == "stacked":   # each week split by choice
        wks = weekly(vals)
        for start, wk in wks:
            x0 = c.g + start * c.sw + 3
            ww = len(wk) * c.sw - 6
            acc = 0
            n = len(wk)
            for k in CHOICES:
                m = sum(1 for x in wk if x == k)
                if m:
                    hh = m / n * H
                    c.rect(x0, TOP + H - acc - hh, ww, hh, shade[k] if shade[k] != "none" else "var(--bg)", 0)
                    if shade[k] == "none":
                        c.parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="var(--dim)"/>' % (x0, TOP + H - acc - hh, ww, hh))
                    if show == "every":
                        c.text(x0 + ww / 2, TOP + H - acc - hh / 2 + 3, str(m), 9, "middle")
                    acc += hh
        c.axis()
        c.parts.append('<text x="0" y="8" font-size="11" fill="var(--dim)">■ home  ▤ packed  □ out  ▢ skipped</text>')
        c.legend = 1
        c.series = 4
    elif f == "pie":
        c.add(pie_svg(cnt, show != "none"), math.pi * 55 * 55, 20)
        c.legend = 1
        c.series = 4
    return finish(c)


def pie_svg(cnt, pct, cx=80, cy=TOP + 66, r=55):
    tot = sum(cnt.values())
    fills = {"home": "var(--ink)", "packed": "var(--dim)", "out": "var(--zone2)", "skipped": "var(--bg)"}
    out, a = [], -math.pi / 2
    for k in CHOICES:
        da = cnt[k] / tot * 2 * math.pi
        x0, y0 = cx + r * math.cos(a), cy + r * math.sin(a)
        x1, y1 = cx + r * math.cos(a + da), cy + r * math.sin(a + da)
        out.append('<path d="M%.1f,%.1f L%.1f,%.1f A%d,%d 0 %d 1 %.1f,%.1f Z" fill="%s" stroke="var(--dim)" stroke-width="0.5"/>' % (cx, cy, x0, y0, r, r, 1 if da > math.pi else 0, x1, y1, fills[k]))
        if pct:
            m = a + da / 2
            out.append('<text x="%.1f" y="%.1f" font-size="10" fill="var(--dim)" text-anchor="middle">%d%%</text>' % (cx + r * 0.68 * math.cos(m), cy + r * 0.68 * math.sin(m) + 3, round(cnt[k] / tot * 100)))
        a += da
    for j, k in enumerate(CHOICES):
        out.append('<rect x="160" y="%d" width="10" height="10" fill="%s" stroke="var(--dim)" stroke-width="0.5"/><text x="176" y="%d" font-size="11" fill="var(--dim)">%s</text>' % (TOP + 30 + j * 20, fills[k], TOP + 39 + j * 20, k))
    return "".join(out)


# ==== the controls: the surveyed apps' own charts ===============================================================================
CONTROLS = {
    "count": [("chronicle", "Chronicle's tracker chart: mode chips, Day/Week/Month/Quarter, a 'Daily average' card of bars with no axis, a stub for a day with no entry"),
              ("trackandgraph", "Track & Graph's line graph: a dynamic range fit to the data, a line through every entry, a y-axis")],
    "rating": [("chronicle", "Chronicle's 'Daily average' bars for a rating, no axis"),
               ("trackandgraph", "Track & Graph's line graph, a dynamic range")],
    "yesno": [("loop", "Loop's habit page: an overview of score, month and year percentages, and the score line 0-100 %"),
              ("streak", "Streak's statistics: completions, best and current streak, completion rate, and the days as squares")],
    "choice": [("atimelogger", "aTimeLogger's pie: a slice per choice, the percent inside, a legend"),
               ("trackandgraph", "Track & Graph's pie chart with a legend")],
    "add": [("timety", "Timety's 'Productivity synergy': focus minutes and a second count on one shared axis, a legend"),
            ("chronicle", "Chronicle's 'Daily average' bars, no axis, mode and period chips")],
    "level": [("openscale", "openScale's Graph tab: four series smoothed, two y-axes (BMI left, kcal right) with the weight on the kcal scale, a legend"),
              ("openscale_home", "openScale's overview: a smoothed line, a dot per entry, every date labelled")],
}
CTL_COSTS = {   # the three questions, as COSTS (hand-set, read from the survey's notes)
    ("count", "chronicle"): (3, 2, 1), ("count", "trackandgraph"): (1, 1, 0),
    ("rating", "chronicle"): (2, 1, 1), ("rating", "trackandgraph"): (1, 1, 0.5),
    ("yesno", "loop"): (2, 1, 3), ("yesno", "streak"): (2, 0, 1),
    ("choice", "atimelogger"): (0, 3, 3), ("choice", "trackandgraph"): (1, 3, 3),
    ("add", "timety"): (1, 2, 1), ("add", "chronicle"): (3, 2, 1),
    ("level", "openscale"): (2, 2, 3), ("level", "openscale_home"): (1, 0, 3),
}


def chips(words, on):
    return '<div class="gl" style="display:flex;gap:4px;font-size:12px;margin:2px 0">%s</div>' % "".join(
        '<span style="padding:4px 8px;border-radius:12px;%s">%s</span>' % ("background:var(--zone2);font-weight:600" if w == on else "box-shadow:inset 0 0 0 1px var(--dim)", w) for w in words)


def draw_control(kind, app):
    cfg = KINDS[kind]
    vals = cfg["vals"]
    pre = ""
    if app == "chronicle":
        c = Chart(kind, {"form": "stubs", "yaxis": "none", "values": "none"})
        if kind == "rating":
            c.lo = 0
            c.misfit["a quantity implied of a rating"] = 0.5
        c.parts.append('<line x1="0" x2="%d" y1="%.1f" y2="%.1f" stroke="var(--dim)" stroke-width="1"/>' % (W, TOP + H, TOP + H))
        daily_bars(c, vals, True, c.lo)
        for i in range(0, DAYS, 7):
            c.text(c.x(i), TOP + H + 13, "MTWTFSS"[(i + 3) % 7], 11)
        pre = chips(["Trend", "Hour", "Weekday", "Month day"], "Trend") + chips(["Day", "Week", "Month", "Quarter"], "Month") + '<div class="gl" style="font-size:13px;margin-top:4px">Daily average · Zoom</div>'
    elif app == "trackandgraph":
        if kind == "choice":
            c = Chart(kind, {"form": "pie", "yaxis": "none", "values": "none"})
            cnt = {k: sum(1 for x in vals if x == k) for k in CHOICES}
            c.add(pie_svg(cnt, False), math.pi * 55 * 55, 20)
            c.legend, c.series = 1, 4
        else:
            c = Chart(kind, {"form": "line", "yaxis": "grid", "values": "none"})
            have = [x for x in vals if x is not None]
            c.lo, c.hi = min(have), max(have)   # range style "Dynamic"
            if kind == "rating" and (c.lo > 1 or c.hi < 5):
                c.misfit["the scale cut short"] = 1
            step = (c.hi - c.lo) / 4
            c.ticks = tuple(round(c.lo + step * k, 1) for k in range(5))
            c.axis()
            line_through(c, vals)
            if kind in ("count", "rating"):
                c.misfit["a line through whole values"] = 0.5
    elif app == "atimelogger":
        c = Chart(kind, {"form": "pie", "yaxis": "none", "values": "every"})
        cnt = {k: sum(1 for x in vals if x == k) for k in CHOICES}
        c.add(pie_svg(cnt, True), math.pi * 55 * 55, 20)
        c.legend, c.series = 1, 4
    elif app == "timety":
        c = Chart(kind, {"form": "line", "yaxis": "grid", "values": "none"})
        c.lo, c.hi, c.ticks = 0, 60, (0, 20, 40, 60)
        c.axis()
        line_through(c, vals, dots=True)
        sessions = [0 if x == 0 else (1 if x < 30 else 2) for x in vals]
        c.poly([(c.x(i), c.y(s)) for i, s in enumerate(sessions)], 2, "var(--dim)")
        c.series, c.legend = 2, 1
        c.misfit["two units on one axis"] = 1
        c.parts.append('<text x="%d" y="8" font-size="11" fill="var(--dim)">— focus minutes  — sessions</text>' % c.g)
    elif app == "loop":
        c = Chart(kind, {"form": "line", "yaxis": "grid", "values": "none"})
        score, s = [], 0.0
        for d in vals:   # Loop's habit strength: an exponential mean
            s = s * 0.9 + d * 0.1
            score.append(s * 100)
        c.lo, c.hi, c.ticks = 0, 100, (0, 20, 40, 60, 80, 100)
        c.axis()
        c.poly([(c.x(i), c.y(x)) for i, x in enumerate(score)], 2)
        for i in range(0, DAYS, 7):
            c.dot(c.x(i), c.y(score[i]), 3)
        c.misfit["a derived score, not the days"] = 0.5
        c.compare = 3
        pre = '<div class="gl" style="display:flex;gap:10px;font-size:13px"><b>%d%%</b> score <b>+5%%</b> month <b>+12%%</b> year <b>%d</b> total</div>' % (round(score[-1]), sum(vals))
    elif app == "streak":
        c = Chart(kind, {"form": "ticks", "yaxis": "none", "values": "none"})
        cell = 22
        for i, d in enumerate(vals):
            r, col = divmod(i, 10)
            c.rect(col * (cell + 4), TOP + 40 + r * (cell + 4), cell, cell, "var(--ink)" if d else "var(--zone2)", 4)
        c.compare = 3
        pre = '<div class="gl" style="display:flex;gap:6px;font-size:12px"><span><b>18</b> completions</span><span><b>4</b> best streak</span><span><b>2</b> current streak</span><span><b>60%</b> rate</span></div>'
    elif app == "openscale":
        c = Chart(kind, {"form": "smooth", "yaxis": "grid", "values": "none"})
        c.g, c.pw = 34, W - 70
        c.sw = c.pw / DAYS
        c.lo, c.hi, c.ticks = 0, 2000, ()
        c.parts.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="var(--dim)"/>' % (c.g, c.g + c.pw, TOP + H, TOP + H))
        for k, t in enumerate(("25.55", "25.65", "25.75")):
            c.text(c.g - 3, TOP + H - k * 50 + 4, t, 9, "end")
        for k, t in enumerate(("0", "1000", "2000")):
            c.text(c.g + c.pw + 3, TOP + H - k * 60 + 4, t, 9, "start")
        line_through(c, vals, smooth=True)
        bmi = [None if x is None else 25.55 + (x - 72) * 0.1 for x in vals]
        c.poly([(c.x(i), TOP + H - (b - 25.55) / 0.3 * 150) for i, b in enumerate(bmi) if b is not None], 2, "var(--dim)")
        c.poly([(c.x(i), TOP + 30 + (i % 5) * 3) for i in range(DAYS)], 1.5, "var(--dim)", "2 2")
        c.poly([(c.x(i), TOP + 70 - (i % 3) * 4) for i in range(DAYS)], 1.5, "var(--dim)", "6 2")
        c.series, c.legend = 4, 1
        c.misfit["two y-axes"] = 1
        c.misfit["the goal not drawn"] = 1
        c.parts.append('<text x="%d" y="8" font-size="10" fill="var(--dim)">— weight — BMI ┄ fat ╌ kcal</text>' % c.g)
        for i, t in X_LABELS:
            c.text(c.x(i), TOP + H + 13, t, 10)
    else:   # openscale_home
        c = Chart(kind, {"form": "smooth", "yaxis": "none", "values": "every", "range": "fit"})
        c.parts.append('<line x1="0" x2="%d" y1="%.1f" y2="%.1f" stroke="var(--dim)"/>' % (W, TOP + H, TOP + H))
        pts = line_through(c, vals, dots=True, smooth=True)
        c.misfit["the goal not drawn"] = 1
        for i, x in enumerate(vals):
            if x is not None:
                c.text(c.x(i), TOP + H + 13, "%02d/%02d" % ((17 + i - 1) % 30 + 1 if i < 14 else i - 13, 9 if i < 14 else 10), 9)
        c.values(pts, "every")
    m = finish(c)
    m["html"] = pre + m["html"]
    m["control"] = True
    return m


def finish(c):
    jit = [abs(c.ys[i + 1] - c.ys[i]) for i in range(len(c.ys) - 1)]
    jit.sort()
    noise = jit[len(jit) // 2] if jit else 0
    if c.k in ("count", "rating"):
        step = H / ((c.hi - c.lo) or 1) * c.cfg["step"] if c.v.get("form") not in ("dist", "weeks") else H / ((c.hi - c.lo) or 1) * (7 if c.v.get("form") == "weeks" else 1)
    elif c.k == "add":
        step = H / ((c.hi - c.lo) or 1) * (5 if c.v.get("form") != "cumul" and c.v.get("form") != "weeks" else 30)
    elif c.k == "level":
        step = (50 if c.v.get("form") == "spark" else H) / ((c.hi - c.lo) or 1) * c.cfg["step"]
    else:
        step = c.sw   # a day's cell
    # ink over a fixed 130 dp plot, not the chart's own area (found 2026-10-17: a taller chart with the same marks read calmer)
    return {"html": '<div class="gk">%s</div>' % c.svg(), "ink": round(c.ink / (W * 130), 4), "min_mark": round(min(c.marks), 2) if c.marks else 0,
            "step_px": round(step, 2), "noise_px": round(noise, 2), "misfit": dict(c.misfit), "series": c.series, "legend": c.legend, "compare": c.compare}


# ==== measuring and scoring =====================================================================================================
GK_JS = r"""(function(){var g=document.querySelector('[data-sec=graph]');var gb=g.getBoundingClientRect();
var ts=[].slice.call(g.querySelectorAll('text,.gl span,.gl b,.gl'));ts=ts.filter(function(t){return !(t.classList&&t.classList.contains('gl')&&t.children.length)});
var o={min_font:99,overlaps:0,cut:0,numbers:0,elements:g.querySelectorAll('svg *').length};
var bs=ts.map(function(t){return t.getBoundingClientRect()});
ts.forEach(function(t,i){var f=parseFloat(getComputedStyle(t).fontSize);if(f<o.min_font)o.min_font=f;
 if(!(t.parentElement&&t.parentElement.closest('.gl')&&t.parentElement!==t))o.numbers+=(t.textContent.match(/\d+([.,]\d+)?/g)||[]).length;
 var b=bs[i];if(b.left<gb.left-1||b.right>gb.right+1)o.cut++});
for(var i=0;i<bs.length;i++)for(var j=i+1;j<bs.length;j++){var a=bs[i],b=bs[j];
 if(ts[i].contains(ts[j])||ts[j].contains(ts[i]))continue;
 if(a.width&&b.width&&a.left<b.right-1&&b.left<a.right-1&&a.top<b.bottom-1&&b.top<a.bottom-1)o.overlaps++}
return o})()"""


def shared(kind, form):
    return sum(1 for k, fs in FORMS.items() if k != kind and form in fs)


def answer_costs(kind, v, m):
    """The three questions' costs for an option or a control, and the forms it shares with the other kinds."""
    if v.get("control"):
        costs = CTL_COSTS[(kind, v["control_app"])]
        sh = 0
    else:
        f = v["form"]
        costs = list(COSTS[kind][f])
        show, ya = v["values"], v["yaxis"]
        if kind == "level":   # now: printed, read off an axis, or not at all
            costs[0] = 0 if (show in ("last", "every") or f == "spark") else ({"grid": 1, "ends": 2, "none": 3}[ya] if f in DAILY else max(2, {"grid": 1, "ends": 2, "none": 3}[ya]))
        if kind == "add" and f == "weeks" and show != "none":
            costs[1] = 0   # this week's total printed
        if kind in ("count", "add") and f in DAILY and show == "none" and ya == "none" and f != "dots":
            costs[1] = max(costs[1], 2)   # a usual day / a week's sum with nothing to read amounts from
        if kind == "level" and "goal outside the range" in m["misfit"]:
            costs[2] = 3
        if kind == "yesno" and show != "none" and f in ("ticks", "weeks", "cumul"):
            costs[1] = min(costs[1], 0 if f != "weeks" else 2)
        # an amount asked of a mark with neither an axis nor a printed value: only guessed (found 2026-10-16: the bare weekly
        # bars ranked first for "this week's total")
        read = 0 if show != "none" else {"grid": 1, "ends": 1, "none": 2}[ya]
        if kind == "add" and f == "weeks":
            costs[1] = read
        if kind == "yesno" and f == "weeks":
            costs[0] = read
        if kind == "yesno" and f == "cumul":
            costs[1] = read
        if kind == "rating" and f != "dist" and show == "none" and ya == "none":
            costs[0] = max(costs[0], 2)   # a usual rating from unlabelled heights
        if kind == "choice" and f in ("hbars", "pie") and show != "none":
            costs[0] = 0
        sh = shared(kind, f)
    return costs, sh


def make_part(ns, kind):
    T, kit, ipdoc = ns["T"], ns["kit"], ns["ipdoc"]

    def page(v):
        m = draw(kind, v)
        body = '<div class="zone" style="padding-bottom:8px"><div class="iph">Last 30 days</div><div data-sec="graph">%s</div></div>' % m["html"]
        return ipdoc(kit.phone(kit.header(KINDS[kind]["name"], (("⚙", "Settings"),), ("‹", "Back")), body, kit.bar("Hub"))), m

    def score(v):
        d, m = page(v)
        key = "gk-%s-%s" % (kind, "-".join(str(x) for x in v.values()))
        b = T.probe(d, key, GK_JS)
        costs, sh = answer_costs(kind, v, m)
        fit = sum(m["misfit"].values())
        enc = CTL_ENCODING.get((kind, v.get("control_app")), ENCODING[v["control_app"] if v.get("control") else v["form"]])
        load = sum(costs) + b["numbers"] / 10 + (m["series"] - 1) * 0.5 + m["legend"]
        return {"fit": fit, "misfit": ", ".join(sorted(k for k, x in m["misfit"].items() if x)) or "-", "min_font": b["min_font"], "overlaps": b["overlaps"],
                "cut": b["cut"], "min_mark": m["min_mark"], "step_px": m["step_px"], "encoding": enc,
                "mark_seen": min(m["min_mark"], MARK_ENOUGH), "step_seen": min(m["step_px"], STEP_ENOUGH), "noise_seen": max(m["noise_px"], NOISE_FLAT), "ink": m["ink"], "noise_px": m["noise_px"], "compare": m["compare"],
                "costs": list(costs), "numbers": b["numbers"], "load": round(load, 2), "shared": sh, "small": []}

    part = "gk_" + kind
    space = {"form": FORMS[kind], "yaxis": ["grid", "ends", "none"], "values": ["none", "last", "every"]}
    if kind == "level":
        space["range"] = ["fit", "plausible", "zero"]
    if kind in ("count", "add"):
        space["range"] = ["zero", "fit"]
    T.SPACES[part] = space
    T.SCORERS[part] = score
    T.VALID[part] = valid(kind)
    T.CONTROLS[part] = [({k: app for k in space} | {"control": True, "control_app": app}, why) for app, why in CONTROLS[kind]]
    T.TITLES[part] = "T3b.7a Graphs for %s: %s (%s)" % ({"count": "counts", "rating": "ratings", "yesno": "yes/no", "choice": "choices", "add": "amounts that add up",
                                                         "level": "amounts that do not add up"}[kind], KINDS[kind]["name"], "; ".join(QUESTIONS[kind]))
    T.DRAW[part] = lambda v: [page(v)[0]]
    T.POOL[part] = lambda ok: [r for r in ok if r.get("front")] + [min((r for r in ok if not r["v"].get("control") and r["v"]["form"] == f), key=lambda r: r["total"])
                                                                   for f in FORMS[kind] if not any(r.get("front") and r["v"].get("form") == f for r in ok)]   # every form drawn once
    T.DRAW_MAX[part] = 18
    T.AXES[part] = {"Fit": ("fit",), "Readability": ("-min_font", "overlaps", "cut", "-mark_seen", "-step_seen", "encoding"), "Calm": ("ink", "noise_seen", "compare"),
                    "Mental load": ("load",), "Consistency": ("-shared",)}
    T.WEIGHTS[part] = {"Consistency": 0.25}
    T.REFS_INFO.add(part)
    for k, tol in (("_ink", 0.01), ("_noise_seen", 1.0), ("_step_seen", 0.5), ("_load", 0.1), ("_mark_seen", 0.5)):
        T.v2.TOL.setdefault(k, tol)


# ==== T3b.7b: the graphs scored inside the item's page (owner, 2026-10-16) =========================================================
"""
  "To assess density and legibility, I think graphs should be scored inside their context/page" (owner). Each option is the
  item's page: the now line and its control, the graph under its period control (7 d / 30 d / 1 y chips, or ‹ October ›),
  and the history under day headers, in both of T3b.7's orders (now, graph, history / now, history, graph), with the plot
  80, 130 or 180 px tall. Axes: T3b.7a's four and consistency (0.25), and T3b.7's density (history rows seen, text cut),
  glance (now, a drawn graph and a history row above the fold) and taps (the graph, a year, editing an entry, the settings).
"""
PAGES = {
    "count": dict(now=("5 glasses today", "last 11:40"), ctl="+ 1 glass", hist=[("Today 11:40", "+ 1 glass"), ("Today 09:15", "+ 2 glasses"), ("Yesterday 20:10", "+ 1 glass"), ("Yesterday 16:05", "+ 2 glasses")]),
    "rating": dict(now=("4 today", "13:10"), ctl="Rate", hist=[("Today 13:10", "4"), ("Yesterday 21:00", "5"), ("Wed 20:30", "4"), ("Tue 19:45", "2")]),
    "yesno": dict(now=("Done today", "07:40"), ctl="✓", hist=[("Today 07:40", "done"), ("Yesterday 18:10", "done"), ("Tue 07:30", "done"), ("Mon 08:00", "done")]),
    "choice": dict(now=("Not logged today", "yesterday packed"), ctl="Log", hist=[("Yesterday 13:00", "packed"), ("Wed 12:40", "packed"), ("Tue 13:10", "home"), ("Mon 12:30", "out")]),
    "add": dict(now=("20 min today", "last 13:40"), ctl="▶", hist=[("Today 13:20–13:40", "20 min"), ("Yesterday 21:00–21:30", "30 min"), ("Yesterday +15 min", "15 min"), ("Mon 20:40–21:15", "35 min")]),
    "level": dict(now=("72.4 kg", "today 07:30 · goal 70 kg"), ctl="Log", hist=[("Today 07:30", "72.4 kg"), ("Yesterday 07:25", "72.1 kg"), ("Mon 07:40", "72.3 kg"), ("Sun 08:10", "72.0 kg")]),
}
CTX = {"order": ["ngh", "nhg"], "period": ["chips", "swipe"], "height": [80, 130, 180]}
# a real history runs long: 12 rows over six days, so the fold decides what is read (found 2026-10-16: with 4 rows every page
# fitted, both orders tied and density could not tell the heights apart)
MORE = {"count": [("Wed 18:30", "+ 1 glass"), ("Wed 12:10", "+ 2 glasses"), ("Tue 19:00", "+ 1 glass"), ("Tue 10:45", "+ 2 glasses"), ("Mon 17:20", "+ 1 glass"), ("Mon 08:30", "+ 1 glass"), ("Sun 20:00", "+ 2 glasses"), ("Sun 11:15", "+ 1 glass")],
        "rating": [("Mon 21:10", "3"), ("Sun 20:40", "4"), ("Sat 19:30", "4"), ("Fri 21:00", "3"), ("Thu 20:15", "5"), ("Wed 19:50", "2"), ("Tue 21:20", "3"), ("Mon 20:05", "4")],
        "yesno": [("Sun 09:10", "done"), ("Sat 17:40", "done"), ("Fri 07:35", "done"), ("Wed 18:00", "done"), ("Tue 07:45", "done"), ("Mon 08:10", "done"), ("Sun 10:00", "done"), ("Sat 16:30", "done")],
        "choice": [("Sun 13:30", "home"), ("Sat 12:50", "out"), ("Fri 13:05", "packed"), ("Thu 12:45", "packed"), ("Wed 13:15", "home"), ("Tue 12:20", "skipped"), ("Mon 13:00", "home"), ("Sun 12:40", "out")],
        "add": [("Mon 13:00–13:25", "25 min"), ("Sun 21:10–21:55", "45 min"), ("Sat 20:30–21:00", "30 min"), ("Fri 21:15–21:35", "20 min"), ("Thu 22:00–22:35", "35 min"), ("Wed 21:00–21:40", "40 min"), ("Tue 20:50–21:15", "25 min"), ("Mon 21:30–22:00", "30 min")],
        "level": [("Sat 07:50", "72.2 kg"), ("Thu 07:35", "72.5 kg"), ("Wed 07:45", "72.3 kg"), ("Mon 07:30", "72.4 kg"), ("Sat 08:05", "72.6 kg"), ("Fri 07:40", "72.5 kg"), ("Wed 07:30", "72.8 kg"), ("Tue 07:55", "72.9 kg")]}
for _k, _rows in MORE.items():
    PAGES[_k]["hist"] = PAGES[_k]["hist"] + _rows


def page_html(kind, v, kit):
    """The item's page around one graph (T3b.7's frame), and the chart's own measures."""
    global H
    with LOCK:
        old = H
        H = v.get("height", 130) if not v.get("control") else 130
        try:
            m = draw(kind, v)
        finally:
            H = old
    pg = PAGES[kind]
    e = kit.e
    now = '<div class="ipn" data-sec="now"><span class="v"><b>%s</b><s>%s</s></span><span class="c" data-tap="Now control">%s</span></div>' % (e(pg["now"][0]), e(pg["now"][1]), e(pg["ctl"]))
    if v.get("period", "chips") == "chips" or v.get("control"):
        per = '<div class="ipr"><span data-tap="Range 7d">7 d</span><span class="on" data-tap="Range 30d">30 d</span><span data-tap="Range 1y">1 y</span></div>'
    else:
        per = '<div class="ipr"><span data-tap="Range prev">‹</span><span class="mo" data-tap="Range month">October</span><span data-tap="Range next">›</span></div>'
    graph = '<div data-sec="graph">%s%s</div>' % (per, m["html"])
    days = []   # a header per run of one day, so last week's Monday is not merged into this week's
    for when, what in pg["hist"]:
        d, t = when.split(" ", 1)
        if not days or days[-1][0] != d:
            days.append((d, []))
        days[-1][1].append((t, what))
    rows = "".join('<div class="iph">%s</div>' % d + "".join('<div class="ipl" data-tap="History row"><span class="t">%s</span>%s</div>' % (e(t), e(w)) for t, w in r) for d, r in days)
    hist = '<div data-sec="hist"><div class="iph">History</div>%s</div>' % rows
    body = now + (graph + hist if (v.get("control") or v.get("order", "ngh") == "ngh") else hist + graph)
    html = kit.phone(kit.header(KINDS[kind]["name"], (("⚙", "Settings"),), ("‹", "Back")), '<div class="zone" style="padding-bottom:8px">%s</div>' % body, kit.bar("Hub"))
    return html, m


def make_page_part(ns, kind):
    T, kit, ipdoc, IP_JS = ns["T"], ns["kit"], ns["ipdoc"], ns["IP_JS"]
    js = "(function(){var a=%s;var b=%s;a.gcut=b.cut;delete b.cut;for(var k in b)a[k]=b[k];return a})()" % (IP_JS, GK_JS)

    def page(v):
        html, m = page_html(kind, v, kit)
        return ipdoc(html), m

    def score(v):
        d, m = page(v)
        b = T.probe(d, "gp-%s-%s" % (kind, "-".join(str(x) for x in v.values())), js)
        costs, sh = answer_costs(kind, v, m)
        fold = b["fold"]
        glance = (b["now_bottom"] <= fold) + (1 if b["has_graph"] and b["graph_bottom"] <= fold else 0) + (b["row_bottom"] <= fold)
        year = 1 if (v.get("control") or v["period"] == "chips") else 2
        taps = (0 if b["graph_bottom"] <= fold else 1) + year + 1 + (0 if b["row_bottom"] <= fold else 1) + 1
        enc = CTL_ENCODING.get((kind, v.get("control_app")), ENCODING[v["control_app"] if v.get("control") else v["form"]])
        load = sum(costs) + b["numbers"] / 10 + (m["series"] - 1) * 0.5 + m["legend"]
        return {"fit": sum(m["misfit"].values()), "misfit": ", ".join(sorted(k for k, x in m["misfit"].items() if x)) or "-",
                "min_font": b["min_font"], "overlaps": b["overlaps"], "gcut": b["gcut"], "encoding": enc, "min_mark": m["min_mark"], "step_px": m["step_px"],
                "mark_seen": min(m["min_mark"], MARK_ENOUGH), "step_seen": min(m["step_px"], STEP_ENOUGH), "noise_seen": max(m["noise_px"], NOISE_FLAT),
                "ink": m["ink"], "noise_px": m["noise_px"], "compare": m["compare"], "costs": list(costs), "load": round(load, 2), "shared": sh,
                "rows_seen": b["rows_seen"], "cut": b["cut"], "glance": glance, "taps": taps, "small": []}

    part = "gp_" + kind
    space = dict(T.SPACES["gk_" + kind]) | CTX
    T.SPACES[part] = space
    T.SCORERS[part] = score
    T.VALID[part] = valid(kind)
    T.CONTROLS[part] = [({k: app for k in space} | {"control": True, "control_app": app}, why + "; in the same page") for app, why in CONTROLS[kind]]
    T.TITLES[part] = T.TITLES["gk_" + kind].replace("T3b.7a Graphs for", "T3b.7b Graphs in the page for")
    T.DRAW[part] = lambda v: [page(v)[0]]
    T.POOL[part] = lambda ok: [r for r in ok if r.get("front")] + [min((r for r in ok if not r["v"].get("control") and r["v"]["form"] == f), key=lambda r: r["total"])
                                                                   for f in FORMS[kind] if not any(r.get("front") and r["v"].get("form") == f for r in ok)]
    T.DRAW_MAX[part] = 18
    T.AXES[part] = {"Fit": ("fit",), "Readability": ("-min_font", "overlaps", "gcut", "-mark_seen", "-step_seen", "encoding"), "Calm": ("ink", "noise_seen", "compare"),
                    "Mental load": ("load",), "Density": ("-rows_seen", "cut"), "Glance": ("-glance",), "Taps": ("taps",), "Consistency": ("-shared",)}
    T.WEIGHTS[part] = {"Consistency": 0.25}
    T.REFS_INFO.add(part)
    T.SUPERSEDED["gk_" + kind] = "scored inside the item's page (owner, 2026-10-16: density and legibility need the context): T3b.7b replaced it"


# ==== T3b.7c: the item's page with its new contents (owner, 2026-10-17) ===========================================================
"""
  The owner's picks per kind (T3b.7b), every past log folded under one line, and on the page: the log control (Paced beside
  it on an activity), Undo of the last log, adding a past entry, Pin to Today (one pin), an optional goal with its reminder,
  a note and labels, a statistics line scored against the graph conveying the same, and the settings behind ⚙ as a bottom
  sheet (habits built on it, labels, Delete, a counter goal's reset). Measured in dp (the mock is 360 dp wide; its CSS px
  are dp).
  Dimensions: the plot's height 80 / 100 / 130 / 180 dp; the statistics as a line, in the graph, or not shown; adding a past
  entry beside the log control, on the folded history line, or by a long press; the pin in the header or on the goal line;
  the note and labels under the name or at the bottom.
  The statistics (owner, the proposal): counts usual a day and this month's total; ratings usual; yes/no days this month
  and the longest gap; choices the most often; minutes this month's total and usual a day; weight the month's change and
  the lowest. Their costs when not shown are HAND-SET (STAT_COSTS), as the graph questions'.
"""
IP2_PICK = {"count": dict(form="dots", yaxis="none", values="none", range="zero"), "rating": dict(form="strip", yaxis="none", values="last"),
            "yesno": dict(form="ticks", yaxis="none", values="last"), "choice": dict(form="strip", yaxis="none", values="none"),
            "add": dict(form="cumul", yaxis="none", values="none", range="zero"), "level": dict(form="dots", yaxis="none", values="last", range="plausible")}
IP2_SPACE = {"height": [80, 100, 130, 180], "stats": ["line", "graph", "none"], "past": ["beside", "histline", "longpress"],
             "pin": ["header", "goal"], "notes": ["top", "bottom"]}
IP2_LABELS = {"count": "health", "rating": "wellbeing", "yesno": "health", "choice": "food", "add": "leisure", "level": "health"}
IP2_GOAL = {"count": "5 of 8 glasses today · reminder 20:00", "add": "20 of 30 min today · reminder 21:00", "level": "goal 70 kg · reminder Mon 07:30"}
STAT_COSTS = {"count": (1, 2), "rating": (1,), "yesno": (0, 1), "choice": (2,), "add": (0, 1), "level": (1, 1)}   # HAND-SET: each statistic read off the picked graph alone


def ip2_stats(kind):
    vals = [x for x in KINDS[kind]["vals"] if x is not None]
    if kind == "count":
        return ["usual %d a day" % round(sum(vals) / len(vals)), "%d this month" % sum(vals)]
    if kind == "rating":
        return ["usual %.1f" % (sum(vals) / len(vals))]
    if kind == "yesno":
        gap, run = 0, 0
        for d in WALK:
            run = 0 if d else run + 1
            gap = max(gap, run)
        return ["%d days this month" % sum(WALK), "longest gap %d days" % gap]
    if kind == "choice":
        top = max(CHOICES, key=lambda k: sum(1 for x in LUNCH if x == k))
        return ["mostly %s" % top]
    if kind == "add":
        return ["%d min this month" % sum(vals), "usual %d min" % round(sum(vals) / len(vals))]
    return ["%+.1f kg this month" % (vals[-1] - vals[0]), "lowest %.1f" % min(vals)]


def ip2_graph_stats(kind, html):
    """The same statistics carried by the graph: a labelled usual line, the total or the change written on the chart."""
    st = ip2_stats(kind)
    return '<div class="gl" style="display:flex;justify-content:space-between;font-size:12px;color:var(--dim);margin:-2px 0 2px">%s</div>%s' % (
        "".join("<span>%s</span>" % s for s in st), html)


def ip2_page(kind, v, kit):
    global H
    e = kit.e
    pg = PAGES[kind]
    with LOCK:
        old = H
        H = 130 if v.get("control") else v["height"]
        try:
            m = draw(kind, {"control": True, "control_app": CONTROLS[kind][0][0]} if v.get("control") else dict(IP2_PICK[kind]))
        finally:
            H = old
    if v.get("control"):   # a Chronicle-like page: Start / Log session, chips, the app's chart, tiles, Goals, recent entries unfolded
        st = ip2_stats(kind)
        rows = "".join('<div class="ipl" data-tap="History row"><span class="t">%s</span>%s</div>' % (e(a), e(b)) for a, b in pg["hist"][:4])
        body = ('<div data-sec="now"><div class="ipr"><span class="on" data-tap="Now control" style="flex:1">%s</span><span data-tap="Past entry" style="flex:1">Log session</span></div></div>' % e(pg["ctl"]) +
                '<div data-sec="graph"><div class="ipr"><span>7 d</span><span class="on">30 d</span><span>90 d</span><span data-tap="Range 1y">1 y</span></div>%s</div>' % m["html"] +
                '<div data-sec="stats" class="ipt">%s</div>' % "".join("<div><b>%s</b><s>%s</s></div>" % tuple((s.split(" ", 1) + [""])[:2]) for s in st) +
                ('<div data-sec="goal"><div class="iph">Goals</div><div class="ipl" data-tap="Pin"><span class="t">%s</span></div></div>' % e(IP2_GOAL[kind]) if kind in IP2_GOAL else "") +
                '<div data-sec="hist"><div class="iph">Recent sessions</div>%s</div>' % rows)
        html = kit.phone(kit.header(KINDS[kind]["name"], (("⋮", "Settings"),), ("‹", "Back")), '<div class="zone" style="padding-bottom:8px">%s</div>' % body, kit.bar("Hub"))
        return html, m
    head_btns = ((("\U0001f4cc", "Pin"),) if v["pin"] == "header" else ()) + (("⚙", "Settings"),)
    notes = ('<div data-sec="notes"><div class="ipr"><span data-tap="Labels">%s</span><span data-tap="Labels add">+ label</span></div>'
             '<div class="ipl" data-tap="Note"><span class="t" style="color:var(--dim)">Add a note</span></div></div>') % IP2_LABELS[kind]
    ctl = '<span class="c" data-tap="Now control">%s</span>' % e(pg["ctl"])
    if kind == "add":
        ctl += '<span class="c" data-tap="Paced" style="background:var(--zone2);color:var(--ink)">⏱</span>'
    if v["past"] == "beside":
        ctl += '<span class="c" data-tap="Past entry" style="background:none;box-shadow:inset 0 0 0 1px var(--dim);color:var(--ink)">Earlier…</span>'
    now = '<div class="ipn" data-sec="now"><span class="v"><b>%s</b><s>%s</s></span>%s</div>' % (e(pg["now"][0]), e(pg["now"][1]), ctl)
    goal = ""
    if kind in IP2_GOAL:
        goal = '<div data-sec="goal" class="ipl"><span class="t" data-tap="Goal">%s</span>%s</div>' % (e(IP2_GOAL[kind]), '<span data-tap="Pin" style="min-width:48px;min-height:48px;display:grid;place-items:center">\U0001f4cc</span>' if v["pin"] == "goal" else "")
    else:
        goal = '<div data-sec="goal" class="ipl"><span class="t" data-tap="Goal" style="color:var(--dim)">Set a goal</span>%s</div>' % ('<span data-tap="Pin" style="min-width:48px;min-height:48px;display:grid;place-items:center">\U0001f4cc</span>' if v["pin"] == "goal" else "")
    stats = '<div data-sec="stats" style="font-size:14px;margin:4px 0;display:flex;gap:14px">%s</div>' % "".join("<span>%s</span>" % s for s in ip2_stats(kind)) if v["stats"] == "line" else ""
    chart = ip2_graph_stats(kind, m["html"]) if v["stats"] == "graph" else m["html"]
    graph = '<div data-sec="graph"><div class="ipr"><span data-tap="Range 7d">7 d</span><span class="on" data-tap="Range 30d">30 d</span><span data-tap="Range 1y">1 y</span></div>%s</div>' % chart
    hist = '<div data-sec="hist" class="ipl"><span class="t" data-tap="History">History · %d entries ›</span>%s</div>' % (
        len(pg["hist"]), '<span data-tap="Past entry" style="min-height:48px;display:grid;place-items:center;padding:0 8px">+ Add past</span>' if v["past"] == "histline" else "")
    body = (notes if v["notes"] == "top" else "") + now + goal + stats + graph + hist + (notes if v["notes"] == "bottom" else "")
    html = kit.phone(kit.header(KINDS[kind]["name"], head_btns, ("‹", "Back")), '<div class="zone" style="padding-bottom:8px">%s</div>' % body, kit.bar("Hub"))
    return html, m


IP2_JS = r"""(function(){var bar=document.querySelector('.bar').getBoundingClientRect().top,top=document.querySelector('.body').getBoundingClientRect().top;
var o={fold:Math.round(bar-top),seen:{},cut:0,clutter:0,numbers:0,taps:{}};
o.unseen=0;['now','goal','stats','graph','hist','notes'].forEach(function(k){var s=document.querySelector('[data-sec='+k+']');if(!s)return;var b=s.getBoundingClientRect();o.seen[k]=b.bottom<=bar?1:0;if(b.bottom>bar)o.unseen++});
document.querySelectorAll('.ipl,.ipn,.ipt div,.ipr span,[data-sec=stats]').forEach(function(x){if(x.scrollWidth>x.clientWidth+1)o.cut++});
document.querySelectorAll('[data-tap]').forEach(function(x){var b=x.getBoundingClientRect();o.taps[x.getAttribute('data-tap')]=b.bottom<=bar&&b.top>=0?1:0;if(b.bottom<=bar&&b.top>=0)o.clutter++});
var txt='';var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);while(w.nextNode()){var n=w.currentNode;if(!n.textContent.trim()||n.parentElement.closest('.bar,script,style'))continue;var p=n.parentElement.getBoundingClientRect();if(p.bottom<=bar&&p.top>=0){o.clutter++;if(!n.parentElement.closest('svg')&&p.top>=top)txt+=' '+n.textContent}}
o.numbers=(txt.match(/\d+([.,]\d+)?/g)||[]).length;return o})()"""
IP2_REACH = ("Now control", "Past entry", "Pin", "Note", "Labels", "History", "Range 1y", "Settings", "Goal")


def make_ip2_part(ns, kind):
    T, kit, ipdoc = ns["T"], ns["kit"], ns["ipdoc"]
    js = "(function(){var a=%s;var b=%s;a.gcut=b.cut;a.min_font=b.min_font;a.overlaps=b.overlaps;return a})()" % (IP2_JS, GK_JS)

    def page(v):
        html, m = ip2_page(kind, v, kit)
        return ipdoc(html), m

    def score(v):
        d, m = page(v)
        b = T.probe(d, "ip2-%s-%s" % (kind, "-".join(str(x) for x in v.values())), js)
        ctl = v.get("control")
        costs, _ = answer_costs(kind, {"control": True, "control_app": CONTROLS[kind][0][0]} if ctl else dict(IP2_PICK[kind]), m)
        stat = 0 if (ctl or v["stats"] != "none") else sum(STAT_COSTS[kind])
        # taps to reach each element from the page as it opens: one, and a scroll when it is below the fold; a long press is one,
        # and hidden; an entry's edit is the history line, then the entry (and Undo is one tap on its snackbar, the same for all)
        taps = sum((1 + (0 if b["taps"][t] else 1)) if t in b["taps"] else 3 for t in IP2_REACH) + (1 if (not ctl and v["past"] == "longpress") else 0) + 2   # a missing element: 3
        hidden = 1 if (not ctl and v["past"] == "longpress") else 0
        seen = b["seen"]
        glance = seen.get("now", 0) + seen.get("goal", 0) + seen.get("graph", 0) + seen.get("hist", 0) + (seen.get("stats", 0) if not ctl and v["stats"] == "line" else (1 if not ctl and v["stats"] == "graph" and seen.get("graph") else 0))
        load = sum(costs) + stat + b["numbers"] / 10 + (m["series"] - 1) * 0.5 + m["legend"]
        consistency = 0 if ctl else (1 if v["pin"] == "goal" else 0)   # T3b.5b pins goals: the pin on the goal it pins
        return {"fit": sum(m["misfit"].values()) + (1 if ctl else 0) * 0, "min_font": b["min_font"], "overlaps": b["overlaps"], "gcut": b["gcut"],
                "mark_seen": min(m["min_mark"], MARK_ENOUGH), "step_seen": min(m["step_px"], STEP_ENOUGH), "step_px": m["step_px"],
                "encoding": CTL_ENCODING.get((kind, CONTROLS[kind][0][0]), ENCODING[CONTROLS[kind][0][0]]) if ctl else ENCODING[IP2_PICK[kind]["form"]],
                "ink": m["ink"], "noise_seen": max(m["noise_px"], NOISE_FLAT), "compare": m["compare"], "clutter": b["clutter"],
                "load": round(load, 2), "stat_cost": stat, "numbers": b["numbers"], "unseen": b["unseen"], "cut": b["cut"],
                "glance": glance, "taps": taps, "hidden": hidden, "consistency": consistency, "fold": b["fold"], "small": []}

    part = "ip2_" + kind
    T.SPACES[part] = dict(IP2_SPACE)
    T.SCORERS[part] = score
    T.VALID[part] = lambda v: True
    ctl_app = CONTROLS[kind][0][0]
    T.CONTROLS[part] = [({k: ctl_app for k in IP2_SPACE} | {"control": True, "control_app": ctl_app},
                         "a Chronicle-like page: Start and Log session, range chips, %s's chart, statistics tiles, a Goals section, the recent entries unfolded" % ctl_app)]
    T.TITLES[part] = "T3b.7c The item's page with its new contents: %s (the picked graph; height, statistics, past entry, pin, note and labels)" % KINDS[kind]["name"]
    T.DRAW[part] = lambda v: [page(v)[0]]
    T.POOL[part] = lambda ok: [r for r in ok if r.get("front")]
    T.DRAW_MAX[part] = 16
    T.AXES[part] = {"Fit": ("fit",), "Readability": ("-min_font", "overlaps", "gcut", "-mark_seen", "-step_seen", "encoding"),
                    "Calm": ("ink", "noise_seen", "compare", "clutter"), "Mental load": ("load",), "Density": ("unseen", "cut"),
                    "Glance": ("-glance",), "Taps": ("taps",), "Discoverability": ("hidden",), "Consistency": ("-consistency",)}
    T.WEIGHTS[part] = {"Consistency": 0.25}
    T.REFS_INFO.add(part)


# ==== T3b.7d: the item's page from real apps' structures, with Harmony (owner, 2026-10-17) ========================================
"""
  The owner: every height drawn for every kind (consistency); chips are not used elsewhere; "all large asymmetric empty
  spaces need to be reconsidered as something to avoid, as they break the glance flow of the page"; the page's
  organisation taken from real apps' structures (survey: _screens-sources/t3/goals/structure/notes.md: Daylio, Habitify,
  Waistline, FitoTrack, a budget app; Loop, Chronicle, openScale and drip from the graph survey).
  Templates (owner): cards (Habitify, Daylio: the period as one full-width header, the graph in a card, the statistics as
  paired tiles), grid (FitoTrack: the statistics as a two-column label/value grid above the graph), form (Waistline: the
  period as a labelled full-width row, the statistics folded under the graph), flat (T3b.7c: a statistics line).
  Period (owner): a full-width segmented control (7 d / 30 d / 1 y) or "‹ October ›" as T2's calendar (no swipes,
  decision 17). Every kind's picked graph at 80 / 100 / 130 / 180 dp; the past entry, the pin, the note and labels as
  T3b.7c. Two facts per kind everywhere, so no template shows more than another.
  Harmony (owner: visual balance both ways without sacrificing density, asymmetric empty space, left/right and top/bottom
  balance, spacing rhythm, edge alignment):
    asym      the empty area on one side only of every row of boxes (controls, chips, tiles, a statistics line), dp^2
              over the first screen's area (a row's two margins differing by more than 8 dp);
    balance   the first screen's ink (luma departing from the ground) split left/right and top/bottom, |share - 0.5|,
              from a screenshot through the kept-open browser (~/.claude/tools/headless_browser.py);
    rhythm    the vertical gaps between the page's blocks: distinct values, and those not a multiple of 4 dp;
    edges     distinct left and right edges of the page's blocks.
  Harmony leads (owner): only pages within 5% of the rank-sum range of the best Harmony reach the front (HAND-SET).
  Weights (owner, a 1-4 scale): Taps 2, Consistency 2, the rest 1. Likeness: the edit distance of the page's block
  sequence to the nearest surveyed app's (token map HAND-SET).
"""
import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.expanduser(r"~\.claude\tools"))
IP3_SPACE = {"template": ["cards", "grid", "form", "flat"], "period": ["segmented", "month"], "height": [80, 100, 130, 180],
             "past": ["beside", "histline", "longpress"], "pin": ["header", "goal"], "notes": ["top", "bottom"]}
IP3_CSS = """
.seg{display:flex;border-radius:24px;box-shadow:inset 0 0 0 1px var(--dim);overflow:hidden;margin:4px 0}.seg span{flex:1;min-height:48px;display:grid;place-items:center;font-size:13px}
.seg span.on{background:var(--zone2);font-weight:600}
.card{border-radius:12px;box-shadow:inset 0 0 0 1px var(--zone2);padding:8px 12px}
.ip3t{display:grid;grid-template-columns:1fr 1fr;gap:8px}.ip3t div{border-radius:12px;background:var(--zone2);padding:8px 12px}.ip3t b{display:block;font-size:20px}.ip3t s{text-decoration:none;font-size:12px;color:var(--dim)}
.ip3g{display:grid;grid-template-columns:1fr 1fr;gap:2px 16px;margin:4px 0}.ip3g s{display:block;text-decoration:none;font-size:12px;color:var(--dim)}.ip3g b{display:block;font-size:17px;font-weight:600}
.ip3l{display:flex;justify-content:space-between;font-size:14px;margin:4px 0}.ip3f{font-size:12px;color:var(--dim);margin:6px 0 0}
"""
SURVEY_SEQ = {"habitify": ["period", "card", "tiles", "calendar", "chart", "chart"], "daylio": ["period", "card", "chart", "card"],
              "fitotrack": ["grid", "chart", "grid"], "waistline": ["period", "chart", "folded"], "loop": ["tiles", "chart", "chart", "calendar", "list"],
              "chronicle": ["log", "period", "chart", "tiles", "list"], "openscale": ["chart", "list"]}


def ip3_facts(kind):
    """Two facts per kind, as (value, label)."""
    vals = [x for x in KINDS[kind]["vals"] if x is not None]
    if kind == "count":
        return [("%d" % round(sum(vals) / len(vals)), "usual a day"), ("%d" % sum(vals), "this month")]
    if kind == "rating":
        return [("%.1f" % (sum(vals) / len(vals)), "usual"), ("%d" % sum(1 for x in vals if x <= 2), "low days")]
    if kind == "yesno":
        gap = run = 0
        for d in WALK:
            run = 0 if d else run + 1
            gap = max(gap, run)
        return [("%d" % sum(WALK), "days this month"), ("%d days" % gap, "longest gap")]
    if kind == "choice":
        top = max(CHOICES, key=lambda k: sum(1 for x in LUNCH if x == k))
        return [(top, "most often"), ("%d of %d" % (sum(1 for x in LUNCH if x == top), len(vals)), "days %s" % top)]
    if kind == "add":
        return [("%d min" % sum(vals), "this month"), ("%d min" % round(sum(vals) / len(vals)), "usual a day")]
    return [("%+.1f kg" % (vals[-1] - vals[0]), "this month"), ("%.1f" % min(vals), "lowest")]


def ip3_period(v):
    if v["period"] == "segmented":
        return '<div class="seg" data-row="box" data-sec="period"><span data-tap="Range 7d">7 d</span><span class="on" data-tap="Range 30d">30 d</span><span data-tap="Range 1y">1 y</span></div>'
    return ('<div class="ipr" data-row="box" data-sec="period"><span data-tap="Range prev">‹</span><span class="mo" data-tap="Range month">October 2026</span>'
            '<span data-tap="Range next">›</span></div>')


def ip3_page(kind, v, kit):
    global H
    e = kit.e
    pg = PAGES[kind]
    with LOCK:
        old = H
        H = 130 if v.get("control") else v["height"]
        try:
            m = draw(kind, {"control": True, "control_app": CONTROLS[kind][0][0]} if v.get("control") else dict(IP2_PICK[kind]))
        finally:
            H = old
    if v.get("control"):
        html, _ = ip2_page(kind, v, kit)
        return html, m, ["log", "chips", "chart", "tiles", "goal", "list"]
    facts = ip3_facts(kind)
    head_btns = ((("\U0001f4cc", "Pin"),) if v["pin"] == "header" else ()) + (("⚙", "Settings"),)
    pin = '<span data-tap="Pin" style="min-width:48px;min-height:48px;display:grid;place-items:center">\U0001f4cc</span>' if v["pin"] == "goal" else ""
    # the labels at the left, "+ label" at the right edge: the row was lopsided, 183 dp empty at its right (Harmony, 2026-10-17)
    notes = ('<div data-sec="notes"><div class="ipr" data-row="box" style="justify-content:space-between"><span data-tap="Labels">%s</span><span data-tap="Labels add">+ label</span></div>'
             '<div class="ipl" data-tap="Note"><span class="t" style="color:var(--dim)">Add a note</span></div></div>') % IP2_LABELS[kind]
    ctl = '<span class="c" data-tap="Now control">%s</span>' % e(pg["ctl"])
    if kind == "add":
        ctl += '<span class="c" data-tap="Paced" style="background:var(--zone2);color:var(--ink)">⏱</span>'
    if v["past"] == "beside":
        ctl += '<span class="c" data-tap="Past entry" style="background:none;box-shadow:inset 0 0 0 1px var(--dim);color:var(--ink)">Earlier…</span>'
    now = '<div class="ipn" data-sec="now" data-row="box"><span class="v"><b>%s</b><s>%s</s></span>%s</div>' % (e(pg["now"][0]), e(pg["now"][1]), ctl)
    goal_text = IP2_GOAL.get(kind)
    goal = '<div data-sec="goal" class="ipl"><span class="t" data-tap="Goal"%s>%s</span>%s</div>' % (
        "" if goal_text else ' style="color:var(--dim)"', e(goal_text or "Set a goal"), pin)
    # the line's two ends filled: "+ Add past" or the chevron at the right edge (the lone text left 189 dp empty, 2026-10-17)
    hist = '<div data-sec="hist" class="ipl" data-row="box" style="justify-content:space-between"><span data-tap="History">History · %d entries</span>%s</div>' % (
        len(pg["hist"]), '<span data-tap="Past entry" style="min-height:48px;display:grid;place-items:center;padding:0 8px">+ Add past</span>' if v["past"] == "histline"
        else '<span style="min-width:48px;min-height:48px;display:grid;place-items:center">›</span>')
    t = v["template"]
    if t == "cards":
        stats = '<div data-sec="stats" class="ip3t" data-row="box">%s</div>' % "".join("<div><b>%s</b><s>%s</s></div>" % (e(a), e(b)) for a, b in facts)
        body = now + goal + ip3_period(v) + '<div class="card" data-sec="graph">%s</div>' % m["html"] + stats + '<div class="card">%s</div>' % hist
        seq = ["log", "goal", "period", "card", "chart", "tiles", "list"]
    elif t == "grid":
        stats = '<div data-sec="stats" class="ip3g" data-row="box">%s</div>' % "".join("<div><s>%s</s><b>%s</b></div>" % (e(b), e(a)) for a, b in facts)
        body = now + goal + stats + ip3_period(v) + '<div data-sec="graph">%s</div>' % m["html"] + hist
        seq = ["log", "goal", "grid", "period", "chart", "list"]
    elif t == "form":
        period = '<div class="ip3f">Period</div>' + ip3_period(v)
        stats = '<div data-sec="stats" class="ipl" data-row="box" style="justify-content:space-between"><span data-tap="Stats">Statistics · %d</span><span>›</span></div>' % len(facts)
        body = now + goal + period + '<div data-sec="graph">%s</div>' % m["html"] + stats + hist
        seq = ["log", "goal", "period", "chart", "folded", "list"]
    else:
        stats = '<div data-sec="stats" class="ip3l" data-row="box">%s</div>' % "".join("<span><b>%s</b> %s</span>" % (e(a), e(b)) for a, b in facts)
        body = now + goal + stats + ip3_period(v) + '<div data-sec="graph">%s</div>' % m["html"] + hist
        seq = ["log", "goal", "line", "period", "chart", "list"]
    if v["notes"] == "top":
        body, seq = notes + body, ["notes"] + seq
    else:
        body, seq = body + notes, seq + ["notes"]
    html = kit.phone(kit.header(KINDS[kind]["name"], head_btns, ("‹", "Back")), '<div class="zone" style="padding-bottom:8px">%s</div>' % body, kit.bar("Hub"))
    return html, m, seq


def edit_distance(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, y in enumerate(b, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (x != y))
    return d[len(b)]


def likeness(seq):
    core = [s for s in seq if s not in ("goal", "notes")]   # the item's own extras, absent from every surveyed app
    return round(min(edit_distance(core, s) / max(len(core), len(s)) for s in SURVEY_SEQ.values()), 3)


HARMONY_JS = r"""(function(){var z=document.querySelector('.zone'),zb=z.getBoundingClientRect(),bar=document.querySelector('.bar').getBoundingClientRect().top;
var ph=document.querySelector('.phone').getBoundingClientRect(),hd=document.querySelector('.hdr').getBoundingClientRect();
var o={asym:0,gaps:[],lefts:{},rights:{},phone:[ph.left,ph.top,ph.width,ph.height],content:[hd.bottom-ph.top,bar-ph.top]};
document.querySelectorAll('[data-row=box],.ipr,.ipt,.ipn,.seg').forEach(function(r){var b=r.getBoundingClientRect();if(b.top>=bar||b.height==0)return;
 var L=1e9,R=-1e9;[].slice.call(r.children).forEach(function(c){var cb=c.getBoundingClientRect();if(cb.width==0)return;L=Math.min(L,cb.left);R=Math.max(R,cb.right)});
 if(L>R)return;var el=L-b.left,er=b.right-R,d=Math.abs(el-er);if(d>8)o.asym+=(d-8)*Math.min(b.height,bar-b.top)});
var kids=[].slice.call(z.children).map(function(c){return c.getBoundingClientRect()}).filter(function(b){return b.height>0&&b.top<bar});
kids.sort(function(a,b){return a.top-b.top});
for(var i=1;i<kids.length;i++)o.gaps.push(Math.round(kids[i].top-kids[i-1].bottom));
kids.forEach(function(b){o.lefts[Math.round(b.left/2)*2]=1;o.rights[Math.round(b.right/2)*2]=1});
o.lefts=Object.keys(o.lefts).length;o.rights=Object.keys(o.rights).length;return o})()"""


def ip3_balance(doc_html, key, geom):
    """The first screen's ink split left/right and top/bottom, from a screenshot through the kept-open browser."""
    import headless_browser as hb
    from PIL import Image
    shots = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "_screens-sources", "t3", "harmony-shots")
    _os.makedirs(shots, exist_ok=True)
    png = _os.path.join(shots, key + ".png")
    hb.screenshot(doc_html, png, 660, 1040)   # the probe's viewport, so the phone sits where it was measured
    x, y, w, h = geom["phone"]
    top, bottom = geom["content"]
    im = Image.open(png).convert("L").crop((int(x), int(y + top), int(x + w), int(y + bottom)))
    _os.remove(png)
    px = im.load()
    W_, H_ = im.size
    hist = im.histogram()
    ground = max(range(256), key=lambda i: hist[i])
    left = right = upper = lower = 0.0
    for j in range(0, H_, 2):
        for i in range(0, W_, 2):
            m = abs(px[i, j] - ground) / 255.0
            if m < 0.04:
                continue
            if i < W_ / 2:
                left += m
            else:
                right += m
            if j < H_ / 2:
                upper += m
            else:
                lower += m
    tot = (left + right) or 1
    return abs(left / tot - 0.5), abs(upper / tot - 0.5)


IP3_REACH = ("Now control", "Past entry", "Pin", "Note", "Labels", "History", "Range 1y", "Settings", "Goal")


def make_ip3_part(ns, kind):
    T, kit, ipdoc = ns["T"], ns["kit"], ns["ipdoc"]
    js = "(function(){var a=%s;var b=%s;var c=%s;a.gcut=b.cut;a.min_font=b.min_font;a.overlaps=b.overlaps;a.h=c;return a})()" % (IP2_JS, GK_JS, HARMONY_JS)

    def page(v):
        html, m, seq = ip3_page(kind, v, kit)
        return ipdoc(html).replace("</style>", IP3_CSS + "</style>", 1), m, seq

    def score(v):
        d, m, seq = page(v)
        key = "ip3-%s-%s" % (kind, "-".join(str(x) for x in v.values()))
        b = T.probe(d, key, js)
        ctl = v.get("control")
        hb_, vb_ = ip3_balance(d, key, b["h"])
        costs, _ = answer_costs(kind, {"control": True, "control_app": CONTROLS[kind][0][0]} if ctl else dict(IP2_PICK[kind]), m)
        taps = sum((1 + (0 if b["taps"][t] else 1)) if t in b["taps"] else 3 for t in IP3_REACH) + (1 if (not ctl and v["past"] == "longpress") else 0) + 2
        if not ctl and v["template"] == "form":
            taps += 1 + (0 if b["seen"].get("stats") else 1)   # the folded statistics opened
        year = 1 if (ctl or v["period"] == "segmented") else 2   # a year: one segment, or the month's picker then the year
        taps += year - 1
        seen = b["seen"]
        glance = sum(seen.get(k, 0) for k in ("now", "goal", "graph", "hist")) + (seen.get("stats", 0) if (not ctl and v["template"] != "form") else 0)
        load = sum(costs) + b["numbers"] / 10 + (m["series"] - 1) * 0.5 + m["legend"]
        gaps = b["h"]["gaps"]
        consistency = 0 if ctl else (1 if v["period"] == "month" else 0) + (1 if v["pin"] == "goal" else 0)
        fold_area = 360.0 * max(1, b["h"]["content"][1] - b["h"]["content"][0])
        return {"fit": sum(m["misfit"].values()), "min_font": b["min_font"], "overlaps": b["overlaps"], "gcut": b["gcut"],
                "mark_seen": min(m["min_mark"], MARK_ENOUGH), "step_seen": min(m["step_px"], STEP_ENOUGH), "step_px": m["step_px"],
                "encoding": CTL_ENCODING.get((kind, CONTROLS[kind][0][0]), ENCODING[CONTROLS[kind][0][0]]) if ctl else ENCODING[IP2_PICK[kind]["form"]],
                "ink": m["ink"], "noise_seen": max(m["noise_px"], NOISE_FLAT), "compare": m["compare"], "clutter": b["clutter"],
                "load": round(load, 2), "unseen": b["unseen"], "cut": b["cut"], "glance": glance, "taps": taps,
                "hidden": 1 if (not ctl and v["past"] == "longpress") else 0, "consistency": consistency,
                "asym": round(b["h"]["asym"] / fold_area, 4), "balance_h": round(hb_, 3), "balance_v": round(vb_, 3),
                "rhythm": len(set(gaps)) + sum(1 for g in gaps if g % 4), "edges": b["h"]["lefts"] + b["h"]["rights"] - 2,
                "likeness": likeness(seq), "seq": " ".join(seq), "small": []}

    part = "ip3_" + kind
    T.SPACES[part] = dict(IP3_SPACE)
    T.SCORERS[part] = score
    T.VALID[part] = lambda v: True
    ctl_app = CONTROLS[kind][0][0]
    T.CONTROLS[part] = [({k: ctl_app for k in IP3_SPACE} | {"control": True, "control_app": ctl_app},
                         "a Chronicle-like page: Start and Log session, range chips, %s's chart, statistics tiles, a Goals section, the recent entries unfolded" % ctl_app)]
    T.TITLES[part] = "T3b.7d The item's page from real apps' structures, with Harmony: %s (template, period control, height, past entry, pin, note and labels)" % KINDS[kind]["name"]
    T.DRAW[part] = lambda v: [page(v)[0]]
    T.POOL[part] = lambda ok: ([r for r in ok if r.get("front")] +
                               [min((r for r in ok if not r["v"].get("control") and r["v"][k] == x), key=lambda r: r["total"])
                                for k in ("height", "template", "period") for x in IP3_SPACE[k]])   # every height, template and period drawn (owner)
    T.DRAW_MAX[part] = 24
    T.AXES[part] = {"Harmony": ("asym", "balance_h", "balance_v", "rhythm", "edges"), "Fit": ("fit",),
                    "Readability": ("-min_font", "overlaps", "gcut", "-mark_seen", "-step_seen", "encoding"),
                    "Calm": ("ink", "noise_seen", "compare", "clutter"), "Mental load": ("load",), "Density": ("unseen", "cut"),
                    "Glance": ("-glance",), "Taps": ("taps",), "Discoverability": ("hidden",), "Likeness": ("likeness",), "Consistency": ("-consistency",)}
    T.WEIGHTS[part] = {"Taps": 2, "Consistency": 2}
    n = 1
    for x in IP3_SPACE.values():
        n *= len(x)
    T.LEAD[part] = ("Harmony", round(0.05 * 5 * (n + 1)))   # HAND-SET: within 5% of the Harmony rank-sum range of the best
    T.REFS_INFO.add(part)
    for k, tol in (("_asym", 0.002), ("_balance_h", 0.01), ("_balance_v", 0.01)):
        T.v2.TOL.setdefault(k, tol)


def register(ns):
    for kind in KINDS:
        make_part(ns, kind)
    for kind in KINDS:
        make_page_part(ns, kind)
    for kind in KINDS:
        make_ip2_part(ns, kind)
    for kind in KINDS:
        make_ip3_part(ns, kind)
    T = ns["T"]
    T.SUPERSEDED["ipage"] = "its graphs and order settled in the page (T3b.7b, owner 2026-10-17), its contents re-scored with the history folded (T3b.7c)"
    c = dict(order="ngh", period="chips", yaxis="none")   # the owner's picks (2026-10-17); the weight's height still open
    T.PICKED.update({"gp_add": [dict(c, form="cumul", values="none", range="zero", height=80)], "gp_choice": [dict(c, form="strip", values="none", height=80)],
                     "gp_count": [dict(c, form="dots", values="none", range="zero", height=80)], "gp_rating": [dict(c, form="strip", values="last", height=80)],
                     "gp_yesno": [dict(c, form="ticks", values="last", height=80)],
                     "gp_level": [dict(c, form="dots", values="last", range="plausible", height=180), dict(c, form="dots", values="last", range="plausible", height=80)]})
