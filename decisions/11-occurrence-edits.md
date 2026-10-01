# ADR 11: Occurrence edits, one edit log for every item

Status: **decided: edit-log+move**. Date: 2026-10-01. Owner: Tendril, the only app that edits single occurrences.

This contest was found by the sole-owner probe (`docs/sole-owner-probe-2026-10-01.md`). Tendril has two mechanisms for "change just this one". ADR 02 put tasks on `item` and ADR 06 put habits there, so both mechanisms now meet on one table.

This ADR builds on:
- ADR 04: recurrence lives on `item`.
- ADR 06: habits are items.
- ADR 01: sync.

It **amends ADR 04** in two places and **ADR 02** in one:
- ADR 04 said planner placements are stored "as per-occurrence exception rows, as Tendril already stores its edits". Tendril stores them as Week-scope edits in `HabitScheduleEdit`.
- ADR 04 said Tendril's exception rows carry over unchanged.
- ADR 02 said the exception columns come with `item`.

## Verified facts

The facts were verified with `tools/verify.py`; the raw output is in `verify/11-occurrence-edits/`.

| App | Fact | Source |
|---|---|---|
| Tendril | **Tasks and events**: an override is an Entry row copied from the item for one occurrence (`originalEntryId`, `originalOccurrenceDate`), so it copies the title at that moment. A skip row (`isExceptionSkip`) is written only by the ICS importer; no UI path skips one task occurrence. The scopes are THIS_ONE or ALL, with no "this and following". | `Entry.kt:47-48`; `EntryEditor.kt:15,92-97`; `IcsImporter.kt:57` |
| Tendril | An exception is keyed by the pair (base, occurrence), with no unique constraint. Two devices overriding the same occurrence leave two rows. `expand()` keeps one of them by list order, not by `updatedAt`, and the other shows as an **orphan** occurrence. | `EntryOccurrences.kt:79,130` |
| Tendril | **Calendar habits**: `HabitScheduleEdit` has 8 columns (`id`, `uid`, `target` HABIT or BLOCK, `refUid`, `scope`, `changes`, `createdAt`, `deletedAt`). Scopes: Occurrence, Day (one habit), Week (a Monday plus optional days), From (a date plus optional days) and Extra (an added occurrence). | `HabitScheduleEdit.kt:25-35`; `CalendarSchedule.kt:97-104`; `PlanCodec.kt:105` |
| Tendril | Edits apply in (`createdAt`, `uid`) order, **field by field**. Sync inserts each row once and tombstones it once, so concurrent edits of different fields both survive. | `CalendarSchedule.kt:222`; `SnapshotSyncOrchestrator.kt:1784-1785` |
| Tendril | A one-off "Move to another day" writes **two** rows, an Occurrence skip and an Extra. The weekly variant writes one From edit that changes the weekdays rule. The planner's confirmed days are one Week edit, and its suggestions are recomputed on every read, never stored. | `EditMode.kt:200-209`; `HabitWeek.kt:71`; `CalendarSchedule.kt:335-339` |
| Tendril | A BLOCK-target edit is decoded but never written by production code (0 hits). `HabitBlock.overrides` is a standing per-weekday rule. | `CalendarSchedule.kt:258-259`; `HabitBlock.kt:38` |
| Chronicle | No per-occurrence edits: a reminder holds one `dueAt`, rolled forward in place, and editing rewrites the whole rule. Snooze is device-local in DataStore. | `ReminderEntity.kt:24`; `ReminderSheet.kt:70`; `PendingAlerts.kt:22,99` |
| Mnemo | No per-occurrence edits. Snooze overwrites `nextFireAtEpochMillis`, so a cron occurrence between the fire and the snooze's end is lost. | `ReminderRepository.kt:126-132,174` |

## Re-scored 2026-10-01

**Why:** the owner's later answer, that a clash on one occurrence asks, became a case (`owner-occurrence-clash-asks`):
- two retimes of the same occurrence must ask;
- a retime against a re-block must not.

Detecting a clash needs a base stamp per edit row, so every option that asks gains one column. A sensitivity pass (`tools/sensitivity.py`) then found the patch-rows count had left out its ADR 01 stamps. It merges field by field, so each of its six data fields carries an `(hlc, device)` pair: +12 columns. The edit log needs only one device column. The current scores are in `11-occurrence-edits-scores.md`.

