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

**Corrections after the owner's question, "why are ✓ and ▤ still the same size?" (2026-10-07).**
- **▤ was never searched:** the model held it at 48. The first run also stopped ✓ at 56, the top of its range, and picked it. A pick on the bound means the range was too narrow.
- **The glyphs never changed.** They stayed 20 px and 18 px whatever their targets. They now follow Material's proportions: ✓ at 43% of its disc (24 in a 56 FAB), and ▤ at 24.
- **The text-width constant was guessed.** The model's 0.52 em per character was measured from the render at 0.47–0.48. That is now 0.48, and it is why the model overstated A′'s sheet.
- **The control had not lost in the refined section.** Its sheet was measured as the line's strip (130 dp), but it covers the screen. The scorer now measures an opaque full-screen capture (`.cover`) to the keyboard, at 490 dp. The earlier "loses" came from reading the exit code through a pipe.

**Searched again with both sizes free** (✓ 48–72, ▤ 48–56; targets never below 48), the search goes to the top of both ranges in every frame. **Nothing in the model counts the cost of size.** Thumb travel and spacing both improve as a button grows. Measured clutter (edge density) cannot see it either: a filled disc adds edges only at its rim, so K at 56, 64 and 72 all fall within 0.002.

So the size is a trade between speed and visual weight, and it is the owner's to make. Along K, with the phone frame and the thumb resting on Enter:

| ✓ size | Thumb travel to ✓ | Change from 56 | Disc area |
|---|---|---|---|
| 48 | 2.80 | +0.17 bits | −27% |
| 56 | 2.63 | 0 | 2,463 dp² |
| 64 | 2.49 | −0.14 bits (about 15–30 ms a capture) | +31% |
| 72 | 2.36 | −0.27 bits (about 30–50 ms) | +65% |

Each step of 4 dp on ▤ saves 0.09 bits on a rarely used action, and changes nothing else. K64 and K72 are drawn beside K.

**Visual weight, measured (owner, 2026-10-07: a big black disc "creates a huge imbalance between the elements on the sheet"; and "consider changing the icons as well").**
- The reach-only search had no measure of visual weight. Neither does edge-density clutter.
- `tools/screens/sheet_weight.py` now measures it on the render, using craftkit's definitions (creative-design-suite `imgstat`): each element's mass is its departure from the sheet's ground tone, and the focal point is where edge energy concentrates.
- It covered 60 variants: ✓ placement (line or chip row) × fill (filled, tonal, outline, ↑ send arrow, the word "Add") × size (48, 56) × ▤'s look (▤, ⤢, the word "Details"). Results are in `docs/screens/t1/sheet-weight.json`.

| ✓ fill | ✓'s share of the sheet's mass | ✓ against the typed text |
|---|---|---|
| filled (A′ as approved, K) | 33–43% | 1.5–2.5× |
| word "Add" | 12–14% | 0.41–0.53× |
| outline, tonal | 8–11% | 0.27–0.41× |
| ↑ arrow | 7–10% | 0.24–0.38× |

**The imbalance was already in A′ as approved:** its 48 px black ✓ is 36% of the sheet's mass, 1.8× the text. Size matters much less than fill: going from 48 to 56 adds a few points; filling the disc multiplies the mass by four. ▤ is light in every form (2–5%); the word "Details" is the heaviest, and the only one whose meaning is plain.

**Critique** (`design-critique-plus`, `craftkit ui` on `docs/screens/t1/sheet-candidates.html`):
- *Measured:*
  - every label passes AA;
  - 9 type sizes, 5 corner radii, and 5 of 9 spacing values off the 4 px grid. These are Low, and are settled when type and density are scored.
- *Judgement:*
  - with the black disc, the eye lands on the button before the words it submits;
  - in tonal grey on the chip row, ✓ shares the chips' fill, so the action reads as one more chip. Placement or an outline has to separate it until colour gives it an accent;
  - on the line, any button with a word wraps the sample to two lines.

## T1.3 v2: one line for every module (owner, 2026-10-07)

