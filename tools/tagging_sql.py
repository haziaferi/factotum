"""Contest 08 (tagging): build each candidate in SQLite beside the decided item table (ADR 07:
activities are items), trackers, and Tendril's pages and page databases (sole owner), then run
each owner behaviour as a query or a refused write. Every statement is a literal.

    python tools/tagging_sql.py      # writes decisions/options/08-tagging.sim.json + a table

Options
  two-vocabs      keep both: Tendril labels (pages many; habit area and database one) and
                  Chronicle categories (activity and tracker one; colour, scope, order)
  labels-only     Tendril's label everywhere: name + colour; pages many, everything else one
  categories-only Chronicle's category everywhere, one per row, pages included
  one-vocab       one tag table (name, colour, scope, order); pages carry many through a join,
                  items, trackers and databases carry one through a column
  many-everywhere one tag table; every owner carries many through its own join table
  polymorphic     one tag table; one tagging(tag, target_type, target_id) join for every owner,
                  one-per-row enforced by a partial unique index; no FK to the target
  inline          CONTROL: names written into the rows; no vocabulary table
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE = {
 "item": "CREATE TABLE item(id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('TASK','EVENT','REMINDER','HABIT','ACTIVITY')), title TEXT NOT NULL, deleted_at TEXT%s);",
 "tracker": "CREATE TABLE tracker(id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL%s);",
 "page": "CREATE TABLE page(id TEXT PRIMARY KEY, title TEXT NOT NULL%s);",
 "page_database": "CREATE TABLE page_database(id TEXT PRIMARY KEY, name TEXT NOT NULL%s);",
}


def base(item="", tracker="", page="", db=""):
    return "\n".join([BASE["item"] % item, BASE["tracker"] % tracker, BASE["page"] % page, BASE["page_database"] % db])


TAGS = "CREATE TABLE tags(id TEXT PRIMARY KEY, name TEXT NOT NULL, color INT NOT NULL);"
CATEGORY = ("CREATE TABLE category(id TEXT PRIMARY KEY, name TEXT NOT NULL, color INT NOT NULL, "
            "applies_to TEXT NOT NULL CHECK(applies_to IN ('ACTIVITY','TRACKER','BOTH')), sort_order INT NOT NULL);")
TAG = ("CREATE TABLE tag(id TEXT PRIMARY KEY, name TEXT NOT NULL, color INT NOT NULL, "
       "applies_to TEXT NOT NULL CHECK(applies_to IN ('ALL','ACTIVITY','TRACKER')), sort_order INT NOT NULL);")
PAGE_TAG = "CREATE TABLE page_tag(page_id TEXT NOT NULL REFERENCES page(id) ON DELETE CASCADE, tag_id TEXT NOT NULL REFERENCES %s(id) ON DELETE CASCADE, PRIMARY KEY(page_id, tag_id));"

DDL = {
 "two-vocabs": TAGS + CATEGORY + base(
    item=", label_id TEXT REFERENCES tags(id) ON DELETE SET NULL, category_id TEXT REFERENCES category(id) ON DELETE SET NULL",
    tracker=", category_id TEXT REFERENCES category(id) ON DELETE SET NULL",
    db=", label_id TEXT REFERENCES tags(id) ON DELETE SET NULL") + PAGE_TAG % "tags",
 "labels-only": TAGS + base(
    item=", label_id TEXT REFERENCES tags(id) ON DELETE SET NULL",
    tracker=", label_id TEXT REFERENCES tags(id) ON DELETE SET NULL",
    db=", label_id TEXT REFERENCES tags(id) ON DELETE SET NULL") + PAGE_TAG % "tags",
 "categories-only": CATEGORY + base(
    item=", category_id TEXT REFERENCES category(id) ON DELETE SET NULL",
    tracker=", category_id TEXT REFERENCES category(id) ON DELETE SET NULL",
    page=", category_id TEXT REFERENCES category(id) ON DELETE SET NULL",
    db=", category_id TEXT REFERENCES category(id) ON DELETE SET NULL"),
 "one-vocab": TAG + base(
    item=", tag_id TEXT REFERENCES tag(id) ON DELETE SET NULL",
    tracker=", tag_id TEXT REFERENCES tag(id) ON DELETE SET NULL",
    db=", tag_id TEXT REFERENCES tag(id) ON DELETE SET NULL") + PAGE_TAG % "tag",
 "many-everywhere": TAG + base() + PAGE_TAG % "tag" + """
    CREATE TABLE item_tag(item_id TEXT NOT NULL REFERENCES item(id) ON DELETE CASCADE, tag_id TEXT NOT NULL REFERENCES tag(id) ON DELETE CASCADE, PRIMARY KEY(item_id, tag_id));
    CREATE TABLE tracker_tag(tracker_id TEXT NOT NULL REFERENCES tracker(id) ON DELETE CASCADE, tag_id TEXT NOT NULL REFERENCES tag(id) ON DELETE CASCADE, PRIMARY KEY(tracker_id, tag_id));
    CREATE TABLE database_tag(database_id TEXT NOT NULL REFERENCES page_database(id) ON DELETE CASCADE, tag_id TEXT NOT NULL REFERENCES tag(id) ON DELETE CASCADE, PRIMARY KEY(database_id, tag_id));""",
 "polymorphic": TAG + base() + """
    CREATE TABLE tagging(tag_id TEXT NOT NULL REFERENCES tag(id) ON DELETE CASCADE,
      target_type TEXT NOT NULL CHECK(target_type IN ('PAGE','ITEM','TRACKER','DATABASE')), target_id TEXT NOT NULL,
      PRIMARY KEY(tag_id, target_type, target_id));
    CREATE UNIQUE INDEX tagging_one ON tagging(target_type, target_id) WHERE target_type <> 'PAGE';""",
 "inline": base(item=", category_name TEXT", tracker=", category_name TEXT", page=", labels TEXT", db=", label_name TEXT"),
}
OPTIONS = list(DDL)
ONE_VOCAB = ("labels-only", "categories-only", "one-vocab", "many-everywhere", "polymorphic")

# vocabulary: (id, name, color, role, scope, order). role: which vocabulary two-vocabs puts it in.
VOCAB = [("W", "work", 1, "label", "ALL", 3), ("U", "urgent", 2, "label", "ALL", 4),
         ("R", "reading-list", 3, "label", "ALL", 5), ("HE", "Health", 4, "label", "ALL", 6),
         ("HC", "Health", 4, "category", "BOTH", 7),
         ("CH", "Chores", 5, "category", "BOTH", 0), ("L", "Leisure", 6, "category", "BOTH", 1),
         ("B", "Body", 7, "category", "TRACKER", 2)]
# (target kind, target id, tag id)
ASSIGN = [("PAGE", "P1", "W"), ("PAGE", "P1", "U"), ("PAGE", "P2", "R"), ("DATABASE", "D1", "R"),
          ("HABIT", "H1", "HE"), ("ACTIVITY", "A1", "L"), ("ACTIVITY", "A2", "HC"), ("TRACKER", "TR1", "B")]
ROWS = ["INSERT INTO item(id,kind,title) VALUES('H1','HABIT','stretch')",
        "INSERT INTO item(id,kind,title) VALUES('A1','ACTIVITY','Reading')",
        "INSERT INTO item(id,kind,title) VALUES('A2','ACTIVITY','Yoga')",
        "INSERT INTO tracker(id,name,type) VALUES('TR1','weight','NUMBER')",
        "INSERT INTO page(id,title) VALUES('P1','Q4 plan')", "INSERT INTO page(id,title) VALUES('P2','Dune')",
        "INSERT INTO page_database(id,name) VALUES('D1','Books')"]

ADD = {
 ("two-vocabs", "label"): "INSERT INTO tags(id,name,color) VALUES(?,?,?)",
 ("two-vocabs", "category"): "INSERT INTO category(id,name,color,applies_to,sort_order) VALUES(?,?,?,?,?)",
 ("labels-only", None): "INSERT INTO tags(id,name,color) VALUES(?,?,?)",
 ("categories-only", None): "INSERT INTO category(id,name,color,applies_to,sort_order) VALUES(?,?,?,?,?)",
 ("one-vocab", None): "INSERT INTO tag(id,name,color,applies_to,sort_order) VALUES(?,?,?,?,?)",
 ("many-everywhere", None): "INSERT INTO tag(id,name,color,applies_to,sort_order) VALUES(?,?,?,?,?)",
 ("polymorphic", None): "INSERT INTO tag(id,name,color,applies_to,sort_order) VALUES(?,?,?,?,?)",
}
# params (tag_id, target_id)
SET = {
 "two-vocabs": {"PAGE": "INSERT INTO page_tag(tag_id,page_id) VALUES(?,?)", "HABIT": "UPDATE item SET label_id=? WHERE id=?",
                "ACTIVITY": "UPDATE item SET category_id=? WHERE id=?", "TRACKER": "UPDATE tracker SET category_id=? WHERE id=?",
                "DATABASE": "UPDATE page_database SET label_id=? WHERE id=?"},
 "labels-only": {"PAGE": "INSERT INTO page_tag(tag_id,page_id) VALUES(?,?)", "HABIT": "UPDATE item SET label_id=? WHERE id=?",
                 "ACTIVITY": "UPDATE item SET label_id=? WHERE id=?", "TRACKER": "UPDATE tracker SET label_id=? WHERE id=?",
                 "DATABASE": "UPDATE page_database SET label_id=? WHERE id=?"},
 "categories-only": {"PAGE": "UPDATE page SET category_id=? WHERE id=?", "HABIT": "UPDATE item SET category_id=? WHERE id=?",
                     "ACTIVITY": "UPDATE item SET category_id=? WHERE id=?", "TRACKER": "UPDATE tracker SET category_id=? WHERE id=?",
                     "DATABASE": "UPDATE page_database SET category_id=? WHERE id=?"},
 "one-vocab": {"PAGE": "INSERT INTO page_tag(tag_id,page_id) VALUES(?,?)", "HABIT": "UPDATE item SET tag_id=? WHERE id=?",
               "ACTIVITY": "UPDATE item SET tag_id=? WHERE id=?", "TRACKER": "UPDATE tracker SET tag_id=? WHERE id=?",
               "DATABASE": "UPDATE page_database SET tag_id=? WHERE id=?"},
 "many-everywhere": {"PAGE": "INSERT INTO page_tag(tag_id,page_id) VALUES(?,?)", "HABIT": "INSERT INTO item_tag(tag_id,item_id) VALUES(?,?)",
                     "ACTIVITY": "INSERT INTO item_tag(tag_id,item_id) VALUES(?,?)", "TRACKER": "INSERT INTO tracker_tag(tag_id,tracker_id) VALUES(?,?)",
                     "DATABASE": "INSERT INTO database_tag(tag_id,database_id) VALUES(?,?)"},
 "polymorphic": {k: "INSERT INTO tagging(tag_id,target_type,target_id) VALUES(?,'%s',?)" % t for k, t in
                 (("PAGE", "PAGE"), ("HABIT", "ITEM"), ("ACTIVITY", "ITEM"), ("TRACKER", "TRACKER"), ("DATABASE", "DATABASE"))},
 # inline gets a tag NAME in place of an id
 "inline": {"PAGE": "UPDATE page SET labels=coalesce(labels||',','')||? WHERE id=?", "HABIT": "UPDATE item SET category_name=? WHERE id=?",
            "ACTIVITY": "UPDATE item SET category_name=? WHERE id=?", "TRACKER": "UPDATE tracker SET category_name=? WHERE id=?",
            "DATABASE": "UPDATE page_database SET label_name=? WHERE id=?"},
}
PAGE_LABELS = {
 "two-vocabs": "SELECT t.name FROM page_tag j JOIN tags t ON t.id=j.tag_id WHERE j.page_id=? ORDER BY t.name",
 "labels-only": "SELECT t.name FROM page_tag j JOIN tags t ON t.id=j.tag_id WHERE j.page_id=? ORDER BY t.name",
 "categories-only": "SELECT c.name FROM page p JOIN category c ON c.id=p.category_id WHERE p.id=?",
 "one-vocab": "SELECT t.name FROM page_tag j JOIN tag t ON t.id=j.tag_id WHERE j.page_id=? ORDER BY t.name",
 "many-everywhere": "SELECT t.name FROM page_tag j JOIN tag t ON t.id=j.tag_id WHERE j.page_id=? ORDER BY t.name",
 "polymorphic": "SELECT t.name FROM tagging j JOIN tag t ON t.id=j.tag_id WHERE j.target_type='PAGE' AND j.target_id=? ORDER BY t.name",
 "inline": "SELECT labels FROM page WHERE id=?",
}
# (name, color) rows of the one tag an item or tracker carries
ITEM_TAG = {
 "two-vocabs": "SELECT name, color FROM tags WHERE id=(SELECT label_id FROM item WHERE id=?1) UNION ALL SELECT name, color FROM category WHERE id=(SELECT category_id FROM item WHERE id=?1)",
 "labels-only": "SELECT name, color FROM tags WHERE id=(SELECT label_id FROM item WHERE id=?)",
 "categories-only": "SELECT name, color FROM category WHERE id=(SELECT category_id FROM item WHERE id=?)",
 "one-vocab": "SELECT name, color FROM tag WHERE id=(SELECT tag_id FROM item WHERE id=?)",
 "many-everywhere": "SELECT t.name, t.color FROM item_tag j JOIN tag t ON t.id=j.tag_id WHERE j.item_id=?",
 "polymorphic": "SELECT t.name, t.color FROM tagging j JOIN tag t ON t.id=j.tag_id WHERE j.target_type='ITEM' AND j.target_id=?",
 "inline": "SELECT category_name, NULL FROM item WHERE id=? AND category_name IS NOT NULL",
}
DB_MEMBERS = {
 "two-vocabs": "SELECT j.page_id FROM page_database d JOIN page_tag j ON j.tag_id=d.label_id WHERE d.id=? ORDER BY 1",
 "labels-only": "SELECT j.page_id FROM page_database d JOIN page_tag j ON j.tag_id=d.label_id WHERE d.id=? ORDER BY 1",
 "categories-only": "SELECT p.id FROM page_database d JOIN page p ON p.category_id=d.category_id WHERE d.id=? ORDER BY 1",
 "one-vocab": "SELECT j.page_id FROM page_database d JOIN page_tag j ON j.tag_id=d.tag_id WHERE d.id=? ORDER BY 1",
 "many-everywhere": "SELECT j.page_id FROM database_tag d JOIN page_tag j ON j.tag_id=d.tag_id WHERE d.database_id=? ORDER BY 1",
 "polymorphic": "SELECT p.target_id FROM tagging d JOIN tagging p ON p.tag_id=d.tag_id AND p.target_type='PAGE' WHERE d.target_type='DATABASE' AND d.target_id=? ORDER BY 1",
 "inline": "SELECT p.id FROM page_database d JOIN page p ON ','||p.labels||',' LIKE '%,'||d.label_name||',%' WHERE d.id=? ORDER BY 1",
}
ORPHANS = {
 "two-vocabs": "SELECT count(*) FROM page_tag WHERE page_id NOT IN (SELECT id FROM page)",
 "labels-only": "SELECT count(*) FROM page_tag WHERE page_id NOT IN (SELECT id FROM page)",
 "one-vocab": "SELECT count(*) FROM page_tag WHERE page_id NOT IN (SELECT id FROM page)",
 "many-everywhere": "SELECT count(*) FROM page_tag WHERE page_id NOT IN (SELECT id FROM page)",
 "polymorphic": "SELECT count(*) FROM tagging WHERE target_type='PAGE' AND target_id NOT IN (SELECT id FROM page)",
}
ORDERED = {
 "two-vocabs": "SELECT name FROM category ORDER BY sort_order",
 "categories-only": "SELECT name FROM category ORDER BY sort_order",
 "one-vocab": "SELECT name FROM tag ORDER BY sort_order",
 "many-everywhere": "SELECT name FROM tag ORDER BY sort_order",
 "polymorphic": "SELECT name FROM tag ORDER BY sort_order",
}
OFFERED_TO_ACTIVITIES = {
 "two-vocabs": "SELECT name FROM category WHERE applies_to IN ('ACTIVITY','BOTH')",
 "categories-only": "SELECT name FROM category WHERE applies_to IN ('ACTIVITY','BOTH')",
 "one-vocab": "SELECT name FROM tag WHERE applies_to IN ('ACTIVITY','ALL')",
 "many-everywhere": "SELECT name FROM tag WHERE applies_to IN ('ACTIVITY','ALL')",
 "polymorphic": "SELECT name FROM tag WHERE applies_to IN ('ACTIVITY','ALL')",
}
# params (name, color, id)
RENAME = {
 ("two-vocabs", "label"): "UPDATE tags SET name=?, color=? WHERE id=?",
 ("two-vocabs", "category"): "UPDATE category SET name=?, color=? WHERE id=?",
 "labels-only": "UPDATE tags SET name=?, color=? WHERE id=?",
 "categories-only": "UPDATE category SET name=?, color=? WHERE id=?",
 "one-vocab": "UPDATE tag SET name=?, color=? WHERE id=?",
 "many-everywhere": "UPDATE tag SET name=?, color=? WHERE id=?",
 "polymorphic": "UPDATE tag SET name=?, color=? WHERE id=?",
}
DELETE = {
 ("two-vocabs", "label"): "DELETE FROM tags WHERE id=?",
 ("two-vocabs", "category"): "DELETE FROM category WHERE id=?",
 "labels-only": "DELETE FROM tags WHERE id=?",
 "categories-only": "DELETE FROM category WHERE id=?",
 "one-vocab": "DELETE FROM tag WHERE id=?",
 "many-everywhere": "DELETE FROM tag WHERE id=?",
 "polymorphic": "DELETE FROM tag WHERE id=?",
}
ROLE = {v[0]: v[3] for v in VOCAB}
NAME = {v[0]: v[1] for v in VOCAB}


def tid(opt, t):
    """In a one-vocabulary option the two 'Health' rows are the same tag."""
    return "HE" if t == "HC" and opt in ONE_VOCAB else t


def stmt(table, opt, t):
    return table.get((opt, ROLE[t])) or table.get(opt)


def db(opt):
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys=ON")
    c.executescript(DDL[opt])
    for s in ROWS:
        c.execute(s)
    for vid, name, color, role, scope, order in VOCAB:
        if opt == "inline" or tid(opt, vid) != vid:
            continue
        sql = ADD.get((opt, role)) or ADD[(opt, None)]
        if "applies_to" in sql:
            scope = {"ALL": "BOTH"}.get(scope, scope) if "category" in sql else {"BOTH": "ALL"}.get(scope, scope)
            c.execute(sql, (vid, name, color, scope, order))
        else:
            c.execute(sql, (vid, name, color))
    for kind, target, t in ASSIGN:
        try:
            c.execute(SET[opt][kind], (NAME[t] if opt == "inline" else tid(opt, t), target))
        except sqlite3.IntegrityError:
            pass
    return c


def page_labels(c, opt, page):
    rows = [r[0] for r in c.execute(PAGE_LABELS[opt], (page,))]
    if opt == "inline":
        return sorted(rows[0].split(",")) if rows and rows[0] else []
    return rows


def case_page_many(opt):
    """tendril: a page carries 'work' and 'urgent' at once (PageLabel is many-to-many, Label.kt:43)."""
    return 1 if page_labels(db(opt), opt, "P1") == ["urgent", "work"] else 0


def case_habit_area(opt):
    """tendril: a habit carries one label, its planner area 'Health' (Habit.kt:88)."""
    return 1 if db(opt).execute(ITEM_TAG[opt], ("H1",)).fetchall() in ([("Health", 4)], [("Health", None)]) else 0


def case_doorway(opt):
    """tendril: the 'Books' database's members are the pages carrying its label (LabelMembership.kt:65)."""
    return 1 if [r[0] for r in db(opt).execute(DB_MEMBERS[opt], ("D1",))] == ["P2"] else 0


