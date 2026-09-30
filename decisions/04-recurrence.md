# ADR 04: How recurrence is encoded

Status: **decided: rrule+ext**. Date: 2026-09-30. Owners: Tendril, Chronicle, Mnemo.

This ADR builds on ADR 03: recurrence lives only on `item`, including items of kind REMINDER, so it is encoded exactly once.

## Verified facts

The facts were verified with `tools/verify.py`; the raw output is in `verify/04-recurrence/`.

| App | Fact | Source | Map said |
|---|---|---|---|
| Tendril | Rules are stored as `"FIXED:<rrule>"` / `"ELASTIC:<ISO period>"`. The RRULE expander supports DAILY/WEEKLY/MONTHLY/YEARLY, INTERVAL, BYDAY (with ordinals), BYMONTHDAY (including negative), BYMONTH, WKST, COUNT and UNTIL. It rejects BYSETPOS, BYWEEKNO, BYYEARDAY, BYHOUR, BYMINUTE and BYSECOND, and silently ignores unknown parts. There is no MINUTELY or HOURLY. | `RecurrenceSpec.kt:33-116`; `Converters.kt:141` | not stated |
| Tendril | Elastic steps forward by whole periods until the date is in the future, and missed occurrences are skipped. Its units are DAY, WEEK and MONTH. The UI offers only None, Daily, Weekly and Monthly. | `ResolveEntryUseCase.kt:117`; `RecurrenceRule.kt:39`; `EntryEditSheet.kt:257` | "a miss goes overdue" (**refuted**) |
| Tendril | Per-occurrence exceptions are Entry rows: a skip row, or an override row with `recurrenceRule = null`. ICS import reduces a task's RRULE to FREQ and INTERVAL only, dropping BYDAY, COUNT and UNTIL, and drops YEARLY rules entirely. | `Entry.kt:48`; `IcsImporter.kt:57` (EXDATE), `:103,125-134` (reduction) | not stated |
| Chronicle | RepeatRule has 7 cases. EveryInterval sits on a grid from `dueAt` (the UI allows 5 min to 365 days; the domain type has no minimum). Daily, Weekly, Monthly, Weekdays and RandomDays step from the previous due time. Missed occurrences are skipped to the first one after now. | `Enums.kt:83`; `RepeatSchedule.kt:30-95` | "7 cases" confirmed; None and EveryInterval were missing from the map's list |
| Chronicle | **The RandomDays gap is not stored.** It is recomputed from a deterministic seed (occurrence time, min, max), so every device gets the same gap. | `RepeatSchedule.kt:39-40` | not stated |
| Tendril + Chronicle | **Month ends drift.** Both step from the previous date, so Jan 31 becomes Feb 28, then Mar 28, and never returns to the 31st. This contradicts Tendril's own rule, "anchored to the original schedule". | `ResolveEntryUseCase.kt:117`; `RepeatSchedule.kt:30`; `RecurrenceRule.kt:27` | not stated (a defect) |
| Mnemo | Cron has exactly 5 numeric fields with lists, ranges and steps. There are no names, no `L W # ?`, and no seconds field. When both day fields are restricted, a day matches either one (the crontab OR rule). Users type raw cron with no builder. | `ScheduleCalculator.kt:76-119`; `EditReminderScreen.kt:235` | "largely converts" (**confirmed**; the one exception is the OR rule) |
| Mnemo | STOCHASTIC draws one uniform time on the next allowed day each time it fires, so one per allowed day over time. On the creation day the window start is clamped to now. The draw is random and stored in `nextFireAt`, so two devices would draw different times. | `ScheduleCalculator.kt:163-181` | confirmed |
| Mnemo | **A missed fire fires once, late, after boot**, and only then moves forward. Tendril and Chronicle skip it. | `BootReceiver.kt:35-47` | "no backlog" (**refuted**) |

## Scores (`04-recurrence-scores.md`, run by `tools/recurrence_sim.py`)

For each case, the harness computes the true occurrence dates with a port of the owner app's verified rule. The one exception is month ends: there the expected series is the anchored one (the fix below), not either app's drifting rule. It then converts the rule into each encoding, expands it with that encoding's own engine, and compares the two. Before scoring, five deliberately wrong conversions were run through it, and all five were rejected: the 31st without the clamp, every 2 days instead of 3, the last Tuesday instead of the second, `*/15` missing :45, and the day-OR-weekday rule written as AND. So the harness can tell a wrong encoding from a right one.