**Owner's answers:**
- The line creates **tasks, events and reminders**, plus **tracker and habit logs, journal lines, timers and time logs, and check-in and ledger entries**.
- **The screen capture opens from sets the default kind.**
- The add method is left to the scoring: Enter, an on-screen ✓, or both.
- Routing is scored with every option together: an inferred kind chip, a kind row, typed prefixes, Todoist's + and TickTick's ⋯. The axes are **harmony, ease of use and clutter**.
- **Colour may not decide anything**, since there is no palette yet.
- **Targets are 48 dp**, but no control is drawn taller than the text box beside it.

**What each kind needs on the sheet.** The fields come from the data model (SPEC §3.2–3.7, the regulation ledger). The extra chips follow the research in `_screens-sources/nl-capture-research.md` (gitignored).

| Kind | Example line | Chips under the line (the kind chip first) | Data |
|---|---|---|---|
| Event | Dentist tomorrow 9am every 6 months | Event · Tue 6 Oct · 09:00 · Every 6 months | item EVENT, schedule, recurrence |
| Task | Call mum fri | Task · *Fri 9 Oct or every Friday?* | item TASK; an ambiguity asks |
| Reminder | Remind me to take meds at 21 | Reminder · Today 21:00 · Notification | item REMINDER + reminder row (alert kind) |
| Tracker log | water 2 | Log · Water · 2 glasses · Now | tracker_reading on the named tracker, its unit |
| Habit | walked 30 min | Log · Walk · 30 min · Now | the habit's tracker reading (the verb is "Log") |
| Journal line | slept badly, calmer after the walk | Journal · Today's page | appended to `journal:<personal day>` |
| Timer | start reading | Timer · Reading · Starts now | time_span opened on the activity |
| Time log | read 30 min | Time · Reading · 30 min, ended now | time_span closed, 30 min back from now |
| Check-in | energy 2 | Check-in · Energy 2 of 5 | check_in axis value with its scale |
| Ledger | masking high | Ledger · Masking: high | the day's masking row (three scales) |

**Elements this adds,** beyond the line and the date and time chips:
- a **kind chip**, always first;
- a **target chip** (which tracker, activity, calendar or page);
- a **value and unit chip**, showing the scale ("2 of 5");
- a **timer-state chip**, either "starts now" or "ended now";
- an **ambiguity chip**, which asks;
- an **unrecognised-phrase hint**.

