"""SPEC §9.2: measure Tendril's calendar-habit rules through Factotum's stored form.

    python tools/spikes/planner_check.py

Truth: a port of Tendril's planner, `CalendarSchedule.kt` expandWeek (:274-371) with dayHabit/
activeOn (:236-249) and the "X times a week" spread and load balancing (:313-342).

Part 1, the rules ADR 06 asserted map to RRULE: each rule is converted to an RRULE (or ADR 04's
RULE_SET) and expanded with tools/recurrence_sim.py's engine, the one contest 04 was scored with.
Two converters for the DTSTART, because ADR 06 says "activeFrom/activeUntil become DTSTART and UNTIL":
  literal  DTSTART = the rule's anchor, or activeFrom when set; UNTIL = activeUntil
  aligned  DTSTART = the first date on or after the window start (or activeFrom) that the rule's
           own anchor allows; UNTIL = activeUntil
Part 2, PLANNED (ADR 04 amendment): random models of TimesPerWeek and block-slot TimesPerDay habits,
with fixed habits as load and confirmed weeks as ADR 11 WEEK edits, are written into Factotum rows
using only the columns the ADRs declare, read back, and planned again; the two plans must match.
  adr      item columns declared in ADRs 02/04/06/07/11 (no block column, no duration outside EVENT)
  adr+fix  the same plus item.block_id and item.duration_min on HABIT
"""
import datetime as dt
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import recurrence_sim as rs  # noqa: E402

D = dt.date.fromisoformat
MON = 0


def monday_of(d):
    return d - dt.timedelta(days=d.weekday())


# ------------------------------------------------------------------ Tendril port (truth)
def spread(k, n):
    return [min(k - 1, int((i + 0.5) * k / n)) for i in range(n)]


def active_on(h, d, week_edit=None):
    p = h.get("pause")
    if p and (p[0] is None or d >= p[0]) and (p[1] is None or d <= p[1]):
        return False
    if h.get("active_from") and d < h["active_from"]:
        return False
    if h.get("active_until") and d > h["active_until"]:
        return False
    return True


def plan_week(habits, blocks, week_edits, monday):
    """-> {date: [(habit, block, time, minutes)]} for the week; blocks ordered by position."""
    days = [monday + dt.timedelta(i) for i in range(7)]
    order = [b["id"] for b in sorted(blocks, key=lambda b: b["position"])]
    placed = {d: [] for d in days}
    weekly = []
    for h in habits:
        r = h["rule"]
        for d in days:
            if not active_on(h, d):
                continue
            k = r[0]
            occ = (h["id"], h.get("block"), h.get("time"), h["minutes"])
            if k == "Daily":
                placed[d].append(occ)
            elif k == "Once" and r[1] == d:
                placed[d].append(occ)
            elif k == "Weekdays" and d.weekday() in r[1]:
                placed[d].append(occ)
            elif k == "EveryNDays" and r[1] > 0 and (d - r[2]).days % r[1] == 0:
                placed[d].append(occ)
            elif k == "EveryNWeeks":
                weeks = (monday_of(d) - monday_of(r[2])).days // 7
                if r[1] > 0 and weeks % r[1] == 0 and d.weekday() in r[3]:
                    placed[d].append(occ)
            elif k == "TimesPerDay":
                slots = r[2] or ([("block", order[i]) for i in spread(len(order), r[1])] if order and 1 <= r[1] <= 48 else [])
                for s in slots:
                    placed[d].append((h["id"], s[1], None, h["minutes"]) if s[0] == "block" else (h["id"], None, s[1], h["minutes"]))
            elif k == "EveryNHours" and 1 <= r[1] <= 24:
                t = r[2]
                while t <= r[3]:
                    placed[d].append((h["id"], None, t, h["minutes"]))
                    t += r[1] * 60
        if r[0] == "TimesPerWeek":
            weekly.append(h)
    load = {d: sum(o[3] for o in placed[d]) for d in days}
    for h in sorted(weekly, key=lambda h: (h.get("sort", 0.0), h["id"])):
        n, allowed = h["rule"][1], h["rule"][2]
        pool = [d for d in days if active_on(h, d) and d.weekday() in allowed]
        if not pool:
            continue
        confirmed = week_edits.get((h["id"], monday))
        if confirmed is None and n <= 0:
            continue
        if confirmed is not None:
            chosen = [d for d in pool if d.weekday() in confirmed]
        else:
            m = min(n, len(pool))
            base = spread(len(pool), m)
            best = None
            for off in range(len(pool)):
                pick = sorted({pool[(i + off) % len(pool)] for i in base})
                trial = dict(load)
                for d in pick:
                    trial[d] += h["minutes"]
                score = (max(trial.values()), sum(v * v for v in trial.values()), off)
                if best is None or score < best[0]:
                    best = (score, pick)
            chosen = best[1]
        for d in chosen:
            if confirmed is not None:
                placed[d].append((h["id"], h.get("block"), h.get("time"), h["minutes"]))
            load[d] += h["minutes"]
    return {d: sorted(v, key=str) for d, v in placed.items()}


