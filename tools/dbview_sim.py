"""Contest 16 (databases in pages): simulates each option's rules over one small world and runs
every behaviour case of decisions/cases/16-databases.jsonl against it. Writes
decisions/options/16-databases.sim.json ({option: {case: 0|1}}), which score_contest.py reads in
place of hand marks.

    python tools/dbview_sim.py

The world: pages in a tree (parent, trashed, labels, kind), databases (a database page, an optional
doorway label, an optional query), views (a database, a filter, an owner: the database page or a
block), blocks (a page's DATABASE or VIEW block naming a database or a view), and items (Factotum's
tasks, ADR 02, which are not pages). An option is a set of capabilities plus a membership rule;
an operation an option cannot perform raises Unsupported and the case scores 0.
"""
import copy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Unsupported(Exception):
    pass


class World:
    def __init__(self, opt):
        self.opt = opt
        self.pages, self.dbs, self.views, self.blocks, self.items = {}, {}, {}, {}, {}
        self.copies = {}  # control option only: a row duplicated per place

    # -- pages
    def page(self, pid, parent=None, labels=(), props=None):
        self.pages[pid] = dict(parent=parent, trashed=False, labels=set(labels), props=dict(props or {}), kind="page")
        return pid

    def trash(self, pid):
        for p, d in self.pages.items():
            if p == pid or self.ancestor(pid, p):
                d["trashed"] = True

    def restore(self, pid):
        for p, d in self.pages.items():
            if p == pid or self.ancestor(pid, p):
                d["trashed"] = False

    def move(self, pid, new_parent):
        self.pages[pid]["parent"] = new_parent

    def ancestor(self, a, p):
        q = self.pages[p]["parent"]
        while q is not None:
            if q == a:
                return True
            q = self.pages[q]["parent"]
        return False

    def live(self, pid):
        return pid in self.pages and not self.pages[pid]["trashed"]

    # -- databases
    def database(self, dbid, parent=None, doorway=None, query=None):
        if query is not None and not self.opt["query"]:
            raise Unsupported("query membership")
        if query is None and not self.opt["owned_rows"] and not self.opt["copies"]:
            query = {"label": dbid}  # query-only: a set of pages of its own type (Anytype Set by type)
        self.page(dbid, parent)
        self.pages[dbid]["kind"] = "database"
        self.dbs[dbid] = dict(doorway=doorway, query=query)
        self.views[dbid + ":v"] = dict(db=dbid, filter=None, owner=dbid)
        return dbid

    def add_row(self, dbid, pid, **kw):
        """A new row made inside the database: a sub-page (Factotum, Tendril), or a query match."""
        if self.opt["owned_rows"]:
            return self.page(pid, parent=dbid, **kw)
        q = self.dbs[dbid]["query"] or {}
        labels = set(kw.pop("labels", ())) | ({q["label"]} if "label" in q else set())
        return self.page(pid, labels=labels, **kw)

    def rows(self, dbid):
        if not self.live(dbid):
            return set()
        if self.opt["copies"]:
            return {p for p, d in self.pages.items() if d.get("copy_of") is not None and d["parent"] == dbid and self.live(p)} | \
                   {p for p, d in self.pages.items() if d["parent"] == dbid and d["kind"] == "page" and self.live(p)}
        db, out = self.dbs[dbid], set()
        for p, d in self.pages.items():
            if p == dbid or not self.live(p) or d["kind"] == "database":
                continue
            if self.opt["owned_rows"] and d["parent"] == dbid:
                out.add(p)
            if db["doorway"] and db["doorway"] in d["labels"]:
                out.add(p)
            q = db.get("query")
            if q and self.matches(d, q):
                out.add(p)
        return out

    def matches(self, d, q):
        if "label" in q and q["label"] not in d["labels"]:
            return False
        for k, v in q.get("props", {}).items():
            if d["props"].get(k) != v:
                return False
        return True

    def join(self, dbid, pid):
        """Make an existing page (living elsewhere) a row of a database without moving it."""
        if self.opt["copies"]:
            # The control: a page shown in a database is copied into it (one copy per place, per join).
            n = sum(1 for d in self.pages.values() if d.get("copy_of") == pid) + 1
            cid = "%s~copy%d" % (pid, n)
            self.page(cid, parent=dbid, labels=self.pages[pid]["labels"], props=self.pages[pid]["props"])
            self.pages[cid]["copy_of"] = pid
            return
        db = self.dbs[dbid]
        if db["doorway"]:
            self.pages[pid]["labels"].add(db["doorway"])
        elif db.get("query") and "label" in db["query"]:
            self.pages[pid]["labels"].add(db["query"]["label"])
        else:
            raise Unsupported("no way to join a page living elsewhere")

    # -- blocks in pages
    def embed(self, page, bid, dbid):
        """A DATABASE block: the database shown in place, among the page's text."""
        if not self.opt["embed"]:
            raise Unsupported("database block")
        self.blocks[bid] = dict(page=page, db=dbid, view=None)

    def inline_database(self, page, bid, dbid, **kw):
        """A database made *inside* a page (Notion inline): it is the page's own, shown in place."""
        if not self.opt["embed"]:
            raise Unsupported("database block")
        self.database(dbid, parent=page, **kw)
        self.embed(page, bid, dbid)
        return dbid

    def view_block(self, page, bid, dbid, filt=None):
        """A VIEW block: a view of a database living elsewhere, with its own filter."""
        if not self.opt["linked_views"]:
            raise Unsupported("linked view")
        if filt and filt.get("this_page") and not self.opt["page_relative"]:
            raise Unsupported("filter relative to the containing page")
        vid = bid + ":view"
        self.views[vid] = dict(db=dbid, filter=filt, owner=bid)
        self.blocks[bid] = dict(page=page, db=dbid, view=vid)

    def shown(self, bid):
        """Rows a block shows, or None when the block's page is trashed or its database is gone."""
        b = self.blocks[bid]
        if not self.live(b["page"]) or not self.live(b["db"]):
            return None
        rows = self.rows(b["db"])
        f = self.views[b["view"]]["filter"] if b["view"] else None
        if f and f.get("this_page"):
            rows = {r for r in rows if b["page"] in self.pages[r]["props"].get("project", ())}
        if f and "props" in f:
            rows = {r for r in rows if all(self.pages[r]["props"].get(k) == v for k, v in f["props"].items())}
        return rows

    # -- items (Factotum's tasks; not pages)
    def item(self, iid, labels=()):
        self.items[iid] = dict(labels=set(labels))

    def item_view(self, page, bid, label):
        if not self.opt["item_views"]:
            raise Unsupported("a view over items")
        self.blocks[bid] = dict(page=page, db=None, view=None, items_label=label)

    def shown_items(self, bid):
        b = self.blocks[bid]
        return {i for i, d in self.items.items() if b["items_label"] in d["labels"]}

    # -- two devices
    def fork(self):
        return copy.deepcopy(self)