**Research findings that shape the parser,** with evidence in the research file:
- match whole words only (Vikunja's partial-word bug);
- leave recognised words in the text (Todoist's "too greedy" complaint);
- separate "start" from "log": no time tracker found does it from one line.

**Reference captures:** Todoist, TickTick, Google Tasks and Any.do, taken on the owner's phone (gitignored).
- **Todoist's + opens a menu of fields** the line can't express: description, attachment, priority, labels, deadline and location.
- **TickTick's ⋯ holds** image, template, "convert to note" (a kind switch), full screen and settings.
- **Both draw their send button no taller than the chips or tools beside it.** Gboard shows the app's IME action on Enter: ✓ in Google Tasks and TickTick, send in Todoist.

**Scored (2026-10-07), `tools/screens/capture_v2.py`.** 70 variants plus a control:
- **routing:** inferred kind chip, kind row, kind chip with typed prefixes, Todoist's +, TickTick's ⋯;
- **add:** Enter only, ✓ on the line, ✓ at the end of the chips;
- **fill:** tonal, plain, outlined;
- **drawn height:** 32 or 36 px, inside 48 px targets.

Each is drawn with three inputs (an event, a tracker log, a journal line) and measured from the render.
- **Harmony:** drawn heights, controls taller than the text box (a constraint), designkit `emphasis_coherence` on the measured masses, aligned left edges, and craftkit `ui` sprawl. Colour codes are excluded.
- **Ease of use:** taps to fix the kind, taps to the full form, Fitts' ID to submit, and what stays hidden.
- **Clutter:** edge density, controls on the sheet, sheet height.
- **No hand-set weights:** each axis is a sum of ranks, and the front is taken over the three axes. **The control loses**: everything at once, with a 56 px filled button. It breaks the height rule, and on all three inputs its button outweighs the text.

**Three defects in my own mockups were found and fixed before these numbers:**
- a class-name clash drew a label dot before every chip and wrapped the chips;
- the trailing controls wrapped to the left edge, away from the thumb;
- a short kind chip was centred in its target, 1 px off the text's edge.

**Front, nearest the ideal first** (distance normalised over the front):

| Option | Harmony | Ease | Clutter | Fix kind | Submit ID | Hidden | Controls | Sheet |
|---|---|---|---|---|---|---|---|---|
| Kind chip, Enter adds | 163.5 | 128 | 80.5 | 2 taps | 2.29 | add | 5 | 170 |
| Kind chip, ✓ at the end of the chips | 163.5 | 112 | 102.5 | 2 taps | 2.44 | none | 6 | 170 |
| Kind chip + prefixes, Enter adds | 163.5 | 86 | 118.5 | typed | 2.29 | add | 5 | 193 |
| Kind chip + prefixes, ✓ at the end | 163.5 | 85 | 133.5 | typed | 2.54 | none | 6 | 193 |
| TickTick's ⋯, Enter adds | 163.5 | 180 | 30.5 | 2 taps | 2.29 | kind + add | 4 | 116 |
| Kind row (Craft), ✓ at the end | 198.5 | 84 | 165.5 | 1 tap | 2.44 | none | 10 | 222 |

(Ranks: lower is better.)

**Dominated:**
- every Todoist + variant;
- every ✓ on the line;
- the outlined ✓;
- the kind row without an on-screen ✓.

**Ties:**
- drawn height 32 against 36, and tonal against plain ✓, tie on every measure;
- once every control shares one drawn height no taller than the text box, harmony separates only the kind row, the one option that adds a second row of controls.

**Prefixes against the plain chip:** the prefix variant's extra height is only its hint line. Mockups: `docs/screens/t1/capture-v2.html`.

## T1.3 v3: prefixes with ⋯, and opening the full form (owner, 2026-10-07)

**Owner's answers:**
- ⋯ replaces Details; TickTick's icon row is also scored, in its place and beside it.
- The parse is shown as chips, underlined or highlighted, with the empty space measured.
- The full form opens from Todoist's + list, TickTick's ⋯ list, or Any.do's label and group lists.
- Every form option is scored over all ten kinds and over the owner's three most used: **task, event and tracker log**.

The reference captures add **Any.do's inline add** (on the phone, gitignored). Its # and group icons sit inside the text field, and each opens a list that grows the sheet upward. Nothing was saved.

**Capture sheet (`tools/screens/capture_v3.py`)**
- **The variants:** prefixes, with the hint shown only while the line is empty × {⋯, icon row, icons and ⋯} × {chips, underline, highlight} × {Enter, ✓}.
- **The measures:** capture_v2's axes, plus `empty` (the sheet's share of near-blank grid cells, from craftkit imgstat's detail report) and `unshown` (resolved values the sheet doesn't show).
- **The control loses.** Front:

| Option | H | U | C | Sheet | Empty share | Unshown | Controls |
|---|---|---|---|---|---|---|---|
| ⋯, highlight, ✓ at the end | 44.5 | 38 | 30.5 | 116 | 0.66 | 5 | 3 |
| ⋯, chips, Enter | 53.5 | 29 | 34.5 | 170 | 0.56 | 0 | 5 |
| icon row, highlight, Enter | 44.5 | 47 | 27 | 116 | 0.62 | 5 | 5 |

**The trade.** Highlighting saves 54 dp and one row of chips, but it hides five resolved values across the three inputs, such as "tomorrow" read as Tue 6 Oct, or a log's unit and tracker. Chips show them all.

**"Empty space" needs two numbers.** Chips have the lower empty *share* (0.56 against 0.66), but their taller sheet holds more empty *area* (about 95 dp of height against 77). That area comes from ⋯ wrapping onto a row of its own.

**Full form (`tools/screens/form_opt.py`)**
- **The variants:** {Todoist's + pop-over, TickTick's ⋯ pop-over, Any.do's inline list} × {linked chips, text becomes the title, underline, highlight}, against a full-page form.
- **What is drawn is hit-tested:** clipped rows count as unseen, and a covered line as covered. A first run trusted element boxes, and counted Any.do's clipped rows as seen and as covering the line.

| Option | H | U | C | Unseen rows | Line covered | Screen covered |
|---|---|---|---|---|---|---|
| Full page, text as the title | 15 | 19 | 32.5 | 0 | no | 100% |
| Todoist's + list (title, underline or highlight) | 21.5 | 33.5 | 16 | 1 | yes | 32% |
| TickTick's ⋯ list | 21.5 | 33.5 | 21.5 | 1 | yes | 32% |
| Any.do's inline list | 21.5 | 39.5 | 21.5 | 3 | no | 44% |

(All ten kinds; the top three rank the same: the page and Todoist's list, highlighted.)

- **The full page was built as the control, and did not lose:** it is best on harmony and ease, and worst only on clutter. So it is a real option, not a straw man, as Google Tasks' and Tasks.org's detail screens suggest.
- **Ten rows** (the fields, Kind and Templates) **are more than any pop-over shows** without clipping or covering the typed line.
- **On the line,** title, underline and highlight tie, and keeping the linked chips under a list does worse everywhere.
- **The same winners hold for all ten kinds and for the top three.**

Mockups: `docs/screens/t1/capture-v3.html` and `docs/screens/t1/form-options.html`.

## T1.3 v4: the short ⋯ list, the kind chip, shorthands (owner, 2026-10-07)

**⋯ opens a short list** (Kind, Templates, Full form), and the full form is its own page. Added to `form_opt.py` as a two-step shape: ease adds both choices, and it takes three taps to reach a field.

| Option | H | U | C | Taps to a field | Screen covered |
|---|---|---|---|---|---|
| Full page (direct) | 19 | 25 | 42.5 | 2 | 100% |
| ⋯ short list, then the page | 27.5 | 47.5 | 15.5 | 3 | 10% |
| Todoist's + list | 27.5 | 43.5 | 24 | 2 | 32% |

(All ten kinds. Over the top three, the page and the short list remain on the front, and Todoist's list with the text as the title.)

**The short list is the least cluttered of any option.** Its cost is a third tap and a second choice.

**Is the kind chip needed?** `tools/screens/capture_v4.py` shows the kind four ways:
- a chip;
- hint-sized text at the start of the row, still a 48 px target;
- a hint-sized line in the hint's place;
- not at all.

Each was crossed with chips or highlighting, and with Enter or a ✓. **The control loses.**

**Front:**
- chip + highlight + Enter;
- chip + chips + Enter;
- no kind + highlight + Enter, which is the least clutter but hides the kind and the resolved values.

**Hint-sized text is dominated by the chip.** Kept as a 48 px target, it takes the chip's room and leaves more empty space (0.73 against 0.68). As a line of its own it adds 23 dp.

**Shorthands** (`tools/screens/shorthands.py`, `docs/screens/t1/shorthands.md`).
- **Two of the hint's shorthands clash with words:** "ci" (Italian) and "log" (English). A line starting with either would switch kind by accident.
- **Proposed kinds:** `td` task · `ev` event · `rm` reminder · `lg` log · `j` journal · `t` timer (or a time log when a duration follows) · `ck` check-in · `ld` ledger.
- **Proposed field markers:** `#` label · `!` reminder · `@` calendar or tracker · `^` page · `~` duration · `*` repeat.
- **The clash check uses a built-in list** of English and Italian words of one to three letters, not a corpus.
- **Fit:** a 12 px hint line holds 5 of the 8 kinds, and all 14 need 3 lines.
