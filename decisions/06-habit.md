# ADR 06: Habit, stored streak or derived presence

Status: **decided: item+tracker**. Date: 2026-09-30. Owners: Tendril and Chronicle, plus the owner's rule.

**Owner's rule (2026-09-30).** Constraint 0.14 applies to Habits: nothing stores or shows a streak or a missed-day count.

This ADR builds on four earlier decisions:
- ADR 02: one `item` table and a completion log.
- ADR 03: reminders are rows hanging off an item, and a day-view toggle.
- ADR 04: recurrence lives on `item`.
- ADR 05: "check-in" means mood, energy and pleasantness.

## Verified facts

The facts were verified with `tools/verify.py`; the raw output is in `verify/06-habit/`.

| App | Fact | Source | Map said |
|---|---|---|---|
| Tendril | `Habit` stores `streak`, `lastCompletedDate`, and `previousStreak`/`previousCompletedDate` as an undo snapshot. It also has `time`, `duration`, a `frequency` (count + DAY/WEEK/MONTH), counting amounts (`unit`, `amountPerCheckIn`, `dailyAmount`), pause and active windows, and `scheduleKind` INTERVAL or CALENDAR with a text `calendarRule`. | `Habit.kt:49-75` | confirmed (partial) |
| Tendril | The streak shows only when `show_habit_streaks` is on, **which defaults to off**; the trash sheet shows it regardless. A gap beyond the period resets it silently. Nothing counts missed days. | `TaskSettings.kt:35`; `TasksHabitsScreen.kt:843`; `CheckInHabitUseCase.kt:55` | not stated |
| Tendril | **Tendril already has `HabitPresence.kt`**: "presence, never absence", with no count of misses and no chain. | `HabitPresence.kt:10-22` | not stated (the map put presence under Chronicle only) |
| Tendril | `HabitCompletion` is tombstoned, not append-only. A redo inserts a new uid. Counting habits and calendar habits allow several rows a day. Sync inserts by uid, and a deletion on any device wins. | `HabitCompletion.kt:18,38-55`; `SnapshotSyncOrchestrator.kt:1984` | "append-only" (**refuted**) |
| Tendril | Habit reminders are a **second mechanism** (`Habit.time` and `HabitReminderAlarmReceiver`), and calendar-rule habits get no reminder at all. The calendar's Habits layer is a menu toggle, off by default. | `HabitSchedule.kt:71`; `CalendarViewModel.kt:50-53` | not stated |
| Chronicle | There is no habit entity. `habitPresenceOf` reads BOOLEAN and RATING trackers: a yes counts, any rating counts, and a no doesn't. It gives days this month, the last date, and a usual time withheld until 3 presences with a majority bucket. NUMBER trackers get a "Typically N apart" strip. | `HabitPresence.kt:20-74`; `TrackerDetailScreen.kt:310-328` | "withheld until three" (partial: only the usual time is withheld) |
| Chronicle | Goals store a period and a value, with progress as a **sum** over the window. Kinds are RECURRING or MILESTONE, and the direction comes from the tracker's polarity. Trackers have no cadence and no reminder. | `Goal.kt:24`; `GoalProgressRepository.kt:235`; `Enums.kt:52` | not stated |

## Scores (`06-habit-scores.md`, run by `tools/habit_sql.py` on SQLite)

| Option | Chronicle | Owner | Shared | Tendril | Growth | Status |
|---|---|---|---|---|---|---|
| habit-table | 0.00 | 1.00 | 0.00 | 1.00 | 56 | dominated (two logs, two reminder paths, two recurrence homes) |
| trackers-only | 1.00 | 1.00 | 0.50 | 0.33 | 38 | front (smallest; no cadence, pause or reminder) |
| item-kind | 0.00 | 1.00 | 1.00 | 1.00 | 42 | dominated by item+tracker |
| **item+tracker** | 1.00 | 1.00 | 1.00 | 1.00 | 41 | **front, the only full coverage** |
| with-streak (control) | 0.00 | 0.00 | 0.00 | 1.00 | 58 | failed the owner's rule, as expected |

One case (`shared-one-log`) was removed before scoring because it was hand-marked. What it meant to test, a tracker reading counting as a habit check-in with no second entry, is measured by `chronicle-tracker-presence`.

## Recommendation

**item+tracker**: a habit is an `item` of kind HABIT.
- **Cadence** is ADR 04's recurrence. That covers Tendril's INTERVAL `frequency` and its CalendarRule cases, and per-day times are BYHOUR/BYMINUTE.
- **Reminders** are ADR 03 reminder rows. This also fixes calendar-rule habits, which get no reminder today.
- **Pause** is a `pause_from`/`pause_until` pair, allowed on HABIT only.
- **The tracker link.** `tracker_id` is required on a HABIT. "Did it" is a BOOLEAN tracker, "8 glasses" a NUMBER tracker with a daily goal of 8. A check-in is a reading on that tracker, so logging it on the Trackers screen or on the habit is the same row.
- **Presence** is `HabitPresence` as both apps already have it: days this month, the last date, and the usual time (withheld below 3 presences). There is no streak and no missed count anywhere. `streak`, `previousStreak` and `lastCompletedDate` are not carried over; the last date is derived.
- **Calendar and timeline.** The calendar layer and day-view toggle are the same kind filter as ADR 03's reminders toggle, and off by default, as Tendril's Habits layer already is.

## Open for the owner

**The word "check-in".** Tendril uses it for ticking a habit (`CheckInHabitUseCase`), and ADR 05 uses it for mood, energy and pleasantness. The habit action needs another word.

## Decision

**item+tracker** was confirmed by the owner on 2026-09-30.

Ticking a habit is called **Log** ("Log water"). "Check-in" is kept for mood, energy and pleasantness (ADR 05).
