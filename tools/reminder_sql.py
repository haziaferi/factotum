"""Contest 03 (reminder location): build each candidate in SQLite on top of ADR 02's item table,
load one fixture, and run every owner behaviour as a query or a write the database must refuse.

    python tools/reminder_sql.py    # writes decisions/options/03-reminder.sim.json + prints a table

Options
  dependent      Tendril: every reminder hangs off an item (item_id NOT NULL, FK CASCADE),
                 fire time = item start + offset (anchor time for date-only items)
  standalone     Chronicle/Mnemo: a reminder carries its own text, due time and repeat rule;
                 nothing links it to an item
  optional-link  a reminder EITHER hangs off an item (offset/anchor) OR carries its own due time
                 and repeat rule (CHECK exactly one)
  item-kind      standalone reminders become items of kind REMINDER; every reminder row hangs
                 off an item, so recurrence has one home (the item)
  bare           CONTROL: no FK, no CHECKs
Every option keeps Chronicle's and Mnemo's alert settings (alert kind, nag, sound, vibration,
mode) on the reminder row; they are per alert, not per schedule.
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ITEM = """
  CREATE TABLE item(id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN (%s)),
    title TEXT NOT NULL, start_date TEXT, start_time TEXT, rrule TEXT,
    status TEXT CHECK(status IS NULL OR status IN ('PENDING','DONE','SKIPPED')),
    CHECK(kind<>'EVENT' OR status IS NULL)%s);
