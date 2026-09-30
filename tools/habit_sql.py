"""Contest 06 (habit): build each candidate in SQLite beside the decided tables (ADR 02 item,
ADR 03 reminder, ADR 04 recurrence on item) and Chronicle's trackers-and-goals module (sole
owner, moves across as-is), then run each owner behaviour as a query or a refused write.

    python tools/habit_sql.py        # writes decisions/options/06-habit.sim.json + a table

Owner rule (2026-09-30): in Habits, no stored or displayed streak and no missed-day count.

Options
  habit-table     Tendril minus streak columns: habit table with its own cadence, time, amounts,
                  pause window; habit_completion log
  trackers-only   Chronicle: no habit; a habit is a BOOLEAN/NUMBER tracker; no cadence, no pause
  item-kind       a habit is an item of kind HABIT: cadence = ADR 04 recurrence, reminder = ADR 03
                  reminder row; completions in the item completion log with a value
  item+tracker    item-kind, plus the habit item links a tracker: its check-ins ARE that tracker's
                  readings (one log); a daily amount is a Chronicle goal on the tracker
  with-streak     CONTROL: habit-table plus Tendril's streak and lastCompletedDate columns
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TRACKERS = """
  CREATE TABLE tracker(id TEXT PRIMARY KEY, name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('NUMBER','BOOLEAN','RATING','CHOICE')), deleted_at TEXT);
  CREATE TABLE tracker_reading(id TEXT PRIMARY KEY, tracker_id TEXT NOT NULL REFERENCES tracker(id) ON DELETE CASCADE,
    at TEXT NOT NULL, bool_value INT, rating INT, number_value REAL, deleted_at TEXT);
  CREATE TABLE goal(id TEXT PRIMARY KEY, tracker_id TEXT REFERENCES tracker(id) ON DELETE CASCADE,
    period TEXT NOT NULL CHECK(period IN ('DAY','WEEK','MONTH')), value REAL NOT NULL);
"""
ITEM_KINDS = "'TASK','EVENT','REMINDER'"


def item(kinds, extra=""):
    return """
  CREATE TABLE item(id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN (%s)), title TEXT NOT NULL,
    start_date TEXT, start_time TEXT, rrule TEXT, status TEXT, deleted_at TEXT%s);
  CREATE TABLE completion(item_id TEXT NOT NULL REFERENCES item(id) ON DELETE CASCADE,
    occurrence TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('DONE','SKIPPED')),
    value REAL, checked_at TEXT, deleted_at TEXT);
  CREATE TABLE reminder(id TEXT PRIMARY KEY, item_id TEXT NOT NULL REFERENCES item(id) ON DELETE CASCADE,
    offset_min INT NOT NULL DEFAULT 0);
""" % (kinds, extra)


HABIT_TABLE = """
  CREATE TABLE habit(id TEXT PRIMARY KEY, title TEXT NOT NULL, rrule TEXT, time TEXT,
    amount_per_checkin REAL, daily_amount REAL, pause_from TEXT, pause_until TEXT, deleted_at TEXT%s);
  CREATE TABLE habit_completion(id TEXT PRIMARY KEY, habit_id TEXT NOT NULL REFERENCES habit(id) ON DELETE CASCADE,
    date TEXT NOT NULL, checked_at TEXT NOT NULL, value REAL, occurrence_key TEXT, deleted_at TEXT);
