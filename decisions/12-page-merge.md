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

## Re-scored 2026-10-01

**Why:** the fresh-eyes audit's fix (finding 4) says a MERGE revision keeps every losing part, not just paragraphs. That became a case, `shared-cell-loser-recoverable`, which Tendril meets today through its full `.tendril-lost` copy.
- Every per-row option now keeps losing cells and canvas nodes, at +2 history columns (`cells_json`, `canvas_json`).
- The design as first decided is scored separately as **per-row+revive-blocks**.
- The whole-page prompt shows both full pages.

The current scores are in `12-page-merge-scores.md`.

| Option | Shared | Tendril | Growth | Status |
|---|---|---|---|---|
| whole-page | 0.20 | 1.00 | 0 | front |
| whole-page+ask | 0.20 | 0.67 | 2 | dominated |
| per-row | 1.00 | 0.67 | 17 | dominated |
| per-row+ask | 1.00 | 0.67 | 19 | dominated |
| **per-row+revive** | 1.00 | 1.00 | 17 | **front, the only full coverage** |
| per-row+revive-blocks | 0.80 | 1.00 | 15 | front: 2 columns cheaper, but it drops a behaviour Tendril has today (a losing cell is recoverable), which the "every sole-owner module moves" rule excludes |
| discard (control) | 0.00 | 0.67 | 0 | failed its 6 cases, as expected |

**Sensitivity:** every option's growth was varied over ×0.5 to ×2, giving 46,656 combinations. The pick is the only full-coverage option on the front in all of them. The decision is unchanged.

## Scores as first scored (2026-10-01, before the audit fix)

| Option | Shared | Tendril | Growth | Status |
|---|---|---|---|---|
| whole-page (as-is) | 0.00 | 1.00 | 0 | front (edits to different paragraphs, cells or canvas nodes are lost) |
| whole-page+ask | 0.00 | 0.67 | 2 | dominated |
| per-row | 1.00 | 0.67 | 15 | dominated (an edit can't bring a trashed page back) |
| per-row+ask | 1.00 | 0.67 | 17 | dominated |
| **per-row+revive** | 1.00 | 1.00 | 15 | **front, full coverage** |
| discard (control) | 0.00 | 0.67 | 0 | failed its 5 cases, as expected |

**Two notes on method:**
- **per-row+revive was added after the first run.** It keeps Tendril's "a later edit beats a trash" rule. **This is a deliberate exception to ADR 01**, where deletion in its own group beats a later change to another group (case `chronicle-delete-beats-status`). For pages, an edit to a *different row* (a block, cell or node) stamped later than the trash brings the page back. The owner chose this knowingly: the option read "a later edit still un-trashes a page, as now". (Corrected 2026-10-01: this note first said the rule doesn't conflict with ADR 01.)
- **The ask/silent choice for a same-paragraph clash was put to the owner separately.** The cases can't see the difference.

## Decision

The owner confirmed **per-row+revive** on 2026-10-01.
- **Most parts of a page are their own rows with ADR 01 stamps and a tombstone**: `block`, `property_value`, `canvas_node`, `canvas_edge` and `page_database_view`. The two exceptions keep Tendril's rules, as the last bullet says: relations are add-only, and the property schema is upsert-by-uid.
  - Edits to different paragraphs, cells or canvas nodes all survive.
  - A canvas edge takes a ULID.
- **Block order** is a fractional sort key, so two concurrent inserts both land where they were put.
- **The page's existence** is its own group. An edit to any part stamped later than the trash restores the page, as in Tendril now.
- **A clash on the same paragraph: the later text wins, with a notice.** The other text goes into the page's History (a `PageRevision`, reason MERGE). A small "replaced by a sync" notice appears on the page and links to it. Tendril records the revision today but never tells the person.
- **Relations** stay add-only and undirected. **Property schema** stays upsert-by-uid, with deletion only by purge.

## Consequences: fixes, not questions

- **The folder's `.tendril-lost` files aren't carried over.** Tendril's `PageRevision` holds only the title and blocks (`PageRevision.kt:40-41`), and the lost file holds the full snapshot (`SnapshotSyncOrchestrator.kt:1366-1367`). So a Factotum MERGE revision stores **every losing part**: block text, property value, canvas node. A clashing cell or canvas edit stays recoverable, and the folder still doesn't collect copies that are never deleted.
- **Labels on pages** merge per `page_label` row (ADR 08), not by rebuilding the set from names.
- **A block's `updatedAt`** becomes its ADR 01 stamp. Tendril carries the field but never uses it.
- **Search** (ADR 10) indexes blocks through triggers, so a merged block is indexed on the write, with no per-page rebuild.

## Owner answers, 2026-10-03

