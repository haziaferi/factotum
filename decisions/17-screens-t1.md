# 17. Screens T1: shared parts

Status: **questions answered 2026-10-07; screens being mocked one at a time.** Method: decision 15, "every screen, one at a time, before colour".

T1 holds the parts every later tier reuses:
- the header and the bar;
- item rows;
- the capture sheet;
- the Hub sheet;
- the date, time and repeat pickers;
- label chips;
- toasts and dialogs;
- empty and error states.

Mockups are in `docs/screens/t1/screens.html`.

## Owner's answers (2026-10-07)

| Question | Answer |
|---|---|
| What a row shows | **Title only** is the default for the screens. The three variants (title only; title plus one quiet line; title plus chips) are mocked side by side in a chapter of their own, to decide later. |
| Acting on a row | **No swipes at all.** |
| Capture | **Parsed chips under the line.** The text stays as typed, and tapping a chip fixes it or drops it. |
| Destructive actions | **An Undo toast, no dialog.** Dialogs only for what Trash cannot bring back: emptying Trash, discarding an unsaved page. |
| Date and time | **Presets first** (Today, Tomorrow, This weekend, Next week, No date), then a month grid and the time. Typing a date also works. |
| Repeat | **A plain-language builder with a live sentence**: common choices as a list, "Custom" for the fields, and the rule read back with its next three dates. |
| Empty states | **One plain sentence and one action.** No illustration, no cheer, no guilt. |
| Labels | **A dot and the text.** The dot takes the user's colour later. |

Already decided elsewhere: a done or skipped item folds into "Done today · n" (decision 15).

**Row actions (owner, 2026-10-07):**
- Tap the circle for Done, with Undo.
- A long press opens the other actions: move, skip this one, edit, label and delete.
- Opening the item offers every action.

There are no swipes.

## Screens

| # | Screen | Status |
|---|---|---|
| T1.1 | Header and bar | **approved 2026-10-07: A′** |
| T1.2 | Item rows (title only), plus the row-variants chapter | **approved 2026-10-07: D** |
| T1.3 | Capture sheet | in progress |
| T1.4 | Hub sheet (cards) | to do |
| T1.5 | Date and time picker | to do |
| T1.6 | Repeat builder | to do |
| T1.7 | Label chips and picker | to do |
| T1.8 | Toasts and dialogs | to do |
| T1.9 | Empty and error states | to do |

## T1.1 Header and bar: approved (2026-10-07)

**A′: a quiet header.** The title sits on the left, with Search and then Settings on the right. The bar is Today · Calendar · Hub · Pages · [check-in]. Search, Capture, the Hub and Settings are each one tap from Today. Scores are in `docs/screens/t1/scores.md`; A′ is on the front, and the control loses.

The critique pass (`design-critique-plus`, measured with `craftkit ui`) found two defects. Both are fixed in `tools/screens/kit.py`:
- **The receded bar and rail labels read at 2.4:1** in light, because opacity .65 was applied on top of the dim grey. Inactive items now recede by colour alone, at 5.3:1 or more. The scorer gained a measure for this, `faint`, and was checked against the old bar: it flags its three labels at 2.2:1.
- **The light-theme dim grey #6B6B66 read 4.48:1** on the bar's surface. It is now #60605B (5.29:1).

Also added: the document language and the viewport meta.

Left as Low:
- some spacing values are not on a 4 px grid;
- the scale is 12 / 13 / 15 / 18 px.

Both are settled when type and density are scored.

## T1.2 Item rows: put to the owner (2026-10-07)

Rows are title only and cover every kind: an event, a task, a reminder, two habits, a checklist and a reading. Three options and a control:
- **A, leading mark:** the left slot says what the row is.
- **B, action at the thumb:** the times sit in a column on the left, and every action at the right edge.
- **C, words, not marks (oblique):** the actions are the words Done, Log, Open and Add.

**Measured, A, B and C tie.** Their clutter differs by at most 0.001 (the front now ignores differences under 0.002, `screen_score.TOLERANCE`). All three show the same 8 rows, with no faint labels and no small targets. **The control loses on every count:** clutter 0.056, and four targets under 48 dp.

What decides between them is not measured: how quickly each kind is recognised, and which hand the actions favour. The states are drawn on C: Done with Undo, the long-press menu, Deleted with Undo, and a long title. So is the chapter of variants (title only, a quiet line, chips).

**Refined after the owner's questions (2026-10-07).**

*Why can Call the bank be done but Dentist can't?* An event is a block of time with no done state (decision 02: no task status on an event row). A reminder is a to-do with an alarm (§3.3). The rows now show this: an event's lead is its span, 09:00 over 09:45.

*Can A and B be merged, so the left column is never empty?* Three new options:
- **D merges A and B.** The left column holds the time, the event's span, or a quiet kind mark; the action is on the right.
- **E keeps a time column always.** It shows the clock time, the span, the habit's time block, or Any time.
- **F is oblique: the action leads and the time trails**, as in Things and Google Tasks.

Two measures were added to `screen_score.py`:
- `blank_lead`, the rows with nothing before the title;
- `title_edges`, the distinct left edges the titles start at.

The first run of `blank_lead` counted circles drawn with `content:""` as blank. That was fixed, and B's six empty time slots still count, so the measure can fail.

| Option | Blank left | Title edges | Clutter | Status |
|---|---|---|---|---|
| A | 0 | 4 (ragged) | 0.036 | dominated |
| B, C | 6 | 2 | 0.035 | dominated |
| **D** | 0 | 2 | 0.036 | **front** |
| E | 0 | 2 | 0.040 | dominated (busier) |
| **F** | 0 | 2 | 0.035 | **front** |
| X (control) | 0 | 4 | 0.056 | loses |

## T1.2 Item rows: approved (2026-10-07)

**D, with A and B merged.**
- The left column shows a time, an event's span, or a quiet kind mark.
- Every action sits at the right edge: the Done circle, and Log, Open or Add.
- Events have no Done (decision 02).

**Routines are in chronological order, and it changes through the day** (owner). A routine with a set time shows and sorts by that time; an "n a day" habit shows its next block's start (Water, 14:00). Done rows fold away, so the next one rises to the top.

*Assumed, to confirm:* an untimed routine sits at the start of its time block. With no block, it goes to the end. The block start times are placeholders until T3.

The states and the variants chapter are redrawn on D.
