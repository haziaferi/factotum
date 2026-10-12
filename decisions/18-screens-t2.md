# 18. Screens T2: items, calendar and alarms

Status: **in progress.**
- Approved: the alarm ringing and an item's page (owner, 2026-10-12).
- Still open: the Reminders list, what a calendar day holds, and Calendar.

The method is decision 15's: every screen, one at a time, before colour. The owner's T2 answers (2026-10-10) are at the end of `decisions/17-screens-t1.md`.

The scorer is `tools/screens/t2_opt.py`. Its files live in `docs/screens/t2/`:
- `t2-options.html`, every option drawn;
- `t2-scores.html`, the measures and the Pareto fronts;
- `t2-<part>.json`;
- the phone references, in `t2-references.json` and `t2-refs.json`.

Each part has a control that must lose, or the scores page fails.

## The owner's picks (2026-10-12)

| Part | Pick | Next |
|---|---|---|
| The alarm ringing | **full, slide, one, upcoming** | approved |
| An item's page | **inplace, all, auto** | approved |
| The Reminders list | **next, days**, and Skip in **the item page's in-place form**, for consistency | new option, scored below |
| What a calendar day holds, and its filter | "everything" looks too much like the control | rescore |
| Calendar | needs different axes | rescore |

## The alarm ringing: approved (owner, 2026-10-12)

**The pick:**
- **Full screen**, over the lock screen and over any app.
- **Slide to dismiss.**
- **One Snooze**, whose length is set in the reminder.
- **Skip for today from the upcoming notification**, a quiet notification an hour before.

