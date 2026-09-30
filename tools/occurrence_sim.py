"""Contest 11 (occurrence edits): simulate how one occurrence of a repeating item is skipped,
moved, retimed, confirmed for a week or changed from a date on, on two devices that then sync.
Only Tendril edits single occurrences (verify/11-occurrence-edits/: Chronicle and Mnemo have 0
hits), so the cases are Tendril's behaviours plus fixes of its verified defects.

    python tools/occurrence_sim.py   # writes decisions/options/11-occurrence-edits.sim.json

Options
  full-copy     Tendril's task exceptions for every item: an override row is a copy of the item
                for one occurrence (title copied), keyed only by uid; a skip row; no added
                occurrences; 'from now on' splits the series; merge is last-writer-wins per row
  edit-log      Tendril's HabitScheduleEdit for every item: insert-once rows (scope + changed
                fields), applied in (created, uid) order; a move is a skip plus an extra
  edit-log+move edit-log, but a move is one Occurrence edit carrying the new date
  as-is         full-copy for tasks and events, edit-log for habits
  patch-rows    one occurrence_edit row per (item, occurrence), UNIQUE; it holds only the fields
                it changes (skip, moved_to, time, block, title), each field stamped (ADR 01 groups);
                an added occurrence is its own keyed row; 'from now on' splits the series
  rewrite       CONTROL: every edit rewrites the whole series
"""
import json
import os
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = date.fromisoformat
WEEK0 = D("2026-10-05")  # a Monday


def series_dates(item, start=WEEK0, days=21):
    """Base occurrence dates of an item in the window, from its weekly rule."""
    out = []
    for i in range(days):
        d = start + timedelta(days=i)
        if item["weekdays"] and d.weekday() in item["weekdays"] and d >= item["from"] and (item["until"] is None or d < item["until"]):
            out.append(d)
    return out


def base_items():
    return {
        "T": {"kind": "TASK", "title": "Report", "time": "09:00", "block": None, "weekdays": {1}, "from": WEEK0, "until": None},
        "H": {"kind": "HABIT", "title": "Stretch", "time": "08:00", "block": "Morning", "weekdays": {0, 2, 4}, "from": WEEK0, "until": None},
        "P": {"kind": "HABIT", "title": "Swim", "time": "18:00", "block": None, "weekdays": set(), "from": WEEK0, "until": None, "planned": True},
    }