def merge(a, b, base):
    """ADR 01/12 per field group: each page's parent, labels (as a set, adds and removes merged
    against base), trashed (later wins, here: either side trashing wins over an untouched base)."""
    out = copy.deepcopy(a)
    for pid in set(a.pages) | set(b.pages):
        if pid not in a.pages:
            out.pages[pid] = copy.deepcopy(b.pages[pid]); continue
        if pid not in b.pages:
            continue
        pa, pb, p0 = a.pages[pid], b.pages[pid], base.pages.get(pid)
        if p0 is None:
            continue
        out.pages[pid]["labels"] = (pa["labels"] | pb["labels"]) - ((p0["labels"] - pa["labels"]) | (p0["labels"] - pb["labels"]))
        out.pages[pid]["parent"] = pb["parent"] if pa["parent"] == p0["parent"] else pa["parent"]
        out.pages[pid]["trashed"] = pa["trashed"] or pb["trashed"]
        out.pages[pid]["props"] = {**pa["props"], **{k: v for k, v in pb["props"].items() if v != p0["props"].get(k)}}
    for k in ("dbs", "views", "blocks", "items"):
        getattr(out, k).update({x: copy.deepcopy(v) for x, v in getattr(b, k).items() if x not in getattr(a, k)})
    for pid, places in b.copies.items():
        out.copies.setdefault(pid, set()).update(places)
    return out