The pick is on the front (`t2-alarm.json`):
- **Half-asleep:** of the full-screen options, only hold or slide with Skip off the ringing screen keep both risks at 0. A tap aimed at Snooze cannot land on a dismiss or Skip target (`aim_risk` 0), and a blind slap dismisses nothing (`slap_risk` 0). Snooze is missed 0.16% of the time.
- **Its costs against tap-to-dismiss:**
  - reach is 1.49 bits against 0.75 (the knob sits at the track's start);
  - dismissing takes about 0.5 s;
  - Dismiss holds 45% of the two targets' visual mass, against 35%.
- **Skip from upcoming:** 2.5 actions, against 2 on the ringing screen. The ringing screen keeps only two things on it.
- **Reference:** Fossify Clock over the locked phone (run 5) is the same form, a full screen with a slide knob.

**To keep when drawing it:**
- The knob stays plain, and Snooze stays the larger target.
- Dismiss's pull must not grow past the measured 0.452.

## An item's page: approved (owner, 2026-10-12)

**The pick:**
- **In place:** the row grows where it is, its fields under its title, and a tap on the title closes it.
- **All fields**, set or not. An unset field reads "Add a reminder".
- **Autosave**, with T1.8 H's Undo toast after a change.

It had the lowest sum of the twelve options (49.5):
- Today's rows stay in view while the item is open;
- an edit takes one action;
- nothing is lost on leaving.

On Windows, the row grows in Today's column.

## The Reminders list: in-place Skip scored (2026-10-12)

The owner's pick:
- **next, days**;
- and, for consistency, **Skip in the same in-place form as an item's page**.

That form was not in the space. Added as `skip: inplace`:
- the row grows in place as an item's page does;
- its fields are listed, with **Skip for today** under When;
- the skipped row folds into "Done today" (decision 15).
- That makes 2 actions: the row, then Skip.

Measured, for next and days (`t2-rem.json`):

| Skip | Actions | Reach (bits) | Hidden | Set off by a scroll |
|---|---|---|---|---|
| **inplace** | **2** | **3.276** | 0 | 0 |
| selection (T1.8 I) | 2 | 3.914 | 0 | 0 |
| page | 3 | 3.436 | 0 | 0 |
| swipe | 1 | 3.390 | 1 | 1 |

In place dominates selection and page on every measure. Only swipe is cheaper, and T1's answer is "no swipes at all".

## What a calendar day holds: rescored with a layout (2026-10-12)

The owner: "the everything option looks too much like the control option, to be reviewed/rescored".

**What was wrong:**
- Every option was drawn as the same tray over the hours.
- So the control differed only in where the filter sat and in row height.
- Nothing measured whether the kinds can be told apart, or how fast an hour is found.

**What changed.** A layout dimension was added. Each item is tagged with its kind and its time, and two measures are read off the laid-out page.

**The layouts:**
- **timeline:** one list in time order, the untimed first.
- **grid:** a tray of the untimed above the hours. On the hours an event is a block, a reminder a round pin, and a timed routine a dashed strip.
- **sections:** Events, Tasks, Reminders and Routines.
- **lanes:** a column of hours per kind.

**The measures:**
- `kind_sep`: the share of three preattentive channels (region, shape, leading glyph) that differ between each pair of kinds.
  - 1 means every pair differs on all three.
  - A day showing one kind scores 0, since there is nothing to tell apart. It first scored 1, which let "events only" win Distinction by showing less; the 12 rows were corrected in place.
- `time_lookup`: readables passed, in reading order, to answer "what is at 09:00" and "what is at 15:00". When the order is not by time (sections), it counts every readable.

**The new control:**
- everything in one list, in the order made;
- every row alike: no mark, no time column, the time on a second line;
- the filter in Settings.
- It is now off the front: sum 191.5, against 143 for the best "everything" option.

**Axes:** Completeness (missed), Ease (other_actions, time_lookup), Distinction (kind_sep), Density (rows_seen, cut), Calm.

With everything shown (`t2-day.json`):

| Layout + filter | Sum | Lookup | Kinds apart | Titles cut | On the front |
|---|---|---|---|---|---|
| timeline + menu | 143 | 7 | 0.333 | 0 | yes |
| timeline + chips | 151 | 7 | 0.333 | 0 | yes |
| sections + menu | 157.5 | 12 | 0.667 | 0 | yes |
| grid + chips | 183.5 | 13 | 0.833 | 0 | yes |
| lanes + chips | 193 | 13 | 0.889 | 4 | yes |
| control | 191.5 | 8 | 0 | 0 | no |

**The trade:**
- The timeline finds an hour fastest but tells the kinds apart by glyph alone, which is the owner's objection.
- The grid tells them apart on region and shape too, for six more readables.
- Lanes cut four titles at phone width.

## Calendar: rescored on the owner's axes (2026-10-12)

The first scoring left all eight options on the front, tied on axes that did not tell them apart. It was redone on the owner's axes.

**Axes:**
- **Now:** actions to see today and the current time.
- **Horizon:** the span of days whose things are on screen, phone and Windows.
- **Legibility:** title characters readable per thing, phone and Windows.
- **Conflicts:** two clashes were added to the sample, School run against Dentist today and Call with Leo against Lunch with Sam on Thursday.
  - 0: drawn side by side;
  - 1: times written, so the reader works the clash out;
  - 2: unseen.
- **Switching** and **Calm**, kept.

**Drawing changes:** the week and day grids now set clashing events side by side, and draw a now line. The agenda draws the now line between rows.

All eight are still on the front, but now on real trade-offs (`t2-cal.json`):

| Default + switch | Sum | Now | Horizon (days) | Legible chars, phone / Windows | Clashes |
|---|---|---|---|---|---|
| week + tabs | 48.5 | 0 | 7 | 5.3 / 10.5 | 0 |
| agenda + tabs | 48.5 | 0 | 4 | 9.4 / 9.4 | 1.5 |
| month + tabs | 49.5 | 1 | 29 | 6.8 / 10.8 | 2 |
| day + tabs | 50 | 0 | 1 | 10.0 / 10.0 | 1 |
| control (year) | 90 | 4 | 0 | 0 / 0 | 2 |

The menu options each sit 1.5 to 4.5 above their tabs twin.

## The two additions, scored (owner: "Score both additions first, then I'll pick", 2026-10-12)

**Day view, `shaped`:**
- the timeline's single list in time order;
- each kind's row in the grid's shape: an event a filled block, a reminder a round pill, a routine a dashed outline, a task a plain row.
- Only its 9 rows were scored and added to `t2-day.json`; the other 37 rows did not change.

With everything shown, and a filter:

| Layout + filter | Sum | Lookup | Kinds apart | Clutter | On the front |
|---|---|---|---|---|---|
| timeline + menu | 186 | 7 | 0.333 | 0.0425 | yes |
| timeline + chips | 193.5 | 7 | 0.333 | 0.0461 | yes |
| sections + menu | 199 | 12 | 0.667 | 0.0464 | yes |
| **shaped + menu** | 212 | **7** | **0.667** | 0.0539 | yes |
| **shaped + chips** | 216.5 | 7 | 0.667 | 0.0575 | yes |
| grid + chips | 226 | 13 | 0.833 | 0.0559 | yes |
| lanes + chips | 238 | 13 | 0.889 | 0.0541 | yes |
| control | 242.5 | 8 | 0 | 0.0491 | no |

- Shaped keeps the timeline's lookup (7) and doubles its separation (0.333 → 0.667), with shape and glyph differing.
- It matches sections' separation for 5 fewer readables, at more clutter (the outlines and fills).
- The grid still separates most (0.833, region too), for 6 more readables.
- (The sums are higher than in the section above because 46 options are now ranked against each other, not 37.)

**Calendar, `3day`:**
- Monday to Wednesday, today first.
- It adds a "3 days" tab, which changes the tabs on every option, so all 11 options were rescored.
- Two corrections came with it:
  - **References:** Fossify's 3-day default had been mapped to "week", for want of the option. It now maps to `3day`.
  - **Legibility** is now the readable share of each title (1: whole). Raw characters favoured views whose visible titles happened to be longer, which put 3-day below week on Windows even though its titles are whole there. This supersedes the characters column in the table above.

| Default + switch | Sum | Now | Horizon (days) | Legible share, phone / Windows | Clashes |
|---|---|---|---|---|---|
| agenda + tabs | 49.5 | 0 | 4 | 1.0 / 1.0 | 1.5 |
| day + tabs | 58 | 0 | 1 | 1.0 / 1.0 | 1 |
| month + tabs | 62 | 1 | 29 | 0.69 / 1.0 | 2 |
| **3day + tabs** | 63.5 | 0 | 3 | **0.96** / 1.0 | 1 |
| week + tabs | 65 | 0 | 7 | 0.56 / 0.97 | **0** |
| control (year) | 109.5 | 4 | 0 | 0 / 0 | 2 |

- All ten options are on the front.
- 3-day fixes week's cut titles (0.56 → 0.96) but loses Thursday's clash and four days of horizon.
- Week is the only view that draws both clashes side by side.

## Week and 3 days: how they read (owner, 2026-10-13)

The owner:
- "There is no week view anymore". The options page drew six options per part, lowest sum first, so week and 3-day were scored but not drawn. The page now draws every tabs option for Calendar (`toast_opt.POOL`).
- "By choosing the tabs version, I still need a 3 day and a week view with good legibility."

**A new part, `wk`.** Week and 3 days under the tabs, each in four forms:
- **line:** the grid, one-line titles;
- **wrap:** the grid, titles wrapping, the hours taller;
- **list:** each day a header with its things and times, empty days kept;
- **planner:** the days as cells, as a paper week planner. The week is 2×4, Mon to Thu down the left and Fri to Sun down the right; 3 days is three full-width cells.

**Legibility measured more strictly.** A title's words count only when read whole: on one line and inside their block. Wrap broke words mid-word in 43 px columns ("Farme / rs"), which the earlier share counted as read. This applies to `cal` too, so it was rescored. Its week figure drops from 0.56 to 0.37 and month's from 0.69 to 0.46.

| Span + form | Sum | Legible, phone / Windows | Clashes | Things on screen, phone / Windows | On the front |
|---|---|---|---|---|---|
| **week + planner** | **31.5** | **1.0 / 1.0** | 1 (times) | **15 / 15** | yes |
| week + list | 35 | 1.0 / 1.0 | 1.5 | 8 / 8 | yes |
| 3 days + planner | 37 | 1.0 / 1.0 | 1.5 | 7 / 7 | yes |
| week + wrap | 38 | 0.49 / 1.0 | 0 | 12 / 13 | yes |
| 3 days + list | 38 | 1.0 / 1.0 | 1.5 | 7 / 7 | no |
| week + line | 44 | 0.37 / 0.97 | 0 | 14 / 15 | yes |
| **3 days + wrap** | 44 | **1.0 / 1.0** | 1 | 5 / 6 | yes |
| 3 days + line | 46.5 | 0.95 / 1.0 | 1 | 7 / 7 | no |
| control | 46 | 0.21 / 0.76 | 0 | 14 / 15 | no |

**Notes on the results:**
- **The week:** the planner has the lowest sum. It reads whole, and it shows the most things (all 15). It gives up only the side-by-side clash, which reads from the start times instead.
- **3 days:**
  - wrap keeps the time grid and its clashes drawn, and reads whole;
  - the planner shows more things but leaves its cells mostly empty.
