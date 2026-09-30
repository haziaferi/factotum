# ADR 07: Timed interval, time log or session

Status: **decided: activity-item; several timers at once**. Date: 2026-09-30. Owners: Tendril and Chronicle.

The map listed this row as *duplicated* ("one model expresses the other without loss"). Verification refuted that: Tendril times items and Chronicle times activities, and neither schema holds the other's owner. So it went through the full contest.

This ADR builds on three earlier decisions:
- ADR 02: one `item` table.
- ADR 03 and ADR 06: reminders and habits are item kinds, and item queries filter by kind.
- ADR 01: sync.

## Verified facts

The facts were verified with `tools/verify.py`; the raw output is in `verify/07-timelog/`.

| App | Fact | Source | Map said |
|---|---|---|---|
| Tendril | `TimeLog` has 8 columns: `id` (local Long), `uid`, `entryId?`, `habitId?`, `startedAt`, `endedAt?` (null while running), `deletedAt?` and `updatedAt`. Exactly one owner is set, which is enforced in code only (`TrackTarget`), not by a CHECK. | `TimeLog.kt:30,42-53`; `TimeTracker.kt:29-32` | "startedAt, endedAt, entryId or habitId" (partial: four columns missing) |
| Tendril | **One timer at a time**: `start()` stops every open log first. After a merge, two devices can each leave one open. | `TimeTracker.kt:36,60-62,73` | not stated |
| Tendril | Both owner foreign keys are `CASCADE`, but the soft-delete of an entry or habit doesn't touch its logs, so they are still counted. | `TimeLog.kt:36-37`; `EntryDao.kt:125,131` | not stated |
| Tendril | There is no manual entry and no editing of a past log: the only calls are start, stop and toggle (a grep for add, edit, update or backfill found 0 hits). | `TimeTracker.kt:60-82` | not stated |
| Tendril | Totals sum each log's clipped duration, so **overlaps count twice**. Day queries select by start time, while `loggedSpans` clips at midnight, so the two rules differ. | `TimeLogTotals.kt:15-21`; `TimeLogDao.kt:32` | not stated |
| Tendril | Sync: a deletion on any device wins; otherwise the later `updatedAt` wins. | `SnapshotSyncOrchestrator.kt:2079-2082` | not stated |
| Chronicle | `SessionEntity` has 9 columns: `id`, `activityId`, `startedAtMillis`, `endedAtMillis?`, `comment?`, `updatedAtMillis`, `updatedByDevice`, `deletedAtMillis?` and `plannedRun?` (a RunStamp). `ActivityEntity` has name, colour, icon, `archived`, `categoryId?` (SET NULL), `sortOrder` and stamps. | `SessionEntity.kt:34-48`; `ActivityEntity.kt:16-38` | "activity sessions" |
| Chronicle | **Several timers at once**: there is no check for a running session. | `SessionRepository.kt:42` | not stated |
| Chronicle | An activity with sessions can't be hard-deleted (FK NO ACTION). A tombstone on the activity also tombstones its live sessions and goals. | `SessionEntity.kt:11-17`; `ActivityRepository.kt:101-133` | not stated |
| Chronicle | Manual entry and editing exist (`logManualSession`, `updateSession`), and an edit can't bring a tombstoned session back. | `SessionRepository.kt:74,96,102` | not stated |
| Chronicle | Totals also count overlaps twice, and a range query selects by start only. | `ActivityDetailViewModel.kt:256-259`; `CoreDao.kt:72-73` | not stated |
| Chronicle | Goals point at `targetType` ACTIVITY or TRACKER plus a `targetId`, with no foreign key. | `GoalEntity` (`targetType`, `targetId`) | not stated |

## Scores (`07-timelog-scores.md`, run by `tools/timelog_sql.py` on SQLite)

