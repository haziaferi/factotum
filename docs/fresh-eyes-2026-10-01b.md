# Fresh-eyes audit, 2026-10-01b: decisions/ after contests 11–12

The runner is `_fresh-eyes-2026-10-01b/run.py`. The design is the same as the two earlier audits: one Opus 5.5 reader with Read, Grep and Glob, run on a planted copy and on the real folder.

| | Result |
|---|---|
| Plants caught | **4/4**: a register count (P1), an ADR 12 score (P2), the PageRevision cap against the source (P3), and the ADR 11 merge rule contradicted (P4) |
| Controls wrongly flagged | **0/2**: the option added after the first run (ADR 11), and a growth figure disclosed as a hand count |
| Real findings | 16. All were confirmed against the ADR text and the cited lines. 15 were fixed and 1 became an owner question. |

## Findings

| # | File | Finding | Outcome |
|---|---|---|---|
| 0 | 12 | "doesn't conflict with ADR 01" is false. Revive lets an edit to another row beat a trash, which ADR 01's groups don't. | fixed: recorded as a deliberate exception to ADR 01 that the owner chose |
| 1 | 02 | ADR 02 still said Tendril's exception columns come with `item`. | fixed: ADR 02 amended |
| 2 | 11 | The `changes` field list omitted rule, rule_patch, pause, sort_order, deleted and week_days (`CalendarSchedule.kt:213-222`). | fixed: full list |
| 3 | 11 | "Move writes two rows" is only the one-off case. The weekly move is one From edit (`EditMode.kt:206-209`). | fixed |
| 4 | 12 | Dropping `.tendril-lost` loses the recovery of cell and canvas losers, because PageRevision holds only the title and blocks. | fixed: a MERGE revision stores every losing part |
| 5 | 12 | "Every part is its own row" contradicted relations (add-only) and the property schema (upsert). | fixed: both named as exceptions |
| 6 | 11 | A concurrent occurrence move or retime was settled silently, whereas ADRs 01, 03 and 04 ask a person about schedule clashes. | **owner question**: answered "ask me, like a series" |
| 7 | 11 | The `created_at` order was wall-clock, so a fast clock always wins. | fixed: ADR 01 stamp order |
| 8 | 11 | It named only one of its ADR 04 amendments. | fixed: both, plus ADR 02 |
| 9 | 11 | Tasks were put on `item` by ADR 02, not ADR 06. | fixed |
| 10 | 11 | Cited `HabitScheduleEdit.kt:25-33`, but the columns run to line 35. | fixed |
| 11 | 07 | "daily totals always add up to the weekly one" fails for overlapping spans that start on different days. | fixed: a week is the sum of its days, and a rare cross-day overlap counts on each day |
| 12 | 05 | The open question said Tendril-origin check-ins "never" inform the engines, but energy taps do. | fixed: corrected in place |
| 13 | 05 | The question said the engines compute "in the background", but they run on demand. | fixed |
| 14 | 05 | "the engines keep running as now", but BurnoutIndex isn't wired. | fixed: SPEC §10.5 |
| 15 | 10 | "title first, as Chronicle does", but Chronicle sorts by time only. Title-first is Tendril's ranking. | fixed |