class Device:
    """One device's store; every option keeps its edit rows in self.rows, series in self.items."""
    def __init__(self, opt):
        self.opt, self.items, self.rows, self.clock = opt, base_items(), [], 0

    def tick(self):
        self.clock += 1
        return self.clock

    def mech(self, item_id):
        if self.opt == "as-is":
            return "log" if self.items[item_id]["kind"] == "HABIT" else "copy"
        return {"full-copy": "copy", "edit-log": "log", "edit-log+move": "log", "patch-rows": "patch", "rewrite": "rewrite"}[self.opt]

    # --- operations ------------------------------------------------------------------------
    def move(self, item_id, occ, to, dev):
        m = self.mech(item_id)
        if m == "copy":
            it = self.items[item_id]
            self.rows.append({"uid": "%s%d" % (dev, self.tick()), "mech": "copy", "item": item_id, "occ": occ,
                              "date": to, "time": it["time"], "block": it["block"], "title": it["title"], "skip": False, "t": self.clock})
        elif m == "log" and self.opt == "edit-log+move":
            t = self.tick()
            self.rows.append({"uid": "%s%d" % (dev, t), "mech": "log", "item": item_id, "scope": ("occ", occ), "changes": {"moved_to": to}, "t": t})
        elif m == "log":
            t = self.tick()
            self.rows.append({"uid": "%s%da" % (dev, t), "mech": "log", "item": item_id, "scope": ("occ", occ), "changes": {"skip": True}, "t": t})
            self.rows.append({"uid": "%s%db" % (dev, t), "mech": "log", "item": item_id, "scope": ("extra", to), "changes": {}, "t": t})
        elif m == "patch":
            self._patch(item_id, occ, {"moved_to": to})
        else:
            self.items[item_id]["weekdays"] = {to.weekday()}

    def edit(self, item_id, occ, changes, dev):
        m = self.mech(item_id)
        if m == "copy":
            it = self.items[item_id]
            row = {"uid": "%s%d" % (dev, self.tick()), "mech": "copy", "item": item_id, "occ": occ, "date": occ,
                   "time": it["time"], "block": it["block"], "title": it["title"], "skip": False, "t": self.clock}
            row.update(changes)
            self.rows.append(row)
        elif m == "log":
            t = self.tick()
            self.rows.append({"uid": "%s%d" % (dev, t), "mech": "log", "item": item_id, "scope": ("occ", occ), "changes": dict(changes), "t": t})
        elif m == "patch":
            self._patch(item_id, occ, changes)
        else:
            self.items[item_id].update({k: v for k, v in changes.items() if k in ("time", "block", "title")})
            if changes.get("skip"):
                self.items[item_id]["weekdays"] = set()

    def confirm_week(self, item_id, monday, days, dev):
        m = self.mech(item_id)
        if m == "copy":
            return  # a copy row needs an original occurrence; a planned habit has none to copy
        if m == "log":
            t = self.tick()
            self.rows.append({"uid": "%s%d" % (dev, t), "mech": "log", "item": item_id, "scope": ("week", monday), "changes": {"weekdays": set(days)}, "t": t})
        elif m == "patch":
            for wd in days:
                self._patch(item_id, "x:" + (monday + timedelta(days=wd)).isoformat(), {"extra": monday + timedelta(days=wd)})
        else:
            self.items[item_id]["weekdays"] = set(days)

    def from_now_on(self, item_id, start, changes, dev):
        m = self.mech(item_id)
        if m == "log":
            t = self.tick()
            self.rows.append({"uid": "%s%d" % (dev, t), "mech": "log", "item": item_id, "scope": ("from", start), "changes": dict(changes), "t": t})
        elif m in ("copy", "patch"):
            old = self.items[item_id]
            new = dict(old, **changes, **{"from": start})
            old["until"] = start
            self.items[item_id + "'"] = new
        else:
            self.items[item_id].update(changes)

    def rename_series(self, item_id, title):
        self.items[item_id]["title"] = title

    def _patch(self, item_id, occ, changes):
        t = self.tick()
        row = next((r for r in self.rows if r["mech"] == "patch" and r["item"] == item_id and r["occ"] == occ), None)
        if row is None:
            row = {"mech": "patch", "item": item_id, "occ": occ, "fields": {}}
            self.rows.append(row)
        for k, v in changes.items():
            row["fields"][k] = (v, t)

    # --- expansion ------------------------------------------------------------------------
    def expand(self, item_id):
        """(date, time, block, title) for the item and any series split off it."""
        out = []
        for iid, it in self.items.items():
            if iid.rstrip("'") != item_id:
                continue
            rows = [r for r in self.rows if r["item"] == iid]
            m = self.mech(item_id)
            base = {d: {"date": d, "time": it["time"], "block": it["block"], "title": it["title"]} for d in series_dates(it)}
            if m == "copy":
                # Tendril expand(): associateBy (item, occ); the last row in list order wins; others are orphans
                by = {}
                for r in rows:
                    by[r["occ"]] = r
                orphans = [r for r in rows if by[r["occ"]] is not r]
                for occ, r in by.items():
                    if occ in base:
                        base[occ] = None if r["skip"] else {k: r[k] for k in ("date", "time", "block", "title")}
                for r in orphans:
                    base[("orphan", r["uid"])] = {k: r[k] for k in ("date", "time", "block", "title")}
            elif m == "log":
                for r in sorted(rows, key=lambda r: (r["t"], r["uid"])):
                    kind, arg = r["scope"]
                    if kind == "week":
                        for i in range(7):
                            d = arg + timedelta(days=i)
                            if d.weekday() in r["changes"]["weekdays"]:
                                base[("w", d)] = {"date": d, "time": it["time"], "block": it["block"], "title": it["title"]}
                        continue
                    if kind == "extra":
                        base[("x", r["uid"])] = {"date": arg, "time": it["time"], "block": it["block"], "title": it["title"]}
                        continue
                    for key, o in list(base.items()):
                        if o is None:
                            continue
                        hit = (kind == "occ" and key == arg) or (kind == "from" and o["date"] >= arg)
                        if hit:
                            if r["changes"].get("skip"):
                                base[key] = None
                            else:
                                if "moved_to" in r["changes"]:
                                    o["date"] = r["changes"]["moved_to"]
                                o.update({k: v for k, v in r["changes"].items() if k in ("time", "block", "title")})
            elif m == "patch":
                for r in rows:
                    f = {k: v for k, (v, _) in r["fields"].items()}
                    if "extra" in f:
                        base[r["occ"]] = {"date": f["extra"], "time": it["time"], "block": it["block"], "title": it["title"]}
                        continue
                    if r["occ"] not in base:
                        continue
                    if f.get("skip"):
                        base[r["occ"]] = None
                        continue
                    o = base[r["occ"]]
                    o["date"] = f.get("moved_to", o["date"])
                    o.update({k: f[k] for k in ("time", "block", "title") if k in f})
            out += [o for o in base.values() if o]
        return sorted((o["date"].isoformat(), o["time"], o["block"], o["title"]) for o in out)


