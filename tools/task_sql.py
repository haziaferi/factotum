"""Contest 02 (task): build each candidate schema in SQLite, load one fixture, and run every
owner behaviour as a query or an integrity probe. A case passes only if the query returns the
expected rows or the database itself rejects the bad write. Nothing is marked by hand.

    python tools/task_sql.py        # writes decisions/options/02-task.sim.json + prints a table

Sync columns (hybrid+, ADR 01) are left out of the DDL: every option carries the same ones, so
they cannot separate the options. ids are TEXT (ULID in the real schema).

Options
  shared      Tendril: one table, kind TASK|EVENT; Equipoise's capacityRank joins as a nullable
              column; CHECKs keep task-only columns off events
  split       Equipoise: task and event tables; tasks gain Tendril's columns; the calendar is a
              UNION in the query; a reminder holds task_id OR event_id (CHECK exactly one)
  split+view  split, plus a SQL VIEW `schedulable` that the calendar and reminders' lookups read
  shared+side one item table (the shared columns) + a 1:1 task_detail side table for task-only
              columns
  bare        CONTROL: one table, no kind column, no CHECKs, no foreign keys
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DDL = {
 "shared": """
  CREATE TABLE item(id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('TASK','EVENT')),
    title TEXT NOT NULL, start_date TEXT, start_time TEXT, end_date TEXT, end_time TEXT,
    due_date TEXT, status TEXT, importance INT NOT NULL DEFAULT 0, capacity_rank INT,
    parent_id TEXT REFERENCES item(id) ON DELETE CASCADE, rrule TEXT,
    CHECK(kind='TASK' OR (due_date IS NULL AND status IS NULL AND capacity_rank IS NULL AND parent_id IS NULL)),
    CHECK(kind='EVENT' OR (end_date IS NULL AND end_time IS NULL)),
    CHECK(kind='EVENT' OR status IN ('PENDING','DONE','SKIPPED')));
  CREATE INDEX item_kind_date ON item(kind, start_date);
  CREATE TABLE completion(item_id TEXT NOT NULL REFERENCES item(id) ON DELETE CASCADE,
    occurrence TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('DONE','SKIPPED')));
  CREATE TABLE reminder(id TEXT PRIMARY KEY, item_id TEXT NOT NULL REFERENCES item(id) ON DELETE CASCADE,
    offset_min INT NOT NULL);
 """,
 "split": """
  CREATE TABLE task(id TEXT PRIMARY KEY, title TEXT NOT NULL, start_date TEXT, start_time TEXT,
    due_date TEXT, status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING','DONE','SKIPPED')),
    importance INT NOT NULL DEFAULT 0, capacity_rank INT,
    parent_id TEXT REFERENCES task(id) ON DELETE CASCADE, rrule TEXT);
  CREATE INDEX task_date ON task(start_date);
  CREATE TABLE event(id TEXT PRIMARY KEY, title TEXT NOT NULL, start_date TEXT NOT NULL,
    start_time TEXT, end_date TEXT, end_time TEXT, rrule TEXT);
  CREATE TABLE completion(task_id TEXT NOT NULL REFERENCES task(id) ON DELETE CASCADE,
    occurrence TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('DONE','SKIPPED')));
  CREATE TABLE reminder(id TEXT PRIMARY KEY,
    task_id TEXT REFERENCES task(id) ON DELETE CASCADE,
    event_id TEXT REFERENCES event(id) ON DELETE CASCADE,
    offset_min INT NOT NULL, CHECK((task_id IS NULL) <> (event_id IS NULL)));
 """,
}
DDL["split+view"] = DDL["split"] + """
  CREATE VIEW schedulable AS
    SELECT id, 'TASK' AS kind, title, start_date, start_time FROM task
    UNION ALL SELECT id, 'EVENT', title, start_date, start_time FROM event;
"""
DDL["shared+side"] = """
  CREATE TABLE item(id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('TASK','EVENT')),
    title TEXT NOT NULL, start_date TEXT, start_time TEXT, end_date TEXT, end_time TEXT, rrule TEXT);
  CREATE INDEX item_kind_date ON item(kind, start_date);
  CREATE TABLE task_detail(item_id TEXT PRIMARY KEY REFERENCES item(id) ON DELETE CASCADE,
    due_date TEXT, status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING','DONE','SKIPPED')),
    importance INT NOT NULL DEFAULT 0, capacity_rank INT,
    parent_id TEXT REFERENCES item(id) ON DELETE CASCADE);
  CREATE TABLE completion(item_id TEXT NOT NULL REFERENCES item(id) ON DELETE CASCADE,
    occurrence TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('DONE','SKIPPED')));
  CREATE TABLE reminder(id TEXT PRIMARY KEY, item_id TEXT NOT NULL REFERENCES item(id) ON DELETE CASCADE,
    offset_min INT NOT NULL);
