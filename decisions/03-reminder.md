# ADR 03: Where a reminder lives

Status: **decided: item-kind**. Date: 2026-09-30. Owners: Tendril, Chronicle, Mnemo.

This ADR builds on the two earlier ones:
- **ADR 01 (hybrid+).** Every row carries a ULID and group stamps, and a concurrent change to the schedule group is shown to a person.
- **ADR 02 (one `item` table).** Tasks and events share one table.

## Verified facts

The facts were verified with `tools/verify.py`; the raw output is in `verify/03-reminder/`.

| App | Fact | Source | Map said |
|---|---|---|---|
| Tendril | The columns are `id, uid, entryId, offset, anchorTime, deletedAt`, with `entryId` NOT NULL and an FK with CASCADE. The UI offers no way to make a standalone reminder. | `Reminder.kt:20-33`; `ReminderViewModel.kt:40` | confirmed; uid and deletedAt missed |
| Tendril | An offset is one of 7 presets (1 h … 1 week) or `Custom(count, DAY/WEEK/MONTH)`. There are no minute offsets. | `ReminderSpec.kt:7-19` | "N minutes before" (partial) |
| Tendril | `anchorTime` applies only when the item has no start time. The fire time is `start + (startTime ?: anchorTime ?: 00:00) + offset`. A reminder on an item with no start date never fires, and nothing in the UI prevents creating one. | `ReminderFirings.kt:71,105`; `ReminderSheet.kt:101` | not stated; the no-date case is a gap |
| Tendril | Reminders fire only while a task is PENDING. Only the next occurrence of a Fixed event is armed. A task's OVERDUE firing is a separate path, not a reminder row. Habits have their own reminder mechanism. | `ReminderFirings.kt:23,62,81,104` | not stated |
| Tendril | There is no nag, no per-reminder sound and no alarm kind: the reminder uses a shared channel with auto-cancel. | `ReminderAlarmReceiver.kt:33-38` | **refuted** |
| Chronicle | 16 columns, standalone, linked to nothing. `kind` is NOTIFICATION or ALARM, and ALARM rings through AlarmService and a full-screen activity. The nag is `nagMaxRepeats` plus `nagMaxDurationMillis`, and the interval is derived. `repeatIntervalMillis` packs three meanings into one value. | `ReminderEntity.kt:23-33`; `Enums.kt:74`; `NagAlarms.kt:38` | partial |
| Chronicle | `dueAt` is a wall-clock LocalDateTime string, resolved per time zone when the alarm is scheduled. Snooze stays on the device, is not synced, and never touches `dueAt`. | `ReminderEntity.kt:7`; `ReminderSnooze.kt:13,29` | not stated |
| Mnemo | 22 columns, standalone. `mode` is EASE, SCHEDULE or ALERT. It also has `skinId`, a three-state `soundUri` (null = default, "" = silent) and a three-state `vibrationPattern`, and `useExactAlarm`. The nag is on/off per reminder, with a global interval. | `Reminder.kt:10,33-81`; `AppSettingsStore.kt:113` | partial |
| Mnemo | Snooze is stored in the row (`snoozedUntil` overwrites `nextFireAt`), so it syncs. Done on a recurring reminder does not advance it: `recordFired` already has. | `ReminderRepository.kt:105-131` | "done advances" (partial) |

## Scores (`03-reminder-scores.md`, run by `tools/reminder_sql.py` on SQLite)

| Option | Chronicle | Mnemo | Shared | Tendril | Growth | Status |
|---|---|---|---|---|---|---|
| dependent | 0.33 | 0.00 | 1.00 | 1.00 | 24 | front (smallest; no standalone reminders) |
| standalone | 1.00 | 1.00 | 0.67 | 0.25 | 25 | dominated ("15 min before" stops following the item) |
| optional-link | 1.00 | 1.00 | 0.67 | 1.00 | 31 | dominated by item-kind (same coverage, recurrence in two places) |
| **item-kind** | 1.00 | 1.00 | 0.67 | 1.00 | 25 | **front** |
| bare (control) | 0.67 | 1.00 | 0.33 | 0.75 | 23 | failed all 3 cases it was expected to fail |

The map said: "A dependent reminder can't express a standalone one without inventing an Entry to hang it on." **item-kind** makes that invented item a real one: a `REMINDER` kind of `Item`. That buys three things:
- Every reminder row keeps Tendril's offset and FK behaviour.
- Chronicle's and Mnemo's standalone reminders fire, repeat, and keep their history when marked done.
- Recurrence has exactly one home (the item), so contest 04 encodes it once.

Its one lost case is `shared-timeline-unchanged`: ADR 02's day-timeline query, left unchanged, now also returns standalone reminders.

## Recommendation

**item-kind**, with the alert settings on the reminder row as a superset of both apps:
- `alert_kind` (NOTIFICATION or ALARM, from Chronicle);
- nag repeat count and duration (from Chronicle), with Mnemo's on/off being a count of 0 or more;
- `sound` and `vibration`, each keeping Mnemo's three states;
- `mode` (EASE, SCHEDULE or ALERT, from Mnemo), `skin` and `exact`.

**Fixes, not decisions.** Two gaps from the verification are fixed in the merged app rather than asked about:
- A reminder on an item with no start date is refused, where Tendril silently never fires it.
- Minute offsets are allowed, where Tendril's presets start at 1 hour.

## Decision

**item-kind** was picked by the owner on 2026-09-30, with two behaviour answers:

1. **Day view.** Whether standalone reminders appear on the day timeline is a user setting, "Like Habits, there should be an option to show them, to avoid crowding the calendar". The setting is off by default. ADR 02's timeline query gains `AND (kind <> 'REMINDER' OR :showReminders)`, which settles the one case this option lost. The default is off because the owner's stated reason is to avoid crowding.
2. **Snooze syncs** (Mnemo's behaviour). `snoozed_until` goes on the reminder row, in a *status* group of its own: a concurrent snooze merges silently and never raises hybrid+'s prompt. Mnemo overwrites `nextFireAt` when snoozing, which loses the original time. Factotum keeps the two separate, and that is a fix, not a decision.

## Consequences

- **Contest 04 (Recurrence).** Recurrence lives only on `item`, including standalone reminders. The encoding has to cover Chronicle's 7 cases and Mnemo's cron and stochastic schedules on one column family.
- **Sync groups (ADR 01).** A reminder row's offset, anchor and alert settings form its own group. The schedule itself is the item's schedule group, so a concurrent retime of "take pills" gets hybrid+'s prompt.