def sync(a, b):
    """Merge two devices both ways, per mechanism, and return one merged store."""
    m = Device(a.opt)
    m.items = {k: dict(v) for k, v in {**a.items, **b.items}.items()}
    if a.opt == "rewrite":
        m.items = {k: dict(v) for k, v in {**a.items, **{k: v for k, v in b.items.items() if v != base_items().get(k)}}.items()}
    rows = []
    for r in a.rows + b.rows:
        if r["mech"] == "copy" or r["mech"] == "log":
            if not any(x.get("uid") == r.get("uid") for x in rows):
                rows.append(dict(r))
        else:  # patch: UNIQUE (item, occ); fields merge by their own stamp
            x = next((x for x in rows if x["mech"] == "patch" and x["item"] == r["item"] and x["occ"] == r["occ"]), None)
            if x is None:
                rows.append({"mech": "patch", "item": r["item"], "occ": r["occ"], "fields": dict(r["fields"])})
            else:
                for k, (v, t) in r["fields"].items():
                    if k not in x["fields"] or t > x["fields"][k][1]:
                        x["fields"][k] = (v, t)
    m.rows = rows
    return m


def dates(dev, item):
    return [o[0] for o in dev.expand(item)]


def case_task_move(opt):
    """tendril: moving Tuesday 13 Oct of the weekly task to Wednesday 14 moves that one only (EntryEditor.kt:95-97)."""
    a = Device(opt)
    a.move("T", D("2026-10-13"), D("2026-10-14"), "A")
    return 1 if dates(a, "T") == ["2026-10-06", "2026-10-14", "2026-10-20"] else 0


def case_habit_skip(opt):
    """tendril: skipping Wednesday 7 Oct of 'Stretch' leaves Mon 5 and Fri 9 (EditScope.Occurrence)."""
    a = Device(opt)
    a.edit("H", D("2026-10-07"), {"skip": True}, "A")
    return 1 if dates(a, "H")[:2] == ["2026-10-05", "2026-10-09"] else 0


def case_habit_move(opt):
    """tendril: moving Wed 7 Oct of 'Stretch' to Thu 8 affects that week only (EditMode.kt:202)."""
    a = Device(opt)
    a.move("H", D("2026-10-07"), D("2026-10-08"), "A")
    return 1 if dates(a, "H")[:4] == ["2026-10-05", "2026-10-08", "2026-10-09", "2026-10-12"] else 0


def case_week_confirm(opt):
    """tendril: the planner's confirmed days for one week (Mon, Wed, Sat) are stored for that week only;
    later weeks stay suggestions, not stored occurrences (HabitWeek.kt:71; CalendarSchedule.kt:239)."""
    a = Device(opt)
    a.confirm_week("P", WEEK0, [0, 2, 5], "A")
    return 1 if dates(a, "P") == ["2026-10-05", "2026-10-07", "2026-10-10"] else 0


def case_from_now_on(opt):
    """tendril: 'Stretch' at 07:00 from 12 Oct on; the first week stays at 08:00 (EditScope.From)."""
    a = Device(opt)
    a.from_now_on("H", D("2026-10-12"), {"time": "07:00"}, "A")
    got = a.expand("H")
    return 1 if [o[1] for o in got] == ["08:00"] * 3 + ["07:00"] * 6 else 0


