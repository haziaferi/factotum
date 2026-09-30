"""Contest 10 (full-text search): build each candidate as real SQLite FTS4 tables beside the
sources the decisions made searchable (pages and blocks, items of every kind, trackers, tracker
readings, time spans), then run each owner behaviour as a search.

    python tools/search_sql.py       # writes decisions/options/10-search.sim.json + a table

Axes: layout (one table with a kind column / one table per kind / Tendril's two plus Chronicle's
one), tokenizer (simple / unicode61), upkeep (SQLite triggers / application code on the
repository write path). A sync import is a raw write that bypasses the repository.

Options
  two-indexes        as-is: Tendril's page_fts + block_fts (simple, app code) beside Chronicle's
                     search_fts (unicode61, triggers) for the other kinds
  tendril-all        Tendril's way for every kind: a table per kind, simple, app code
  chronicle-all      Chronicle's way for every kind: one search_fts(text, kind, row_key), unicode61, triggers
  one-index-app      one search_fts, unicode61, maintained by app code
  per-kind-triggers  a table per kind, unicode61, triggers
  like-only          CONTROL: no index; LIKE over every source table
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCES = """
  CREATE TABLE page(id TEXT PRIMARY KEY, title TEXT NOT NULL, deleted_at TEXT);
  CREATE TABLE block(id TEXT PRIMARY KEY, page_id TEXT NOT NULL REFERENCES page(id), content TEXT NOT NULL, deleted_at TEXT);
  CREATE TABLE item(id TEXT PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL, deleted_at TEXT);
  CREATE TABLE tracker(id TEXT PRIMARY KEY, name TEXT NOT NULL, deleted_at TEXT);
  CREATE TABLE tracker_reading(id TEXT PRIMARY KEY, tracker_id TEXT NOT NULL, note TEXT, deleted_at TEXT);
  CREATE TABLE time_span(id TEXT PRIMARY KEY, item_id TEXT NOT NULL, comment TEXT, deleted_at TEXT);