# ---- the options -------------------------------------------------------------------------------
OPTIONS = {
    "O1-full-page": dict(owned_rows=True, query=False, embed=False, linked_views=False, page_relative=False, item_views=False, copies=False),
    "O2-inline-owned": dict(owned_rows=True, query=False, embed=True, linked_views=False, page_relative=False, item_views=False, copies=False),
    "O3-linked-views": dict(owned_rows=True, query=False, embed=True, linked_views=True, page_relative=True, item_views=False, copies=False),
    "O4-query-only": dict(owned_rows=False, query=True, embed=True, linked_views=True, page_relative=True, item_views=False, copies=False),
    "O5-hybrid": dict(owned_rows=True, query=True, embed=True, linked_views=True, page_relative=True, item_views=False, copies=False),
    "O6-hybrid-items": dict(owned_rows=True, query=True, embed=True, linked_views=True, page_relative=True, item_views=True, copies=False),
    "C0-copy-per-place": dict(owned_rows=False, query=False, embed=True, linked_views=True, page_relative=False, item_views=False, copies=True),
}


# ---- the cases (one function per case id in decisions/cases/16-databases.jsonl) ------------------
def c_tendril_db_is_page(w):
    w.page("home"); w.database("books", parent="home")
    return w.pages["books"]["parent"] == "home" and w.pages["books"]["kind"] == "database"


def c_tendril_rows_are_subpages(w):
    w.database("books"); w.add_row("books", "dune")
    return w.pages["dune"]["parent"] == "books" and w.rows("books") == {"dune"}


def c_tendril_doorway_label(w):
    w.page("notes"); w.page("idea", parent="notes", labels=["reading"])
    if w.opt["copies"]:
        w.database("books"); w.join("books", "idea")
        return "idea" in w.rows("books") and w.pages["idea"]["parent"] == "notes"
    w.database("books", doorway="reading")
    return "idea" in w.rows("books") and w.pages["idea"]["parent"] == "notes"


def c_tendril_trash_db_trashes_owned_rows(w):
    w.page("other", labels=["reading"]); w.database("books", doorway=None if w.opt["copies"] else "reading")
    w.add_row("books", "dune")
    if w.opt["copies"]:
        w.join("books", "dune"); w.join("books", "other")
    w.trash("books")
    return w.pages["dune"]["trashed"] and not w.pages["other"]["trashed"]


def c_owner_inline_in_page(w):
    w.page("trip"); w.inline_database("trip", "b1", "packing")
    return w.blocks["b1"]["page"] == "trip" and w.shown("b1") == set()


def c_owner_project_shows_its_tasks(w):
    w.database("tasks"); w.page("garden"); w.page("trip")
    w.add_row("tasks", "dig", props={"project": ("garden",)}); w.add_row("tasks", "book", props={"project": ("trip",)})
    w.view_block("garden", "gv", "tasks", filt={"this_page": True})
    return w.shown("gv") == {"dig"}


def c_owner_same_page_two_places(w):
    w.page("dune")
    w.database("books", doorway=None if w.opt["copies"] else "reading")
    w.database("gifts", doorway=None if w.opt["copies"] else "gift")
    w.join("books", "dune"); w.join("gifts", "dune")
    return "dune" in w.rows("books") and "dune" in w.rows("gifts")


def c_owner_one_db_many_places(w):
    w.database("tasks"); w.add_row("tasks", "dig", props={"status": "open"}); w.add_row("tasks", "mow", props={"status": "done"})
    w.page("garden"); w.page("week")
    w.view_block("garden", "g", "tasks", filt={"props": {"status": "open"}}); w.view_block("week", "k", "tasks")
    w.pages["dig"]["props"]["status"] = "done"
    return w.shown("g") == set() and w.shown("k") == {"dig", "mow"}


