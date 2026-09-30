# Sole-owner overlap probe, 2026-10-01

The map calls three modules "sole owner, none contested": Pages & canvas (Tendril), Trackers & goals (Chronicle) and Regulation (Equipoise). The map was wrong on all four of its "duplicated" rows, so its sole-owner rows were probed too.

The probe checked each of the 16 entities that no ADR covered against the ten decided schemas. It ran `tools/verify.py` (Sonnet 5.5), and the raw output is in `decisions/verify/11-sole-owners/`.

## Overlaps found: new contests

| Contest | Overlap | Evidence |
|---|---|---|
| 11 occurrence edits | Tendril has two mechanisms for editing one occurrence of a repeating thing. Tasks and events use exception rows (`Entry.kt:48`). Calendar habits use `HabitScheduleEdit`, a log of scoped edits (occurrence, day, week, from here on, extra) whose target is HABIT or BLOCK. ADR 06 put both on `item`. ADR 04:74 said planner placements are stored "as Tendril already stores its edits", but Tendril's habit edits are not exception rows. | `HabitScheduleEdit.kt:19-28`; `CalendarSchedule.kt:97-103`; `EntryDao.kt:69` |
| 12 page merge | Pages sync as whole snapshots, last-writer-wins, and the loser is kept locally in `PageRevision`. Block, property value, canvas and relation rows have no tombstone of their own. ADR 01's hybrid+ was scored on items and reminders, not on pages. | `PagesSyncEngine.kt:681-687`; `PageRevision.kt:18-26`; `PurgedRecord.kt:19` |

## Independent: move across as-is

| Entity | Why it's independent |
|---|---|
| Chronicle `checklist`, `checklist_item` | A reusable, resettable template, which is not a to-do list. Items have a done flag and an order but no due date, and ticks are current state with no history. Nothing links to them from reminders, activities or trackers (0 hits). (`Checklist.kt:10`; `ChecklistItemRepository.kt:74`) |
| Chronicle `tracker_choice`, `saved_chart`, `goal` | They are, in order: a CHOICE tracker's options; a chart definition with no values; a target over a period (RECURRING never completes, MILESTONE completes once). (`TrackerChoiceEntity.kt:38`; `GoalAndSavedChartEntities.kt:19-44`; `Enums.kt:62,70`) |
| Equipoise `sensory_log` | A five-channel snapshot (sound, light, crowd, temperature, touch). A tracker reading, with one value per row, can't hold it without loss. (`Entities.kt:24-31`) |
| Equipoise `masking_entry` | One row per day of model outputs from three felt levels, never typed in. (`Entities.kt:34-40`) |
| Equipoise `regulation_event` | A single instant with direction, tool and outcome. It has no end, so it isn't a time span. Its FK points at the check-in. (`Entities.kt:44-55`) |
| Equipoise `pending_outcome` | A single row resolved at the next app open. It has no fire time and no notification (0 hits for AlarmManager or WorkManager), so it isn't a reminder. (`Entities.kt:59-64`; `OutcomeAtNextOpen.kt:25`) |
| Equipoise `daily_index` | A derived, stored daily score. (`BurnoutIndex.kt:12,40`) |
| Tendril `page`, `block`, `page_relation`, `page_canvas`, `canvas_node`, `canvas_edge`, `page_database_view`, `page_revision` | Page-only concepts, except for their sync, which is contest 12. |
| Tendril `calendar_link` | A device-local link to the system calendar that copies no events. (`CalendarLink.kt:12`) |
| Tendril `habit_block` | Named time-of-day blocks with per-weekday overrides. They are the planner's input, and one-day changes to them are part of contest 11. (`HabitBlock.kt:15,38`) |

## Fixes for the SPEC, not decisions

- **Page database → task.** `syncToTasks` writes a second row, a TASK (`DatabaseSyncManager.kt:124-139`). In Factotum this row is an `item` of kind TASK with `source_row_id`. The bound properties (done, dates, recurrence) stay live proxies of the item, as in Tendril.
- **The INTERVAL property** (`n:UNIT`, `Property.kt:164`) is a third recurrence encoding. When bound, it is written as ADR 04's RRULE (`FREQ` plus `INTERVAL`), as ADR 04 already did for Elastic.
- **Goal and saved-chart ids.** `goal.target_id` with ACTIVITY, and ACTIVITY ids packed inside `saved_chart.source_ids`, point at `item` ids (ADR 07). The start is fresh, so no stored ids need remapping.
- **The Equipoise burnout index is not computed in production.** `BurnoutIndex.compute` has no caller outside a test (0 hits), and `sleepHours` has no producing table; the domain names it `sleepDeficit`, a value from 0 to 1. This is open work in the SPEC. The obvious sleep source is a tracker.
- **Two system-calendar links in Tendril.** `calendar_link` and `Entry.providerEventId` are both device-local (`CalendarLink.kt:19`). They move as-is, as ADR 09's DEVICE_STATE.
- **Checklist text isn't in the search index**, in Chronicle today or in ADR 10. Adding it later is a feature.