def case_page_delete(opt):
    """tendril: deleting a page leaves no label rows pointing at it (page_tags FK CASCADE, Label.kt:48-49)."""
    c = db(opt)
    c.execute("DELETE FROM page WHERE id='P1'")
    q = ORPHANS.get(opt)
    return 1 if q is None or c.execute(q).fetchone()[0] == 0 else 0


def case_one_per_row(opt):
    """chronicle: an activity is in one category; giving it a second replaces or is refused, never both
    (one nullable categoryId, ActivityEntity.kt:32)."""
    c = db(opt)
    try:
        c.execute(SET[opt]["ACTIVITY"], ("Chores" if opt == "inline" else "CH", "A1"))
    except sqlite3.IntegrityError:
        pass
    return 1 if len(c.execute(ITEM_TAG[opt], ("A1",)).fetchall()) == 1 else 0


def case_rename(opt):
    """chronicle: renaming and recolouring 'Leisure' once shows on every member (CategoryRepository)."""
    c = db(opt)
    sql = stmt(RENAME, opt, "L")
    if not sql:
        return 0
    c.execute(sql, ("Hobbies", 9, "L"))
    return 1 if c.execute(ITEM_TAG[opt], ("A1",)).fetchall() == [("Hobbies", 9)] else 0


def case_delete_clears(opt):
    """chronicle: deleting a category keeps its activities, uncategorised (SET NULL, ActivityEntity.kt:21)."""
    c = db(opt)
    sql = stmt(DELETE, opt, "L")
    if not sql:
        return 0
    c.execute(sql, ("L",))
    alive = c.execute("SELECT count(*) FROM item WHERE id='A1'").fetchone()[0]
    return 1 if alive == 1 and c.execute(ITEM_TAG[opt], ("A1",)).fetchall() == [] else 0


