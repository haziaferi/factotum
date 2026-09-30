"""Contest 04 (recurrence encoding): for every real rule the owner apps can hold, compute its true
occurrences with a port of that app's verified semantics, convert it into each candidate
encoding, expand the encoding with that encoding's own engine, and compare over a horizon.

    python tools/recurrence_sim.py   # writes decisions/options/04-recurrence.sim.json + a table

Truth generators and encoding engines are separate code, so a conversion that is wrong cannot
agree with itself. Sources:
  tendril  Elastic = start + k*period, anchored (ResolveEntryUseCase.kt:105-121); RRULE parts per
           RecurrenceSpec.kt:33-116
  chronicle RepeatSchedule.kt: EveryInterval grid from dueAt (:82), Weekdays (:44), Monthly
           steps from the previous due (:30, drifts), RandomDays seeded gap in [min, max] (:39-40)
  mnemo    ScheduleCalculator.kt: 5-field numeric cron, dom/dow OR'd when both restricted (:100);
           STOCHASTIC one uniform draw per allowed day inside the window (:153-178)
Month ends follow Tendril's own rule, "anchored to the original schedule" (RecurrenceRule.kt:27):
Jan 31 -> Feb 28 -> Mar 31. Both apps' step-from-previous drift (-> Mar 28) is a defect the
verification found, so the expected series is the anchored one.

Encodings
  rrule          RFC 5545 RRULE only (one rule per item)
  rrule+ext      RRULE plus three typed extensions: RANDOM_DAYS(min,max), RANDOM_WINDOW(mask,start,end),
                 and RULE_SET (a union of RRULEs, for cron's dom-OR-dow)
  cron+ext       Mnemo's cron plus the same two random extensions
  chronicle-enum Chronicle's 7-case RepeatRule
  one-shot       CONTROL: no recurrence at all
"""
import calendar
import datetime as dt
import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START = dt.datetime(2026, 10, 5, 9, 0)          # a Monday
HORIZON = dt.datetime(2027, 1, 5)
DAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


# ---------------------------------------------------------------------------------------------
# RRULE engine (brute force over candidates; RFC 5545 subset incl. BYSETPOS, ordinals, COUNT/UNTIL)
# ---------------------------------------------------------------------------------------------
def parse_rrule(s):
    p = dict(kv.split("=") for kv in s.split(";"))
    out = {"FREQ": p["FREQ"], "INTERVAL": int(p.get("INTERVAL", 1))}
    for k in ("BYMONTH", "BYMONTHDAY", "BYHOUR", "BYMINUTE", "BYSETPOS"):
        if k in p:
            out[k] = [int(x) for x in p[k].split(",")]
    if "BYDAY" in p:
        out["BYDAY"] = [(int(d[:-2]) if d[:-2] else None, DAYS.index(d[-2:])) for d in p["BYDAY"].split(",")]
    if "COUNT" in p:
        out["COUNT"] = int(p["COUNT"])
    if "UNTIL" in p:
        out["UNTIL"] = dt.datetime.strptime(p["UNTIL"], "%Y%m%dT%H%M%S")
    return out