"""
ALERT = """alert_kind TEXT NOT NULL DEFAULT 'NOTIFICATION' CHECK(alert_kind IN ('NOTIFICATION','ALARM')),
    nag_repeats INT, nag_minutes INT, sound TEXT, vibration TEXT,
    mode TEXT NOT NULL DEFAULT 'SCHEDULE' CHECK(mode IN ('EASE','SCHEDULE','ALERT'))"""

DDL = {
 "dependent": ITEM % ("'TASK','EVENT'", "") + """
  CREATE TABLE reminder(id TEXT PRIMARY KEY, item_id TEXT NOT NULL REFERENCES item(id) ON DELETE CASCADE,
    offset_min INT NOT NULL DEFAULT 0, anchor_time TEXT, %s);""" % ALERT,
 "standalone": ITEM % ("'TASK','EVENT'", "") + """
  CREATE TABLE reminder(id TEXT PRIMARY KEY, text TEXT NOT NULL, due_at TEXT NOT NULL, rrule TEXT,
    done INT NOT NULL DEFAULT 0, %s);""" % ALERT,
 "optional-link": ITEM % ("'TASK','EVENT'", "") + """
  CREATE TABLE reminder(id TEXT PRIMARY KEY, item_id TEXT REFERENCES item(id) ON DELETE CASCADE,
    offset_min INT NOT NULL DEFAULT 0, anchor_time TEXT,
    text TEXT, due_at TEXT, rrule TEXT, done INT NOT NULL DEFAULT 0, %s,
    CHECK((item_id IS NULL) = (due_at IS NOT NULL)),
    CHECK(item_id IS NULL OR (text IS NULL AND rrule IS NULL)),
    CHECK(item_id IS NOT NULL OR text IS NOT NULL));""" % ALERT,
 "item-kind": ITEM % ("'TASK','EVENT','REMINDER'",
                      ",\n    CHECK(kind<>'REMINDER' OR (start_date IS NOT NULL AND start_time IS NOT NULL))") + """
  CREATE TABLE reminder(id TEXT PRIMARY KEY, item_id TEXT NOT NULL REFERENCES item(id) ON DELETE CASCADE,
    offset_min INT NOT NULL DEFAULT 0, anchor_time TEXT, %s);""" % ALERT,
 "bare": """
  CREATE TABLE item(id TEXT PRIMARY KEY, kind TEXT, title TEXT, start_date TEXT, start_time TEXT,
    rrule TEXT, status TEXT);
  CREATE TABLE reminder(id TEXT PRIMARY KEY, item_id TEXT, offset_min INT, anchor_time TEXT,
    text TEXT, due_at TEXT, rrule TEXT, done INT, alert_kind TEXT, nag_repeats INT, nag_minutes INT,
    sound TEXT, vibration TEXT, mode TEXT);""",
}

MON = "2026-10-05"
BASE = [
 "INSERT INTO item(id,kind,title,start_date,start_time) VALUES('E1','EVENT','standup','%s','10:00')" % MON,
 "INSERT INTO item(id,kind,title,start_date,start_time,status) VALUES('T1','TASK','call','%s','14:00','PENDING')" % MON,
 "INSERT INTO item(id,kind,title,start_date,status) VALUES('T2','TASK','tax form','%s','PENDING')" % MON,
]
LINKED = {  # R1: 5 min before T1; R2: day before T2 at 09:00; R3: 15 min before E1
 "dependent": ["INSERT INTO reminder(id,item_id,offset_min) VALUES('R1','T1',-5)",
               "INSERT INTO reminder(id,item_id,offset_min,anchor_time) VALUES('R2','T2',-1440,'09:00')",
               "INSERT INTO reminder(id,item_id,offset_min) VALUES('R3','E1',-15)"],
}
LINKED["optional-link"] = LINKED["item-kind"] = LINKED["bare"] = LINKED["dependent"]
LINKED["standalone"] = [   # the best a standalone model can do: copy the time in
 "INSERT INTO reminder(id,text,due_at) VALUES('R1','call','%s 13:55')" % MON,
 "INSERT INTO reminder(id,text,due_at) VALUES('R2','tax form','2026-10-04 09:00')",
 "INSERT INTO reminder(id,text,due_at) VALUES('R3','standup','%s 09:45')" % MON,
]
# P1: "take pills", 08:00 daily, belongs to nothing
PILLS = {
 "standalone": ["INSERT INTO reminder(id,text,due_at,rrule) VALUES('P1','take pills','%s 08:00','FREQ=DAILY')" % MON],
 "optional-link": ["INSERT INTO reminder(id,text,due_at,rrule) VALUES('P1','take pills','%s 08:00','FREQ=DAILY')" % MON],
 "item-kind": ["INSERT INTO item(id,kind,title,start_date,start_time,rrule,status) VALUES('IP','REMINDER','take pills','%s','08:00','FREQ=DAILY','PENDING')" % MON,
               "INSERT INTO reminder(id,item_id) VALUES('P1','IP')"],
 "bare": ["INSERT INTO reminder(id,text,due_at,rrule) VALUES('P1','take pills','%s 08:00','FREQ=DAILY')" % MON],
 "dependent": [],   # no way to write it
}

# fire time of every live reminder, ordered; the one query each option's alarm code would run
FIRES = {
 "dependent": """SELECT r.id, datetime(i.start_date||' '||COALESCE(i.start_time, r.anchor_time, '00:00'), r.offset_min||' minutes')
   FROM reminder r JOIN item i ON i.id=r.item_id WHERE i.status IS NULL OR i.status='PENDING' ORDER BY 2, 1""",
 "standalone": "SELECT id, datetime(due_at) FROM reminder WHERE done=0 ORDER BY 2, 1",
 "optional-link": """SELECT r.id, COALESCE(datetime(i.start_date||' '||COALESCE(i.start_time, r.anchor_time, '00:00'), r.offset_min||' minutes'), datetime(r.due_at))
   FROM reminder r LEFT JOIN item i ON i.id=r.item_id
   WHERE (r.item_id IS NULL AND r.done=0)
      OR (r.item_id IS NOT NULL AND (i.status IS NULL OR i.status='PENDING')) ORDER BY 2, 1""",
}
FIRES["item-kind"] = FIRES["dependent"]
FIRES["bare"] = FIRES["optional-link"].replace("r.done=0", "COALESCE(r.done,0)=0")
TIMELINE = "SELECT id FROM item WHERE start_date=? ORDER BY start_time IS NULL, start_time, id"  # ADR 02, unchanged


def db(opt, pills=False):
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys=ON")
    c.executescript(DDL[opt])
    for s in BASE + LINKED[opt] + (PILLS[opt] if pills else []):
        c.execute(s)
    return c


def fires(c, opt):
    return {r[0]: r[1] for r in c.execute(FIRES[opt])}


def refuses(c, sql):
    try:
        c.execute(sql)
        return False
    except sqlite3.IntegrityError:
        return True


MOVE_T1 = "UPDATE item SET start_time='16:00' WHERE id='T1'"
DELETE_T1 = "DELETE FROM item WHERE id='T1'"


def case_follows_item(opt):
    """tendril: '5 minutes before' still means 5 minutes before after the call moves to 16:00."""
    c = db(opt)
    c.execute(MOVE_T1)
    return 1 if fires(c, opt).get("R1") == "%s 15:55:00" % MON else 0


def case_anchor_date_only(opt):
    """tendril: a date-only task, reminded the day before at 09:00."""
    return 1 if fires(db(opt), opt).get("R2") == "2026-10-04 09:00:00" else 0


def case_cascade(opt):
    """tendril: deleting the task removes its reminders."""
    c = db(opt)
    c.execute(DELETE_T1)
    return 1 if c.execute("SELECT count(*) FROM reminder WHERE id='R1'").fetchone()[0] == 0 else 0


def case_quiet_when_done(opt):
    """tendril: a done task's reminders stop."""
    c = db(opt)
    c.execute("UPDATE item SET status='DONE' WHERE id='T1'")
    return 1 if "R1" not in fires(c, opt) else 0


def case_standalone(opt):
    """chronicle + mnemo: 'take pills' at 08:00 exists with no task or event, and fires."""
    if not PILLS[opt]:
        return 0
    return 1 if fires(db(opt, pills=True), opt).get("P1") == "%s 08:00:00" % MON else 0