| Option | Chronicle | Mnemo | Tendril | Columns | Status |
|---|---|---|---|---|---|
| rrule | 0.67 | 0.50 | 1.00 | 1 | front (smallest; loses both random schedules and cron's OR rule) |
| **rrule+ext** | 1.00 | 1.00 | 1.00 | 7 + 4 kinds | **front, the only full coverage** |
| cron+ext | 0.67 | 1.00 | 0.00 | 7 + 3 kinds | front (loses every Tendril rule and 90-minute intervals) |
| chronicle-enum | 1.00 | 0.00 | 0.25 | 2 + 7 kinds | front (loses cron, windows, ordinals, UNTIL, and month ends) |
| one-shot (control) | 0 | 0 | 0 | 0 | failed all 11 |

The map listed two irreducible forms, "anchored" and "stochastic". Measured, the anchored interval is **reducible**: it is `FREQ=…;INTERVAL=n` from DTSTART, and the month-end clamp is `BYMONTHDAY=31,-1;BYSETPOS=1`. Three forms need an extension. Chronicle's RandomDays and Mnemo's random window cannot be written in RRULE at all. Cron's day-OR-weekday rule can, as a union of two RRULEs stored as RULE_SET.

## Recommendation

**rrule+ext**, stored on `item`:

- `recurrence_kind` is one of RRULE, RULE_SET, RANDOM_DAYS or RANDOM_WINDOW.
- `rrule` holds the rule text. For RULE_SET it holds several RRULEs, one per line.
- RANDOM_DAYS uses `rand_min_days` and `rand_max_days`. RANDOM_WINDOW uses `window_days_mask`, `window_start` and `window_end`.
- CHECKs tie each kind to its columns. Chronicle's mapper crashes on a kind without its value (`EntityMappers.kt:213`), and the database refuses that here instead.
- The expander must support MINUTELY, HOURLY, BYHOUR, BYMINUTE and BYSETPOS, which Tendril's rejects today.
- The UI offers presets and a builder. Raw cron is accepted as input and converted, never stored.

**Fixes, not decisions.**
- **Month ends** are anchored to the original date. Neither app does this today, although Tendril's own comment promises it.
- **Random draws are seeded** deterministically, from the item's id and the occurrence date, for both extensions. Every device then computes the same time, and nothing drawn is stored. Mnemo's random stored draw would make two synced devices ring at different times.

## Decision

The owner picked **rrule+ext** on 2026-09-30.

**Missed occurrences depend on the reminder's `alert_kind` (ADR 03).** The owner's words: "If it's an alarm, it should wake the phone if it's off and sound anyway if the app is killed, otherwise, if it's only a notification, it fires once late, then continues."

- **ALARM** is scheduled with `setAlarmClock`, as Chronicle already does for ALARM (`AndroidAlarmScheduler.kt:69`). It rings through a foreground service and a full-screen activity. The OS holds the alarm, so it fires while the app process is dead and while the phone sleeps or dozes.
- **NOTIFICATION** follows Mnemo's rule. A missed fire is delivered once, late, when the phone boots or the app next starts. Then the schedule continues from the next future occurrence. There is never a backlog of several missed occurrences.

**Platform limits, recorded so they aren't mistaken for defects:**
1. **A phone that is powered off cannot be switched on** by a third-party app. Only some manufacturers' own clock apps have a power-off alarm. What Factotum does is ring the missed ALARM as soon as the phone boots, which is the late-fire rule applied to alarms.
2. **A *force-stopped* app** (Settings → Force stop, or some vendors' aggressive task killers) has its alarms cancelled by Android until the app is opened again. A killed process is fine; a force-stop is not. The app should detect this case on its next start and say so, rather than stay silent.

## Consequences

- **Per-occurrence edits** are ADR 11's `occurrence_edit` log. (Amended 2026-10-01: this line first said Tendril's exception rows carry over unchanged; ADR 11 replaced them.)
- **Sync (ADR 01).** All recurrence columns are in the item's *schedule* group, so a concurrent change to a rule gets hybrid+'s prompt.

## Amendment: fresh-eyes audit, 2026-09-30

Tendril's habit planner rules were not in the harness (ADR 06 found them). `CalendarRule.TimesPerWeek(n, days)` places n days a week, spread and load-balanced against the week's other habits, then confirmed or edited per week. `TimesPerDay` with block slots places occurrences inside time blocks (`CalendarSchedule.kt:40-50,313-333`). Neither is a fixed schedule, so no encoding here can express them. rrule+ext therefore gains a fifth kind:
- **PLANNED** stores `n`, the allowed days, and an optional block list.
- The planner's confirmed weeks are stored as WEEK edits in ADR 11's `occurrence_edit` log, as Tendril stores them in `HabitScheduleEdit` (`HabitWeek.kt:71`). (Amended 2026-10-01: this line first said "exception rows", which is not how Tendril stores habit edits.)

This was **asserted, not measured**, and it changes no ranking, because no other encoding could express these rules either. **Measured 2026-10-01** (`docs/spikes-2026-10-01.md` §9.2): 500 random weeks round-trip through PLANNED plus WEEK edits to identical plans, once a HABIT item carries `block_id` and `duration_min` (ADR 06). Random draws use FNV-1a 64 of `itemId|occurrenceDate|kind` and SplitMix64 (§9.4 of the same file).
