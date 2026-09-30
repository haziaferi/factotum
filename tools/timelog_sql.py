"""Contest 07 (timed interval): build each candidate in SQLite beside the decided item table
(ADR 02/03/06 kinds) and Chronicle's activity/category/goal module (sole owner, moves across
as-is), then run each owner behaviour as a query or a refused write.

    python tools/timelog_sql.py      # writes decisions/options/07-timelog.sim.json + a table

Options
  two-tables     keep both: time_log(item_id) as Tendril, session(activity_id) as Chronicle
  timelog-only   Tendril: time_log on an item; activities have no timed sessions
  session-only   Chronicle: session on an activity; a task or habit cannot be timed
  one-span       one time_span table, owner = item_id XOR activity_id (CHECK); item FK cascades,
                 activity FK refuses (each owner's delete rule kept on its own column)
  activity-item  an activity becomes item kind ACTIVITY (icon, colour, category, archived, order
                 on item); time_span(item_id) only; a trigger refuses deleting a timed ACTIVITY
  bare           CONTROL: time_span(start, end) with no owner
Growth = tables + columns + triggers.
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ITEM = """
  CREATE TABLE item(id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN (%s)), title TEXT NOT NULL,
    start_date TEXT, start_time TEXT, rrule TEXT, status TEXT, deleted_at TEXT%s);
"""
KINDS = "'TASK','EVENT','REMINDER','HABIT'"
CATEGORY = """
  CREATE TABLE category(id TEXT PRIMARY KEY, name TEXT NOT NULL, color INT NOT NULL,
    applies_to TEXT NOT NULL, sort_order INT NOT NULL, deleted_at TEXT);
"""
ACTIVITY = """
  CREATE TABLE activity(id TEXT PRIMARY KEY, name TEXT NOT NULL, color INT NOT NULL, icon TEXT NOT NULL,
    archived INT NOT NULL DEFAULT 0, category_id TEXT REFERENCES category(id) ON DELETE SET NULL,
    sort_order INT NOT NULL DEFAULT 0, deleted_at TEXT);
"""
GOAL = """
  CREATE TABLE goal(id TEXT PRIMARY KEY, target_type TEXT NOT NULL CHECK(target_type IN ('ACTIVITY','TRACKER')),
    target_id TEXT NOT NULL, period TEXT NOT NULL, value REAL NOT NULL, deleted_at TEXT);
"""
TIME_LOG = """
  CREATE TABLE time_log(id TEXT PRIMARY KEY, item_id TEXT NOT NULL REFERENCES item(id) ON DELETE CASCADE,
    started_at TEXT NOT NULL, ended_at TEXT, deleted_at TEXT);
"""
SESSION = """
  CREATE TABLE session(id TEXT PRIMARY KEY, activity_id TEXT NOT NULL REFERENCES activity(id),
    started_at TEXT NOT NULL, ended_at TEXT, comment TEXT, planned_run TEXT, deleted_at TEXT);
"""
ONE_SPAN = """
  CREATE TABLE time_span(id TEXT PRIMARY KEY,
    item_id TEXT REFERENCES item(id) ON DELETE CASCADE, activity_id TEXT REFERENCES activity(id),
    started_at TEXT NOT NULL, ended_at TEXT, comment TEXT, planned_run TEXT, deleted_at TEXT,
    CHECK((item_id IS NULL) <> (activity_id IS NULL)));
"""
ACT_ITEM_COLS = """, icon TEXT, color INT, category_id TEXT REFERENCES category(id) ON DELETE SET NULL,
    archived INT, sort_order INT,
    CHECK(kind='ACTIVITY' OR (icon IS NULL AND color IS NULL AND category_id IS NULL AND archived IS NULL AND sort_order IS NULL))"""
ACT_ITEM_SPAN = """
  CREATE TABLE time_span(id TEXT PRIMARY KEY, item_id TEXT NOT NULL REFERENCES item(id) ON DELETE CASCADE,
    started_at TEXT NOT NULL, ended_at TEXT, comment TEXT, planned_run TEXT, deleted_at TEXT);
  CREATE TRIGGER activity_keeps_spans BEFORE DELETE ON item
    WHEN OLD.kind='ACTIVITY' AND EXISTS(SELECT 1 FROM time_span WHERE item_id=OLD.id)
    BEGIN SELECT RAISE(ABORT, 'activity has sessions'); END;
