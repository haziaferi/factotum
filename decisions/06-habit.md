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
| Tendril | `Habit` stores `streak`, `lastCompletedDate`, and `previousStreak`/`previousCompletedDate` as an undo snapshot. It also has `time`, `duration`, a `frequency` (count + DAY/WEEK/MONTH), counting amounts (`unit`, `amountPerCheckIn`, `dailyAmount`), pause and active windows, and `scheduleKind` INTERVAL or CALENDAR with a text `calendarRule`. | `Habit.kt:49-95` | confirmed (partial) |
| Tendril | The streak shows only when `show_habit_streaks` is on, **which defaults to off**; the trash sheet shows it regardless. A gap beyond the period resets it silently. Nothing counts missed days. | `TaskSettings.kt:35`; `TasksHabitsScreen.kt:843`; `HabitTrashSheet.kt:169` (ungated); `CheckInHabitUseCase.kt:57` | not stated |
| Tendril | **Tendril already has `HabitPresence.kt`**: "presence, never absence", with no count of misses and no chain. | `HabitPresence.kt:10-22` | not stated (the map put presence under Chronicle only) |
| Tendril | `HabitCompletion` is tombstoned, not append-only. A redo inserts a new uid. Counting habits and calendar habits allow several rows a day. Sync inserts by uid, and a deletion on any device wins. | `HabitCompletion.kt:18,38-55`; `SnapshotSyncOrchestrator.kt:1984` | "append-only" (**refuted**) |
| Tendril | Habit reminders are a **second mechanism** (`Habit.time` and `HabitReminderAlarmReceiver`), and calendar-rule habits get no reminder at all. The calendar's Habits layer is a menu toggle, off by default. | `HabitSchedule.kt:71`; `CalendarViewModel.kt:50-53` | not stated |
| Chronicle | There is no habit entity. `habitPresenceOf` reads BOOLEAN and RATING trackers: a yes counts, any rating counts, and a no doesn't. It gives days this month, the last date, and a usual time withheld until 3 presences with a majority bucket. Every tracker type gets a "Typically N apart" strip, and presence is computed only for BOOLEAN and RATING. | `HabitPresence.kt:20-82`; `TrackerDetailScreen.kt:302-328`; `TrackerDetailViewModel.kt:139-141` | "withheld until three" (partial: only the usual time is withheld) |
| Chronicle | Goals store a period and a value, with progress as a **sum** over the window. Kinds are RECURRING or MILESTONE, and the direction comes from the tracker's polarity. Trackers have no cadence and no reminder. | `Goal.kt:24`; `GoalProgressRepository.kt:231-235`; `Enums.kt:52` (MILESTONE_DAYS), `:62` (GoalKind) | not stated |

## Re-scored 2026-10-01

**Why:** the planner check (`docs/spikes-2026-10-01.md` §9.2) proved a HABIT needs `block_id` and `duration_min`. Both columns were added to **every** option that can hold a habit, together with a case that requires them (`tendril-planner-fields`). The current scores are in `06-habit-scores.md`.

| Option | Chronicle | Owner | Shared | Tendril | Growth | Status |
|---|---|---|---|---|---|---|
| habit-table | 0.00 | 1.00 | 0.00 | 1.00 | 58 | dominated |
| trackers-only | 1.00 | 1.00 | 0.50 | 0.25 | 38 | front (it has no habit to carry the columns) |
| item-kind | 0.00 | 1.00 | 1.00 | 1.00 | 44 | dominated |
| **item+tracker** | 1.00 | 1.00 | 1.00 | 1.00 | 43 | **front, still the only full coverage** |
| with-streak (control) | 0.00 | 0.00 | 0.00 | 1.00 | 60 | failed as expected |

The decision is unchanged.

## Scores as first scored (2026-09-30)

| Option | Chronicle | Owner | Shared | Tendril | Growth | Status |
|---|---|---|---|---|---|---|
| habit-table | 0.00 | 1.00 | 0.00 | 1.00 | 56 | dominated (tracker readings don't count as presence; two reminder paths; two recurrence homes) |
| trackers-only | 1.00 | 1.00 | 0.50 | 0.33 | 38 | front (smallest; no cadence, pause or reminder) |
| item-kind | 0.00 | 1.00 | 1.00 | 1.00 | 42 | dominated by item+tracker |
| **item+tracker** | 1.00 | 1.00 | 1.00 | 1.00 | 41 | **front, the only full coverage** |
| with-streak (control) | 0.00 | 0.00 | 0.00 | 1.00 | 58 | failed the owner's rule, as expected, plus the 3 cases habit-table loses |

One case (`shared-one-log`) was removed before scoring because it was hand-marked. What it meant to test, a tracker reading counting as a habit check-in with no second entry, is measured by `chronicle-tracker-presence`.

## Recommendation

**item+tracker**: a habit is an `item` of kind HABIT.
- **Cadence** is ADR 04's recurrence. Measured: one INTERVAL case (every 2 days at 08:00).
  - **Measured 2026-10-01** (`docs/spikes-2026-10-01.md` §9.2): Daily, Once, Weekdays, EveryNDays, EveryNWeeks and EveryNHours map to RRULE, and all 8 test rules match. TimesPerDay with fixed times is a **RULE_SET**, one RRULE per time: a single BYHOUR/BYMINUTE rule gave 336 extra occurrences when the minutes differ. (Amended: this line first said BYHOUR/BYMINUTE and was unmeasured.)
  - **Not expressible in RRULE:** Tendril's **planner** rules. `TimesPerWeek(n, days)` places n days per week, load-balanced and confirmed per week, and `TimesPerDay` can place slots in time blocks (`CalendarSchedule.kt:40-50,313-333`). ADR 04 gains a PLANNED kind for these (see its amendment).
  - **Active window:** `activeUntil` becomes UNTIL. DTSTART is the **first date on or after `activeFrom` (or the day the habit was created) that the rule's own anchor allows**; for EveryNWeeks, the Monday of an aligned week. (Amended 2026-10-01: this line first said activeFrom *becomes* DTSTART. Measured, that shifts an off-grid every-3-days habit onto different days, 14/14 wrong.)
  - **Two more columns on HABIT** (measured 2026-10-01, PLANNED round trip 0/500 without them and 500/500 with them): `block_id`, the default time block (Tendril's `blockUid`), and `duration_min` (Tendril's `duration`). The planner places a habit by the first and balances the week by the second.
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

## Owner answers, 2026-10-02

A source survey before building slice 06 found gaps the decision did not settle (Tendril `HabitSchedule.kt:36`, `HabitPresence.kt:50-67`; Chronicle `HabitPresence.kt:44-48`). The owner answered:

1. **Rolling habits stay rolling.** Tendril's default schedule, "due again N days, weeks or months after the last Log", becomes a recurrence kind of its own, ROLLING, beside ADR 04's. A late Log moves the next due date.
2. **Presence counts a "yes", any rating, and a number above 0.** A "no" does not count. Number habits also show today's and this month's amounts, as Tendril's did.
3. **The day boundary is a personal setting** (ADR 09), default midnight: it decides which day a Log made after midnight counts for.
4. **Deleting a tracker that a habit uses:** open. The owner asked whether making the tracker optional would be simpler.