"""
HABIT_ITEM_COLS = """, amount_per_checkin REAL, daily_amount REAL, pause_from TEXT, pause_until TEXT,
    CHECK(kind='HABIT' OR (amount_per_checkin IS NULL AND daily_amount IS NULL AND pause_from IS NULL AND pause_until IS NULL))"""
HABIT_TRACKER_COLS = """, tracker_id TEXT REFERENCES tracker(id), pause_from TEXT, pause_until TEXT,
    CHECK((kind='HABIT') = (tracker_id IS NOT NULL)),
    CHECK(kind='HABIT' OR (pause_from IS NULL AND pause_until IS NULL))"""

DDL = {
 "habit-table": item(ITEM_KINDS) + TRACKERS + HABIT_TABLE % "",
 "trackers-only": item(ITEM_KINDS) + TRACKERS,
 "item-kind": item(ITEM_KINDS + ",'HABIT'", HABIT_ITEM_COLS) + TRACKERS,
 "item+tracker": TRACKERS + item(ITEM_KINDS + ",'HABIT'", HABIT_TRACKER_COLS),
 "with-streak": item(ITEM_KINDS) + TRACKERS + HABIT_TABLE % ", streak INT NOT NULL DEFAULT 0, last_completed_date TEXT",
}

# fixture: "water", 8 glasses a day, every 2 days from Mon, reminder 08:00, paused 12-14 Oct;
# "meditate", a yes/no habit, logged through the Trackers screen on 3 mornings
FIX = {
 "habit-table": [
  "INSERT INTO habit(id,title,rrule,time,amount_per_checkin,daily_amount,pause_from,pause_until) VALUES('H1','water','FREQ=DAILY;INTERVAL=2','08:00',1,8,'2026-10-12','2026-10-14')",
  "INSERT INTO habit(id,title,rrule) VALUES('H2','meditate','FREQ=DAILY')",
  "INSERT INTO tracker VALUES('TM','meditated','BOOLEAN',NULL)",
 ] + ["INSERT INTO habit_completion VALUES('W%d','H1','2026-10-05','2026-10-05T%02d:00',1,NULL,NULL)" % (i, 9 + i) for i in range(8)],
 "trackers-only": [
  "INSERT INTO tracker VALUES('TW','water','NUMBER',NULL)", "INSERT INTO goal VALUES('G1','TW','DAY',8)",
  "INSERT INTO tracker VALUES('TM','meditated','BOOLEAN',NULL)",
 ] + ["INSERT INTO tracker_reading(id,tracker_id,at,number_value) VALUES('W%d','TW','2026-10-05T%02d:00',1)" % (i, 9 + i) for i in range(8)],
 "item-kind": [
  "INSERT INTO item(id,kind,title,start_date,start_time,rrule,amount_per_checkin,daily_amount,pause_from,pause_until) VALUES('H1','HABIT','water','2026-10-05','08:00','FREQ=DAILY;INTERVAL=2',1,8,'2026-10-12','2026-10-14')",
  "INSERT INTO item(id,kind,title,start_date,start_time,rrule) VALUES('H2','HABIT','meditate','2026-10-05','07:00','FREQ=DAILY')",
  "INSERT INTO reminder(id,item_id) VALUES('R1','H1')",
  "INSERT INTO tracker VALUES('TM','meditated','BOOLEAN',NULL)",
 ] + ["INSERT INTO completion VALUES('H1','2026-10-05','DONE',1,'2026-10-05T%02d:00',NULL)" % (9 + i) for i in range(8)],
 "item+tracker": [
  "INSERT INTO tracker VALUES('TW','water','NUMBER',NULL)", "INSERT INTO goal VALUES('G1','TW','DAY',8)",
  "INSERT INTO tracker VALUES('TM','meditated','BOOLEAN',NULL)",
  "INSERT INTO item(id,kind,title,start_date,start_time,rrule,tracker_id,pause_from,pause_until) VALUES('H1','HABIT','water','2026-10-05','08:00','FREQ=DAILY;INTERVAL=2','TW','2026-10-12','2026-10-14')",
  "INSERT INTO item(id,kind,title,start_date,start_time,rrule,tracker_id) VALUES('H2','HABIT','meditate','2026-10-05','07:00','FREQ=DAILY','TM')",
  "INSERT INTO reminder(id,item_id) VALUES('R1','H1')",
 ] + ["INSERT INTO tracker_reading(id,tracker_id,at,number_value) VALUES('W%d','TW','2026-10-05T%02d:00',1)" % (i, 9 + i) for i in range(8)],
}
FIX["with-streak"] = FIX["habit-table"]
MEDITATE_VIA_TRACKERS = ["INSERT INTO tracker_reading(id,tracker_id,at,bool_value) VALUES('M%d','TM','2026-10-0%dT07:10',1)" % (i, 5 + i) for i in range(3)]


def db(opt):
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys=ON")
    c.executescript(DDL[opt])
    for s in FIX[opt]:
        c.execute(s)
    return c


def cols(c, table):
    return [r[0] for r in c.execute("SELECT name FROM pragma_table_info(?)", (table,))]


def tables(c):
    return [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]


# How much water today, and the day's target, in each model
WATER = {
 "habit-table": "SELECT (SELECT sum(value) FROM habit_completion WHERE habit_id='H1' AND date='2026-10-05' AND deleted_at IS NULL), (SELECT daily_amount FROM habit WHERE id='H1')",
 "trackers-only": "SELECT (SELECT sum(number_value) FROM tracker_reading WHERE tracker_id='TW' AND substr(at,1,10)='2026-10-05' AND deleted_at IS NULL), (SELECT value FROM goal WHERE tracker_id='TW' AND period='DAY')",
 "item-kind": "SELECT (SELECT sum(value) FROM completion WHERE item_id='H1' AND occurrence='2026-10-05' AND deleted_at IS NULL), (SELECT daily_amount FROM item WHERE id='H1')",
 "item+tracker": "SELECT (SELECT sum(r.number_value) FROM tracker_reading r JOIN item i ON i.tracker_id=r.tracker_id WHERE i.id='H1' AND substr(r.at,1,10)='2026-10-05' AND r.deleted_at IS NULL), (SELECT g.value FROM goal g JOIN item i ON i.tracker_id=g.tracker_id WHERE i.id='H1' AND g.period='DAY')",
}
WATER["with-streak"] = WATER["habit-table"]
UNDO_ONE = {
 "habit-table": "UPDATE habit_completion SET deleted_at='x' WHERE id='W0'",
 "trackers-only": "UPDATE tracker_reading SET deleted_at='x' WHERE id='W0'",
 "item-kind": "UPDATE completion SET deleted_at='x' WHERE rowid=(SELECT min(rowid) FROM completion)",
 "item+tracker": "UPDATE tracker_reading SET deleted_at='x' WHERE id='W0'",
}
UNDO_ONE["with-streak"] = UNDO_ONE["habit-table"]
# Chronicle's HabitPresence input for "meditate": distinct days with a live yes
PRESENCE = {
 "habit-table": "SELECT count(DISTINCT date) FROM habit_completion WHERE habit_id='H2' AND deleted_at IS NULL",
 "trackers-only": "SELECT count(DISTINCT substr(at,1,10)) FROM tracker_reading WHERE tracker_id='TM' AND bool_value=1 AND deleted_at IS NULL",
 "item-kind": "SELECT count(DISTINCT occurrence) FROM completion WHERE item_id='H2' AND deleted_at IS NULL",
 "item+tracker": "SELECT count(DISTINCT substr(r.at,1,10)) FROM tracker_reading r JOIN item i ON i.tracker_id=r.tracker_id WHERE i.id='H2' AND r.bool_value=1 AND r.deleted_at IS NULL",
}
PRESENCE["with-streak"] = PRESENCE["habit-table"]


def case_cadence(opt):
    """tendril: 'every 2 days' with a time of day is stored with the habit."""
    c = db(opt)
    q = {"habit-table": "SELECT rrule, time FROM habit WHERE id='H1'", "with-streak": "SELECT rrule, time FROM habit WHERE id='H1'",
         "item-kind": "SELECT rrule, start_time FROM item WHERE id='H1'", "item+tracker": "SELECT rrule, start_time FROM item WHERE id='H1'"}.get(opt)
    return 1 if q and c.execute(q).fetchone() == ("FREQ=DAILY;INTERVAL=2", "08:00") else 0


def case_counting(opt):
    """tendril: 8 one-glass check-ins meet an 8-glass day; undoing one leaves 7 of 8."""
    c = db(opt)
    if c.execute(WATER[opt]).fetchone() != (8.0, 8.0):
        return 0
    c.execute(UNDO_ONE[opt])
    return 1 if c.execute(WATER[opt]).fetchone() == (7.0, 8.0) else 0


def case_pause(opt):
    """tendril: a pause window is stored, and only on habits."""
    c = db(opt)
    t = "habit" if opt in ("habit-table", "with-streak") else "item"
    if "pause_from" not in cols(c, t):
        return 0
    if t == "item":
        try:
            c.execute("INSERT INTO item(id,kind,title,pause_from) VALUES('X','TASK','x','2026-10-12')")
            return 0
        except sqlite3.IntegrityError:
            return 1
    return 1


def case_one_reminder_path(opt):
    """ADR 03: a habit's 08:00 reminder is a row in the one reminder table, not a second mechanism."""
    c = db(opt)
    if opt not in ("item-kind", "item+tracker"):
        return 0
    return 1 if c.execute("SELECT count(*) FROM reminder r JOIN item i ON i.id=r.item_id WHERE i.kind='HABIT'").fetchone()[0] == 1 else 0


