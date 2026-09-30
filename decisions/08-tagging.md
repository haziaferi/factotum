# ADR 08: Tagging, label or category

Status: **decided: one-vocab; the word is "Label"**. Date: 2026-09-30. Owners: Tendril and Chronicle.

The map listed this row as *duplicated*. Verification found that neither model holds the other:
- Tendril labels are many per page. They have no rename, delete, order or scope, and sync by name.
- Chronicle categories are one per activity or tracker, with a chosen colour, an order and a scope.

This ADR builds on:
- ADR 07: activities are items.
- ADR 06: habits are items.
- ADR 01: every row has an id and stamps.

## Verified facts

The facts were verified with `tools/verify.py`; the raw output is in `verify/08-tagging/`.

| App | Fact | Source | Map said |
|---|---|---|---|
| Tendril | `Label` is in table `tags`: `id`, `uid`, `name`, and `color`, which is **derived from a hash of the name** over an 8-colour palette, not chosen. `PageLabel` (`page_tags`) is many-to-many, with CASCADE on both sides. Labels are flat, and they replaced a removed `category` field. | `Label.kt:9-53` | "name + colour" (partial) |
| Tendril | Labels also attach, one at a time, to a **habit** (its planner "area") and to a **page database** (its "doorway": a page carrying the label becomes a member). Neither link has a foreign key. | `Habit.kt:88-89`; `LabelMembership.kt:65` | not stated |
| Tendril | There is **no rename, recolour or delete** of a label (a grep for update, delete or rename paths found 0 hits). Names aren't unique at the database level, and lookup is an exact match. | `LabelDao.kt:9-46`; `LabelDao.kt:16,23` | "rename/recolour/delete" was Chronicle's (the map had it right) |
| Tendril | Sync is **by name inside the page record**. A winning page replaces the page's whole label set, a label is created by name if missing, and the uid and colour never travel. | `PagesSyncEngine.kt:684-687`; `PageSnapshotRecords.kt:37` | not stated |
| Chronicle | `CategoryEntity` has `id`, `name`, `colorArgb`, `appliesTo` (ACTIVITY, TRACKER or BOTH), `sortOrder`, `updatedAtMillis`, `updatedByDevice` and `deletedAtMillis`. It is flat and ordered. | `CategoryEntity.kt:13-22`; `Enums.kt:76`; `CoreDao.kt:15` | "name + colour" (partial) |
| Chronicle | **One category per activity or tracker** (nullable `categoryId`, SET NULL). Nothing else carries one. | `ActivityEntity.kt:21,32`; `TrackerEntity.kt:44` | not stated |
| Chronicle | Rename, recolour and delete exist. A delete tombstones the category and clears the members in the same transaction, with fresh stamps. | `CategoriesSettingsScreen.kt:38`; `CategoryRepository.kt:50-65` | confirmed |
| Chronicle | Names aren't unique, and the tracker sheet picks a new category **by name**, so a duplicate name can pick the wrong one. | `TrackerCreationSheet.kt:107` | not stated |
| Chronicle | Categories group the Track and Data lists and colour the pie chart's wedges. | `TrackListViewModel.kt:135`; `DataListViewModel.kt:128`; `ChartDataRepository.kt:184` | not stated |

## Scores (`08-tagging-scores.md`, run by `tools/tagging_sql.py` on SQLite)

| Option | Chronicle | Shared | Tendril | Growth | Status |
|---|---|---|---|---|---|
| two-vocabs | 1.00 | 0.00 | 1.00 | 32 | dominated ("Health" as an area and as a category are two rows) |
| labels-only | 0.60 | 1.00 | 1.00 | 25 | front (no order, no scope) |
| categories-only | 1.00 | 1.00 | 0.75 | 25 | front (a page holds one) |
| **one-vocab** | 1.00 | 1.00 | 1.00 | 27 | **front, the only full coverage** |
| many-everywhere | 0.80 | 1.00 | 1.00 | 33 | dominated (an activity can sit in two categories, so the pie chart double-counts) |
| polymorphic | 1.00 | 1.00 | 0.75 | 26 | dominated by categories-only (no foreign key to the target, so deleting a page orphans its label rows) |
| inline (control) | 0.20 | 0.00 | 1.00 | 19 | failed its 5 vocabulary cases, as expected |

## Decision

**one-vocab**, with the on-screen word **Label**, was confirmed by the owner on 2026-09-30.

**The `label` table** holds `name`, `color`, `applies_to` and `sort_order`, plus ADR 01's identity and stamps.
- `applies_to` is ALL (the default), ACTIVITY or TRACKER. Chronicle's BOTH maps to ALL.
- The table is called `label`, not `tag`. "Tag" keeps Tendril's meaning: a Select property inside a page database (`Label.kt:12-16`).

**Cardinality stays as each owner has it:**
- **Pages** carry many labels through `page_label`, with CASCADE on both sides.
- **Items** carry at most one, through `item.label_id` (SET NULL). This is an activity's category and a habit's area, and it is allowed on ACTIVITY and HABIT only.
- **Trackers** carry at most one, through `tracker.label_id` (SET NULL).
- **Page databases** carry at most one doorway label, through `page_database.label_id`. It now has a foreign key (SET NULL).

## Consequences: fixes, not questions

- **Names are unique, ignoring case** (a unique index on `lower(name)`). Neither app enforces this. Chronicle's by-name pick can choose the wrong row (`TrackerCreationSheet.kt:107`), and Tendril relies on the create-on-type path.
- **Colour.** A new label takes Tendril's name-derived colour as its default, so creating one as you type needs no picker. It can then be changed, as in Chronicle, and the chosen colour syncs.
- **Labels sync as rows** under ADR 01, with id, stamps and tombstone. They no longer travel as names inside a page record. A page's label set merges per `page_label` row rather than replacing the whole set, so a label removed on the losing side isn't lost.
- **Rename, recolour and delete apply to every label.** Tendril has none of these today. Deleting a label clears it from members and keeps them, as Chronicle does.
- **Scope in the pickers.** The activity picker offers ALL and ACTIVITY labels, and the tracker picker offers ALL and TRACKER labels. Pages and habits are offered ALL labels.
