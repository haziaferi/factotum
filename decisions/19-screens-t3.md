# 19. Screens T3: habits, trackers, time, goals, charts and checklists

Status: **re-cut by purpose (owner, 2026-10-13): T3a Daily basics, T3b Measuring, T3c Looking back; see `docs/screens/purpose-map.md`. T3a.1 the Habits list approved; next, the Add Habit screen and the Planner.** The method is decision 15's: every screen, one at a time, before colour, each scored with a control that must lose.

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
- **Chronicle debug** (Data tab): the sample tracker "Water" (a number, no unit) with one reading of 1, added 2026-10-13. The tracker "Sleep", the activity "Reading" and one archived activity were there before and are not ours.
- **Track & Graph** (already installed, never opened before): its intro and logging tutorial seen once; the sample tracker "Water" with one reading of 1, added 2026-10-13.

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

## Consistency across screens; T1's counted-habit row amended (owner, 2026-10-13)

Asked whether T1's approved Today row for a counted habit should drop its fraction ("3 of 8") for the plain amount ("3 glasses today"), so that Today and Habits read alike:
> "Yes, let's aim for consistency across elements between screens."

**A standing rule from now on.** The same element reads and acts the same on every screen:
- its wording;
- its marks;
- where its action sits.

An option that breaks this needs a measured reason that outweighs it, and the owner decides.