def period_index(r, start, c):
    f = r["FREQ"]
    if f == "MINUTELY":
        return int((c - start).total_seconds() // 60)
    if f == "HOURLY":
        return int((c.replace(minute=0) - start.replace(minute=0)).total_seconds() // 3600)
    if f == "DAILY":
        return (c.date() - start.date()).days
    if f == "WEEKLY":
        return ((c.date() - dt.timedelta(c.weekday())) - (start.date() - dt.timedelta(start.weekday()))).days // 7
    if f == "MONTHLY":
        return (c.year - start.year) * 12 + c.month - start.month
    return c.year - start.year


def nth_weekday_ok(c, n, wd, scope_month):
    if c.weekday() != wd:
        return False
    if n is None:
        return True
    if scope_month:
        days = [d for d in range(1, calendar.monthrange(c.year, c.month)[1] + 1)
                if dt.date(c.year, c.month, d).weekday() == wd]
    else:
        days = [d for d in range(1, 367 if calendar.isleap(c.year) else 366)
                if (dt.date(c.year, 1, 1) + dt.timedelta(d - 1)).weekday() == wd]
        c_ord = (c.date() - dt.date(c.year, 1, 1)).days + 1
        return days[n - 1 if n > 0 else n] == c_ord if len(days) >= abs(n) else False
    return len(days) >= abs(n) and days[n - 1 if n > 0 else n] == c.day


def matches(r, start, c):
    f = r["FREQ"]
    if period_index(r, start, c) % r["INTERVAL"]:
        return False
    if "BYMONTH" in r and c.month not in r["BYMONTH"]:
        return False
    if "BYMONTHDAY" in r:
        last = calendar.monthrange(c.year, c.month)[1]
        if not any(c.day == (d if d > 0 else last + 1 + d) for d in r["BYMONTHDAY"]):
            return False
    if "BYDAY" in r:
        if not any(nth_weekday_ok(c, n, wd, f == "MONTHLY" or "BYMONTH" in r) for n, wd in r["BYDAY"]):
            return False
    # RFC defaults: anything coarser than the frequency and not given by a BY rule comes from DTSTART
    order = ["MINUTELY", "HOURLY", "DAILY", "WEEKLY", "MONTHLY", "YEARLY"]
    lvl = order.index(f)
    if lvl >= 1 and "BYMINUTE" not in r and c.minute != start.minute:
        return False
    if lvl >= 2 and "BYHOUR" not in r and c.hour != start.hour:
        return False
    if "BYHOUR" in r and c.hour not in r["BYHOUR"]:
        return False
    if "BYMINUTE" in r and c.minute not in r["BYMINUTE"]:
        return False
    if f == "WEEKLY" and "BYDAY" not in r and c.weekday() != start.weekday():
        return False
    if f == "MONTHLY" and "BYDAY" not in r and "BYMONTHDAY" not in r and c.day != start.day:
        return False
    if f == "YEARLY" and not ({"BYMONTH", "BYDAY", "BYMONTHDAY"} & set(r)) and \
            (c.month, c.day) != (start.month, start.day):
        return False
    return True


def expand_rrule(s, start, until):
    r = parse_rrule(s)
    fine = r["FREQ"] in ("MINUTELY", "HOURLY") or "BYHOUR" in r or "BYMINUTE" in r
    step = dt.timedelta(minutes=1) if fine else dt.timedelta(days=1)
    c = start if fine else start.replace(hour=start.hour, minute=start.minute)
    hits = []
    while c < until:
        if matches(r, start, c):
            hits.append(c)
        c += step
    if "BYSETPOS" in r:
        groups = {}
        for h in hits:
            groups.setdefault(period_index(r, start, h), []).append(h)
        hits = sorted(g[p - 1 if p > 0 else p] for g in groups.values() for p in r["BYSETPOS"] if len(g) >= abs(p))
        hits = sorted(set(hits))
    if "UNTIL" in r:
        hits = [h for h in hits if h <= r["UNTIL"]]
    if "COUNT" in r:
        hits = hits[:r["COUNT"]]
    return hits


# ---------------------------------------------------------------------------------------------
# Mnemo cron engine (port of ScheduleCalculator: numeric fields, lists, ranges, steps, OR quirk)
# ---------------------------------------------------------------------------------------------
def cron_field(spec, lo, hi):
    vals = set()
    for part in spec.split(","):
        rng, _, stp = part.partition("/")
        a, b = (lo, hi) if rng == "*" else (tuple(int(x) for x in rng.split("-")) if "-" in rng else (int(rng), int(rng) if not stp else hi))
        vals |= set(range(a, b + 1, int(stp) if stp else 1))
    return vals


def expand_cron(expr, start, until):
    mi, hr, dom, mon, dow = expr.split()
    M, H, D, MO = cron_field(mi, 0, 59), cron_field(hr, 0, 23), cron_field(dom, 1, 31), cron_field(mon, 1, 12)
    W = {d % 7 for d in cron_field(dow, 0, 7)}           # 0 and 7 are Sunday
    dom_r, dow_r = dom != "*", dow != "*"
    out, c = [], start
    while c < until:
        cw = (c.weekday() + 1) % 7
        dm, wm = c.day in D, cw in W
        day_ok = (dm or wm) if dom_r and dow_r else (dm and wm)
        if c.minute in M and c.hour in H and c.month in MO and day_ok:
            out.append(c)
        c += dt.timedelta(minutes=1)
    return out


# ---------------------------------------------------------------------------------------------
# Chronicle enum engine (port of RepeatSchedule: steps from the previous due)
# ---------------------------------------------------------------------------------------------
def add_month(d, n=1):
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    return d.replace(year=y, month=m, day=min(d.day, calendar.monthrange(y, m)[1]))


def expand_chronicle(rule, start, until):
    kind, arg = rule
    out, c = [], start
    while c < until:
        out.append(c)
        if kind == "EveryInterval":
            c = c + arg
        elif kind == "Daily":
            c = c + dt.timedelta(days=1)
        elif kind == "Weekly":
            c = c + dt.timedelta(days=7)
        elif kind == "Monthly":
            c = add_month(c)                              # from the previous due: drifts
        elif kind == "Weekdays":
            c = c + dt.timedelta(days=1)
            while DAYS[c.weekday()] not in arg:
                c = c + dt.timedelta(days=1)
        else:
            return out
    return out


# ---------------------------------------------------------------------------------------------
# random extensions: property checks (the apps' draws cannot be reproduced bit-for-bit, and
# the property is what the owner app promises)
# ---------------------------------------------------------------------------------------------
def gen_random_days(mn, mx, start, until, seed_fn):
    out, c = [], start
    while c < until:
        out.append(c)
        c = c + dt.timedelta(days=random.Random(seed_fn(c, mn, mx)).randint(mn, mx))
    return out


def seed(c, mn, mx):
    return int(c.replace(tzinfo=dt.timezone.utc).timestamp()) * 31 + mn * 7 + mx   # RepeatSchedule.kt:39


def ok_random_days(series, mn, mx):
    gaps = [(b - a) for a, b in zip(series, series[1:])]
    return len(series) > 5 and all(g.seconds == 0 and mn <= g.days <= mx for g in gaps) and \
        series == gen_random_days(mn, mx, series[0], series[-1] + dt.timedelta(seconds=1), seed)


def gen_window(mask, ws, we, start, until, rng):
    out, d = [], start.date()
    while dt.datetime.combine(d, dt.time()) < until:
        if mask[d.weekday()]:
            lo = dt.datetime.combine(d, ws)
            out.append(lo + dt.timedelta(minutes=rng.randrange(int((dt.datetime.combine(d, we) - lo).total_seconds() // 60))))
        d += dt.timedelta(days=1)
    return out


def ok_window(series, mask, ws, we, start, until):
    days = [s.date() for s in series]
    want = [start.date() + dt.timedelta(i) for i in range((until.date() - start.date()).days)
            if mask[(start.date() + dt.timedelta(i)).weekday()]]
    return days == want and all(ws <= s.time() < we for s in series)


# ---------------------------------------------------------------------------------------------
# cases: (owner, truth(), {encoding: encoded form or None}, how to expand/check)
# ---------------------------------------------------------------------------------------------
WEEKDAYS5 = ["MO", "TU", "WE", "TH", "FR"]
MASK5 = [1, 1, 1, 1, 1, 0, 0]


def month_anchor(start, until):
    out, k = [], 0
    while True:
        d = add_month(start, k)          # always from the ORIGINAL start: no drift
        if d >= until:
            return out
        out.append(d)
        k += 1


JAN31 = dt.datetime(2026, 1, 31, 9, 0)
JAN31_END = dt.datetime(2026, 7, 1)

CASES = {
 "tendril-elastic-3d": ("tendril",
    lambda: [START + dt.timedelta(days=3 * k) for k in range(31)],
    {"rrule": "FREQ=DAILY;INTERVAL=3", "rrule+ext": "FREQ=DAILY;INTERVAL=3",
     "cron+ext": None, "chronicle-enum": ("EveryInterval", dt.timedelta(days=3))}),
 "tendril-monthly-31st": ("tendril",
    lambda: month_anchor(JAN31, JAN31_END),
    {"rrule": "FREQ=MONTHLY;BYMONTHDAY=31,-1;BYSETPOS=1", "rrule+ext": "FREQ=MONTHLY;BYMONTHDAY=31,-1;BYSETPOS=1",
     "cron+ext": None, "chronicle-enum": ("Monthly", None)}),
 "tendril-second-tuesday": ("tendril",
    lambda: [dt.datetime(y, m, d, 9) for (y, m) in [(2026, 10), (2026, 11), (2026, 12)]
             for d in range(8, 15) if dt.date(y, m, d).weekday() == 1],
    {"rrule": "FREQ=MONTHLY;BYDAY=2TU", "rrule+ext": "FREQ=MONTHLY;BYDAY=2TU",
     "cron+ext": "0 9 8-14 * 2", "chronicle-enum": None}),
 "tendril-until": ("tendril",
    lambda: [START + dt.timedelta(days=i) for i in range(0, 28) if (START + dt.timedelta(days=i)).weekday() in (0, 2)],
    {"rrule": "FREQ=WEEKLY;BYDAY=MO,WE;UNTIL=20261101T235900", "rrule+ext": "FREQ=WEEKLY;BYDAY=MO,WE;UNTIL=20261101T235900",
     "cron+ext": None, "chronicle-enum": None}),
 "chronicle-every-90min": ("chronicle",
    lambda: [START + dt.timedelta(minutes=90 * k) for k in range(40)],
    {"rrule": "FREQ=MINUTELY;INTERVAL=90", "rrule+ext": "FREQ=MINUTELY;INTERVAL=90",
     "cron+ext": None, "chronicle-enum": ("EveryInterval", dt.timedelta(minutes=90))}),
 "chronicle-weekdays": ("chronicle",
    lambda: expand_chronicle(("Weekdays", WEEKDAYS5), START.replace(hour=7, minute=30), HORIZON),
    {"rrule": "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR", "rrule+ext": "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR",
     "cron+ext": "30 7 * * 1-5", "chronicle-enum": ("Weekdays", WEEKDAYS5)}),
 "chronicle-random-days": ("chronicle", None,
    {"rrule": None, "rrule+ext": ("RANDOM_DAYS", 2, 4), "cron+ext": ("RANDOM_DAYS", 2, 4),
     "chronicle-enum": ("RandomDays", (2, 4))}),
 "mnemo-cron-every-15": ("mnemo",
    lambda: expand_cron("*/15 9-17 * * 1-5", START, START + dt.timedelta(days=14)),
    {"rrule": "FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=9,10,11,12,13,14,15,16,17;BYMINUTE=0,15,30,45",
     "rrule+ext": "FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=9,10,11,12,13,14,15,16,17;BYMINUTE=0,15,30,45",
     "cron+ext": "*/15 9-17 * * 1-5", "chronicle-enum": None}),
 "mnemo-cron-twice-daily": ("mnemo",
    lambda: expand_cron("30 8,20 * * *", START, START + dt.timedelta(days=30)),
    {"rrule": "FREQ=DAILY;BYHOUR=8,20;BYMINUTE=30", "rrule+ext": "FREQ=DAILY;BYHOUR=8,20;BYMINUTE=30",
     "cron+ext": "30 8,20 * * *", "chronicle-enum": None}),
 "mnemo-cron-dom-or-dow": ("mnemo",
    lambda: expand_cron("0 9 1 * 1", START, HORIZON),
    {"rrule": None, "rrule+ext": ("RULE_SET", ["FREQ=MONTHLY;BYMONTHDAY=1", "FREQ=WEEKLY;BYDAY=MO"]),
     "cron+ext": "0 9 1 * 1", "chronicle-enum": None}),
 "mnemo-stochastic-window": ("mnemo", None,
    {"rrule": None, "rrule+ext": ("RANDOM_WINDOW", MASK5, dt.time(10), dt.time(12)),
     "cron+ext": ("RANDOM_WINDOW", MASK5, dt.time(10), dt.time(12)), "chronicle-enum": None}),
}
ENCODINGS = ["rrule", "rrule+ext", "cron+ext", "chronicle-enum", "one-shot"]
BOUNDS = {"tendril-monthly-31st": (JAN31, JAN31_END), "mnemo-cron-every-15": (START, START + dt.timedelta(days=14)),
          "mnemo-cron-twice-daily": (START, START + dt.timedelta(days=30))}


def expand(enc, form, start, until):
    if isinstance(form, tuple) and form[0] == "RULE_SET":
        return sorted(set(h for r in form[1] for h in expand_rrule(r, start, until)))
    if enc in ("rrule", "rrule+ext"):
        return expand_rrule(form, start, until)
    if enc == "cron+ext":
        return expand_cron(form, start, until)
    return expand_chronicle(form, start, until)


def run_case(cid, enc):
    owner, truth, forms = CASES[cid]
    form = forms.get(enc)
    if form is None:
        return 0
    start, until = BOUNDS.get(cid, (START, HORIZON))
    if cid == "chronicle-random-days":
        series = gen_random_days(2, 4, START, HORIZON, seed)
        return 1 if ok_random_days(series, 2, 4) else 0
    if cid == "mnemo-stochastic-window":
        series = gen_window(MASK5, dt.time(10), dt.time(12), START, HORIZON, random.Random(7))
        return 1 if ok_window(series, MASK5, dt.time(10), dt.time(12), START, HORIZON) else 0
    if cid == "tendril-second-tuesday" or cid == "mnemo-cron-dom-or-dow":
        start = start.replace(hour=9, minute=0)
    if cid == "chronicle-weekdays":
        start = start.replace(hour=7, minute=30)
    if cid == "mnemo-cron-every-15":
        start = start.replace(hour=0, minute=0)
    want = [t for t in truth() if start <= t < until]
    got = [t for t in expand(enc, form, start, until) if start <= t < until]
    if cid == "tendril-elastic-3d":
        want = [t for t in want if t < START + dt.timedelta(days=90)]
        got = [t for t in got if t < START + dt.timedelta(days=90)]
    if cid == "chronicle-every-90min":
        want, got = want[:40], got[:40]
    return 1 if got == want and want else 0


def main():
    sim = {e: {cid: run_case(cid, e) for cid in CASES} for e in ENCODINGS}
    with open(os.path.join(ROOT, "decisions", "options", "04-recurrence.sim.json"), "w",
              encoding="utf-8", newline="") as fh:
        json.dump(sim, fh, indent=1)
    print("%-28s" % "case" + "".join("%-16s" % e for e in ENCODINGS))
    for cid in CASES:
        print("%-28s" % cid + "".join("%-16s" % sim[e][cid] for e in ENCODINGS))


if __name__ == "__main__":
    main()
