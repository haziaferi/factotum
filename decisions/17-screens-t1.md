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
| T1.3 | Capture sheet | **approved 2026-10-07: A′** |
| T1.4 | Hub sheet (cards) | **paused by the owner (2026-10-07), to be decided** |
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

**Confirmed by the owner (2026-10-07):** an untimed routine sits at the start of its time block. With no block, it goes to the end. The block start times are placeholders until T3.

The states and the variants chapter are redrawn on D.

## T1.3 Capture sheet: put to the owner (2026-10-07)

Three options and a control; `build_section` in `tier_t1.py` now builds every screen from here on.
- **A, a sheet over the screen.** It sits above the keyboard: the line, the chips under it, and Add at the thumb. On Windows it is a small window opened from anywhere (Ctrl+Shift+Space).
- **B grows in place.** The home's line expands, and the day stays visible.
- **C, in the keyboard's strip (oblique).** One strip of chips sits right on the keyboard.
- **X, the control:** a nine-field form.

**Front: A and C. B is busier, and X loses** (6 taps and 9 fields against 2 and 1).

The control first came out on the front. That traced to two real defects and one fault in the measure:
- **The chips were 36 px tall.** They are now drawn at 34 px inside a 48 px target.
- **The dimmed screen behind the Windows window** was counted as tappable.
- **The measure itself:** `faint` compared every label with the page and not with its own fill, so the dark Add button read 1.0:1. It now uses the nearest painted background. T1.1 and T1.2 are unchanged, and the old faded bar is still flagged at 2.1:1.

States, drawn on A: empty (what it accepts), understood, two readings (it asks and never guesses: "Fri 9 Oct or every Friday?"), nothing to parse (added as typed, no date), and added (with Undo).

**Page conventions (owner, 2026-10-07):**
- Once a screen is approved, the options not picked fold into a closed "Options not picked" section under the chosen one.
- No emojis anywhere. The capture chips are text only. The placeholder glyphs are plain text symbols until icons are scored (Q8).

## T1.3 Capture sheet: approved (2026-10-07)

**A′: A, refined by the owner.**
- The sheet sits over Today, and Today **stays visible under a slight shade**, as on Windows.
- **Add is a 48 px check** (✓).
- **A small Full form button** (▤) sits before the check, for when one line is not enough.

A′ measures busier than A (clutter 0.034 against 0.022). That is the visible day itself, which is the trade the owner chose: context over calm. The states are redrawn on A′.

## T1.4 Hub sheet (cards): put to the owner (2026-10-07)

The Hub opens a sheet with the capture line, Pinned and recent, and every screen of every module on cards (27 in all). A long press on the Hub goes straight to capture. Three options and a control:
- **A:** one column.
- **B:** two columns.
- **C (oblique, a store map):** cards sit where the bar says they live. Calendar and Routines are on the left, Pages and check-in on the right, and Review and App across the foot.
- **X (control):** one long list.

**"Every screen visible" is the owner's requirement, so it is applied as a constraint, not a score.** On clutter alone the control's long list wins (0.035), but only because it shows 12 of the 27 screens. With the constraint, **only C passes (0 below the fold)**. A hides 5 and B hides 2; tightening them could make them pass.

Fixes found on the way:
- **The feature labels were pills inside cards:** 55 targets under 48 dp, and clutter 0.065. They are now plain 48 px text targets on the card, at clutter 0.047–0.054.
- **The Windows Hub panel escaped its frame,** because `.desk` was not positioned. Fixed in `kit.py`.

`build_section` gained `must`, for the owner's requirements.

## T1.3 refined: where ✓ and ▤ go, and how big: put to the owner (2026-10-07)

The owner left the placement and the sizes of ✓ and ▤ free, asked for a balanced result (a front), and chose right-thumb-first with a left-hand mirror setting.
- `tools/screens/capture_opt.py` enumerated 1,296 layouts. The variables were placement (line, chip row, action row, split), text 15–18 px, line height, chip height, ✓ size 48–56 and gap.
- The search ran in two frames: the assumed 360 dp phone, and the owner's phone as measured (384 × 832 dp, Gboard's Enter at 355, 751). Each frame ran with the thumb resting on Enter and on the keyboard's centre. **The knee was the same in all four runs:** ✓ and ▤ at the end of the chip row, 18 px text, ✓ 56.
- Chip height changes no objective, because the target is 48 dp either way.

**Reference apps, measured on the owner's phone** (placeholder accounts; the sample was typed and cleared, and nothing was saved). Thumb travel is Fitts' ID from Enter to Add, using the smaller of the target's width and height.

| App | Add sits | Add dp | Thumb travel | Sheet dp | Parses |
|---|---|---|---|---|---|
| Todoist | end of the chip row | 44×48 | 2.98 | 153 | yes |
| Microsoft To Do | end of the line | 42×44 | 3.15 | 104 | yes |
| Google Tasks | action row (text "Save") | 88×48 | 2.81 | 113 | no |
| TickTick | action row | 40×30 | 3.36 | 130 | yes |
| Any.do | top right, full screen | 41×41 | 4.16 | full | yes |
| Keep | back arrow, top left | 56×56 | 3.87 | full | no |
| Tasks.org | top left, full form | 48×48 | 4.08 | full | no |

**The options, re-measured from the render** (`docs/screens/t1/scores.md`):

| Option | Thumb travel to ✓ | to ▤ | Sheet dp | Lines | Text | Status |
|---|---|---|---|---|---|---|
| A′ as approved (on the line) | 2.91 | 2.93 | 130 | 2 | 16 px | front |
| **K: both at the end of the chip row, ✓ 56** | **2.49** | 2.69 | 178 | **1** | **18 px** | front |
| S: ▤ on the line, ✓ on the chip row | 2.49 | 3.09 | 178 | 1 | 16 px | dominated by K |
| R: action row above the keyboard | 2.57 | 3.19 | 182 | 1 | 18 px | dominated by K |
| X: control, Any.do's top line | 4.15 | none | 130 | 1 | 16 px | loses |

**The trade between A′ and K.** K is the easiest ✓ to reach of any layout or app measured: 14% less thumb travel than A′. Its sample reads on one line at 18 px. But the sheet is 48 dp taller, because the buttons take the chip row's end and four chips then wrap to two rows. With one to three chips, the usual case, the row does not wrap.

The model was checked against the render, and it overstated A′'s sheet (181 against 130). Its glyph width (0.52 em) is wider than the rendered font, so A′'s chips fit on one row. It got thumb travel right (K 2.49 in both).

States drawn on K: empty, two readings, and the left-hand setting (mirrored), with S mirrored for comparison.
