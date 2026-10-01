# Decision register

The contests are taken in dependency order. There is one row per contest.

| # | Contest | Status | Pick | Cases | ADR |
|---|---|---|---|---|---|
| 01 | Sync identity and conflict | decided | hybrid+ | 10 | [01-sync.md](01-sync.md) |
| 02 | Task: Entry kind or own table | decided | shared (Item / TrackerReading) | 9 | [02-task.md](02-task.md) |
| 03 | Reminder location | decided | item-kind; timeline toggle (off); snooze syncs | 11 | [03-reminder.md](03-reminder.md) |
| 04 | Recurrence encoding | decided | rrule+ext; missed: ALARM rings via setAlarmClock, NOTIFICATION fires once late | 11 | [04-recurrence.md](04-recurrence.md) |
| 05 | Check-in | decided | own-axis (mood separate); no numbers on screen | 7 | [05-checkin.md](05-checkin.md) |
| 06 | Habit | decided | item+tracker; the verb is "Log" | 8 | [06-habit.md](06-habit.md) |
| 07 | Timed interval (map: duplicated; verification: contested) | decided | activity-item; several timers at once; a span counts for its start day | 9 | [07-timelog.md](07-timelog.md) |
| 08 | Tagging (map: duplicated; verification: contested) | decided | one-vocab; the word is "Label" | 10 | [08-tagging.md](08-tagging.md) |
| 09 | Settings store (map: duplicated; verification: contested) | decided | scoped-live (owner, against the recommendation) | 9 | [09-settings.md](09-settings.md) |
| 10 | Full-text search (map: duplicated; verification: contested) | decided | chronicle-all (one FTS4 index, unicode61, triggers) | 7 | [10-search.md](10-search.md) |
| 11 | Occurrence edits (sole-owner probe) | decided | edit-log+move; a clash on one occurrence asks; ADR 02 and 04 amended | 10 | [11-occurrence-edits.md](11-occurrence-edits.md) |
| 12 | Page merge granularity (sole-owner probe) | decided | per-row+revive; same-paragraph clash: later wins, with a notice | 8 | [12-page-merge.md](12-page-merge.md) |
| 13 | Sync folder layout (SPEC §10.9) | decided | device-log+copies: per-device 16 KiB log segments, snapshot every 64, conflict copies merged | 4 | [13-folder.md](13-folder.md) |

Standing owner answers (2026-09-30):
- Fresh start.
- Folder sync with no server.
- Constraint 0.14 (no streaks or missed-day counts) applies to Habits only.

Standing owner answers (2026-10-01):
- Platforms: Android and Windows, as Tendril ships now from shared code.
- Every sole-owner module moves across; no single-app feature is dropped.
