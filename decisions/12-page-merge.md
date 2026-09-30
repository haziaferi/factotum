# ADR 12: Page merge granularity

Status: **decided: per-row+revive; for a clash on the same paragraph, the later text wins, with a notice**. Date: 2026-10-01. Owner: Tendril, the only app with pages.

The sole-owner probe (`docs/sole-owner-probe-2026-10-01.md`) found this. ADR 01's hybrid+ was scored on items and reminders, and Tendril's pages sync by a different rule, so nothing had decided how a page merges.

## Verified facts

The facts were verified with `tools/verify.py`; the raw output is in `verify/12-page-merge/`.

| Fact | Source |
|---|---|
| A page travels as one snapshot (`pages/<uid>.json`). It carries the page row, its blocks, its property values and schema, its labels (by name) and its canvas. Relations are separate: one flat `page_relations.json`, merged add-only. | `PageSnapshotRecords.kt:7,38,46,207`; `PagesSyncEngine.kt:728` |
| **The merge is whole-page last-writer-wins on `Page.updatedAt`.** The winner deletes and reinserts every block, every property value and the whole canvas. Nothing merges per block. | `PagesSyncEngine.kt:134,491,633,681,691`; `BlockSnapshots.kt:85` |
| The loser is kept as a `PageRevision` (reason MERGE, title and blocks only, at most 50 per page, never synced). A full `<uid>.tendril-lost-<updatedAt>.json` file is also written to the folder. The person isn't told: the only trace is a History row labelled "replaced by a sync". | `PageHistory.kt:55-58,97`; `PageRevision.kt:26`; `SnapshotSyncOrchestrator.kt:1366`; `HistorySheet.kt:149` |
| Blocks carry a `uid`, plus `updatedAt` and `createdAt` that are never compared. There's no block `deletedAt`: a block is deleted by being absent from the winner. Block references point at the uid. | `Block.kt:62,107`; `PageSnapshotRecords.kt:65,91` |
| Trash and restore both set `updatedAt`, so **a later edit beats an earlier trash**, and a later trash beats an earlier edit. | `PageDao.kt:108-111`; `PagesSyncEngine.kt:802` |
| Properties (the column schema) are upserted by uid and deleted only through a purge record. Views are replaced with the winner. Canvas edges have no uid. | `PagesSyncEngine.kt:543-562`; `PageSnapshotRecords.kt:199` |

## Scores (`12-page-merge-scores.md`, run by `tools/page_merge_sim.py`, two devices that sync)

| Option | Shared | Tendril | Growth | Status |
|---|---|---|---|---|
| whole-page (as-is) | 0.00 | 1.00 | 0 | front (edits to different paragraphs, cells or canvas nodes are lost) |
| whole-page+ask | 0.00 | 0.67 | 2 | dominated |
| per-row | 1.00 | 0.67 | 15 | dominated (an edit can't bring a trashed page back) |
| per-row+ask | 1.00 | 0.67 | 17 | dominated |
| **per-row+revive** | 1.00 | 1.00 | 15 | **front, full coverage** |
| discard (control) | 0.00 | 0.67 | 0 | failed its 5 cases, as expected |

**Two notes on method:**
- **per-row+revive was added after the first run.** It keeps Tendril's "a later edit beats a trash" rule. That rule doesn't conflict with ADR 01: under ADR 01 a whole row is one group by default, so the same rule already holds there.
- **The ask/silent choice for a same-paragraph clash was put to the owner separately.** The cases can't see the difference.

## Decision

The owner confirmed **per-row+revive** on 2026-10-01.
- **Every part of a page is its own row with ADR 01 stamps and a tombstone.** That means `block`, `property_value`, `canvas_node`, `canvas_edge` and `page_database_view`.
  - Edits to different paragraphs, cells or canvas nodes all survive.
  - A canvas edge takes a ULID.
- **Block order** is a fractional sort key, so two concurrent inserts both land where they were put.
- **The page's existence** is its own group. An edit to any part stamped later than the trash restores the page, as in Tendril now.
- **A clash on the same paragraph: the later text wins, with a notice.** The other text goes into the page's History (a `PageRevision`, reason MERGE). A small "replaced by a sync" notice appears on the page and links to it. Tendril records the revision today but never tells the person.
- **Relations** stay add-only and undirected. **Property schema** stays upsert-by-uid, with deletion only by purge.

## Consequences: fixes, not questions

- **The folder's `.tendril-lost` files aren't carried over.** The revision plus the notice replace them, so the folder doesn't collect copies that are never deleted.
- **Labels on pages** merge per `page_label` row (ADR 08), not by rebuilding the set from names.
- **A block's `updatedAt`** becomes its ADR 01 stamp. Tendril carries the field but never uses it.
- **Search** (ADR 10) indexes blocks through triggers, so a merged block is indexed on the write, with no per-page rebuild.
