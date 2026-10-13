# 19. Screens T3: habits, trackers, time, goals, charts and checklists

Status: **questions answered (owner, 2026-10-13); screens not started.** The method is decision 15's: every screen, one at a time, before colour, each scored with a control that must lose.

**Already settled in the SPEC, and not asked again:**
- **Habits (§3.6):**
  - no streaks;
  - the verb is "Log";
  - presence is the days this month, the last date and the usual time (withheld below 3);
  - pause;
  - rolling habits;
  - "n a day" in time blocks.
- **Timed intervals (§3.7):**
  - several timers at once;
  - a span counts for the day it started;
  - the 12-hour question;
  - finishing a task stops its timer.
- **Goals (§3.7):** a day, a week from Monday, a month from the 1st, or a milestone over the last 400 days.

The Hub's Routines card already lists Habits, Trackers, Activities, Checklists, Charts and Goals (T1.4). Review adds Time totals, and Calendar adds the habits' week Planner.

## The owner's answers (2026-10-13)

| Question | Answer |
|---|---|
| Which screens | **All four groups:** <br>• Habits, Planner and Log (the Habits list, a habit's page, the week Planner, and the Log sheet for a rating or a number); <br>• Trackers and Goals (the Trackers list, a tracker's page with its readings, Goals); <br>• Activities and time (Activities, running timers, editing a session, Time totals); <br>• Checklists and Charts |
| How a habit shows its presence | **Score all:** days this month, a month of dots, the last date with the usual time, and combinations, against a control |
| Where running timers show | **Score all:** a strip on Today, an ongoing notification, a mark on the bar, the Activities screen only, against a control |
| Where charts and goals live | **Score all:** on each tracker's or activity's page, a Charts screen, both, against a control |

**Defaults taken without a question.** They follow T2's practice, and the owner can change them at any screen:
- **How a Log is entered.** A rating or a number gets every form scored: chips, a stepper, a keypad, a slider.
- **How a goal shows its progress.** Every form is scored, a plain number among them. Nothing guilt-laden: no red, no "missed".
- **Axes:** T2's axes, plus the register: these screens are ambient and non-judgmental (`app-register-layout`, `register_fit`). Windows too.
- **References:**
  - the four source apps;
  - open-source habit and tracker apps installed through Droid-ify (Loop Habit Tracker first);
  - others through Aurora, only if a gap remains.
  - Placeholder data only, geometry only for the owner's own apps.

## Survey samples left on the phone (to delete when T3's survey ends)

- **Loop Habit Tracker** (installed for the T1 survey on 2026-10-05): the sample habits "Walk" (from T1, with today ticked on 2026-10-13) and "Water" (measured: 8 glasses a day, added 2026-10-13).
- **Tendril debug:** the sample habits "Walk" (Morning) and "Water" (any time, counts glasses, 8 a day), added 2026-10-13.

## T3.1 The Habits list: scored (2026-10-13)

**References** (`docs/screens/t3/t3-references.json`; screenshots in `_screens-sources/t3/`):
- **Loop Habit Tracker:**
  - a score ring on each row;
  - the last 4 days as 48 dp cells, a cross on each day not done;
  - a tap on a day opens a tick, cross and note picker.
- **Tendril:**
  - one day at a time, grouped by time block;
  - a checkbox, or + for a counted habit;
  - no presence in the list.
  - Tendril's own rule, on its add-habit sheet: a daily number "is shown once, in the sheet, and never as a fraction, a bar or a percentage".

**The space** (`tools/screens/t3_opt.py`): 60 options plus the control.
- presence: none / count / last / dots / count + last;
- grouping: blocks / flat;
- Log: on the row / day cells / the habit's page;
- a count's amount: plain ("3 glasses today") / fraction ("3 of 8").

The sample is six placeholder habits on Tue 13 Oct.

**The measures:**
- the actions and the reach to Log;
- the share of habits whose presence a row states, and the marks read for it;
- guilt marks: empty past dots, crosses, and a fraction below its number;
- rows seen, titles cut;
- clutter, on the phone and on Windows;
- whether Log sits where Today's rows have it.

**The control:** Loop-like, with a streak and a percentage on every row, and the last 4 days as ticks and crosses. It loses, at 349.5.

**Result.** "None" ranks first, but only by showing nothing, so it does not answer the question. Among the options that show presence:

| Option | Sum | Log actions | Presence marks | Guilt marks | Titles cut | Like Today's rows | On the front |
|---|---|---|---|---|---|---|---|
| count, flat, page, plain | 272.5 | 3 | 1 | 0 | 0 | no | yes |
| **count, flat, row, plain** | **282.5** | **1** | 1 | 0 | 0 | **yes** | yes |
| last, flat, page, plain | 284 | 3 | 1 | 0 | 0 | no | no |
| count, blocks, row, plain | 306 | 1 | 1 | 0 | 0 | yes | yes |
| count, flat, row, fraction | 316.5 | 1 | 1 | 2 | 0 | yes | no |
| count, flat, cells, plain | 329 | 1 | 1 | 7 | 2 | no | yes |

Averaged over each dimension's options, lower being better:

| Dimension | Averages |
|---|---|
| presence | count 325 < last 340 < count + last 369 < dots 389 |
| grouping | flat 342 < blocks 369 |
| Log | page 338 < row 349 < cells 377 |
| amount | **plain 343 < fraction 368** |

**What the averages say:**
- **Presence:** a count of days reads best. Dots cost 13 marks per row, and their empty past days read as misses.
- **The amount:** plain beats the fraction everywhere, which supports Tendril's rule over T1's approved "3 of 8".
- **Log:** the page wins on reach and calm, at 3 actions to Log, against 1 on the row.