"""
# kind -> (table, text column)
KINDS = {"PAGE": ("page", "title"), "BLOCK": ("block", "content"), "ITEM": ("item", "title"),
         "TRACKER": ("tracker", "name"), "READING": ("tracker_reading", "note"), "SPAN": ("time_span", "comment")}
TENDRIL_KINDS = ("PAGE", "BLOCK")


def fts_one(tok):
    return "CREATE VIRTUAL TABLE search_fts USING fts4(text, kind, row_key, tokenize=%s, notindexed=kind, notindexed=row_key);" % tok


def fts_kind(kind, tok):
    return "CREATE VIRTUAL TABLE fts_%s USING fts4(text, row_key, tokenize=%s, notindexed=row_key);" % (kind.lower(), tok)


def triggers_one(kinds):
    out = []
    for k in kinds:
        t, col = KINDS[k]
        ins = "INSERT INTO search_fts(text, kind, row_key) SELECT NEW.%s, '%s', NEW.id WHERE NEW.deleted_at IS NULL AND NEW.%s IS NOT NULL;" % (col, k, col)
        dele = "DELETE FROM search_fts WHERE kind='%s' AND row_key=OLD.id;" % k
        out += ["CREATE TRIGGER fts_%s_ai AFTER INSERT ON %s BEGIN %s END;" % (t, t, ins),
                "CREATE TRIGGER fts_%s_au AFTER UPDATE ON %s BEGIN %s %s END;" % (t, t, dele, ins),
                "CREATE TRIGGER fts_%s_ad AFTER DELETE ON %s BEGIN %s END;" % (t, t, dele)]
    return "\n".join(out)


def triggers_kind(kinds):
    out = []
    for k in kinds:
        t, col = KINDS[k]
        f = "fts_" + k.lower()
        ins = "INSERT INTO %s(text, row_key) SELECT NEW.%s, NEW.id WHERE NEW.deleted_at IS NULL AND NEW.%s IS NOT NULL;" % (f, col, col)
        dele = "DELETE FROM %s WHERE row_key=OLD.id;" % f
        out += ["CREATE TRIGGER %s_ai AFTER INSERT ON %s BEGIN %s END;" % (f, t, ins),
                "CREATE TRIGGER %s_au AFTER UPDATE ON %s BEGIN %s %s END;" % (f, t, dele, ins),
                "CREATE TRIGGER %s_ad AFTER DELETE ON %s BEGIN %s END;" % (f, t, dele)]
    return "\n".join(out)


REST = [k for k in KINDS if k not in TENDRIL_KINDS]
DDL = {
 "two-indexes": SOURCES + "".join(fts_kind(k, "simple") for k in TENDRIL_KINDS) + fts_one("unicode61") + triggers_one(REST),
 "tendril-all": SOURCES + "".join(fts_kind(k, "simple") for k in KINDS),
 "chronicle-all": SOURCES + fts_one("unicode61") + triggers_one(KINDS),
 "one-index-app": SOURCES + fts_one("unicode61"),
 "per-kind-triggers": SOURCES + "".join(fts_kind(k, "unicode61") for k in KINDS) + triggers_kind(KINDS),
 "like-only": SOURCES,
}
OPTIONS = list(DDL)
# which kinds each option indexes from application code (on the repository write path)
APP_KINDS = {"two-indexes": TENDRIL_KINDS, "tendril-all": tuple(KINDS), "one-index-app": tuple(KINDS)}

# literal re-index statements, one per (layout, kind); params (id, id)
REINDEX_ONE = {k: ("DELETE FROM search_fts WHERE kind='%s' AND row_key=?1; "
                   "INSERT INTO search_fts(text, kind, row_key) SELECT %s, '%s', id FROM %s WHERE id=?1 AND deleted_at IS NULL AND %s IS NOT NULL"
                   % (k, c, k, t, c)) for k, (t, c) in KINDS.items()}
REINDEX_KIND = {k: ("DELETE FROM fts_%s WHERE row_key=?1; "
                    "INSERT INTO fts_%s(text, row_key) SELECT %s, id FROM %s WHERE id=?1 AND deleted_at IS NULL AND %s IS NOT NULL"
                    % (k.lower(), k.lower(), c, t, c)) for k, (t, c) in KINDS.items()}
# searches: list of (kind or None, sql); a None kind means the table carries its own kind column
SEARCH = {
 "two-indexes": [("PAGE", "SELECT 'PAGE', row_key FROM fts_page WHERE fts_page MATCH ?"),
                 ("BLOCK", "SELECT 'BLOCK', row_key FROM fts_block WHERE fts_block MATCH ?"),
                 (None, "SELECT kind, row_key FROM search_fts WHERE search_fts MATCH ?")],
 "chronicle-all": [(None, "SELECT kind, row_key FROM search_fts WHERE search_fts MATCH ?")],
 "one-index-app": [(None, "SELECT kind, row_key FROM search_fts WHERE search_fts MATCH ?")],
 "like-only": [(k, "SELECT '%s', id FROM %s WHERE deleted_at IS NULL AND %s LIKE '%%' || ? || '%%'" % (k, t, c))
               for k, (t, c) in KINDS.items()],
}
for _o in ("tendril-all", "per-kind-triggers"):
    SEARCH[_o] = [(k, "SELECT '%s', row_key FROM fts_%s WHERE fts_%s MATCH ?" % (k, k.lower(), k.lower())) for k in KINDS]
SNIPPET = {
 "two-indexes": "SELECT snippet(fts_block, '[', ']', '...') FROM fts_block WHERE fts_block MATCH ?",
 "tendril-all": "SELECT snippet(fts_block, '[', ']', '...') FROM fts_block WHERE fts_block MATCH ?",
 "chronicle-all": "SELECT snippet(search_fts, '[', ']', '...') FROM search_fts WHERE search_fts MATCH ?",
 "one-index-app": "SELECT snippet(search_fts, '[', ']', '...') FROM search_fts WHERE search_fts MATCH ?",
 "per-kind-triggers": "SELECT snippet(fts_block, '[', ']', '...') FROM fts_block WHERE fts_block MATCH ?",
}

FIXTURE = [
 ("PAGE", "INSERT INTO page VALUES('P1','Dune',NULL)", "P1"),
 ("BLOCK", "INSERT INTO block VALUES('B1','P1','The spice and quantum physics',NULL)", "B1"),
 ("BLOCK", "INSERT INTO block VALUES('B2','P1','Mi chiedo perché no',NULL)", "B2"),
 ("PAGE", "INSERT INTO page VALUES('P2','Stretching',NULL)", "P2"),
 ("BLOCK", "INSERT INTO block VALUES('B3','P2','yoga notes',NULL)", "B3"),
 ("ITEM", "INSERT INTO item VALUES('A2','ACTIVITY','Yoga',NULL)", "A2"),
 ("ITEM", "INSERT INTO item VALUES('R1','REMINDER','buy yoga mat',NULL)", "R1"),
 ("TRACKER", "INSERT INTO tracker VALUES('TR1','yoga minutes',NULL)", "TR1"),
 ("READING", "INSERT INTO tracker_reading VALUES('E1','TR1','yoga class, felt good',NULL)", "E1"),
 ("SPAN", "INSERT INTO time_span VALUES('S1','A2','yoga flow',NULL)", "S1"),
]


def repo_write(c, opt, kind, sql, rid):
    """A write through the repository: app-code options re-index the row afterwards."""
    c.execute(sql)
    if kind in APP_KINDS.get(opt, ()):
        stmts = (REINDEX_ONE if opt == "one-index-app" else REINDEX_KIND)[kind]
        for s in stmts.split("; "):
            c.execute(s, (rid,))


def db(opt):
    c = sqlite3.connect(":memory:")
    c.executescript(DDL[opt])
    for kind, sql, rid in FIXTURE:
        repo_write(c, opt, kind, sql, rid)
    return c


def search(c, opt, term):
    """(hits as a set of (kind, row_key), number of queries it took)."""
    q = term if opt == "like-only" else term + "*"
    hits = set()
    for _, sql in SEARCH[opt]:
        hits |= {(r[0], r[1]) for r in c.execute(sql, (q,))}
    return hits, len(SEARCH[opt])


def case_snippet(opt):
    """tendril: 'quantum' finds block B1 of 'Dune' with a highlighted snippet (BlockFts.kt:43)."""
    c = db(opt)
    hits, _ = search(c, opt, "quantum")
    if ("BLOCK", "B1") not in hits or opt not in SNIPPET:
        return 0
    return 1 if any("[quantum]" in r[0] for r in c.execute(SNIPPET[opt], ("quantum*",))) else 0


def case_title_and_body(opt):
    """tendril: a page is found by a word of its title and by a word of its body (PageContentRepository.kt:37)."""
    c = db(opt)
    return 1 if ("PAGE", "P1") in search(c, opt, "dune")[0] and ("BLOCK", "B1") in search(c, opt, "spice")[0] else 0


def case_any_write_path(opt):
    """chronicle: a row written by any path, a sync import included, is found at once (SearchFts.kt:21)."""
    c = db(opt)
    c.execute("INSERT INTO tracker_reading VALUES('E9','TR1','knee pain after run',NULL)")
    c.execute("INSERT INTO block VALUES('B9','P2','knee exercises',NULL)")
    hits, _ = search(c, opt, "knee")
    return 1 if {("READING", "E9"), ("BLOCK", "B9")} <= hits else 0


def case_accents(opt):
    """chronicle's tokenizer (unicode61, SearchFts.kt:31): 'perche' finds 'perché' in a page."""
    return 1 if ("BLOCK", "B2") in search(db(opt), opt, "perche")[0] else 0