def case_standalone_repeats(opt):
    """chronicle + mnemo: the standalone reminder carries a daily repeat."""
    if not PILLS[opt]:
        return 0
    c = db(opt, pills=True)
    q = ("SELECT i.rrule FROM reminder r JOIN item i ON i.id=r.item_id WHERE r.id='P1'" if opt == "item-kind"
         else "SELECT rrule FROM reminder WHERE id='P1'")
    return 1 if c.execute(q).fetchone() == ("FREQ=DAILY",) else 0


def case_standalone_done(opt):
    """mnemo: Done on a one-shot standalone keeps the row (history) and stops it firing."""
    if not PILLS[opt]:
        return 0
    c = db(opt, pills=True)
    c.execute("UPDATE item SET status='DONE' WHERE id='IP'" if opt == "item-kind"
              else "UPDATE reminder SET done=1 WHERE id='P1'")
    kept = c.execute("SELECT count(*) FROM reminder WHERE id='P1'").fetchone()[0] == 1
    return 1 if kept and "P1" not in fires(c, opt) else 0


def case_alert_settings(opt):
    """chronicle + mnemo: an ALARM-kind reminder with nag, sound, vibration and mode is stored;
    an unknown alert kind or mode is refused."""
    c = db(opt)
    c.execute("UPDATE reminder SET alert_kind='ALARM', nag_repeats=3, nag_minutes=15, sound='', vibration='0', mode='ALERT' WHERE id='R3'")
    return 1 if refuses(c, "UPDATE reminder SET alert_kind='SIREN' WHERE id='R3'") and \
        refuses(c, "UPDATE reminder SET mode='LOUD' WHERE id='R3'") else 0


def case_no_half_link(opt):
    """integrity: a reminder with neither an item nor a time, or with both, is refused."""
    c = db(opt)
    if opt in ("dependent", "item-kind"):
        return 1 if refuses(c, "INSERT INTO reminder(id,item_id) VALUES('X1',NULL)") else 0
    if opt == "standalone":
        return 1 if refuses(c, "INSERT INTO reminder(id,text,due_at) VALUES('X1','x',NULL)") else 0
    neither = refuses(c, "INSERT INTO reminder(id,text) VALUES('X1','x')")
    both = refuses(c, "INSERT INTO reminder(id,item_id,due_at) VALUES('X2','T1','%s 09:00')" % MON)
    return 1 if neither and both else 0


def case_one_recurrence_home(opt):
    """contest 04: recurrence is stored in exactly one table, so it is encoded exactly once."""
    c = db(opt)
    homes = [t for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'")
             if c.execute("SELECT count(*) FROM pragma_table_info(?) WHERE name='rrule'", (t,)).fetchone()[0]]
    return 1 if len(homes) == 1 else 0


def case_timeline_unchanged(opt):
    """ADR 02: the day timeline query, unchanged, still returns exactly the tasks and events."""
    got = [r[0] for r in db(opt, pills=True).execute(TIMELINE, (MON,))]
    return 1 if got == ["E1", "T1", "T2"] else 0


CASES = {
    "tendril-follows-item": case_follows_item,
    "tendril-anchor-date-only": case_anchor_date_only,
    "tendril-cascade": case_cascade,
    "tendril-quiet-when-done": case_quiet_when_done,
    "chronicle-standalone": case_standalone,
    "chronicle-standalone-repeats": case_standalone_repeats,
    "chronicle-alert-settings": case_alert_settings,
    "mnemo-standalone-done": case_standalone_done,
    "shared-no-half-link": case_no_half_link,
    "shared-one-recurrence-home": case_one_recurrence_home,
    "shared-timeline-unchanged": case_timeline_unchanged,
}
OPTIONS = ["dependent", "standalone", "optional-link", "item-kind", "bare"]


def growth(opt):
    c = db(opt)
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    cols = sum(c.execute("SELECT count(*) FROM pragma_table_info(?)", (t,)).fetchone()[0] for t in tables)
    checks = DDL[opt].count("CHECK(")
    return {"tables": len(tables), "columns": cols, "checks": checks}


def main():
    sim = {o: {cid: fn(o) for cid, fn in CASES.items()} for o in OPTIONS}
    with open(os.path.join(ROOT, "decisions", "options", "03-reminder.sim.json"), "w",
              encoding="utf-8", newline="") as fh:
        json.dump(sim, fh, indent=1)
    print("%-32s" % "case" + "".join("%-15s" % o for o in OPTIONS))
    for cid in CASES:
        print("%-32s" % cid + "".join("%-15s" % sim[o][cid] for o in OPTIONS))
    print("%-32s" % "growth tables/columns/checks" +
          "".join("%-15s" % "/".join(str(v) for v in growth(o).values()) for o in OPTIONS))


if __name__ == "__main__":
    main()
