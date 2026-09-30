# ADR 11: Occurrence edits, one edit log for every item

Status: **decided: edit-log+move**. Date: 2026-10-01. Owner: Tendril, the only app that edits single occurrences.

This contest was found by the sole-owner probe (`docs/sole-owner-probe-2026-10-01.md`). Tendril has two mechanisms for "change just this one", and ADR 06 put both of their owners, tasks and habits, on `item`.

This ADR builds on:
- ADR 04: recurrence lives on `item`.
- ADR 06: habits are items.
- ADR 01: sync.

It **amends ADR 04**, whose line 74 said planner placements are stored "as per-occurrence exception rows, as Tendril already stores its edits". Tendril stores them as Week-scope edits in `HabitScheduleEdit`.

## Verified facts

The facts were verified with `tools/verify.py`; the raw output is in `verify/11-occurrence-edits/`.

| App | Fact | Source |
|---|---|---|
| Tendril | **Tasks and events**: an override is an Entry row copied from the item for one occurrence (`originalEntryId`, `originalOccurrenceDate`), so it copies the title at that moment. A skip row (`isExceptionSkip`) is written only by the ICS importer; no UI path skips one task occurrence. The scopes are THIS_ONE or ALL, with no "this and following". | `Entry.kt:47-48`; `EntryEditor.kt:15,92-97`; `IcsImporter.kt:57` |
| Tendril | An exception is keyed by the pair (base, occurrence), with no unique constraint. Two devices overriding the same occurrence leave two rows. `expand()` keeps one of them by list order, not by `updatedAt`, and the other shows as an **orphan** occurrence. | `EntryOccurrences.kt:79,130` |
| Tendril | **Calendar habits**: `HabitScheduleEdit` has 8 columns (`id`, `uid`, `target` HABIT or BLOCK, `refUid`, `scope`, `changes`, `createdAt`, `deletedAt`). Scopes: Occurrence, Day (one habit), Week (a Monday plus optional days), From (a date plus optional days) and Extra (an added occurrence). | `HabitScheduleEdit.kt:25-33`; `CalendarSchedule.kt:97-104`; `PlanCodec.kt:105` |
| Tendril | Edits apply in (`createdAt`, `uid`) order, **field by field**. Sync inserts each row once and tombstones it once, so concurrent edits of different fields both survive. | `CalendarSchedule.kt:222`; `SnapshotSyncOrchestrator.kt:1784-1785` |
| Tendril | "Move to another day" writes **two** rows: an Occurrence skip and an Extra. The planner's confirmed days are one Week edit, and its suggestions are recomputed on every read, never stored. | `EditMode.kt:202-203`; `HabitWeek.kt:71`; `CalendarSchedule.kt:335-339` |
| Tendril | A BLOCK-target edit is decoded but never written by production code (0 hits). `HabitBlock.overrides` is a standing per-weekday rule. | `CalendarSchedule.kt:258-259`; `HabitBlock.kt:38` |
| Chronicle | No per-occurrence edits: a reminder holds one `dueAt`, rolled forward in place, and editing rewrites the whole rule. Snooze is device-local in DataStore. | `ReminderEntity.kt:24`; `ReminderSheet.kt:70`; `PendingAlerts.kt:22,99` |
| Mnemo | No per-occurrence edits. Snooze overwrites `nextFireAtEpochMillis`, so a cron occurrence between the fire and the snooze's end is lost. | `ReminderRepository.kt:126-132,174` |

## Scores (`11-occurrence-edits-scores.md`, run by `tools/occurrence_sim.py`, two devices that sync)

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
  - `changes` holds only the fields the edit sets: skip, moved_to, time, duration, block and title.
  - Edits apply in (`created_at`, `id`) order, field by field.
- **A move is one OCCURRENCE edit with `moved_to`.** Two concurrent moves of one occurrence leave it once, and the later edit wins.
- **An occurrence shows the series' current fields** except the ones an edit sets, so renaming a series renames its moved occurrences.
- **Tasks and events gain** "this week" and "from now on", which only habits had.
- **The planner** (ADR 04's PLANNED kind) stores confirmed weeks as WEEK edits. Its suggestions stay recomputed and unstored.
- **Tendril's exception columns on Entry aren't carried over.** An ICS EXDATE becomes an OCCURRENCE skip edit.

## Consequences: fixes, not questions

- **The target is `item_id` only.** Tendril's BLOCK target was never written, and time-block changes stay on the block row (`HabitBlock.overrides`).
- **Undo** tombstones the edit row, so the series underneath shows again.
- **Log growth.** Edits on occurrences more than a year in the past may be folded into the completion log or dropped. That is a storage policy, left for the SPEC.
- **Chronicle and Mnemo** lose nothing: they have no per-occurrence edits, and editing a whole series stays a rewrite of the rule. Snooze remains ADR 03's.