| Option | Owner | Shared | Tendril | Growth | Status |
|---|---|---|---|---|---|
| full-copy | 0.00 | 0.33 | 0.67 | 4 | front (a copy row can't tell a re-block from a retime, so it asks wrongly) |
| edit-log | 1.00 | 0.67 | 1.00 | 11 | dominated |
| **edit-log+move** | 1.00 | 1.00 | 1.00 | 11 | **front, the only full coverage on the front** |
| as-is | 1.00 | 0.00 | 1.00 | 15 | dominated |
| patch-rows | 1.00 | 1.00 | 1.00 | 24 | dominated (+12 per-field stamp columns) |
| rewrite (control) | 0.00 | 0.33 | 0.00 | 0 | failed its 9 cases, as expected |

**Sensitivity:** every option's growth was varied independently over ×0.5 to ×2, giving 7,776 combinations. The pick stays the only full-coverage option on the front in 88.9% of them. Displacing it would need its own count roughly doubled and patch-rows' roughly halved at the same time. The decision is unchanged.

## Scores as first scored (2026-10-01, before the clash answer)

| Option | Shared | Tendril | Growth | Status |
|---|---|---|---|---|
| full-copy | 0.33 | 0.67 | 3 | front (no week confirmations; concurrent edits and renames lost) |
| edit-log (Tendril's exact encoding) | 0.67 | 1.00 | 9 | dominated (a move is skip + extra, so two concurrent moves make two occurrences) |
| **edit-log+move** | 1.00 | 1.00 | 9 | **front, full coverage** |
| as-is (both mechanisms) | 0.00 | 1.00 | 12 | dominated |
| patch-rows | 1.00 | 1.00 | 11 | dominated by 2 columns, a hand count |
| rewrite (control) | 0.33 | 0.00 | 0 | failed its 8 cases, as expected |

**edit-log+move was added after the first run.** Without it, patch-rows would have won only because of Tendril's skip-plus-extra encoding of a move. Growth for edit-log is Tendril's real table and for full-copy the three Entry columns; for patch-rows it is a hand count of the designed columns.

## Decision

**edit-log+move** was confirmed by the owner on 2026-10-01.
- **One `occurrence_edit` table** for every repeating item: `id`, `item_id`, `scope`, `changes`, `created_at`, `deleted_at`, plus ADR 01's identity. It is insert-once and tombstone-once.
  - `scope` is OCCURRENCE (an occurrence key), DAY, WEEK (a Monday plus optional days), FROM (a date plus optional days) or EXTRA (a date).
  - `changes` holds only the fields the edit sets: skip, deleted, moved_to, time, duration, block, sort_order, title, rule, rule_patch, pause and week_days. These are Tendril's full set (`CalendarSchedule.kt:213-222`) plus `moved_to` and `title`.
  - Edits apply in the order of their ADR 01 `(hlc, deviceId)` stamp, field by field. `created_at` is that stamp, not a wall-clock time, so a device with a fast clock can't win every comparison.
- **A move is one OCCURRENCE edit with `moved_to`.** Two concurrent moves of one occurrence leave it once.
- **A clash on one occurrence asks the person** (owner answer, 2026-10-01, raised by the fresh-eyes audit). Two OCCURRENCE or FROM edits made on different devices since the last sync that set the same schedule field (moved_to, time, duration, rule, week_days) raise ADR 01's prompt: keep mine / take theirs / keep both. "Keep both" keeps two occurrences. Non-schedule fields (title, block, sort_order) merge silently, later stamp first.
- **An occurrence shows the series' current fields** except the ones an edit sets, so renaming a series renames its moved occurrences.
- **Tasks and events gain** "this week" and "from now on", which only habits had.
- **The planner** (ADR 04's PLANNED kind) stores confirmed weeks as WEEK edits. Its suggestions stay recomputed and unstored.
- **Tendril's exception columns on Entry aren't carried over.** An ICS EXDATE becomes an OCCURRENCE skip edit.

**How the clash prompt relates to the scores.** `occurrence_sim.py` models the silent later-wins path. The prompt only adds a question on top: an answer of mine or theirs gives the simulated result, and "keep both" is the person's explicit choice. So no case's outcome changes.

## Consequences: fixes, not questions

- **The target is `item_id` only.** Tendril's BLOCK target was never written, and time-block changes stay on the block row (`HabitBlock.overrides`).
- **Undo** tombstones the edit row, so the series underneath shows again.
- **Log growth.** Edits on occurrences more than a year in the past may be folded into the completion log or dropped. That is a storage policy, left for the SPEC.
- **Chronicle and Mnemo** lose nothing: they have no per-occurrence edits, and editing a whole series stays a rewrite of the rule. Snooze remains ADR 03's.