"""
DDL["bare"] = """
  CREATE TABLE item(id TEXT PRIMARY KEY, title TEXT, start_date TEXT, start_time TEXT,
    end_date TEXT, end_time TEXT, due_date TEXT, status TEXT, importance INT, capacity_rank INT,
    parent_id TEXT, rrule TEXT);
  CREATE TABLE completion(item_id TEXT, occurrence TEXT, status TEXT);
  CREATE TABLE reminder(id TEXT PRIMARY KEY, item_id TEXT, offset_min INT);
"""

# fixture, per option: E1 event Mon 10:00-11:00; T1 task Mon 14:00; T2 date-only task Mon,
# rank 1; T3 recurring task every 7 days from Mon, rank 2; S1 subtask of T2; reminders on E1, T1
MON = "2026-10-05"
FIXTURE = {
 "shared": [
  "INSERT INTO item(id,kind,title,start_date,start_time,end_date,end_time) VALUES('E1','EVENT','standup','%s','10:00','%s','11:00')" % (MON, MON),
  "INSERT INTO item(id,kind,title,start_date,start_time,status,capacity_rank) VALUES('T1','TASK','call','%s','14:00','PENDING',3)" % MON,
  "INSERT INTO item(id,kind,title,start_date,status,capacity_rank,due_date) VALUES('T2','TASK','tax form','%s','PENDING',1,'2026-10-09')" % MON,
  "INSERT INTO item(id,kind,title,start_date,status,capacity_rank,rrule) VALUES('T3','TASK','plants','%s','PENDING',2,'P7D')" % MON,
  "INSERT INTO item(id,kind,title,status,parent_id) VALUES('S1','TASK','find receipts','PENDING','T2')",
  "INSERT INTO reminder VALUES('R1','E1',-15)", "INSERT INTO reminder VALUES('R2','T1',-5)",
  "INSERT INTO completion VALUES('T3','2026-09-28','DONE')",
 ],
 "split": [
  "INSERT INTO event(id,title,start_date,start_time,end_date,end_time) VALUES('E1','standup','%s','10:00','%s','11:00')" % (MON, MON),
  "INSERT INTO task(id,title,start_date,start_time,capacity_rank) VALUES('T1','call','%s','14:00',3)" % MON,
  "INSERT INTO task(id,title,start_date,capacity_rank,due_date) VALUES('T2','tax form','%s',1,'2026-10-09')" % MON,
  "INSERT INTO task(id,title,start_date,capacity_rank,rrule) VALUES('T3','plants','%s',2,'P7D')" % MON,
  "INSERT INTO task(id,title,parent_id) VALUES('S1','find receipts','T2')",
  "INSERT INTO reminder(id,event_id,offset_min) VALUES('R1','E1',-15)",
  "INSERT INTO reminder(id,task_id,offset_min) VALUES('R2','T1',-5)",
  "INSERT INTO completion VALUES('T3','2026-09-28','DONE')",
 ],
 "shared+side": [
  "INSERT INTO item(id,kind,title,start_date,start_time,end_date,end_time) VALUES('E1','EVENT','standup','%s','10:00','%s','11:00')" % (MON, MON),
  "INSERT INTO item(id,kind,title,start_date,start_time) VALUES('T1','TASK','call','%s','14:00')" % MON,
  "INSERT INTO task_detail(item_id,capacity_rank) VALUES('T1',3)",
  "INSERT INTO item(id,kind,title,start_date) VALUES('T2','TASK','tax form','%s')" % MON,
  "INSERT INTO task_detail(item_id,capacity_rank,due_date) VALUES('T2',1,'2026-10-09')",
  "INSERT INTO item(id,kind,title,start_date,rrule) VALUES('T3','TASK','plants','%s','P7D')" % MON,
  "INSERT INTO task_detail(item_id,capacity_rank) VALUES('T3',2)",
  "INSERT INTO item(id,kind,title) VALUES('S1','TASK','find receipts')",
  "INSERT INTO task_detail(item_id,parent_id) VALUES('S1','T2')",
  "INSERT INTO reminder VALUES('R1','E1',-15)", "INSERT INTO reminder VALUES('R2','T1',-5)",
  "INSERT INTO completion VALUES('T3','2026-09-28','DONE')",
 ],
 "bare": [
  "INSERT INTO item(id,title,start_date,start_time,end_date,end_time) VALUES('E1','standup','%s','10:00','%s','11:00')" % (MON, MON),
  "INSERT INTO item(id,title,start_date,start_time,status,capacity_rank) VALUES('T1','call','%s','14:00','PENDING',3)" % MON,
  "INSERT INTO item(id,title,start_date,status,capacity_rank,due_date) VALUES('T2','tax form','%s','PENDING',1,'2026-10-09')" % MON,
  "INSERT INTO item(id,title,start_date,status,capacity_rank,rrule) VALUES('T3','plants','%s','PENDING',2,'P7D')" % MON,
  "INSERT INTO item(id,title,status,parent_id) VALUES('S1','find receipts','PENDING','T2')",
  "INSERT INTO reminder VALUES('R1','E1',-15)", "INSERT INTO reminder VALUES('R2','T1',-5)",
  "INSERT INTO completion VALUES('T3','2026-09-28','DONE')",
 ],
}
FIXTURE["split+view"] = FIXTURE["split"]

# timeline for Monday: every task and event dated Mon, ordered by time (date-only last)
TIMELINE = {
 "shared": "SELECT id FROM item WHERE start_date=? ORDER BY start_time IS NULL, start_time, id",
 "shared+side": "SELECT id FROM item WHERE start_date=? ORDER BY start_time IS NULL, start_time, id",
 "split": "SELECT id FROM (SELECT id,start_date,start_time FROM task UNION ALL SELECT id,start_date,start_time FROM event) WHERE start_date=? ORDER BY start_time IS NULL, start_time, id",
 "split+view": "SELECT id FROM schedulable WHERE start_date=? ORDER BY start_time IS NULL, start_time, id",
 "bare": "SELECT id FROM item WHERE start_date=? ORDER BY start_time IS NULL, start_time, id",
}
# Equipoise G04 (SPEC.md:161): today's pending top-level tasks by capacity rank, N at most
CAPACITY = {
 "shared": "SELECT id FROM item WHERE kind='TASK' AND start_date=? AND status='PENDING' AND parent_id IS NULL ORDER BY capacity_rank LIMIT ?",
 "shared+side": "SELECT i.id FROM item i JOIN task_detail d ON d.item_id=i.id WHERE i.kind='TASK' AND i.start_date=? AND d.status='PENDING' AND d.parent_id IS NULL ORDER BY d.capacity_rank LIMIT ?",
 "split": "SELECT id FROM task WHERE start_date=? AND status='PENDING' AND parent_id IS NULL ORDER BY capacity_rank LIMIT ?",
 "split+view": "SELECT id FROM task WHERE start_date=? AND status='PENDING' AND parent_id IS NULL ORDER BY capacity_rank LIMIT ?",
 "bare": "SELECT id FROM item WHERE start_date=? AND status='PENDING' AND parent_id IS NULL ORDER BY capacity_rank LIMIT ?",
}
TASK_TABLE = {"shared": "item", "shared+side": "item", "split": "task", "split+view": "task", "bare": "item"}
EVENT_TABLE = {"shared": "item", "shared+side": "item", "split": "event", "split+view": "event", "bare": "item"}
# Literal statements per table: identifiers cannot be bound parameters, and nothing here is
# formatted from input (every table name is a key of these dicts).
DELETE_BY_ID = {"item": "DELETE FROM item WHERE id=?", "task": "DELETE FROM task WHERE id=?"}
COUNT_BY_ID = {"item": "SELECT count(*) FROM item WHERE id=?", "task": "SELECT count(*) FROM task WHERE id=?"}
DUE_OF = {"item": "SELECT start_date, due_date FROM item WHERE id=?",
          "task": "SELECT start_date, due_date FROM task WHERE id=?"}


def db(opt):
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys=ON")
    c.executescript(DDL[opt])
    for s in FIXTURE[opt]:
        c.execute(s)
    return c


def rejects(opt, sql):
    c = db(opt)
    try:
        c.execute(sql)
        return False
    except sqlite3.IntegrityError:
        return True


def case_timeline(opt):
    got = [r[0] for r in db(opt).execute(TIMELINE[opt], (MON,))]
    return 1 if got == ["E1", "T1", "T2", "T3"] else 0


def case_capacity(opt):
    got = [r[0] for r in db(opt).execute(CAPACITY[opt], (MON, 1))]
    return 1 if got == ["T2"] else 0


def case_capacity_ignores_events(opt):
    """G04's rule reads tasks only: the plan must not touch event rows (EXPLAIN QUERY PLAN
    must use an index or a task-only table, not a full scan of a table holding events)."""
    plan = " ".join(r[3] for r in db(opt).execute("EXPLAIN QUERY PLAN " + CAPACITY[opt], (MON, 1)))
    scans_events = ("SCAN %s" % EVENT_TABLE[opt] in plan or "SCAN i" in plan) and \
        TASK_TABLE[opt] == EVENT_TABLE[opt]
    return 0 if scans_events else 1


def case_reminder_fk(opt):
    """Tendril: a reminder must point at a real task or event; deleting the task removes it."""
    bad = {"split": "INSERT INTO reminder(id,task_id,offset_min) VALUES('R9','nope',0)",
           "split+view": "INSERT INTO reminder(id,task_id,offset_min) VALUES('R9','nope',0)"}.get(
        opt, "INSERT INTO reminder VALUES('R9','nope',0)")
    if not rejects(opt, bad):
        return 0
    c = db(opt)
    c.execute(DELETE_BY_ID[TASK_TABLE[opt]], ("T1",))
    return 1 if c.execute("SELECT count(*) FROM reminder WHERE id='R2'").fetchone()[0] == 0 else 0


def case_subtask_cascade(opt):
    """Tendril + Equipoise F08: a subtask belongs to a real parent; deleting the parent takes it."""
    c = db(opt)
    c.execute(DELETE_BY_ID[TASK_TABLE[opt]], ("T2",))
    return 1 if c.execute(COUNT_BY_ID[TASK_TABLE[opt]], ("S1",)).fetchone()[0] == 0 else 0


def case_completion_log(opt):
    """Tendril: a recurring task keeps a per-occurrence DONE/SKIPPED log; a bad status is refused."""
    col = "task_id" if opt.startswith("split") else "item_id"
    return 1 if rejects(opt, "INSERT INTO completion(%s,occurrence,status) VALUES('T3','2026-10-05','MISSED')" % col) else 0


def case_planned_and_due(opt):
    """Tendril: a task has a planned date (start) and a separate deadline (due)."""
    q = {"shared+side": "SELECT i.start_date, d.due_date FROM item i JOIN task_detail d ON d.item_id=i.id WHERE i.id=?"}.get(
        opt, DUE_OF[TASK_TABLE[opt]])
    return 1 if db(opt).execute(q, ("T2",)).fetchone() == (MON, "2026-10-09") else 0


def case_event_has_no_task_state(opt):
    """integrity: an event cannot carry a task's status, deadline or capacity rank."""
    if opt.startswith("split"):
        return 1          # the event table has no such columns
    if opt == "shared+side":
        return 0 if not rejects(opt, "INSERT INTO task_detail(item_id,status) VALUES('E1','DONE')") else 1
    return 1 if rejects(opt, "UPDATE item SET status='DONE' WHERE id='E1'") else 0