def case_concurrent_fields(opt):
    """tendril: A retimes Fri 9 Oct to 07:30 while B moves it to the Evening block; after sync the
    occurrence has both (habit edits apply field by field, CalendarSchedule.kt:222)."""
    a, b = Device(opt), Device(opt)
    a.edit("H", D("2026-10-09"), {"time": "07:30"}, "A")
    b.edit("H", D("2026-10-09"), {"block": "Evening"}, "B")
    got = [o for o in sync(a, b).expand("H") if o[0] == "2026-10-09"]
    return 1 if got == [("2026-10-09", "07:30", "Evening", "Stretch")] else 0


def case_concurrent_moves(opt):
    """shared (fix): A moves the task's 13 Oct to the 14th while B moves it to the 15th; after sync the
    occurrence exists once. Tendril shows the losing override as an orphan (EntryOccurrences.kt:79,130),
    and the habit log's skip+extra shows it twice."""
    a, b = Device(opt), Device(opt)
    a.move("T", D("2026-10-13"), D("2026-10-14"), "A")
    b.move("T", D("2026-10-13"), D("2026-10-15"), "B")
    got = dates(sync(a, b), "T")
    return 1 if len(got) == 3 and got[0] == "2026-10-06" and got[2] == "2026-10-20" else 0


def case_rename_reaches_moved(opt):
    """shared (fix): renaming the series after moving one occurrence renames that occurrence too;
    a Tendril override copies the title at the moment of override (EntryEditor.kt:92)."""
    a = Device(opt)
    a.move("T", D("2026-10-13"), D("2026-10-14"), "A")
    a.rename_series("T", "Weekly report")
    return 1 if {o[3] for o in a.expand("T")} == {"Weekly report"} else 0


def case_one_mechanism(opt):
    """shared: tasks and habits keep their occurrence edits in one mechanism (ADR 06 put habits on item)."""
    a = Device(opt)
    return 1 if len({a.mech("T"), a.mech("H")}) == 1 and a.mech("T") != "rewrite" else 0


CASES = {
    "tendril-task-move-one": ("tendril", case_task_move),
    "tendril-habit-skip-one": ("tendril", case_habit_skip),
    "tendril-habit-move-this-week": ("tendril", case_habit_move),
    "tendril-planner-week-confirm": ("tendril", case_week_confirm),
    "tendril-habit-from-now-on": ("tendril", case_from_now_on),
    "tendril-concurrent-field-edits": ("tendril", case_concurrent_fields),
    "shared-concurrent-moves-once": ("shared", case_concurrent_moves),
    "shared-rename-reaches-moved": ("shared", case_rename_reaches_moved),
    "shared-one-mechanism": ("shared", case_one_mechanism),
}
# columns each option adds to the decided schema (from the verified entities; see the ADR)
GROWTH = {
    "full-copy": {"tables": 0, "columns": 3},          # item.original_item_id, original_occurrence, is_exception_skip
    "edit-log": {"tables": 1, "columns": 8},           # HabitScheduleEdit's 8 columns
    "edit-log+move": {"tables": 1, "columns": 8},       # same table; the move is a field of an Occurrence edit
    "as-is": {"tables": 1, "columns": 11},
    "patch-rows": {"tables": 1, "columns": 10},        # id, item_id, occurrence, skip, moved_to, time, block, title, extra_date, deleted_at (+ ADR 01 stamps)
    "rewrite": {"tables": 0, "columns": 0},
}
OPTIONS = list(GROWTH)


def main():
    sim = {o: {cid: fn(o) for cid, (_, fn) in CASES.items()} for o in OPTIONS}
    with open(os.path.join(ROOT, "decisions", "options", "11-occurrence-edits.sim.json"), "w",
              encoding="utf-8", newline="") as fh:
        json.dump(sim, fh, indent=1)
    print("%-32s" % "case" + "".join("%-12s" % o for o in OPTIONS))
    for cid in CASES:
        print("%-32s" % cid + "".join("%-12s" % sim[o][cid] for o in OPTIONS))


if __name__ == "__main__":
    main()