def c_owner_move_page_keeps_inline_db(w):
    w.page("trip"); w.page("archive"); w.inline_database("trip", "b1", "packing"); w.add_row("packing", "socks")
    w.move("trip", "archive")
    return w.shown("b1") == {"socks"} and w.ancestor("archive", "packing")


def c_owner_trash_page_with_inline_db(w):
    w.page("trip"); w.inline_database("trip", "b1", "packing", doorway="travel")
    w.add_row("packing", "socks"); w.page("passport", labels=["travel"])
    w.trash("trip")
    ok_trash = w.pages["socks"]["trashed"] and not w.pages["passport"]["trashed"]
    w.restore("trip")
    return ok_trash and w.shown("b1") == {"socks", "passport"}


def c_ref_query_by_property(w):
    w.page("a", props={"status": "open"}); w.page("b", props={"status": "done"}); w.page("c", parent="a", props={"status": "open"})
    w.database("open", query={"props": {"status": "open"}})
    return w.rows("open") == {"a", "c"}


def c_ref_deleting_a_view_keeps_pages(w):
    """Anytype/Obsidian: removing a view or query block never deletes the pages it showed."""
    w.database("tasks"); w.add_row("tasks", "dig"); w.page("garden")
    w.view_block("garden", "g", "tasks")
    del w.blocks["g"]
    return w.live("dig") and "dig" in w.rows("tasks")


def c_ref_item_rows(w):
    w.page("garden"); w.item("t1", labels=["garden"]); w.item("t2", labels=["trip"])
    w.item_view("garden", "iv", "garden")
    return w.shown_items("iv") == {"t1"}


def c_factotum_concurrent_join(w):
    """Two devices apart both put the same page into the same database: after sync, one row."""
    w.page("dune"); w.database("books", doorway=None if w.opt["copies"] else "reading")
    base = w.fork(); a, b = w.fork(), w.fork()
    a.join("books", "dune"); b.join("books", "dune")
    m = merge(a, b, base)
    rows = m.rows("books")
    return "dune" in rows and len(rows) == 1


def c_factotum_leave_while_edited(w):
    """Device A takes the page out of the database while device B edits it: the page leaves and
    keeps B's edit; nothing is duplicated or lost."""
    w.page("dune", props={"title": "Dune"}); w.database("books", doorway=None if w.opt["copies"] else "reading")
    w.join("books", "dune")
    base = w.fork(); a, b = w.fork(), w.fork()
    if a.opt["copies"]:
        return False  # a copy cannot leave: the original never joined, the copy has no tie back
    a.pages["dune"]["labels"].discard("reading")
    b.pages["dune"]["props"]["title"] = "Dune (1965)"
    m = merge(a, b, base)
    return "dune" not in m.rows("books") and m.pages["dune"]["props"]["title"] in ("Dune", "Dune (1965)")


def c_factotum_embed_of_trashed_db(w):
    w.page("home"); w.database("books"); w.embed("home", "e", "books")
    w.trash("books")
    return w.shown("e") is None and w.live("home")


def c_factotum_one_label_vocab(w):
    w.page("idea", labels=["reading"])
    if w.opt["copies"]:
        return False
    w.database("books", doorway="reading") if w.opt["owned_rows"] else w.database("books", query={"label": "reading"})
    return "idea" in w.rows("books")


CASES = {name[2:].replace("_", "-"): fn for name, fn in list(globals().items()) if name.startswith("c_")}


def run():
    out = {}
    for opt_id, opt in OPTIONS.items():
        out[opt_id] = {}
        for case_id, fn in CASES.items():
            try:
                out[opt_id][case_id] = 1 if fn(World(opt)) else 0
            except Unsupported:
                out[opt_id][case_id] = 0
    return out


if __name__ == "__main__":
    res = run()
    path = os.path.join(ROOT, "decisions", "options", "16-databases.sim.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1)
    ids = list(CASES)
    print("%-20s %s" % ("", " ".join("%-2d" % i for i in range(len(ids)))))
    for o, r in res.items():
        print("%-20s %s  %d/%d" % (o, " ".join("%-2d" % r[c] for c in ids), sum(r.values()), len(ids)))
    for i, c in enumerate(ids):
        print(i, c)