"""
BARE = """
  CREATE TABLE time_span(id TEXT PRIMARY KEY, started_at TEXT NOT NULL, ended_at TEXT, deleted_at TEXT);
"""

DDL = {
 "two-tables": ITEM % (KINDS, "") + CATEGORY + ACTIVITY + GOAL + TIME_LOG + SESSION,
 "timelog-only": ITEM % (KINDS, "") + CATEGORY + ACTIVITY + GOAL + TIME_LOG,
 "session-only": ITEM % (KINDS, "") + CATEGORY + ACTIVITY + GOAL + SESSION,
 "one-span": ITEM % (KINDS, "") + CATEGORY + ACTIVITY + GOAL + ONE_SPAN,
 "activity-item": CATEGORY + ITEM % (KINDS + ",'ACTIVITY'", ACT_ITEM_COLS) + GOAL + ACT_ITEM_SPAN,
 "bare": ITEM % (KINDS, "") + CATEGORY + ACTIVITY + GOAL + BARE,
}
OPTIONS = list(DDL)

# fixture: task T1 "write report", habit H1 "stretch", activity A1 "Reading" in category C1 "Leisure"
BASE = [
 "INSERT INTO category VALUES('C1','Leisure',1,'BOTH',0,NULL)",
 "INSERT INTO item(id,kind,title) VALUES('T1','TASK','write report')",
 "INSERT INTO item(id,kind,title) VALUES('H1','HABIT','stretch')",
 "INSERT INTO goal VALUES('G1','ACTIVITY','A1','WEEK',180,NULL)",
]
ACT_ROW = "INSERT INTO activity(id,name,color,icon,category_id) VALUES('A1','Reading',2,'book','C1')"
ACT_AS_ITEM = "INSERT INTO item(id,kind,title,icon,color,category_id,archived,sort_order) VALUES('A1','ACTIVITY','Reading','book',2,'C1',0,0)"

# (owner, start, end, comment, planned_run); times on 2026-10-05
SPANS = [("T1", "09:00", "09:25", None, None), ("H1", "12:00", "12:10", None, None),
         ("A1", "20:00", "20:40", "ch. 3", "P25/5")]


def insert_span(c, opt, sid, owner, a, b, comment=None, run=None):
    s, e = "2026-10-05T" + a, "2026-10-05T" + b
    is_act = owner.startswith("A")
    if opt == "two-tables" or opt == "timelog-only" or opt == "session-only":
        if is_act:
            c.execute("INSERT INTO session VALUES(?,?,?,?,?,?,NULL)", (sid, owner, s, e, comment, run))
        else:
            c.execute("INSERT INTO time_log VALUES(?,?,?,?,NULL)", (sid, owner, s, e))
    elif opt == "one-span":
        c.execute(SPAN_INSERT["activity_id" if is_act else "item_id"], (sid, owner, s, e, comment, run))
    elif opt == "activity-item":
        c.execute("INSERT INTO time_span(id,item_id,started_at,ended_at,comment,planned_run) VALUES(?,?,?,?,?,?)",
                  (sid, owner, s, e, comment, run))
    else:
        c.execute("INSERT INTO time_span(id,started_at,ended_at) VALUES(?,?,?)", (sid, s, e))


def db(opt):
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys=ON")
    c.executescript(DDL[opt])
    for s in BASE:
        c.execute(s)
    c.execute(ACT_AS_ITEM if opt == "activity-item" else ACT_ROW)
    for i, sp in enumerate(SPANS):
        try:
            insert_span(c, opt, "S%d" % i, *sp)
        except sqlite3.Error:
            pass  # the option cannot hold this span; the cases that need it will fail
    return c


def cols(c, table):
    return [r[0] for r in c.execute("SELECT name FROM pragma_table_info(?)", (table,))]


def tables(c):
    return [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]


def triggers(c):
    return c.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]


MINUTES = "sum((julianday(ended_at)-julianday(started_at))*1440)"
SPAN_INSERT = {
 "item_id": "INSERT INTO time_span(id,item_id,started_at,ended_at,comment,planned_run) VALUES(?,?,?,?,?,?)",
 "activity_id": "INSERT INTO time_span(id,activity_id,started_at,ended_at,comment,planned_run) VALUES(?,?,?,?,?,?)",
}
OWNER_MINUTES = {
 ("time_log", "item_id"): "SELECT round(sum((julianday(ended_at)-julianday(started_at))*1440)) FROM time_log WHERE item_id=? AND deleted_at IS NULL",
 ("session", "activity_id"): "SELECT round(sum((julianday(ended_at)-julianday(started_at))*1440)) FROM session WHERE activity_id=? AND deleted_at IS NULL",
 ("time_span", "item_id"): "SELECT round(sum((julianday(ended_at)-julianday(started_at))*1440)) FROM time_span WHERE item_id=? AND deleted_at IS NULL",
 ("time_span", "activity_id"): "SELECT round(sum((julianday(ended_at)-julianday(started_at))*1440)) FROM time_span WHERE activity_id=? AND deleted_at IS NULL",
}
OWNERLESS = {
 "time_log": "INSERT INTO time_log(id,started_at) VALUES('X','2026-10-05T10:00')",
 "session": "INSERT INTO session(id,started_at) VALUES('X','2026-10-05T10:00')",
 "time_span": "INSERT INTO time_span(id,started_at) VALUES('X','2026-10-05T10:00')",
}
DAY_TOTAL = "SELECT round(sum((julianday(ended_at)-julianday(started_at))*1440)) FROM time_span WHERE deleted_at IS NULL"


def minutes_for(c, opt, owner):
    """Tracked minutes for one owner, or None when the option has nowhere to look."""
    is_act = owner.startswith("A")
    if opt in ("two-tables", "timelog-only", "session-only"):
        t, col = ("session", "activity_id") if is_act else ("time_log", "item_id")
        if t not in tables(c):
            return None
    elif opt == "one-span":
        t, col = "time_span", "activity_id" if is_act else "item_id"
    elif opt == "activity-item":
        t, col = "time_span", "item_id"
    else:
        return None
    return c.execute(OWNER_MINUTES[(t, col)], (owner,)).fetchone()[0]


def case_task(opt):
    """tendril: 25 minutes timed on the task 'write report' total 25 for that task."""
    return 1 if minutes_for(db(opt), opt, "T1") == 25 else 0


def case_habit(opt):
    """tendril: 10 minutes timed on the habit 'stretch' (an item since ADR 06) total 10."""
    return 1 if minutes_for(db(opt), opt, "H1") == 10 else 0


def case_one_owner(opt):
    """tendril: exactly one owner per log; a log with no owner is refused by the schema."""
    c = db(opt)
    t = "time_log" if opt in ("two-tables", "timelog-only") else "session" if opt == "session-only" else "time_span"
    try:
        c.execute(OWNERLESS[t])
        return 0
    except sqlite3.IntegrityError:
        return 1


def case_task_delete_cascades(opt):
    """tendril: deleting the task for good removes its time logs (FK CASCADE, TimeLog.kt:36)."""
    c = db(opt)
    if minutes_for(c, opt, "T1") != 25:
        return 0
    c.execute("DELETE FROM item WHERE id='T1'")
    return 1 if minutes_for(c, opt, "T1") is None else 0


def case_activity(opt):
    """chronicle: 40 minutes of 'Reading' total 40 for the activity and 40 for its category 'Leisure'."""
    c = db(opt)
    if minutes_for(c, opt, "A1") != 40:
        return 0
    q = {"two-tables": "SELECT round(sum((julianday(s.ended_at)-julianday(s.started_at))*1440)) FROM session s JOIN activity a ON a.id=s.activity_id WHERE a.category_id='C1'",
         "session-only": "SELECT round(sum((julianday(s.ended_at)-julianday(s.started_at))*1440)) FROM session s JOIN activity a ON a.id=s.activity_id WHERE a.category_id='C1'",
         "one-span": "SELECT round(sum((julianday(s.ended_at)-julianday(s.started_at))*1440)) FROM time_span s JOIN activity a ON a.id=s.activity_id WHERE a.category_id='C1'",
         "activity-item": "SELECT round(sum((julianday(s.ended_at)-julianday(s.started_at))*1440)) FROM time_span s JOIN item a ON a.id=s.item_id WHERE a.category_id='C1'"}.get(opt)
    return 1 if q and c.execute(q).fetchone()[0] == 40 else 0


def case_comment_run(opt):
    """chronicle: a session keeps its comment and its planned-run stamp (SessionEntity.kt:39,48)."""
    c = db(opt)
    q = {"two-tables": "SELECT comment, planned_run FROM session WHERE id='S2'",
         "session-only": "SELECT comment, planned_run FROM session WHERE id='S2'",
         "one-span": "SELECT comment, planned_run FROM time_span WHERE id='S2'",
         "activity-item": "SELECT comment, planned_run FROM time_span WHERE id='S2'"}.get(opt)
    return 1 if q and c.execute(q).fetchone() == ("ch. 3", "P25/5") else 0


def case_activity_delete_refused(opt):
    """chronicle: an activity with sessions cannot be deleted for good (FK NO ACTION, SessionEntity.kt:11)."""
    c = db(opt)
    if minutes_for(c, opt, "A1") != 40:
        return 0
    try:
        c.execute("DELETE FROM item WHERE id='A1'" if opt == "activity-item" else "DELETE FROM activity WHERE id='A1'")
        return 0
    except sqlite3.IntegrityError:
        return 1


def case_goal(opt):
    """chronicle: a weekly 3 h goal on 'Reading' reads 40 of 180 minutes from its sessions."""
    c = db(opt)
    q = {"two-tables": "SELECT round(sum((julianday(s.ended_at)-julianday(s.started_at))*1440)), g.value FROM goal g JOIN session s ON s.activity_id=g.target_id WHERE g.id='G1'",
         "session-only": "SELECT round(sum((julianday(s.ended_at)-julianday(s.started_at))*1440)), g.value FROM goal g JOIN session s ON s.activity_id=g.target_id WHERE g.id='G1'",
         "one-span": "SELECT round(sum((julianday(s.ended_at)-julianday(s.started_at))*1440)), g.value FROM goal g JOIN time_span s ON s.activity_id=g.target_id WHERE g.id='G1'",
         "activity-item": "SELECT round(sum((julianday(s.ended_at)-julianday(s.started_at))*1440)), g.value FROM goal g JOIN time_span s ON s.item_id=g.target_id WHERE g.id='G1'"}.get(opt)
    return 1 if q and c.execute(q).fetchone() == (40, 180) else 0


def case_one_home(opt):
    """shared: tracked time lives in one table, so the day's total (75 min) and 'what is running'
    are one query each (as ADR 03/04's one-home cases)."""
    c = db(opt)
    homes = [t for t in tables(c) if "started_at" in cols(c, t)]
    if homes != ["time_span"]:
        return 0
    return 1 if c.execute(DAY_TOTAL).fetchone()[0] == 75 else 0


CASES = {
    "tendril-time-on-task": ("tendril", case_task),
    "tendril-time-on-habit": ("tendril", case_habit),
    "tendril-exactly-one-owner": ("tendril", case_one_owner),
    "tendril-task-delete-cascades": ("tendril", case_task_delete_cascades),
    "chronicle-activity-and-category-totals": ("chronicle", case_activity),
    "chronicle-comment-and-planned-run": ("chronicle", case_comment_run),
    "chronicle-activity-delete-refused": ("chronicle", case_activity_delete_refused),
    "chronicle-activity-goal": ("chronicle", case_goal),
    "shared-one-time-home": ("shared", case_one_home),
}


def growth(opt):
    c = db(opt)
    return {"tables": len(tables(c)), "columns": sum(len(cols(c, t)) for t in tables(c)), "triggers": triggers(c)}


def main():
    sim = {o: {cid: fn(o) for cid, (_, fn) in CASES.items()} for o in OPTIONS}
    with open(os.path.join(ROOT, "decisions", "options", "07-timelog.sim.json"), "w",
              encoding="utf-8", newline="") as fh:
        json.dump(sim, fh, indent=1)
    print("%-40s" % "case" + "".join("%-14s" % o for o in OPTIONS))
    for cid in CASES:
        print("%-40s" % cid + "".join("%-14s" % sim[o][cid] for o in OPTIONS))
    print("%-40s" % "growth tables/columns/triggers" + "".join("%-14s" % "/".join(str(v) for v in growth(o).values()) for o in OPTIONS))


if __name__ == "__main__":
    main()
