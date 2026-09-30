# Decision register

The contests are taken in dependency order. There is one row per contest.

| # | Contest | Status | Pick | Cases | ADR |
|---|---|---|---|---|---|
| 01 | Sync identity and conflict | decided | hybrid+ | 10 | [01-sync.md](01-sync.md) |
| 02 | Task: Entry kind or own table | decided | shared (Item / TrackerReading) | 9 | [02-task.md](02-task.md) |
| 03 | Reminder location | decided | item-kind; timeline toggle (off); snooze syncs | 11 | [03-reminder.md](03-reminder.md) |
| 04 | Recurrence encoding | decided | rrule+ext; missed: ALARM rings via setAlarmClock, NOTIFICATION fires once late | 11 | [04-recurrence.md](04-recurrence.md) |
| 05 | Check-in | decided | own-axis (mood separate); no numbers on screen | 7 | [05-checkin.md](05-checkin.md) |
| 06 | Habit | open | - | - | - |

Standing owner answers (2026-09-30):
- Fresh start.
- Folder sync with no server.
- Constraint 0.14 (no streaks or missed-day counts) applies to Habits only.