A source survey before building slice 12 (Tendril's pages, `PagesSyncEngine.kt`, `PageDetailViewModel.kt`, `PurgeRegistry.kt`) found choices the decision does not settle. The owner answered:

1. **A later edit brings back a deleted block**, as revive does for a trashed page; nothing typed is lost, and it can be deleted again.
2. **Trashing a page trashes its sub-pages**, and restoring brings them back together (Tendril left them live but unreachable).
3. **"Delete forever" on a page deletes its sub-pages forever too**, as a task's subtasks go with it. A purge stays permanent (ADR 01): revive is for the trash only.
4. **Revive brings back a page's trashed parents** with it, so it reappears in its place.
5. **The "replaced by a sync" notice syncs**: it shows on every device until dismissed on any one. A clash on a page's title counts as one on a paragraph.
6. **Journal days follow the personal day boundary** (ADR 06, ADR 09).
7. **Select options are rows**, so options added on two devices both stay (amends "properties upsert by id" for options).
8. **Scope, in order:** 12a pages, blocks, labels on pages, search, History, revive and the notice; 12b databases; 12c canvas; 12d journal, relations and templates. Images, formulas and rollups, and database rows as tasks wait for §7 step 3.

## Owner answers on databases, 2026-10-03 (slice 12b)

A survey of Tendril's databases (`PageDatabase.kt`, `Property.kt`, `PageDatabaseView.kt`, `PageDatabaseViewModel.kt`, `PageSnapshotRecords.kt`, `PagesSyncEngine.kt`) found choices the decision does not settle. Tendril cannot rename or delete a property's options, never converts values on a type change, and syncs a whole database page as one record, so two edits to one row's different cells lose one. The owner answered:

1. **A deleted Select option**: the cells that picked it read as empty (a Board's "No" column) and keep the pick; a later pick of the option, on any device, brings it back, as a later edit brings back a deleted block.
2. **A type change keeps the stored values** and reads them under the new type; changing back restores them. No row is written.
3. **A view's sort, filter and visible columns sync**, each its own group, so a sort and a filter changed apart both stand. Column widths wait for the screens.
4. **A Multi-select cell merges its picks**: each pick is its own row, as a label on a page is, so two devices adding different options both keep theirs.
5. **A database's members are the union** of the rows made inside it and the pages carrying its label (Tendril's rule).
6. **Two options with one name**, made on two devices, merge into the one made first; a cell that picked the other reads as it, and nothing is rewritten (ADR 08's label rule).
7. **A property, option or view renamed on two devices**: the later name wins, silently. The notice stays for what a person types into a page: titles, text and cells.

## Owner answers on the canvas, 2026-10-03 (slice 12c)

A survey of Tendril's canvas (`PageCanvas.kt`, `CanvasViewModel.kt`, `CanvasScreen.kt`, `Frames.kt`, `Tree.kt`, `PageSnapshotRecords.kt`, `PagesSyncEngine.kt`) found choices the decision does not settle. Tendril syncs a canvas as one whole page and rebuilds it on every winning record, so two devices moving two different cards lose one move, and edges get fresh ids on every device. The owner answered:

1. **A card moved on two devices** takes the later position, silently; a move of one card never touches another.
2. **A frame or a branch moved on one device while a card in it is moved on another**: each card keeps its own later position. A card can so end up outside its frame and leave it; frame membership stays geometric, as in Tendril.
3. **Deleting a card deletes its lines in the same step**, and a card that comes back (a later edit, answer 1 of the first set) brings back the lines deleted with it.
4. **A line drawn to, or a child added under, a card deleted on another device brings the card back**, as a sub-page made under a trashed page does.
5. **A page card whose page is in the Trash** stays, marked as in the Trash, offering Restore; **one whose page was deleted forever** stays as a "deleted page" placeholder the person can remove. A purge never deletes a card. The look waits for the screens.
6. **A line's label changed on two devices** keeps the later and puts the earlier in History with a notice, as a card's text does.

Waiting for the screens: whether the viewport and zoom are remembered per device (Tendril keeps neither), "bring to front" and "send to back" (a stacking key is stored now, in creation order), and whether a board re-tidies after a sync changes its structure.

## Owner answers on the journal, relations and templates, 2026-10-03 (slice 12d)

A survey of Tendril (`JournalToday.kt`, `PagesViewModel.kt`, `PageDao.kt`, `PageRelation.kt`, `Property.kt`, `PageDatabaseViewModel.kt`, `TemplateManager.kt`, `PagesSyncEngine.kt`) found that two devices opening one day offline make two day pages (and two "Journal" roots); that ADR 12's "relations stay add-only and undirected" was written for the Road Map's `page_relations`, not the database relation column, whose cells Tendril lets a person unlink; that a relation's two sides are separate cells that a sync can leave disagreeing; and that a canvas copied from a template loses its mind-map links. The owner answered:

1. **A journal day's title** shows the date until renamed; renaming keeps it the day's page, as its date is its identity.
2. **The journal is one page per day under one "Journal" page**, and two devices that open one day make one page.
3. **A Road Map link can be removed**, and relating the two pages again brings it back (amends "add-only" for removal; links stay undirected and merge as one).
4. **A link made to a page trashed on another device brings that page back**, as a line drawn to a deleted card does.
5. **A link in a database relation column can be removed**, and linking again brings it back; links made on two devices both stay.
6. **A database relation is always two-way**: the related database shows a matching column, and both read one stored link.
7. **A relation to a page in the Trash** shows it marked, **one to a page deleted forever** a placeholder the person can remove; a blocker in the Trash does not block.
8. **A journal day and a database's new rows start empty**; templates for either can come later.
9. **A template copies structure, not content**: a page's blocks; a database's properties, options, views and colour (no rows, no doorway label); a canvas's whole board; no sub-pages, no labels.
10. **A relation column in a database template** is copied to relate to the same database, with a new matching column there.
11. **A copy is independent of its template**: editing the template changes no copy.

Waiting for the screens: whether opening a trashed day shows it in the Trash (typing in it brings it back, by revive), how trashed and deleted links look, and a list for opening, editing and deleting templates (templates are kept out of the tree, links and pickers).

