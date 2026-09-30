# Fresh-eyes audit of decisions/, 2026-09-30

Run with the fresh-eyes-audit skill. There was one whole-corpus Opus 5.5 reader with Read/Grep, which could open the four source repos. The skill's own measurements show that contradictions across documents need whole documents, not chunks. The script is `_fresh-eyes-2026-09-30/run.py`, and the raw output is in `seeded.json` and `real.json`.

## Measurement on this corpus

A planted copy of `decisions/` was audited alongside the real folder.
- **Four planted defects:** a register case count, a default stated two ways, a source number (90 days changed to 30), and an ADR score that disagrees with its scores file. All **4 of 4 were caught**, each quoting the planted text.
- **Two controls:** correct text that looks suspicious. These were an owner decision recorded as going against the recommendation, and a platform limit ("a phone that is powered off cannot be switched on"). **0 of 2 were flagged.**

## Findings on the real folder: 35, all fixed

The source was read by hand for the findings that could change a decision:
- R1, the column name: `ReminderEntity.kt:39`.
- R5, Tendril reminders are delete-wins: `SnapshotSyncOrchestrator.kt:1869`.
- R10 and R11, the column counts: 17 and 19.
- R27, Tendril's planner rules: `CalendarSchedule.kt:40-50,313-333`.

A sample of the citation fixes was checked the same way: `AppSettingsStore.kt:36`, `CheckInShape.kt:12`, `Types.kt:28`, `BurnoutIndex.kt:47` and `Repositories.kt:63,159`. The edits are in `_fresh-eyes-2026-09-30/apply_fixes.py`, where each replacement must match exactly once.

| Class | Count | Examples |
|---|---|---|
| Wrong correction of the map | 1 | ADR 01 called the map's `scheduleUpdatedByDevice` wrong. It is the Room column, and `scheduleUpdatedAtDevice` is the JSON key. |
| Scope overclaim | 6 | "A later edit beats a trash" holds for Tendril's entries and habits, not its reminders, check-ins or completions. "hybrids are the only options that…". "growth alone separates them". "Tendril check-ins never reach the engines" is false for energy taps. "engines compute in the background": there is no worker yet. BurnoutIndex does not read "energy only". |
| Count | 5 | Chronicle's reminder has 17 columns, not 16. Mnemo's has 19, not 22. The ADR 04 growth column left out the enum kinds for two options. Two controls' extra losses were unreported. |
| Coverage asserted, not measured | 2 | Tendril's CalendarRule planner (`TimesPerWeek`, block slots) cannot be written as RRULE, so ADR 04 is amended with a PLANNED kind, marked asserted. The active window maps to DTSTART and UNTIL. |
| Wrong line in a citation | 15 | See `real.json` 7-9, 12, 16, 17, 22-26, 29-32, 34. |
| Case wording vs scoring scale | 1 | Three Sync cases said "(or a person is asked)" but the scale scores that as 0.5. The wording now states the scale, and no score changed. |
| Removed-case residue | 1 | ADR 06 still cited the removed `shared-one-log` case in a reason. |
| Stated a Mixed path that doesn't exist | 1 | ADR 05's unchosen onto+levels recommendation. It is now annotated. |
| Other | 3 | Equipoise's REPLACE deletes on a clashing id, and CASCADE deletes the check-in's events. Recurrence month ends use the anchored expectation, not the app's rule. The count of irreducible forms is now "three need an extension, two are irreducible". |

**Decisions changed: none.** Two findings could have moved a score:
- R4 would only raise hybrid+.
- The Tendril reminder rule would move the unchosen `tendril` option from 0 to 1 on one case.

Neither changes any pick. The planner gap (R27) is a coverage amendment, not a reversal, because no encoding could express it.

## Not reviewed

- The tools' code (`tools/*.py`) was not read by the audit. Its outputs were checked through the scores files, and each harness has a control or negative controls.
- The source repos were read only as evidence, not audited.
