# Fresh-eyes audit, 2026-10-01: decisions/ after contests 07–10

The runner is `_fresh-eyes-2026-10-01/run.py`. It used one Opus 5.5 reader over the whole folder, with Read, Grep and Glob over the source repos, run twice in parallel:
- once on a copy with four planted defects, all in ADRs 07–10;
- once on the real folder.

The design is the same as the 2026-09-30 audit's.

## Measurement

| | Result |
|---|---|
| Plants caught | **4/4**: a register count (P1), a scope-table contradiction (P2), a trigger count against the source (P3), a score against the scores file (P4) |
| Controls wrongly flagged | **0/2**: the owner's pick against the recommendation (ADR 09), and FTS5 stated as unmeasured (ADR 10) |
| Real findings | 10. All ten were confirmed by reading the cited lines. Nine were fixed and one became an owner question. None was withdrawn. |

## Findings

| # | File | Class | Finding | Outcome |
|---|---|---|---|---|
| 0 | 08, 07 | contradiction | ADR 08 puts the activity's category in `item.label_id`, allowed on ACTIVITY and HABIT, but ADR 07 still said `category_id`, ACTIVITY only. | fixed: ADR 07 amended, and ADR 08 names the change |
| 1 | 08 | source | "lookup is an exact match" cited `LabelDao.kt:23`, which is a substring `LIKE`. | fixed: exact by name (`:16`), substring in the picker (`:23`) |
| 2 | 08 | contradiction | The same line against ADR 10's "the label picker keeps substring LIKE". | fixed with #1 |
| 3 | 07 | overclaim | "Both apps have these gaps", when three of the five bullets are single-app gaps or features. | fixed: each bullet names its app |
| 4 | 07 | overclaim | The midnight-crossing span was filed as a gap. Tendril counts it for its start day on purpose (`TimeLogDao.kt:31-33`). | **owner question**: answered "the day it started", recorded in ADR 07 |
| 5 | 07 | contradiction | `sort_order` was ACTIVITY-only, but Tendril habits keep a manual order (`Habit.kt:86-87`). | fixed: allowed on ACTIVITY and HABIT |
| 6 | 09 | count | The control's `expect_fail` listed 4 cases, yet it lost 8. | fixed: `options/09-settings.json` expects all 8, rescored, control check passes |
| 7 | 09 | source | Alarm codes, pending alerts and `device_id` cited `SettingsRepository.kt:117-128`, which holds ordinary settings keys. | fixed: cites `AlarmCodes.kt:70`, `PendingAlerts.kt:100`, `DeviceIdRepository.kt:24` |
| 8 | 10 | source | "a grep found 0 files" doesn't reproduce over all files: tests, tooling and the vendored llama.cpp match. | fixed: the claim is scoped to `*.kt` and the other hits are named. The conclusion (no index) stands. |
| 9 | 10 | contradiction | tendril-all's "a sync import isn't indexed" is wrong, because Tendril's merge calls the rebuild (`PagesSyncEngine.kt:682`). | fixed: "a raw write that skips the rebuild call" |

## Not reviewed

- The harness code in `tools/*_sql.py` and `settings_sim.py` was proved by its controls, not read by the auditor.
- `timelog_sql.py` still names the activity's category column `category_id`. The name doesn't change any case or the growth count.