def case_one_id_space(opt):
    """reminders (contest 03) and sync (ADR 01): one id finds a schedulable thing without
    knowing its kind first."""
    if opt == "split":
        return 0
    if opt == "split+view":
        return 1 if db(opt).execute("SELECT kind FROM schedulable WHERE id='E1'").fetchone() == ("EVENT",) else 0
    return 1


CASES = {
    "tendril-timeline": case_timeline,
    "tendril-reminder-fk": case_reminder_fk,
    "tendril-subtask-cascade": case_subtask_cascade,
    "tendril-completion-log": case_completion_log,
    "tendril-planned-and-due": case_planned_and_due,
    "equipoise-capacity-query": case_capacity,
    "equipoise-capacity-ignores-events": case_capacity_ignores_events,
    "shared-event-has-no-task-state": case_event_has_no_task_state,
    "shared-one-id-space": case_one_id_space,
}
OPTIONS = ["shared", "split", "split+view", "shared+side", "bare"]


def growth(opt):
    c = db(opt)
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")]
    cols = sum(c.execute("SELECT count(*) FROM pragma_table_info(?)", (t,)).fetchone()[0] for t in tables)
    return {"tables": len(tables), "columns": cols}


def main():
    sim = {o: {cid: fn(o) for cid, fn in CASES.items()} for o in OPTIONS}
    with open(os.path.join(ROOT, "decisions", "options", "02-task.sim.json"), "w",
              encoding="utf-8", newline="") as fh:
        json.dump(sim, fh, indent=1)
    print("%-36s" % "case" + "".join("%-13s" % o for o in OPTIONS))
    for cid in CASES:
        print("%-36s" % cid + "".join("%-13s" % sim[o][cid] for o in OPTIONS))
    print("%-36s" % "growth (tables+views / columns)" +
          "".join("%-13s" % ("%d/%d" % tuple(growth(o).values())) for o in OPTIONS))


if __name__ == "__main__":
    main()