# ------------------------------------------------------------------ Part 1: RRULE-mapped rules
def to_rrule(h, win_start, policy):
    """-> (list of RRULE strings, dtstart datetime) or None when the rule is not an RRULE form."""
    r = h["rule"]
    tm = h.get("time") or 0
    af, au = h.get("active_from"), h.get("active_until")
    until = ";UNTIL=%sT235959" % au.strftime("%Y%m%d") if au else ""
    hm = lambda m: (m // 60, m % 60)
    def at(d, m=tm):
        return dt.datetime(d.year, d.month, d.day, *hm(m))
    k = r[0]
    if k == "Daily":
        start = af or win_start
        return ["FREQ=DAILY" + until], at(start)
    if k == "Once":
        return ["FREQ=DAILY;COUNT=1"], at(r[1])
    if k == "Weekdays":
        return ["FREQ=WEEKLY;BYDAY=%s" % ",".join(rs.DAYS[x] for x in sorted(r[1])) + until], at(af or win_start)
    if k == "EveryNDays":
        n, anchor = r[1], r[2]
        if policy == "literal":
            start = af or anchor
        else:
            lo = af or win_start
            start = lo + dt.timedelta((anchor - lo).days % n)
        return ["FREQ=DAILY;INTERVAL=%d" % n + until], at(start)
    if k == "EveryNWeeks":
        n, anchor, days = r[1], r[2], r[3]
        byday = ",".join(rs.DAYS[x] for x in sorted(days))
        if policy == "literal":
            start = af or anchor
        else:
            lo = af or win_start
            wk = (monday_of(lo) - monday_of(anchor)).days // 7
            start = monday_of(lo) + dt.timedelta(7 * ((-wk) % n))
        return ["FREQ=WEEKLY;INTERVAL=%d;BYDAY=%s" % (n, byday) + until], at(start)
    if k == "EveryNHours":
        n, frm, unt = r[1], r[2], r[3]
        hours = sorted({(frm + i * n * 60) // 60 for i in range(48) if frm + i * n * 60 <= unt})
        return ["FREQ=DAILY;BYHOUR=%s;BYMINUTE=%d" % (",".join(map(str, hours)), frm % 60) + until], at(af or win_start, 0)
    if k == "TimesPerDay" and r[2] and all(s[0] == "at" for s in r[2]):
        mins = [s[1] for s in r[2]]
        if policy == "single":
            return ["FREQ=DAILY;BYHOUR=%s;BYMINUTE=%s" % (",".join(str(m // 60) for m in mins), ",".join(sorted({str(m % 60) for m in mins}, key=int))) + until], at(af or win_start, 0)
        return ["FREQ=DAILY;BYHOUR=%d;BYMINUTE=%d" % (m // 60, m % 60) + until for m in mins], at(af or win_start, 0)
    return None


def truth_times(h, win_start, weeks):
    out = set()
    for w in range(weeks):
        mon = monday_of(win_start) + dt.timedelta(7 * w)
        for d, occs in plan_week([h], [], {}, mon).items():
            if d >= win_start:
                for o in occs:
                    out.add((d, o[2] if o[2] is not None else (h.get("time") or 0)))
    return out


def rrule_times(rules, dtstart, win_start, win_end):
    out = set()
    for s in rules:
        for x in rs.expand_rrule(s, dtstart, dt.datetime.combine(win_end, dt.time())):
            if x.date() >= win_start:
                out.add((x.date(), x.hour * 60 + x.minute))
    return out


RULES = [
    ("daily-0700", {"id": "a", "rule": ("Daily",), "time": 420, "minutes": 10}),
    ("once", {"id": "b", "rule": ("Once", D("2026-10-14")), "time": 540, "minutes": 10}),
    ("weekdays-until", {"id": "c", "rule": ("Weekdays", {0, 2, 4}), "time": 480, "minutes": 10, "active_until": D("2026-11-01")}),
    ("every-3-days, window before anchor", {"id": "d", "rule": ("EveryNDays", 3, D("2026-10-01")), "time": 450, "minutes": 10}),
    ("every-3-days, activeFrom off-grid", {"id": "e", "rule": ("EveryNDays", 3, D("2026-10-01")), "time": 450, "minutes": 10, "active_from": D("2026-10-06")}),
    ("every-2-weeks, anchor mid-week", {"id": "f", "rule": ("EveryNWeeks", 2, D("2026-10-07"), {0, 3}), "time": 1080, "minutes": 10}),
    ("every-3-hours 07:30-22:00", {"id": "g", "rule": ("EveryNHours", 3, 450, 1320), "minutes": 5}),
    ("3-a-day at set times, mixed minutes", {"id": "h", "rule": ("TimesPerDay", 3, [("at", 450), ("at", 720), ("at", 1155)]), "minutes": 5}),
]


def part1():
    win_start, weeks = D("2026-09-21"), 8
    win_end = win_start + dt.timedelta(7 * weeks)
    rows = []
    for name, h in RULES:
        truth = truth_times(h, win_start, weeks)
        res = {}
        for policy in ("literal", "aligned", "single", "rule_set"):
            if h["rule"][0] == "TimesPerDay" and policy in ("literal", "aligned"):
                continue
            if h["rule"][0] != "TimesPerDay" and policy in ("single", "rule_set"):
                continue
            conv = to_rrule(h, win_start, "single" if policy == "single" else ("literal" if policy == "literal" else "aligned"))
            got = rrule_times(*conv, win_start, win_end)
            res[policy] = (len(truth), len(got), len(truth - got), len(got - truth))
        rows.append((name, res))
    return rows


# ------------------------------------------------------------------ Part 2: PLANNED round trip
def to_factotum(habits, blocks, week_edits, with_fix):
    """Only ADR-declared columns (+ the two fix columns when asked)."""
    items = []
    for h in habits:
        r = h["rule"]
        row = {"id": h["id"], "kind": "HABIT", "start_time": h.get("time"), "sort_order": h.get("sort", 0.0),
               "pause_from": (h.get("pause") or (None, None))[0], "pause_until": (h.get("pause") or (None, None))[1]}
        if r[0] == "TimesPerWeek":
            row.update(recurrence_kind="PLANNED", planned_n=r[1], planned_days=sorted(r[2]), planned_blocks=None)
        elif r[0] == "TimesPerDay" and all(s[0] == "block" for s in r[2]):
            row.update(recurrence_kind="PLANNED", planned_n=r[1], planned_days=None, planned_blocks=[s[1] for s in r[2]])
        else:
            row.update(recurrence_kind="RRULE", rule=r)  # fixed load habits; Part 1 measures their mapping
        if with_fix:
            row.update(block_id=h.get("block"), duration_min=h["minutes"])
        items.append(row)
    edits = [{"item_id": hid, "scope": ("WEEK", mon), "changes": {"week_days": sorted(days)}} for (hid, mon), days in week_edits.items()]
    return items, [dict(b) for b in blocks], edits


def from_factotum(items, blocks, edits):
    habits = []
    for it in items:
        if it["recurrence_kind"] == "PLANNED" and it["planned_days"] is not None:
            rule = ("TimesPerWeek", it["planned_n"], set(it["planned_days"]))
        elif it["recurrence_kind"] == "PLANNED":
            rule = ("TimesPerDay", it["planned_n"], [("block", b) for b in it["planned_blocks"]])
        else:
            rule = it["rule"]
        pause = (it["pause_from"], it["pause_until"]) if (it["pause_from"] or it["pause_until"]) else None
        habits.append({"id": it["id"], "rule": rule, "time": it["start_time"], "sort": it["sort_order"], "pause": pause,
                       "block": it.get("block_id"), "minutes": it.get("duration_min", 0)})
    we = {(e["item_id"], e["scope"][1]): set(e["changes"]["week_days"]) for e in edits if e["scope"][0] == "WEEK"}
    return habits, blocks, we


def random_model(rng):
    blocks = [{"id": "morning", "start": 360, "end": 600, "position": 0}, {"id": "midday", "start": 600, "end": 840, "position": 1},
              {"id": "evening", "start": 1080, "end": 1320, "position": 2}]
    rng.shuffle(blocks)
    for i, b in enumerate(blocks):
        b["position"] = i
    habits = []
    for i in range(rng.randint(1, 3)):  # fixed habits: load for the balancing
        habits.append({"id": "fix%d" % i, "rule": ("Weekdays", set(rng.sample(range(7), rng.randint(1, 5)))),
                       "block": rng.choice([b["id"] for b in blocks]), "minutes": rng.choice([10, 20, 45]), "sort": rng.random()})
    for i in range(rng.randint(1, 3)):
        habits.append({"id": "tpw%d" % i, "rule": ("TimesPerWeek", rng.randint(1, 5), set(rng.sample(range(7), rng.randint(3, 7)))),
                       "block": rng.choice([None] + [b["id"] for b in blocks]), "minutes": rng.choice([15, 30, 60]), "sort": rng.random(),
                       "pause": (D("2026-10-07"), D("2026-10-08")) if rng.random() < 0.2 else None})
    if rng.random() < 0.5:
        habits.append({"id": "tpd", "rule": ("TimesPerDay", rng.randint(1, 3), [("block", b["id"]) for b in rng.sample(blocks, rng.randint(1, 3))]),
                       "minutes": 5, "sort": rng.random()})
    mon = D("2026-10-05")
    week_edits = {}
    for h in habits:
        if h["rule"][0] == "TimesPerWeek" and rng.random() < 0.4:
            week_edits[(h["id"], mon)] = set(rng.sample(sorted(h["rule"][2]), min(h["rule"][1], len(h["rule"][2]))))
    return habits, blocks, week_edits


def part2(n=500):
    out = {}
    for fix in (False, True):
        rng = random.Random(9_2)
        bad, first = 0, None
        for i in range(n):
            habits, blocks, we = random_model(rng)
            mon = D("2026-10-05")
            want = plan_week(habits, blocks, we, mon)
            got = plan_week(*from_factotum(*to_factotum(habits, blocks, we, fix)), mon)
            if want != got:
                bad += 1
                if first is None:
                    d = next(d for d in want if want[d] != got[d])
                    first = "model %d, %s: want %s got %s" % (i, d, want[d][:2], got[d][:2])
        out["adr+fix" if fix else "adr"] = (n - bad, n, first)
    return out


def main():
    print("Part 1: rule -> RRULE, expanded by recurrence_sim.py (truth n, rrule n, missing, extra)")
    for name, res in part1():
        print("  %-40s %s" % (name, "  ".join("%s=%s" % (k, v) for k, v in res.items())))
    print("Part 2: PLANNED round trip through Factotum rows, 500 random models")
    for k, (ok, n, first) in part2().items():
        print("  %-8s %d/%d plans identical%s" % (k, ok, n, ("; first difference: " + first) if first else ""))


if __name__ == "__main__":
    main()