**Applied:**
- **T1's Today row for Water** now reads "3 glasses today · next block 14:00" (`tier_t1.KINDS`). T1's page was rebuilt.
- **The T0 exploration tools that drew the old text** (`frames_all`, `colour_roles`, `module_palettes`, `module_personality`, `palette_groups`) now draw the new text too. Their pages are regenerated when the palette work resumes.
- **T3.1, the Habits list, recorded as approved** on that rule: days this month, flat, Log on the row (where Today's rows have it), plain amount.
  - It is on the front with a sum of 282.5: 1 action to Log, 0 guilt marks.
  - The habit's page as the place to Log scored lower (272.5), but takes 3 actions and breaks the rule.

## T3 re-cut by purpose (owner, 2026-10-13)

The owner observed that screens had been grouped and scored by the app they came from rather than by what they do ("Habits resembles Equipoise more than it does Calendar or Trackers"), and asked which screens share a purpose, and which have no parent app.

The answer is the **purpose map**:
- `docs/screens/purpose-map.json` holds it as data;
- `docs/screens/purpose-map.md` renders it, through `tools/screens/purpose_map.py`.

The script fails if any navigation screen or Hub entry is left unplaced, and a negative test showed it does.

**The map:** 55 screens under 9 purposes; 5 have no parent app; 9 are approved. It shows six overlap groups:
- three strong: daily basics; measuring; looking back;
- two medium: planning the week; recording myself;
- one weak and settled: what's next.

**The owner's answers:**
1. **T3 and T4 are re-cut by purpose:** T3a Daily basics, T3b Measuring, T3c Looking back. The cut is refined as the tiers go.
2. **Checklists split.** Routine checklists join Daily basics; one-off lists (packing, shopping) stay lists.
3. **The purpose map, once settled, decides how the Hub's elements are grouped.**

**Habits, as the owner defines them (2026-10-13).** Very basic daily things that are easy to forget:
- making the bed, brushing teeth, washing the face, showering;
- held as if-then cues;
- a clear reference on a day of depression or dissociation;
- the least judgment possible.

Quantities (water, exercise, studying, knitting) are trackers.

**What this means for T3.1:**
- Its approval stands for the rule it set: Log on the row, exactly Today's button. (The owner, 2026-10-13: "the Log button should be the same as the Today's page"; one consistency pass across screens comes later.)
- Its scoring is redone as T3a on the axes proposed: Judgment, Cue, Day flow, Low-capacity ease, Consistency. Amount is dropped.
- The three questions put to the owner are still open:
  - whether habits are yes/no only;
  - what the "if" is (a block, a written cue, or both);
  - whether "a clear reference" is the list itself.

## T3a Daily basics: the owner's answers (2026-10-13)

1. **Habits are yes/no only.** Anything counted or rated is a tracker. **Trackers appear on Today**: Water stays on Today as a tracker row ("Today screen might need future tinkering").
2. **The "if" is (c), both:**
   - the time block sets the order;
   - a short cue written per habit sets the wording ("After breakfast").
3. **"A clear reference" is the list itself**, with no history on it. And a new feature:
   > "when creating a Habit the user will select an energy level (low/mid/high) and in Today and the Habits screen they will have a filter to only show the habits they are able to handle at that moment. The filter resets every day at midnight."

**Read as follows; each point is checked with the owner at the screen that shows it:**
- **The filter is cumulative.** Low shows the low habits; Mid shows low and mid; High shows all. Unset means all.
- **"Midnight" is the personal day boundary** (§3.6). It defaults to midnight, so the filter resets when the person's day starts.
- **Where the filter's state lives is open.** It is either per device (DEVICE_STATE) or for the person on every device (PERSONAL). It is put to the owner with the filter.

**Owed in the data layer**, built once T3a's screens settle the field shapes:
- **Habits:** a HABIT is yes/no only. A rating or number habit becomes its tracker alone, and §3.6's number-habit rules (amount per Log, the DAY goal, today's and the month's amounts) move to trackers. Existing rows need a migration path.
- **A habit's cue:** short text, synced in the item's details group.
- **A habit's energy:** LOW, MID or HIGH, synced.
- **The energy filter:** a PERSONAL setting (owner): High by default, reset to High at the personal day's start.
- **Today lists trackers:** which ones (a daily goal, pinned, or all) is part of the "future tinkering".
- The SPEC amendment for all of the above.

## T3a.1 Habits as Daily basics: scored (2026-10-13)

**Part `basics` in `tools/screens/t3_opt.py`.** The first scoring is kept as `t3-habits-v1.json`.

**Fixed in every option:**
- yes/no habits;
- T1's own Log button at the row's right;
- no history on the list;
- each habit's written cue, ordered by its block;
- an energy filter (cumulative).

The sample is eight placeholder basics: Make the bed, Take meds, Brush teeth, Shower, Tidy the desk, Put a wash on, Wash face, Floss.

**The 54 options:**
- **layout:** blocks with the cue under the title / flow, one list in the day's order / sentence ("After breakfast, brush teeth");
- **filter:** chips (Low · Mid · High) / a single "Low energy only" switch / a menu under ✎;
- **energy mark:** none / dots / a word;
- **done:** folds into "Done today" as on Today / stays, ticked.

**Axes:**
- Judgment (history marks);
- Cue (cue shown, day order);
- Low capacity (words per row, actions and reach to filter, reach to Log);
- Choice (the filter can say Mid);
- Consistency (done folds as on Today);
- Density;
- Calm.

**The control, changed once.** The first control was Loop-like: alphabetical, no cue, no filter, streaks and crosses. **It reached the front on Calm alone**: with no cue lines and no filter row, it drew the least. Making "no judgment" a gate would not do, because the machinery rightly counts a gated control as not lost. The new control is the leading design with history added ("streak 3 · 62%" on every row), so it isolates what the owner's rule forbids. It loses at 451.5: 14 history marks, 9.6 words per row against 4.6, and more clutter.

**The front, lowest sums:**

| Option | Sum | Words per row | Filter actions | Filter says Mid | Done like Today | Clutter, phone / Windows |
|---|---|---|---|---|---|---|
| flow, chips, none, stay | 291 | 4.6 | 1 | yes | no | 0.045 / 0.020 |
| **blocks, chips, none, fold** | **300.5** | 4.6 | 1 | yes | **yes** | 0.047 / 0.021 |
| flow, chips, none, fold | 311 | 4.6 | 1 | yes | yes | 0.043 / 0.020 |
| blocks, chips, none, stay | 333 | 4.9 | 1 | yes | no | 0.049 / 0.021 |

Averaged over each dimension, lower being better:

| Dimension | Averages |
|---|---|
| filter | chips 364 < switch 391 < menu 416 |
| energy mark | none 357 < dots 391 < word 424 |
| layout | flow 367 ≈ blocks 375 < sentence 430 |
| done | fold 390 ≈ stay 391 |

**Recommended: blocks, chips, no energy mark, fold.**
- Chips are the cheapest filter that can also say Mid.
- An energy mark on the row only adds to read; the filter already does the sorting.
- Fold keeps a Logged habit doing what it does on Today (the consistency rule).
- Blocks show the "if" order the owner chose (answer c), at 7.5 above flow on the average.

## T3a.1 Habits as Daily basics: approved (owner, 2026-10-13)

**The pick:** blocks, chips, no energy mark, fold, with two changes from the owner:
- **The "if" sits above the habit:** the cue is a small line above the title.
- **The energy filter:**
  > "Default filter is High (High + Medium + Low). Medium only includes Low. Low is standalone."

  So High (the default) shows all, Mid shows low and mid, and Low shows low only. It resets to High when the personal day starts.
- **Its setting is "one setting for you, on every device"** (PERSONAL, synced).

Both changes are drawn, and the part is rescored with them.

**Next, at the owner's ask: the Add Habit screen.** Since habits are daily, the habit Planner (a weekly re-assessment that confirms "n a week" habits into days) may be removed or repurposed.

Rescored with the approved drawings (the cue above the title, High on by default):
- the approved option sits on the front at 301;
- the control loses at 450.5;
- the order is unchanged.

## The Add Habit screen and the Planner: the owner's answers (2026-10-13)

1. **The habit Planner is dropped:**
   > "Currently dropped, its empty structure might be repurposed for something other than habits in the future."

   - Habits no longer use "n a week" or "n a day" (PLANNED). A habit twice a day is two habits, each with its own cue.
   - The structure is kept, not deleted: the PLANNED kind, `core.plan` and `habit_block`'s planner columns stay in the data layer, unused by habits, for a possible later use.
   - This is an owner-accepted exception to §0.1.5, as Tendril's Claude text verbs were. It drops a Tendril feature from habits.
2. **A habit repeats daily, or on chosen weekdays.** Nothing else; rolling ("again N days after the last Log") is not offered for habits.
3. **Adding a habit: both forms are scored, with a control:**
   - the capture line, then the row growing in place with its fields (as an item's page, T2);
   - a dedicated sheet (as Tendril's Add habit).
4. **A habit's reminder is off by default.** When on, it is either at the start of its block or at a set time.

**Owed in the data layer:**
- a HABIT's recurrence is daily or chosen weekdays only;
- PLANNED and ROLLING are not offered for habits, and rows that have them need a migration path;
- a reminder at the block's start or at a set time (both exist in §3.6b and §3.3).

## T3a.2 Adding a habit: scored (2026-10-13)

**Part `addhabit`.** The fields come in the owner's order:
- the name;
- If (the cue);
- Block;
- Energy (Low · Mid · High);
- Repeat (Every day, or chosen days);
- Reminder (off; at the block's start or at a set time);
- Label;
- Notes.

**The 8 options:**
- **form:** in place (the T1.3 capture line takes the name, then the new row grows in place, autosaved, as an item's page) / sheet (all fields, with Cancel and Add pinned at its foot);
- **the If:** free text / suggested anchors as chips plus "Write your own";
- **block:** chips / set by the chosen anchor.

**The walk:** adding "Brush teeth", after breakfast, Morning, Low, every day.

**The control:** Tendril's sheet as it is, with the cue last. It loses at 63, behind seven of the eight options.

| Option | Sum | Taps | Keyboards | Reach | Hidden targets | Lost on leaving | Like an item's page | Clutter, phone / Windows |
|---|---|---|---|---|---|---|---|---|
| **in place, suggest, from the cue** | **47.5** | **4** | 1 | 3.45 | 0 | no | yes | 0.053 / 0.025 |
| in place, suggest, chips | 48 | 5 | 1 | 3.08 | 0 | no | yes | 0.056 / 0.027 |
| sheet, suggest, chips | 50.5 | 6 | 1 | 2.95 | 1 | yes | no | 0.041 / 0.021 |
| in place, text, chips | 52.5 | 5 | 2 | 3.37 | 0 | no | yes | 0.048 / 0.023 |
| sheet, suggest, from the cue | 52.5 | 5 | 1 | 3.02 | 1 | yes | no | 0.042 / 0.021 |
| in place, text, from the cue | 55.5 | 6 | 2 | 3.42 | 0 | no | yes | 0.045 / 0.021 |
| sheet, text, chips | 61 | 6 | 2 | 3.13 | 1 | yes | no | 0.038 / 0.021 |
| sheet, text, from the cue | 64.5 | 7 | 2 | 3.16 | 1 | yes | no | 0.034 / 0.021 |
| control (Tendril's sheet) | 63 | 5 | 2 | 1.72 | 1 | yes | no | 0.042 / 0.021 |

All eight options are on the front; the control is not.

**Reading the table:**
- **The sheet** is calmer and nearer the thumb. But one target sits below its fold, leaving loses the habit, and it is not how an item's page works.
- **Suggested anchors** save a keyboard and set the block for free.

**Recommended: in place, suggested anchors, the block set by the anchor.**

## Routines, and adding a habit as a sentence (owner, 2026-10-13)

**The owner's proposal.** Instead of suggested anchors, which fit only once or twice a day and add to the screen, a habit is added as an open fill-in sentence:
> If/After/Before/When/During [premise] then [habit], daily / days of the week (several), no set time / at [time] / from [start] to [end].

And an "if" can be a parent: a routine the user names (e.g. "Morning routine") holds habits in the user's order. It shows that they belong to one sequence, and how much the series asks of the person, "an invisible 'what to expect' layer". The owner: "a 'complexity' addition to the creation step is worth it if it enhances the user's experience overall."

**Assessed:**
- **The sentence is T1.5 and T1.6's approved "When" sentence pattern.** It is consistent, not new. Defaults are filled (every day, no set time), so the minimum is two blanks.
- **A routine is a behaviour chain:** each step cues the next.
- **The routine's name replaces the block header.** It does not add a layer, and its header can carry a forecast, not history.
- **A user's routine of ordered habits is a routine checklist,** so the strong overlap group O1 (Daily basics) resolves into one concept.

**The owner's answers:**
1. **The routine carries the "if" and the time.** The habits inside are ordered steps that inherit it. A habit outside any routine keeps its own sentence.
2. **Routine checklists merge into routines.** Checklists remain only as one-off lists (packing, shopping).
3. **With the energy filter on, steps above the level are hidden.** The routine stays, and its header says how many steps show ("2 of 3 steps").
4. **The routine header's "what to expect" preview: score the forms.** None, steps, steps with the highest energy, steps with time, against a control.

**Owed in the data layer:**
- **A routine:** a name, its sentence (connective, premise, days, no time, at a time, or from and to), its ordered habits, and a habit's place in at most one routine.
- **The merge with Chronicle's resettable checklists** (`checklist`, `checklist_item`): a routine checklist becomes a routine; a one-off list stays a checklist.
- **A habit's own sentence:** connective, premise, days, time.

The cue field recorded earlier becomes the premise; the block is now set by the sentence's time.

## T3a.1b The Habits list with routines: scored (2026-10-13)

**Part `routines`.**
- **The sample:** two routines and three lone habits:
  - Morning routine (After waking · every day): Make the bed (done), Wash face, Brush teeth, Take meds;
  - Evening wind-down (Before bed · 22:00–23:00): Lay out clothes, Floss, Set the alarm;
  - lone: Shower, Tidy the desk, Put a wash on.
- **The 12 options:** preview (none / steps / steps with the highest energy / steps with time) × sequence (a line / numbers / plain).
- **The axes:**
  - Judgment;
  - Expect (forecast facts in the header, the order marked, and whether the Low-energy drawing says how many steps show);
  - Low capacity (words per unit);
  - Density;
  - Calm.
- **The control:** the routine as a checklist with progress ("1/4 done · 25%"). It loses at 83.5.

| Option | Sum | Forecast facts | Order marked | Words | Clutter, phone / Windows | On the front |
|---|---|---|---|---|---|---|
| none, numbers | 54.5 | 0 | yes | 4.3 | 0.048 / 0.021 | yes |
| steps, numbers | 55.5 | 1 | yes | 4.7 | 0.049 / 0.022 | yes |
| **energy, numbers** ("4 steps · up to Mid") | **59.5** | **2** | yes | 5.5 | 0.051 / 0.022 | yes |
| time, numbers ("4 steps · about 8 min") | 59.5 | 2 | yes | 5.5 | 0.051 / 0.023 | yes |
| none, line | 58.5 | 0 | yes | 4.3 | 0.050 / 0.022 | no |
| none, plain | 61.5 | 0 | no | 4.3 | 0.049 / 0.022 | no |

**What the scores say:**
- **Numbers mark the sequence** more calmly than a joining line, and both beat plain rows.
- **A fuller forecast costs words.** "None" is cheapest because it forecasts nothing, which is the owner's reason for the header.
- **Energy and time forecast equally on the measures.** The energy form names the "mental load" the owner asked to convey, and it matches the energy filter's own words.

**Recommended: energy, numbers.**

**Two changes from the owner (2026-10-13), drawn and rescored:**
- **No kind glyph on the Habits page.**
  > "Since we already are in the Habits page, could the icon/glyph be removed?"

  Every row there is a habit. The mark that tells kinds apart stays where kinds mix (Today, the Day screen, search). Steps keep their numbers, and lone habits line up with the routine headers.
- **The sentence line shows only the parts that are set.**
  > "If a habit has a set time or duration, it could be written next to the if, like days?"

  So the line reads: the if, then the days when chosen, then a set time or a window ("After the walk · 08:30", "Before bed · 22:00–23:00", "When I get home · Mon, Thu"). "Every day" is the default, so it is not written; it had been under Morning routine but not on the lone habits.

Rescored: energy and numbers stays on the front (60.5), and the control still loses (83).

## T3a.1b The Habits list with routines: approved (owner, 2026-10-13)

**Approved:**
- routines with the if-then sentence in the header;
- lone habits with their sentence line above;
- no kind glyph;
- energy chips, High by default;
- Today's Log button;
- done steps fold.

**The forecast is optional:**
> "the energy forecast with numbered steps should be optional, the user can set it to ON in Settings or by editing the page (to be determined). Default is OFF."

- **Default (OFF):** a routine's steps are plain rows under its header, with no forecast.
- **ON:** the header adds "4 steps · up to Mid", and the steps are numbered.
- Read as one switch for both; to confirm.
- Where the switch lives (Settings, or editing the page) is to be decided.

## T3a.2b Adding a habit as an open sentence: scored (2026-10-13)

**Part `addsent`.** It supersedes T3a.2's field form, which is kept here as the baseline.

**The sentence's words are tappable**, as in T1's approved When sheet:
> If/After… [premise] then [habit], [days], [time], plus energy and the routine.

**The 12 options:**
- **form:** the When sheet (fixed height, the sentence pinned at its foot, the chooser above) / the new row growing in place with the sentence inside / T3a.2's fields;
- **energy:** a word of the sentence / chips under it;
- **routine:** a word of the sentence / a row of its own.

**Two walks:**
- "Brush teeth" into Morning routine, Low. The routine sets the if, days and time.
- A lone "After breakfast then floss, Mon Wed Fri, at 08:30, Low".

The taps are walked per path as written in the docstring. The field form's lone walk first left out the days and the time, which every form needs; it was corrected before ranking.

**The control:** Tendril's sheet. It loses at 97.5.

| Option | Sum | Taps (routine / lone) | Reads as one sentence | Like T1's When | Clutter, phone / Windows | On the front |
|---|---|---|---|---|---|---|
| **When sheet, energy and routine as words** | **72.5** | 6 / 14 | yes | yes | 0.033 / 0.021 | yes |
| When sheet, energy chips, routine as a word | 73.5 | 5 / 13 | partly | yes | 0.034 / 0.021 | yes |
| When sheet, energy chips, routine row | 74 | 5 / 13 | partly | yes | 0.036 / 0.021 | no |
| in place, energy chips, routine as a word | 79 | 5 / 13 | partly | no | 0.055 / 0.025 | yes |
| in place, both as words | 79.5 | 6 / 14 | yes | no | 0.053 / 0.025 | yes |
| fields (T3a.2) | 92 | 4 / 13 | no | no | 0.055 / 0.025 | no |
| control (Tendril's sheet) | 97.5 | 6 / 7 | no | no | 0.042 / 0.021 | no |

**Reading the table:**
- **The When sheet** is the calmest form, and it is the pattern already approved for dates and repeats. Its fixed height keeps the sentence in one place.
- **Putting energy and the routine in the sentence** costs one tap each against chips. In return, the whole rule reads back as one line to check.
- **The fields form** is quickest only for a habit going into a routine (4 taps). It never shows the rule as a sentence.

**Recommended:** the When sheet, with energy and the routine as words of the sentence.

## Ifs and routines, one entity (owner, 2026-10-13)

> "From my understanding routines are just IFs with more than one habit under them. Am I mistaken?"

**Not mistaken, and simpler.** The one entity is an if: a connective, a premise, days and a time, holding ordered habits.
- An if with one habit shows as a lone habit.
- An if with two or more habits shows as a routine.
- A routine is never created as such. It appears when a second habit takes an if, and it disappears when only one habit is left on it.
- **Proposed** (to be confirmed by the owner): the same if means the same connective, premise, days and time, chosen from the existing ifs rather than retyped; an optional name; the order set by dragging.

## T3a.2c The New habit sheet: a prototype on the When sheet's pattern (owner, 2026-10-13)

**What the owner rejected in the earlier drawings:**
- Always-present chips of routines and ifs, which "could become numerous and excessively crowd the screen".
- "Put it in", "New routine", "in a routine…".
- The drawings themselves: "None of the screens proposed display the options available once each word is clicked, nor the text boxes for the user to fill in the blanks."

**What the owner asked for instead:**
- "a small line right above the picker sentence, e.g. 'Available IFs'". Choosing from it auto-fills the first part of the sentence, and the sheet grows upward only when needed.
- Consistency with T1.5 + T1.6, minding the different axes.

**Built:** the interactive prototype `docs/screens/t3/habit-prototype.html`, taking the When prototype's own parts:
- the foot anchored and the sheet growing upward only;
- the tappable words;
- the weekday row and its shortcuts;
- the dial with a typed field;
- Undo and Redo, and the readout line.

**New for habits:**
- the blanks are text boxes, sized to their text;
- "Available ifs · 5" opens upward, and choosing one fills the connective, premise, days and time;
- a chosen if's words read dotted, and changing one says it changes the if for its habits;
- the readout says what will happen: "Joins 'After waking' as step 5: 5 habits, shown as a routine", "A new if, with this one habit", or that a typed premise is already an if;
- Add appears once the premise and the habit are written.

The states are rendered from the prototype itself, as `when_page.py` renders the When sheet: `docs/screens/t3/habit/*.png`.

**Scored (part `hsheet`):**
- **The variant:** the blanks as text boxes in the sentence, or as words opening a text box above.
- **The walks:** joining After waking; a new "After breakfast then floss, Mon Wed Fri, at 08:30, Low".
- **The control:** Tendril's sheet, which cannot set weekdays or energy. It loses.

**Two measures were corrected on the way:**
- **The gate:** the "At" chip was 38 dp wide, under 48. It comes from the When prototype, which has the same defect. Chips get a 48 dp minimum here, and the When prototype goes on the consistency-pass list.
- **The stability measure:** it first read the sentence's top, which moves by design as blanks fill and the sentence gains a line. The When rule is the foot's bottom, which now stays at one pixel in every state.

| Variant | Join taps | New-if taps | Foot moves | Clutter |
|---|---|---|---|---|
| **text boxes in the sentence** | **5** | 15 | 0 px | 0.032 |
| words opening a box above | 6 | 15 | 0 px | 0.031 |
| control (Tendril's sheet) | 6 | cannot | n/a | 0.042 |

**Recommended:** text boxes in the sentence. It answers the owner's "text boxes for the user to fill in the blanks" directly, and a chosen if puts the cursor in the habit's box.

**The consistency pass (owner, 2026-10-13: "We will later discuss one consistency pass across screens") will take:**
- Today's Log button against the Habits page's;
- Today showing trackers;
- the forecast option's switch (Settings or editing the page).

## Two owner corrections (2026-10-13)

1. **One writable time box** in the habit sheet and in T1.5 + T1.6's When sheet. The display pill and the typed field merge (decision 17 amended). Checked in the browser: tapping the "to" box makes it the dial's target, and typing sets it.
2. **The 48 dp gate is not blanket:**
   > "The 48 dp minimum cannot be a blanket choice applied to input screens, as it would bulk up every visible element and create an issue in visual priority across different elements."

   **Proposed rule, applied from now on pending the owner's confirmation:**
   - primary actions keep 48 dp (the sentence's words, Add, Log, Done, the bar);
   - a control inside a chooser (a chip, a weekday, the dial's inner ring) needs WCAG 2.2 AA's 24 dp (2.5.8);
   - visual size follows the element's priority, not the gate.

   This is `tiered_small` in `t3_opt.py`. The earlier widening of the habit sheet's chips to 48 dp is withdrawn: the chips match the When sheet's again, and the "At" chip (38 dp) passes the tiered gate.

   The consistency-pass list drops "the When prototype's chips under 48 dp". It is no longer a defect under the tiered rule.

## T3a.2d What the premise box opens, and "+ time" (owner, 2026-10-13)

**The owner, on the prototype:**
> "When tapping the premise, either the available IFs do not open or only the same kind are shown. Score both options."

The axes are the owner's choice: Ease, Duplicate guard, Room with keyboard, Scan load.

**Part `premise`.** The Available ifs line stays in both variants. The walk is in the sentence's order: After, the premise box, then join "waking". Measured with the keyboard up, as a 280 dp block at the foot.

**The control:** the box opens every if, whatever the connective (the prototype as it was). It loses. With the keyboard up its list is cut after three rows.

| Box opens | Taps to join | Typed to join | Duplicate guard | Rows to scan | Sentence in view | Clutter |
|---|---|---|---|---|---|---|
| nothing (A) | 5 | yes ("waking", then the readout says it exists) | no | 0 | yes | 0.034 |
| **the same connective's ifs (B)** | **4** | **no** | **yes** | 3 | yes | 0.044 |

Both variants are on the front:
- **A** is calmer and has nothing to scan.
- **B** joins in one tap less with nothing typed, and shows an existing premise before it is typed twice.

The one-entity model depends on matching ifs: a retyped "waking" makes a second if instead of joining the routine. That makes the guard worth its three rows. **Recommended: B.**

**"+ time" on "at"** (the owner: "'at' lacks the '+ time' button"):
- "at" now takes "+ time" and "− time", as the When sheet's does: "at 08:00 and 20:30".
- Each time is its own writable box.
- **To confirm:** several times on one habit repeat it within the day, close to the "n a day" form dropped with the Planner.

## T3a.2 The New habit sheet: approved (owner, 2026-10-13)

**The owner's answers:**
1. **The premise box opens the ifs of the same connective (B),** with no message when there are none:
   > "B, but with no 'No "..." ifs yet: this one will be the first.' message when no other premise of the same kind exists yet."

   Nothing opens instead.
2. **Several "at" times are kept, with "and" between their boxes** so they read apart from "from–to":
   > "between time boxes there should be an 'and' or '&' to differentiate it from 'from-to'."

   - It is done in the habit sheet and in the When sheet. T1's rendered states are unaffected: none of them shows two times.
   - A habit with several times is **"same habit, shown twice (or more) in screens where time constraints matter"** (Today, the Day screen).
3. **The rest:**
   - **Tap size:**
     > "Tap size is fine on screen, might be adjusted once the app is phone tested."

     The tiered rule stands until the phone test.
   - **The sheet:** "This is the new habit sheet." It is approved: the blanks as text boxes in the sentence, Available ifs above it, B for the premise box, one writable time box per time.
   - **Matching ifs:**
     > "The same premise exists when the user selects the same IF, no need to work around it since the B option solves this."

     Two habits share an if when it is chosen from the list; nothing else matches them.
   - **Order:**
     > "Untimed Habits are in chronological order (older first), and can be dragged to reorder them."

**Asked again:** the optional name for a routine (an if with two or more habits). It would be a title such as "Morning routine" above its if ("After waking"); without it, the if is the header.

**Owed in the data layer, added:**
- a habit's several "at" times, each an occurrence shown on Today and the Day screen;
- an untimed habit's manual order, defaulting to its creation order.

## T3a.1c The Habits list: the optional name, and every if as a header (2026-10-13)

> "Score the Habits screen (not the New habit screen) with the optional name included and showing every habit with an if, against the current proposed screens."

**Part `habits2`.** Every form keeps the forecast OFF (the default), no glyph, the energy chips with High on, Today's Log and the fold. The control is every if as a checklist with progress. It loses at 36.

| Form | Sum | Every habit in one shape | Names in view | Words per row | Header px | Rows seen | Clutter, phone / Windows |
|---|---|---|---|---|---|---|---|
| headers for routines only, **named** | **23.5** | no | 2 | 5.3 | 104 | 8 | 0.047 / 0.021 |
| headers for routines only, no names (approved) | 24 | no | 0 | 4.8 | 68 | 8 | 0.045 / 0.020 |
| every if a header, no names | 24.5 | yes | 0 | 5.3 | 149 | 7 | 0.042 / 0.019 |
| every if a header, named | 27 | yes | 2 | 6.3 | 185 | 6 | 0.043 / 0.020 |

All four forms are on the front, within 3.5 of each other.

**What the scores say:**
- **The name** adds a line per routine (36 px) and a few words, and makes the routines recognisable by the person's own words.
- **Every if as a header** makes every habit one shape and is a little calmer. It costs header space: 149 px against 68, one row fewer in view.
- **Since the name is optional,** "headers for routines only" with and without names are one design: a routine shows its name when the person has written one.

## The options pages fold what was discarded (owner, 2026-10-13)

> "Also remove or collapse all discarded screens."

`toast_opt` takes two lists:
- `PICKED`: a decided part shows its picks, with the options not picked and the control folded under "Not picked".
- `SUPERSEDED`: a superseded part folds whole.

**Applied:**
- **T2:** all six parts show their picks (`t2_opt.T.PICKED`).
- **T3:** the routines, the sheet and the premise box show their picks. Daily basics' first list, adding a habit with fields, and the first sentence fold as superseded. The first T3.1 presence scoring has no options page entry, so it is not drawn at all.
- The scores pages keep every row.

## T3a.1c approved: headers for routines, named (owner, 2026-10-13)

"routines, named":
- An if with two or more habits is a routine, under a header.
- A routine shows the name the person wrote ("Morning routine") over its if ("After waking").
- A routine with no name shows its if as the header.
- A lone habit keeps its if as a small line above it.
- Everything else is as approved: no glyph; energy chips with High on; Today's Log; done steps fold; the forecast with numbered steps an option, OFF by default.

**Owed in the data layer, added:** a routine's optional name, kept on the if.

**T3a Daily basics is complete:**
- the Habits list (T3a.1c);
- the New habit sheet (T3a.2, `habit-prototype.html`).

Next: T3b Measuring (trackers, activities and timers, goals).

## T3b.1 The Trackers list: scored (2026-10-13)

Trackers are what is counted or rated; a habit is yes/no (T3a). The four kinds are Chronicle's: a number with a unit, yes/no, a rating 1-5, a choice. No goal shows on this list: goals are their own T3b screen, and an amount reads plain, never as a fraction (T3.1, Tendril's rule).

**References** (`docs/screens/t3/t3-references.json`, `trackers_list`; screenshots in `_screens-sources/t3/`):
- **Chronicle** (source app), Data tab:
  - each tracker is a card with a kind glyph (# for a number), its name, a line under it, and a filled "+ Log" pill;
  - the line reads "no entries yet", then "1 today · last just now";
  - category headers with a count and a fold;
  - Checklists sit below on the same screen, and a folded Quick add line (typed logs) sits at the top;
  - "+ Log" opens a sheet with six controls: Quick presets with Set, a − value + stepper, Label, Note, When, Save;
  - its New tracker sheet: name; type (Number, Yes / No, Rating, Choice); unit chips; "Set a default value (1-tap logging)"; direction; category.
- **Track & Graph:**
  - two columns of cards: the name, the last time ("1 minuto fa"), never a value, and a + at the corner;
  - graphs and groups are cards in the same grid;
  - + opens a dialog: date, time, the value filled with 1 and the keypad up, label and note folded as chips, then Add.
- **Loop**, a measurable habit:
  - the last 4 days as cells with the amount and unit ("0 glasses");
  - a cell opens a popup with a note and the value on the system keypad.

**The space** (`tools/screens/t3_opt.py`, part `trackers`): 60 options plus the control. Nine placeholder trackers sit under four labels.
- layout:
  - rows: Today's and Habits' rows;
  - grid: Track & Graph's cards.
- what a row says:
  - none: the name only;
  - today: "3 glasses today";
  - last: "last 11:40";
  - today + last: Chronicle's line;
  - spark: today and the last 7 days as small bars, with a day with no reading drawn as a tick.
- what Log does:
  - sheet: Today's Log opens the Log sheet with the usual amount filled in, so 2 taps;
  - default: Log logs the usual amount at once, with a toast offering Change and Undo; a tracker with no usual amount opens the sheet;
  - stepper: − n + on the row for a number with a usual amount; the others keep Log.
- grouping:
  - flat;
  - labels.

**Axes:** T2's practice plus the register (decision 19's defaults):
- Ease: taps to log a usual glass; reach to the first Log.
- Predictable: whether Log acts alike on every row; writes made with no confirming step.
- Glance: the share of rows that say something.
- Judgment: empty-day ticks, fractions, percentages, streaks.
- Find: the rows read on average to find a tracker, a label header counting as one.
- Consistency: rows and Log as Today's.
- Density: rows seen, titles cut, words per row.
- Calm: clutter, Windows' clutter.
- Refs: distance from the three references.

**Control:** a dashboard. Each card shows today against its goal ("3/8 · 38%"), a progress bar, a streak and the 7-day bars; Log goes through the sheet. **It lost:** rank sum 528, last but for nothing, with 52 judgment marks against 0.

**Drawn** (`t3-options.html`): the best of each layout × Log family, plus the leader's family with each thing a row can say. The front holds 40 of 61, because eight axes leave room for many trade-offs.

| Option | Sum | Front | Ease | Predictable | Glance | Judgment | Find | Consistency | Density | Calm | Refs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rows · none · sheet · labels | 296.5 | ★ | 91.5 | 22 | 55.5 | 24.5 | 15.5 | 10.5 | 45.5 | 16.5 | 15 |
| rows · today · sheet · labels | 327.5 | ★ | 91.5 | 22 | 39 | 24.5 | 15.5 | 10.5 | 62 | 47.5 | 15 |
| rows · last · sheet · labels | 331 | ★ | 91.5 | 22 | 13 | 24.5 | 15.5 | 10.5 | 99.5 | 50 | 4.5 |
| grid · none · sheet · labels | 352.5 | ★ | 61 | 22 | 55.5 | 24.5 | 15.5 | 41 | 84.5 | 24.5 | 24 |
| rows · none · default · labels | 361.5 | ★ | 61 | 83 | 55.5 | 24.5 | 15.5 | 10.5 | 45.5 | 16.5 | 49.5 |
| rows · none · stepper · labels | 388 | ★ | 61 | 83 | 55.5 | 24.5 | 15.5 | 41 | 45.5 | 12.5 | 49.5 |
| rows · today + last · sheet · labels | 389.5 | | 91.5 | 22 | 13 | 24.5 | 15.5 | 10.5 | 111.5 | 96.5 | 4.5 |
| rows · spark · sheet · labels | 397.5 | ★ | 90 | 22 | 31.5 | 51.5 | 15.5 | 10.5 | 108.5 | 53 | 15 |
| grid · none · stepper · labels | 415.5 | ★ | 30.5 | 83 | 55.5 | 24.5 | 15.5 | 41 | 84.5 | 22.5 | 58.5 |
| grid · last · default · labels | 427.5 | ★ | 30.5 | 83 | 13 | 24.5 | 15.5 | 41 | 122 | 56.5 | 41.5 |
| control | 528 | | 61 | 22 | 13 | 61 | 46 | 41 | 147 | 122 | 15 |

**What the scores say:**
- **Labels win on Find:** 4.1 rows read on average against 5.0.
- **Rows win on Consistency and Density:** 9 rows seen against 7 cards.
- **What a row says** is the one real trade:
  - The name alone is calmest (clutter 0.033), but says nothing.
  - "today" leaves the three trackers with nothing today bare.
  - "last" says something on every row.
  - "today + last" doubles the words (5.4 a row).
  - The spark puts 15 empty-day ticks on screen, which counts as judgment.
- **What Log does** trades Ease against Predictable:
  - default and stepper log in 1 tap, but act differently on trackers with no usual amount, and write with no confirming step;
  - sheet always opens the sheet, at 2 taps.
- Today's Log button is the same pill in every option but the stepper. What Today's Log does on a counted row is decided here too, for the consistency pass.

Found on the way: `.tgrid` and `.trow` were already used by other scorers' styles; the cards collapsed to two. They are now `.kgrid`, `.krow` and `.kcard`.

Status: **scored, awaiting the owner's pick.**

## T3b.1b The Measuring list, taps first (2026-10-13)

The owner: trackers belong to P4 Measuring, "one of the screens that can be busy in exchange for least taps to log data or start a timer". T3b.1 is superseded.

**The owner's answers:**
- Score one merged list (trackers and activities, with ▶ / ■ on an activity's row) against two screens.
- A stray tap's write is an axis (Recovery).
- Today's tracker rows wait for the consistency pass.
- Judgment marks stay an axis.

**The space** (`t3_opt.py`, part `measure`): 160 options plus the control.
- scope: merged / apart;
- layout, what a row says and grouping: as T3b.1;
- Log: sheet / default / stepper / **inline**, a control per kind on the row:
  - "+ 1 glass" for a number with a usual amount;
  - Yes for yes/no;
  - the five ratings as chips;
  - the two most recent choices as chips, then …;
  - a number with no usual amount keeps Log.

**The walk:** a usual glass of water; 7.5 hours of sleep; Mood 4; Headache yes; Commute by bike; starting and stopping the Reading timer. A target out of view adds a scroll.

**Axes:**
- Taps (mean over the walk);
- Reach (mean Fitts over the walk's targets);
- Recovery (the share of logs written by one tap with no confirming step);
- Glance (rows that say something; a running timer shown);
- Judgment;
- Find;
- Refs.

**Gate:** no title cut; primary targets at 48 dp, chips at 24 dp. 16 options are out, all for cut titles.

**Found on the way:** reach to Water's Log alone put the control on the front, because its progress bar had pushed that one button nearer the thumb. Reach now averages the whole walk.

**The control is still on the front (the gate fails), and the reason is the weighting:**
- Recovery is exactly the price of fewer taps.
- Refs rewards the sheet, which all three reference apps use.
- With Calm and Density dropped, nothing charges the dashboard for its busyness.

Under equal weights a sheet leads again (merged · grid · last · sheet · flat, 2.5 taps).

**Taps-led previews** both pick **merged · grid · last · inline · labels**, at 1.67 taps against the control's 3.0:
- the fewest taps first (within 0.17), the other axes breaking ties;
- or Taps counted twice, with Refs dropped.

Status: **awaiting the owner's choice of weighting.**