def case_all_kinds(opt):
    """chronicle: 'yoga' finds the activity, the reminder, the tracker, the reading note and the
    session comment (SearchRepository.kt:21)."""
    want = {("ITEM", "A2"), ("ITEM", "R1"), ("TRACKER", "TR1"), ("READING", "E1"), ("SPAN", "S1")}
    return 1 if want <= search(db(opt), opt, "yoga")[0] else 0


def case_tombstone(opt):
    """chronicle: a tombstoned reminder leaves the results (SearchFts.kt:68)."""
    c = db(opt)
    repo_write(c, opt, "ITEM", "UPDATE item SET deleted_at='x' WHERE id='R1'", "R1")
    return 1 if ("ITEM", "R1") not in search(c, opt, "yoga")[0] else 0


def case_one_search(opt):
    """shared: one query over one index returns the page block, the items, the reading and the span."""
    hits, n = search(db(opt), opt, "yoga")
    return 1 if n == 1 and {("BLOCK", "B3"), ("ITEM", "A2"), ("SPAN", "S1")} <= hits else 0


CASES = {
    "tendril-block-snippet": ("tendril", case_snippet),
    "tendril-title-and-body": ("tendril", case_title_and_body),
    "chronicle-any-write-path": ("chronicle", case_any_write_path),
    "chronicle-accents-folded": ("chronicle", case_accents),
    "chronicle-all-kinds": ("chronicle", case_all_kinds),
    "chronicle-tombstone-leaves": ("chronicle", case_tombstone),
    "shared-one-search": ("shared", case_one_search),
}


def growth(opt):
    c = db(opt)
    fts = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND sql LIKE 'CREATE VIRTUAL%'")]
    ncols = sum(len(list(c.execute("SELECT name FROM pragma_table_info(?)", (t,)))) for t in fts)
    trig = c.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]
    return {"fts_tables": len(fts), "columns": ncols, "triggers": trig}


def main():
    sim = {o: {cid: fn(o) for cid, (_, fn) in CASES.items()} for o in OPTIONS}
    with open(os.path.join(ROOT, "decisions", "options", "10-search.sim.json"), "w",
              encoding="utf-8", newline="") as fh:
        json.dump(sim, fh, indent=1)
    print("%-28s" % "case" + "".join("%-18s" % o for o in OPTIONS))
    for cid in CASES:
        print("%-28s" % cid + "".join("%-18s" % sim[o][cid] for o in OPTIONS))
    print("%-28s" % "growth fts/cols/triggers" + "".join("%-18s" % "/".join(str(v) for v in growth(o).values()) for o in OPTIONS))


if __name__ == "__main__":
    main()