| Option | Chronicle | Shared | Tendril | Growth | Status |
|---|---|---|---|---|---|
| two-tables | 1.00 | 0.00 | 1.00 | 46 | dominated (the day's total and "what is running" live in two tables) |
| timelog-only | 0.00 | 0.00 | 1.00 | 38 | dominated (activities can't be timed) |
| session-only | 1.00 | 0.00 | 0.25 | 40 | dominated (tasks and habits can't be timed) |
| one-span | 1.00 | 1.00 | 1.00 | 41 | dominated by activity-item (same coverage, +4) |
| **activity-item** | 1.00 | 1.00 | 1.00 | 37 | **front** |
| bare (control) | 0.00 | 1.00 | 0.00 | 37 | failed its 8 owner cases, as expected |

The 4-point margin between activity-item and one-span doesn't depend on how large `item` grows:
- activity-item adds 5 columns and 1 trigger to `item`, and drops the `activity` table (8 columns).
- one-span keeps `activity` and adds a second owner column.

The growth metric can't see one cost, the same one ADR 03 and ADR 06 accepted: every item reader filters by kind.

## Decision

**activity-item** was confirmed by the owner on 2026-09-30.
- **An activity is an `item` of kind ACTIVITY.** `icon`, `color` and `archived` are allowed on ACTIVITY only (CHECK). `sort_order` is allowed on ACTIVITY and HABIT, because Tendril habits keep a manual order inside a time block (`Habit.kt:86-87`). The activity's category is ADR 08's `label_id`, which is allowed on ACTIVITY and HABIT (amended 2026-10-01; this line first said `category_id`, on ACTIVITY only).
  - Activities never appear on the calendar, the task list or the day view; those readers filter by kind.
  - Goals with `target_type` ACTIVITY now point at the item id.
- **One `time_span` table**: `item_id` (required; CASCADE for tasks and habits), `started_at`, `ended_at` (null while running), `comment`, `planned_run`, plus ADR 01's identity and stamps.
  - A trigger refuses to hard-delete an ACTIVITY item that still has spans, keeping Chronicle's backstop.
  - Tombstoning an activity tombstones its live spans and goals, as Chronicle does now.
- **Several timers at once** (the owner's answer; Chronicle's rule). Starting a timer doesn't stop another. Tendril's "start stops the other" rule is not carried over.

## Consequences: fixes, not questions

Each bullet names which app has the gap or the feature. All are fixed in the merge.
- **Overlaps are merged in every total.** Both apps count overlapping time twice (`TimeLogTotals.kt:21`; `ActivityDetailViewModel.kt:256`). With several timers allowed, overlap is normal, so totals such as "time tracked today" take the union of intervals. A total for one owner still counts that owner's own spans.
- **Midnight-crossing spans** were an owner question, not a gap. Tendril counts a span for the day it began, on purpose (`TimeLogDao.kt:31-33`). Chronicle selects by start but clips to the window (`CoreDao.kt:73`; `ActivityDetailViewModel.kt:256-259`). See *Owner answer, 2026-10-01* below.
- **Spans whose owner is tombstoned drop out of totals** (Tendril's gap). Tendril's soft-delete leaves them counted, whereas Chronicle already tombstones them (`ActivityRepository.kt:118-132`).
- **Manual entry and editing** are a Chronicle feature that Tendril lacks. They apply to every owner, tasks and habits included.
- **Running spans after a sync merge** (Tendril's case, `TimeTracker.kt:45-46`): ADR 01's merge can leave one open span per device. That is now allowed rather than a conflict, because several timers may run.

## Owner answer, 2026-10-01

This question was raised by the fresh-eyes audit (`docs/fresh-eyes-2026-10-01.md`).

**A span counts wholly for the day it started**, as in Tendril (`TimeLogDao.kt:31-33`, "the day the person was working"). A 23:00–01:00 span gives 2 h to Monday.
- **Every window follows the same rule**: day, week, and a goal's period. So daily totals always add up to the weekly one. Tendril's week summary clips (`TimeLogTotals.kt:15-21`), and Chronicle's `totalIn` clips (`ActivityDetailViewModel.kt:256-259`). Neither clip is carried over.
- **A running span** counts up to now, for the day it started.
