# ADR 10: Full-text search, one index kept by triggers

Status: **decided: chronicle-all**. Date: 2026-10-01. Owners: Tendril and Chronicle. Mnemo and Equipoise have no search index: a grep of their Kotlin sources (`*.kt`) for `@Fts`, `USING fts`, `MATCH :` and `fts` found 0 files. A grep over all files hits only tests, tooling scripts and Equipoise's vendored `third_party/llama.cpp`.

The map listed this row as *duplicated*. Verification found the two indexes differ on three axes: tokenizer, how the index is kept current, and layout. Neither holds the other: Tendril's tokenizer misses accented words, and Chronicle doesn't index pages. The index also has to cover what ADRs 02–08 made searchable.

## Verified facts

The facts were verified with `tools/verify.py`; the raw output is in `verify/10-search/`.

| App | Fact | Source | Map said |
|---|---|---|---|
| Tendril | `page_fts(pageId, plainText)` and `block_fts(pageId, blockId, plainText)`. Both are standalone FTS4 tables using the `simple` tokenizer. `page_fts` packs the title and the block text into one column. | `PageFts.kt:15-38`; `BlockFts.kt:16-20`; `PageContentRepository.kt:37` | "BlockFtsEntry PageFtsEntry" |
| Tendril | Kept current by **application code** (`rebuildFtsForPage`), which the sync merge and the Notion import each call, plus `healIndex` at startup. There are no triggers (0 hits). `healIndex` only fills pages that have no index row, so a stale row is never repaired. | `PageContentRepository.kt:34-44`; `PagesSyncEngine.kt:682`; `TendrilApp.kt:23`; `Migrations.kt:304` | not stated |
| Tendril | Only pages and blocks are indexed. Labels and the block picker use `LIKE`. A query ANDs a prefix term per letter/digit run. Ranking is done in Kotlin, and `snippet()` highlights block hits. A `LIMIT` is applied with no `ORDER BY`. | `PageFts.kt:58,78,102`; `BlockFts.kt:43-45`; `LabelDao.kt:23`; `BlockDao.kt:51` | not stated |
| Chronicle | One FTS4 table: `search_fts(text, kind, targetId, rowKey)` with the `unicode61` tokenizer. Only `text` is indexed. | `SearchFts.kt:31-41`; `Migrations.kt:42` | "FTS4, kept by triggers" (confirmed) |
| Chronicle | **15 triggers** (insert, update and delete on activity, tracker, entry, session and reminder), created on every open. A tombstoned, archived or blank row leaves the index. The backfill runs only in migration 2→3. | `SearchFts.kt:21,62-81,105-106`; `Migrations.kt:44` | confirmed |
| Chronicle | Categories, checklists, goals and charts aren't indexed. There is no ranking or snippet: hits are resolved in memory and sorted by time. | `SearchFts.kt:62`; `SearchRepository.kt:85` | not stated |

## Scores (`10-search-scores.md`, run by `tools/search_sql.py` on real SQLite FTS4 tables)

| Option | Chronicle | Shared | Tendril | Growth | Status |
|---|---|---|---|---|---|
| two-indexes (as-is) | 0.50 | 0.00 | 1.00 | 22 | dominated |
| tendril-all | 0.50 | 0.00 | 1.00 | 18 | dominated (`simple` doesn't fold "perché"; a raw write that skips the rebuild call isn't indexed. Tendril's sync merge does make that call, `PagesSyncEngine.kt:682`) |
| **chronicle-all** | 1.00 | 1.00 | 1.00 | 22 | **front, the only full coverage** |
| one-index-app | 0.75 | 1.00 | 1.00 | 4 | front (a row written outside the repository isn't searchable) |
| per-kind-triggers | 1.00 | 0.00 | 1.00 | 36 | dominated (six queries) |
| like-only (control) | 0.75 | 0.00 | 0.50 | 0 | failed snippet, accents and one-search, as expected |

Growth counts every trigger as 1. The 18 triggers are generated from one list of sources, so this overstates the maintenance cost.

**FTS5 was not scored.** Room's annotations generate FTS3 and FTS4 only, and whether a device's SQLite includes FTS5 depends on the build. That hasn't been measured on a device, so FTS5 remains an unmeasured alternative, open for a later spike.

## Decision

**chronicle-all** was confirmed by the owner on 2026-10-01.
- **The index** is one standalone FTS4 table, `search_fts(text, kind, row_key)`, with the `unicode61` tokenizer, which folds accents, so "perche" finds "perché". `kind` and `row_key` aren't indexed.
- **Triggers** keep it current on every source table, so every write path is covered, ADR 01's sync import included.
  - Sources: `page` (title), `block` (content), `item` (title, every kind), `tracker` (name), `tracker_reading` (label + note) and `time_span` (comment).
  - A tombstoned or archived row, or blank text, leaves the index.
- **Queries** AND a prefix term per letter/digit run, as both apps already do. Block and page hits get `snippet()` highlights, as in Tendril.

## Consequences: fixes, not questions

- **The index is local and never syncs.** Row keys are ADR 01 ids, but the index is derived data. Each device builds its own from its synced rows, as both apps do now.
- **A full rebuild is available** (delete everything, then re-insert from the sources). It runs after a restore and on a detected mismatch. This replaces Tendril's `healIndex`, which missed stale rows, and Chronicle's migration-only backfill.
- **Result order is defined.** Tendril's `LIMIT` without `ORDER BY` returns an arbitrary subset. Hits are now ordered: title matches first, as Tendril ranks in Kotlin, then by recency, as Chronicle sorts.
- **Labels (ADR 08) aren't in the text index.** The label picker keeps substring `LIKE`, as Tendril's does, because a label name is short and found by part of a word.
- **Check-ins and journal text** (ADR 05) aren't indexed in either app today. Adding them is a feature, not part of this decision.
