"""Contest 12 (page merge granularity): simulate two devices editing one page between syncs, then
merge per option. Timestamps are explicit so each case sets which edit is later (an HLC, ADR 01).

    python tools/page_merge_sim.py   # writes decisions/options/12-page-merge.sim.json + a table

A page: title, trash stamp, blocks {uid: text, order}, database cells {property: value},
canvas nodes {uid: position}. Tendril sends it as one snapshot (verify/12-page-merge/).

Options
  whole-page      Tendril: the page with the later updatedAt replaces the other entirely; the
                  loser's body is kept (PageRevision + .tendril-lost file); trash is a field of it
  whole-page+ask  whole-page, but a page changed on both sides since the last sync asks the person
  per-row         ADR 01 hybrid+ applied to the page's parts: every block, cell and canvas node is
                  its own row with a stamp and a tombstone; the page's existence is its own group;
                  a same-block conflict keeps the later text and saves the loser as a revision
  per-row+ask     per-row, and a block changed on both sides since its base asks the person
                  (keep mine / take theirs / keep both), as ADR 01 does for a schedule
  per-row+revive  per-row, and an edit to any part stamped later than the trash restores the page,
                  as Tendril's whole-page merge does (a later edit beats an earlier trash)
  discard         CONTROL: whole-page, and the loser's body is thrown away
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def base_page():
    return {"title": ("Trip", 0), "trashed": (False, 0),
            "blocks": {"b1": ("Flights", 1.0, 0), "b2": ("Hotel", 2.0, 0), "b3": ("Budget", 3.0, 0)},
            "cells": {"status": ("Planning", 0)}, "nodes": {"n1": ("0,0", 0), "n2": ("5,0", 0)}}


class Dev:
    def __init__(self):
        self.page, self.changed_at = base_page(), 0

    def _touch(self, t):
        self.changed_at = max(self.changed_at, t)

    def edit_block(self, uid, text, t):
        _, order, _ = self.page["blocks"][uid]
        self.page["blocks"][uid] = (text, order, t)
        self._touch(t)

    def insert_block(self, uid, text, order, t):
        self.page["blocks"][uid] = (text, order, t)
        self._touch(t)

    def set_cell(self, prop, value, t):
        self.page["cells"][prop] = (value, t)
        self._touch(t)

    def move_node(self, uid, pos, t):
        self.page["nodes"][uid] = (pos, t)
        self._touch(t)

    def trash(self, t):
        self.page["trashed"] = (True, t)
        self._touch(t)


def body(p):
    return [text for text, order, _ in sorted(p["blocks"].values(), key=lambda b: b[1])]


def merge(opt, a, b):
    """-> (merged page, kept loser bodies, questions put to the person)."""
    base = base_page()
    kept, asked = [], []
    if opt.startswith("whole-page") or opt == "discard":
        a_changed, b_changed = a.changed_at > 0, b.changed_at > 0
        if opt == "whole-page+ask" and a_changed and b_changed:
            full = lambda pg: body(pg) + [v[0] for v in pg["cells"].values()] + [v[0] for v in pg["nodes"].values()]
            asked.append(("page", full(a.page), full(b.page)))
            return a.page, kept, asked  # shown with both versions; mine stays live until answered
        win, lose = (a, b) if a.changed_at >= b.changed_at else (b, a)
        if opt != "discard" and lose.changed_at > 0:
            # PageRevision keeps the body; the .tendril-lost file keeps the full snapshot (cells, canvas too)
            kept.append(body(lose.page) + [v[0] for v in lose.page["cells"].values()] + [v[0] for v in lose.page["nodes"].values()])
        return win.page, kept, asked
    # per-row: every part merges by its own stamp
    m = base_page()
    for part in ("blocks", "cells", "nodes"):
        keys = set(a.page[part]) | set(b.page[part])
        for k in keys:
            va, vb = a.page[part].get(k), b.page[part].get(k)
            if va is None or vb is None:
                m[part][k] = va or vb
                continue
            ta, tb = va[-1], vb[-1]
            bt = base[part].get(k, (None,) * 3)[-1] if k in base[part] else 0
            if ta > bt and tb > bt and va[0] != vb[0]:
                if opt == "per-row+ask" and part == "blocks":
                    asked.append((k, va[0], vb[0]))
                    m[part][k] = va
                    continue
                # ADR 12 amendment: a MERGE revision keeps every losing part; the pre-amendment design kept blocks only
                if part == "blocks" or opt != "per-row+revive-blocks":
                    kept.append([(vb if ta >= tb else va)[0]])
            m[part][k] = va if ta >= tb else vb
    # existence is its own group: only a trash or restore stamp moves it
    m["trashed"] = max(a.page["trashed"], b.page["trashed"], key=lambda x: x[1])
    if opt.startswith("per-row+revive") and m["trashed"][0] and max(a.changed_at, b.changed_at) > m["trashed"][1]:
        m["trashed"] = (False, max(a.changed_at, b.changed_at))
    return m, kept, asked


def run(opt, ops_a, ops_b):
    a, b = Dev(), Dev()
    for f in ops_a:
        f(a)
    for f in ops_b:
        f(b)
    return merge(opt, a, b)


def case_loser_recoverable(opt):
    """tendril: A and B both rewrite 'Hotel'; the losing text is kept somewhere the person can get it
    (PageRevision reason MERGE, PageHistory.kt:58; .tendril-lost file, SnapshotSyncOrchestrator.kt:1366)."""
    m, kept, asked = run(opt, [lambda d: d.edit_block("b2", "Hotel Rome", 5)], [lambda d: d.edit_block("b2", "Hotel Milan", 6)])
    texts = {t for k in kept for t in k} | {x for q in asked for x in (q[1:] if isinstance(q[1], str) else ())}
    flat = " ".join(" ".join(k) for k in kept) + " ".join(str(q) for q in asked)
    live = " ".join(body(m))
    return 1 if ("Hotel Rome" in live or "Hotel Rome" in flat) and ("Hotel Milan" in live or "Hotel Milan" in flat) else 0


def case_later_edit_beats_trash(opt):
    """tendril: B trashes the page at t=5; A, not having seen it, edits a block at t=7; after sync the
    page is live, because trash is an ordinary field of the whole-page merge (PageDao.kt:108-111)."""
    m, _, asked = run(opt, [lambda d: d.edit_block("b1", "Flights booked", 7)], [lambda d: d.trash(5)])
    return 1 if not m["trashed"][0] and not asked else 0


def case_block_uid_stable(opt):
    """tendril: a block keeps its uid through a merge, so another page's reference to it still resolves
    (PageSnapshotRecords.kt:65)."""
    m, _, _ = run(opt, [lambda d: d.edit_block("b3", "Budget 900", 5)], [])
    return 1 if "b3" in m["blocks"] else 0


def case_different_blocks(opt):
    """shared: A edits 'Flights' while B edits 'Budget'; after sync both edits are live with no question."""
    m, _, asked = run(opt, [lambda d: d.edit_block("b1", "Flights booked", 5)], [lambda d: d.edit_block("b3", "Budget 900", 6)])
    return 1 if body(m)[0] == "Flights booked" and body(m)[2] == "Budget 900" and not asked else 0


def case_concurrent_inserts(opt):
    """shared: A adds 'Visa' after 'Flights' while B adds 'Packing' at the end; both are on the page."""
    m, _, asked = run(opt, [lambda d: d.insert_block("bA", "Visa", 1.5, 5)], [lambda d: d.insert_block("bB", "Packing", 4.0, 6)])
    return 1 if body(m) == ["Flights", "Visa", "Hotel", "Budget", "Packing"] and not asked else 0


def case_cell_vs_body(opt):
    """shared: on a database row page, A sets Status to 'Booked' while B edits the body; both survive
    (Tendril deletes and reinserts cells with the winning page, PagesSyncEngine.kt:691)."""
    m, _, asked = run(opt, [lambda d: d.set_cell("status", "Booked", 5)], [lambda d: d.edit_block("b2", "Hotel Milan", 6)])
    return 1 if m["cells"]["status"][0] == "Booked" and body(m)[1] == "Hotel Milan" and not asked else 0


def case_canvas_nodes(opt):
    """shared: A moves canvas node 1 while B moves node 2; both moves survive (Tendril rebuilds the
    canvas wholesale, PagesSyncEngine.kt:633)."""
    m, _, asked = run(opt, [lambda d: d.move_node("n1", "1,1", 5)], [lambda d: d.move_node("n2", "6,2", 6)])
    return 1 if m["nodes"]["n1"][0] == "1,1" and m["nodes"]["n2"][0] == "6,2" and not asked else 0


def case_cell_loser(opt):
    """shared (re-scored 2026-10-01, ADR 12 amendment): A sets Status to 'Booked' while B sets it to
    'Cancelled'; the losing value stays recoverable, as Tendril's .tendril-lost file keeps it today
    (SnapshotSyncOrchestrator.kt:1366-1367)."""
    m, kept, asked = run(opt, [lambda d: d.set_cell("status", "Booked", 5)], [lambda d: d.set_cell("status", "Cancelled", 6)])
    seen = {m["cells"]["status"][0]} | {t for k in kept for t in k} | {t for q in asked for side in q[1:] for t in (side if isinstance(side, list) else [side])}
    return 1 if {"Booked", "Cancelled"} <= seen else 0


CASES = {
    "tendril-loser-recoverable": ("tendril", case_loser_recoverable),
    "tendril-later-edit-beats-trash": ("tendril", case_later_edit_beats_trash),
    "tendril-block-uid-stable": ("tendril", case_block_uid_stable),
    "shared-different-blocks-both-live": ("shared", case_different_blocks),
    "shared-concurrent-inserts": ("shared", case_concurrent_inserts),
    "shared-cell-and-body": ("shared", case_cell_vs_body),
    "shared-canvas-nodes": ("shared", case_canvas_nodes),
    "shared-cell-loser-recoverable": ("shared", case_cell_loser),
}
# columns added to Tendril's page tables: per-row adds (hlc, device, deleted_at) to block, property_value,
# canvas_node, canvas_edge and page_database_view (5 x 3); +ask adds a base stamp pair to block; a full MERGE
# revision adds cells_json and canvas_json to page_revision (+2; whole-page keeps Tendril's lost file instead)
GROWTH = {"whole-page": {"columns": 0}, "whole-page+ask": {"columns": 2}, "per-row": {"columns": 17},
          "per-row+ask": {"columns": 19}, "per-row+revive": {"columns": 17}, "per-row+revive-blocks": {"columns": 15},
          "discard": {"columns": 0}}
OPTIONS = list(GROWTH)


def main():
    sim = {o: {cid: fn(o) for cid, (_, fn) in CASES.items()} for o in OPTIONS}
    with open(os.path.join(ROOT, "decisions", "options", "12-page-merge.sim.json"), "w",
              encoding="utf-8", newline="") as fh:
        json.dump(sim, fh, indent=1)
    print("%-34s" % "case" + "".join("%-16s" % o for o in OPTIONS))
    for cid in CASES:
        print("%-34s" % cid + "".join("%-16s" % sim[o][cid] for o in OPTIONS))


if __name__ == "__main__":
    main()