def case_presence(opt):
    """chronicle: 3 mornings of 'meditated: yes' logged on the Trackers screen show as 3 presences
    for the meditate habit, with no second entry."""
    c = db(opt)
    for s in MEDITATE_VIA_TRACKERS:
        c.execute(s)
    return 1 if c.execute(PRESENCE[opt]).fetchone()[0] == 3 else 0


def case_no_streak(opt):
    """owner rule 0.14 in Habits: no streak, last-completed or missed column anywhere."""
    c = db(opt)
    banned = [(t, col) for t in tables(c) for col in cols(c, t)
              if any(w in col for w in ("streak", "missed", "last_completed"))]
    return 0 if banned else 1


def case_one_recurrence_home(opt):
    """ADR 03/04: recurrence is stored in exactly one table."""
    c = db(opt)
    return 1 if sum("rrule" in cols(c, t) for t in tables(c)) == 1 else 0


CASES = {
    "tendril-cadence-and-time": ("tendril", case_cadence),
    "tendril-counting-and-undo": ("tendril", case_counting),
    "tendril-pause-window": ("tendril", case_pause),
    "chronicle-tracker-presence": ("chronicle", case_presence),
    "owner-no-streak": ("owner", case_no_streak),
    "shared-one-reminder-path": ("shared", case_one_reminder_path),
    "shared-one-recurrence-home": ("shared", case_one_recurrence_home),
}
OPTIONS = ["habit-table", "trackers-only", "item-kind", "item+tracker", "with-streak"]


def growth(opt):
    c = db(opt)
    return {"tables": len(tables(c)), "columns": sum(len(cols(c, t)) for t in tables(c))}


def main():
    sim = {o: {cid: fn(o) for cid, (_, fn) in CASES.items()} for o in OPTIONS}
    with open(os.path.join(ROOT, "decisions", "options", "06-habit.sim.json"), "w",
              encoding="utf-8", newline="") as fh:
        json.dump(sim, fh, indent=1)
    print("%-28s" % "case" + "".join("%-15s" % o for o in OPTIONS))
    for cid in CASES:
        print("%-28s" % cid + "".join("%-15s" % sim[o][cid] for o in OPTIONS))
    print("%-28s" % "growth tables/columns" + "".join("%-15s" % "/".join(str(v) for v in growth(o).values()) for o in OPTIONS))


if __name__ == "__main__":
    main()