def case_order(opt):
    """chronicle: categories list in their chosen order Chores, Leisure, Body (sortOrder, CoreDao.kt:15)."""
    q = ORDERED.get(opt)
    if not q:
        return 0
    names = [r[0] for r in db(opt).execute(q) if r[0] in ("Chores", "Leisure", "Body")]
    return 1 if names == ["Chores", "Leisure", "Body"] else 0


def case_scope(opt):
    """chronicle: 'Body' is scoped to trackers, so the activity picker offers Leisure but not Body (Enums.kt:76)."""
    q = OFFERED_TO_ACTIVITIES.get(opt)
    if not q:
        return 0
    names = {r[0] for r in db(opt).execute(q)}
    return 1 if "Leisure" in names and "Body" not in names else 0


def case_one_vocabulary(opt):
    """shared: 'Health' as the habit's area and the Yoga activity's category is one tag: renaming it
    once renames both."""
    c = db(opt)
    sql = stmt(RENAME, opt, "HE")
    if not sql:
        return 0
    c.execute(sql, ("Wellbeing", 4, "HE"))
    return 1 if c.execute(ITEM_TAG[opt], ("A2",)).fetchall() == [("Wellbeing", 4)] else 0


CASES = {
    "tendril-page-many-labels": ("tendril", case_page_many),
    "tendril-habit-area": ("tendril", case_habit_area),
    "tendril-database-doorway": ("tendril", case_doorway),
    "tendril-page-delete-no-orphans": ("tendril", case_page_delete),
    "chronicle-one-category-per-row": ("chronicle", case_one_per_row),
    "chronicle-rename-recolour-once": ("chronicle", case_rename),
    "chronicle-delete-keeps-members": ("chronicle", case_delete_clears),
    "chronicle-category-order": ("chronicle", case_order),
    "chronicle-applies-to-scope": ("chronicle", case_scope),
    "shared-one-vocabulary": ("shared", case_one_vocabulary),
}


def cols(c, table):
    return [r[0] for r in c.execute("SELECT name FROM pragma_table_info(?)", (table,))]


def tables(c):
    return [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]


def growth(opt):
    c = db(opt)
    idx = c.execute("SELECT count(*) FROM sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchone()[0]
    return {"tables": len(tables(c)), "columns": sum(len(cols(c, t)) for t in tables(c)), "indexes": idx}


def main():
    sim = {o: {cid: fn(o) for cid, (_, fn) in CASES.items()} for o in OPTIONS}
    with open(os.path.join(ROOT, "decisions", "options", "08-tagging.sim.json"), "w",
              encoding="utf-8", newline="") as fh:
        json.dump(sim, fh, indent=1)
    print("%-32s" % "case" + "".join("%-16s" % o for o in OPTIONS))
    for cid in CASES:
        print("%-32s" % cid + "".join("%-16s" % sim[o][cid] for o in OPTIONS))
    print("%-32s" % "growth tbl/col/idx" + "".join("%-16s" % "/".join(str(v) for v in growth(o).values()) for o in OPTIONS))


if __name__ == "__main__":
    main()
