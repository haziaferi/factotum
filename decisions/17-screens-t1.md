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
| T1.3 | Capture sheet | **approved 2026-10-07: v4** (no chips, highlight, kind and markers in the hint's place, ⋯ beside the line, context-aware placeholder); it superseded A′ the same day |
| T1.4 | Hub sheet (cards) | **approved 2026-10-08: A0** (one column, Pinned and recent kept; the App card moved behind ⚙) |
| T1.5 | Date and time picker | **approved 2026-10-08: merged with T1.6 into the When sheet** |
| T1.6 | Repeat builder | **approved 2026-10-08: the When sheet** (one sentence, Once or Every) |
| T1.7 | Label chips and picker | **approved 2026-10-09:** dots, a filter bar, the picker sheet, # chips above the line, the legend list |
| T1.8 | Toasts and dialogs | questions answered 2026-10-09; references and scoring next |
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

## T1.3 Capture sheet: approved v4 (owner, 2026-10-07)

**The owner's design:**
- **No chips.** The understood words are **highlighted** in the line.
- **The kind replaces the hint.** While the line is empty, the hint lists the shorthands; once text is typed, the same small line shows the kind ("Event", "Log", "Journal").
- **⋯ sits beside the text box.**
- **When the text wraps to two rows, it stays a rectangle.** It never flows under ⋯.
- **Enter adds** (kept from the front; the owner did not name the add).

**Scored with the v4 variants** (`docs/screens/t1/capture-v4-owner.json`). It is on the front, with **the least clutter of any variant (C 21)** and **the shortest sheet: 96 dp with the hint, 91 to 96 typed**. It has one control on the sheet, every drawn height is the same, and there is one left edge.

**What it gives up, measured:**
- the resolved values are not shown before adding (5 across the three inputs);
- changing the kind without typing takes ⋯ › Kind, three taps;
- a typed prefix still takes none.

**Fixed with it:** the empty-line hint used "ci" and "log", which clash with words (`shorthands.md`). It now reads "j journal · lg log · t timer · ck check-in · td task".

**Mockup:** `docs/screens/t1/capture-approved.html`.

**Decided by the owner, 2026-10-07:**
- **The full form opens as the page, directly.**
- **The shorthand set is accepted,** on the condition that it is safe in text containing those letters inside a word (see the rules below).
- **The legend uses both places:** the hint scrolls sideways while the line is empty; once a kind is typed, the small line shows the kind and its field markers.

**⋯ is level with the first line** when the text wraps (owner, 2026-10-07). It is measured: ⋯'s centre equals the first line's centre in the empty, typed and wrapped states. The text line is 22 px, with 13 px above it, so one line keeps the 48 px row and each extra line adds 22.

**Found with it:** the empty line's placeholder, "Add a task, event, log or journal line…", wraps to two lines beside ⋯. That makes the empty sheet 100 dp against 91 typed. Shorter wording would keep it to one line, and that is the owner's choice.

## T1.3 Shorthand legend: five places, scored (owner, 2026-10-07)

`tools/screens/legend_opt.py` scores each place against the approved sheet. The places:
- the hint scrolling sideways;
- a context-aware hint: kinds while the line is empty, then that kind's field markers once its shorthand is typed;
- ⋯ › Shorthands;
- a "?" at the hint's end;
- Settings › Help.

The control shows all 14 at all times, in three lines.

The measures:
- **readable:** how many shorthands can actually be read at rest and once a kind is typed, hit-tested;
- **reach:** taps or swipes to see all 14;
- **leaving:** whether consulting the legend closes capture;
- **size and clutter:** sheet height, clutter, controls, and how much of the screen an open table covers;
- **harmony:** as before.

| Place | Readable at rest | Readable after `ev` | To see all 14 | Sheet | Covered when open | Status |
|---|---|---|---|---|---|---|
| Scrolling hint | 6 | 0 | 2 swipes | 96 | none | **front** |
| Context-aware hint | 5 | 5 (the event's markers) | never all at once | 96 | none | **front** |
| ⋯ › Shorthands | 5 | 0 | 2 taps | 96 | 36% | dominated by scrolling |
| "?" at the hint's end | 4 | 0 | 1 tap | 120 | 36% | dominated (its 48 px target adds 24 dp) |
| Settings › Help | 5 | 0 | 3 taps, and capture closes | 96 | none | dominated by context |
| All 14 always on (control) | 13 | 13 | none needed | 130 | none | breaks the approved rule (the kind replaces the hint), so it is a constraint failure |

**The two can be combined.** The scrolling hint covers the empty line, and the context hint covers the typed one. Combined, all 14 can be found while typing, at no extra height. This combination is not scored separately.

Mockups: `docs/screens/t1/legend-options.html`.

**The legend, both places together** (`legend_opt.py`, variant `both`), is better than either place alone, on every measure:
- 6 shorthands readable at rest, and 5 once a kind is typed;
- all 14 within 2 swipes;
- the sheet stays 96 dp.

Mockup: `docs/screens/t1/capture-approved.html`.

## Shorthand rules: safe inside words (owner's condition, 2026-10-07)

`tools/screens/shorthand_rules.py` is a reference matcher. Its 48 cases are in `docs/screens/t1/shorthand-cases.jsonl`, which is the acceptance test for the app's parser.

1. **A kind shorthand counts only as the line's whole first token,** followed by a space and more text. "tdah", "event", "ldap", "evening", "rmdir", "t-shirt", "j.k." and a lone "td" all stay text.
2. **A field marker counts only at a token's start, and only when its value parses:**
   - `#`, `@` and `^` need a letter after them;
   - `~` needs a duration;
   - `!` needs a time or an offset;
   - `*` needs a repeat word.

   So "C#", "#1", "a@b.com", "user@home", "2^8", "Wow!", "wow!10m", "2*3", "*important*" and "~approx" all stay text.
3. **Whatever counted is highlighted.** Tapping a highlight offers "Keep as text".

**The cases were checked against deliberately broken rules,** so a pass means something:
- matching a kind by the prefix of a word fails 9 cases;
- accepting any value after a marker fails 5;
- matching a marker anywhere in a word failed only 1 case at first. Six in-word cases were added, and it now fails 7.

**The text box (owner, 2026-10-07):** it always spans its full width and stays one line high by default. It grows only when typed text wraps. So the placeholder must fit on one line beside ⋯.

**Placeholder options, scored** (`tools/screens/placeholder_opt.py`; fit is measured from the render):
- **Ease:** the kinds it names, whether it starts with a verb, and whether it matches the screen it opens from.
- **Cost:** characters and words.

| Placeholder | Fits | Kinds named | Verb first | Context | Chars | Status |
|---|---|---|---|---|---|---|
| Context-aware: Today "Add anything…", Journal "Write a line…", a tracker "Log water…", Calendar "Add an event…" | yes | 1 (the one it will make) | yes | yes | ≤13 | **front** |
| "Add anything…" | yes | 0 | yes | no | 13 | **front** |
| "What's next?" | yes | 0 | no | no | 12 | **front** (shortest; says least) |
| "Type anything…" | yes | 0 | yes | no | 14 | dominated by "Add anything…" |
| "Add a task or event…" | yes | 2 | yes | no | 20 | dominated by context-aware |
| "Add a task, event, log…" | yes | 3 | yes | no | 23 | dominated by context-aware |
| "Task, event, log, journal…" | yes | 4 | no | no | 26 | dominated |
| "Add a task, event, log or journal line…" (the current one) | **no, wraps** | 4 | yes | no | 39 | fails the one-line rule |

Every option that fits keeps the empty sheet at 91 dp. Naming kinds in the placeholder repeats what the hint line below already lists.

**Placeholder: context-aware** (owner, 2026-10-07):
- Today: "Add anything…"
- Journal: "Write a line…"
- a tracker: "Log water…"
- Calendar: "Add an event…"

**v4 is now T1.3's selected option in `docs/screens/t1/screens.html`.** It has phone and Windows versions, and six states: empty from Today, a kind typed, wrapped, and empty from Journal, the water tracker and Calendar. A′ and the earlier options are folded under "Options not picked". On Windows, the keyboard line (Enter, Esc, Ctrl+Shift+Space) sits inside the quick-add window; a first draft put it outside, over the rail.

**Windows quick-add (owner, 2026-10-07):** "two rows of instructive text" are fine on desktop. The empty line's 14 shorthands wrap onto two rows instead of scrolling sideways, and the keyboard line (Enter, Esc, Ctrl+Shift+Space) sits under them, inside the window.

This was checked in the full page with the browser: both lines sit inside the window, at 60 px and 101 px from its top. The owner's screenshot showed the keyboard line outside the window, over the rail; that was an earlier copy of the page, generated before the fix. The first check had rendered the window alone, which could not have caught the problem where the owner saw it. Checks now look at the page.

**Page order (owner, 2026-10-07: "my choice disappeared").** The T1 page opened on the superseded size exploration ("T1.3 refined"), which showed the old ✓ options; the selected v4 sat far below it, after T1.4. T1.3 with the selected option now comes first. The exploration is folded, closed, under it. T1.4, T1.2 and T1.1 follow.

## T1.4 Hub sheet: unpaused and re-scored with T1.3's carry-overs (owner, 2026-10-07)

**Carry-overs applied to every option:**
1. the T1.3 v4 capture line on top, with the shorthand hint and Today's placeholder, "Add anything…";
2. one drawn height, with features as plain text on 48 px targets;
3. text, not pills;
4. the feature names must outweigh the card headers, by measured mass;
5. empty space measured;
6. every card on Windows.

**The measuring fix found in T1.3 applies here too.** A feature counts as seen only if it is drawn at its centre. The old measure counted it by position, so a feature cut off by the sheet's edge could count as visible.

**The scorer is `tools/screens/hub_opt.py`** (results in `docs/screens/t1/hub-opt.json`), on three axes:
- **Harmony:** designkit `emphasis_coherence` over the measured masses (features first, then the line, then the headers), the headers' share of the mass, and craftkit sprawl.
- **Ease of use:** thumb reach (Fitts' ID from the Hub's slot) and whether Pinned and recent is there.
- **Clutter:** edge density and empty share.

"Every screen visible" is a constraint. B− and C− were added: the same layouts without Pinned and recent.

| Option | Hidden (of 27) | Reach | Headers' share | Clutter | Empty | Status |
|---|---|---|---|---|---|---|
| C, store map, with Pinned and recent | 0 | 2.82 | 0.089 | 0.056 | 0.16 | **front** (best harmony and ease) |
| B−, two columns, no Pinned and recent | 0 | 2.90 | 0.101 | 0.051 | 0.14 | **front** (least clutter) |
| C−, store map, no Pinned and recent | 0 | 3.02 | 0.095 | 0.051 | 0.24 | front on the three axes; the page's own columns put it behind B− |
| A, one column | 6 (the App card) | 2.86 | 0.095 | 0.050 | 0.11 | fails the constraint |
| B, two columns | 6 | 3.00 | 0.089 | 0.054 | 0.11 | fails the constraint |
| X, the control (a long list) | 16 | 2.93 | | 0.035 | 0.06 | fails; loses |

- **The feature names outweigh the headers** in every option, so none needs lighter headers.
- **The Windows panel hides nothing.**

**Two defects were fixed on the way:**
- The page's T1.4 section was rendered without T1.3's styles, which lays the sheet out differently: B showed 2 hidden on the page against 6 in the scorer.
- The page ranked by clutter alone. It now carries the same reach and Pinned measures, and its front matches the scorer's on C and B−.

**The ideas raised before unpausing are not applied:** navigating from the Hub's line, shorthands on the cards, and a short list for rare screens. Each would need the owner's decision and its own scoring.

**Would shorter cards in A remove the scroll?** (owner, 2026-10-07)

**Not on their own.** A overflows the sheet by 135 px. Its height is spent on:
- the capture line, hint, and Pinned and recent: 163 px;
- eight 48 px rows of screens: 384 px, fixed by the target rule;
- six card headers: 114 px;
- card padding and the gaps between cards: 96 px.

**What was tried** (`hub_opt.py`):
- **Tighter padding and gaps** still hide 6 screens.
- **Headers inline as a first word, or in a label column,** hide 3. Sharing the row pushes two cards onto an extra row of screens.
- **Without Pinned and recent:**
  - plain A hides 2;
  - A with tighter cards (**A-tight−**) hides **none**.

**A-tight− joins the front,** with the least clutter of any option. Its harmony is the worst of the four, because its headers carry the largest share of the mass (0.121).

**The front is now C, B−, C− and A-tight−.** A-tight− is drawn in T1.4 on the page.

**What if the App card left the Hub and lived behind ⚙?** (owner, 2026-10-08)

Its six screens (Labels, Time blocks, Calendars, Settings, Trash and About) would sit behind the header's ⚙ (T1.1). Scored with `hub_opt.py`'s measures (`docs/screens/t1/hub-noapp.json`), keeping Pinned and recent, and ranked with the earlier options (`hub-noapp-ranked.json`):
- **One column (A0) fits with Pinned and recent,** and hides nothing. It is the **balanced pick**: the lowest rank sum, with harmony 12.5, ease 5.5 and clutter 5.5.
- **Tight one column (A0-tight) and the store map (C0)** also fit, and are on the front.
- **Two columns (B0)** still hide 2 screens (History, Time totals).
- **B− and C− fall off the front.**
- **The front is A0, C, A0-tight, A-tight− and C0.**

**Navigation cost** (`nav_score2.py` weights, assumed 0.25 a week each, about 1.5 visits a week in total):
- Settings becomes 1 tap (⚙) instead of 2 (Hub, then Settings);
- the other five stay at 2 taps (⚙, then the item);
- ⚙ sits in the top-right corner, the hardest reach for a thumb, so those visits trade ease of reach for a shorter Hub.

**Not decided:** whether the App card leaves the Hub. That is the owner's choice.

**A0, A0-tight and C0 are drawn in T1.4 on the page** (owner, 2026-10-08: "where is it in the mockup?"); they had only been scored. Each option is now checked against the screens it is meant to show: 21 without the App card, whose six are behind ⚙. Before, the six moved behind ⚙ would have counted as hidden. On Windows, the no-App options' panel also drops the App card.

## T1.4 Hub sheet: approved (owner, 2026-10-08)

**A0: one column of cards, with Pinned and recent kept. The App card leaves the Hub.**
- **The Hub shows:** the T1.3 v4 capture line, Pinned and recent, then Calendar, Routines, Check-in, Pages and Review. All 21 screens are visible above the bar, and on Windows too.
- **⚙ in the header** (T1.1, top right) now holds the App card's screens: Settings, Labels, Time blocks, Calendars, Trash and About. Settings is 1 tap; the others are 2. They are each used about once a month (`nav_score2.py`, assumed).
- **Drawn in T1.4:** the Hub open from the bar, and ⚙'s screens.

**"Check-in" is written with a capital letter** (owner, 2026-10-08) wherever it is drawn on the T1 page:
- the bar and the Windows rail;
- the Hub card and its screen;
- the shorthand hint, now "ck Check-in";
- the legend and the shorthand table.

The internal names, and the T0 pages already settled, keep the lowercase form; they are not on screen.

## T1.5 Date and time picker: first scoring (2026-10-08)

**Owner's answers:**
- **Time entry:** score the planner's time blocks as presets, a typed field with suggestions, scroll wheels, a clock dial, and cron with its calculator.
- **Cron:** in both pickers (T1.5 and T1.6).
- **Week start and clock:** follow the system.
- **Event end:** score both duration presets and an end time.
- **Day load:** score with and without.
- **Containers:** replaces the keyboard, a sheet, a pop-over by the date, a full page.
- **Windows:** score the options.

**References** captured on the owner's phone (gitignored; nothing saved):
- Todoist: a near-full sheet with typed date, presets showing weekdays, a month grid with a load line, Add time (a clock dial in a dialog, keyboard toggle) and Repeat;
- TickTick: Date and Duration tabs, icon presets including "this morning", a dial, start and end with a duration readout, and an all-day switch;
- Google Tasks: a dialog, with no presets;
- Microsoft To Do: a pop-over of presets, then a calendar.

**Phone (`tools/screens/picker_opt.py`):** 80 variants plus a control (everything at once). The control loses.
- Ease is counted, not timed: taps, keystrokes and drags over five tasks, each kept as its own measure, because a wheel drag and a keystroke are not the same effort. Reach and cut-off controls are also measured.
- **The repeat task without cron is counted as 2 taps through T1.6's builder.** That is an assumption until T1.6 is drawn.
- **Defects of mine fixed before any numbers:** the time field was under 48 px; day cells were 3 px narrow; preset chips were drawn as squares with their words overflowing; the end-time option had no All-day control, so "all day" cost it nothing.

**Result:**
- **The front is wide** (14), across every container and time entry. Without a rule against cutting off controls, nothing clearly wins.
- **With "nothing the tasks need cut off" as a rule, only one passes:** the full page, with a typed time, duration presets and day load.
- **Every other picker is too tall.** Presets, a 48 px month grid, the time and the end do not fit together.
- **Day load is on 10 of the 14 front members,** and an end time on 9 of 14.

**Windows (`tools/screens/picker_desk.py`):** both one-column shapes (a drop-down, and a side panel) cut off the time and end in a 660 px window. **A two-column drop-down** (the month left; presets, time and end right) shows everything, with the easiest pointing (mean index of difficulty 2.37). It covers 41% of the window.

**Open:**
- whether cut-off controls (scrolling inside the picker) are acceptable;
- a two-step picker, the date first and then the time, as Todoist and TickTick do, which was not yet scored.

Mockups: `docs/screens/t1/picker-options.html`.

**T1.5 re-scored (2026-10-08) under the owner's rule that everything a task needs is visible.**

**Two measuring bugs, both mine, were found and fixed:**
- **Viewport.** Headless Edge's `--dump-dom` lays the page out at 492 × 648 whatever `--window-size` says. So since T1.4, every hit-test ("seen") counted anything below 648 px as hidden, even when it was drawn. It is fixed in `screen_score.measure`: the page is measured in a window that holds the whole frame, and the hit-test uses the frame's 360 × 740.
  - **Re-checked:** the Hub (A still hides its six App screens; B hides 2, not 6; **A0 is unchanged and stays approved**), the full-form menus and the legend (fronts unchanged).
- **Wheels.** A wheel is dragged, not tapped, so it was left out of the visibility check. A picker with its wheels cut off had passed.

Also: the empty space was trimmed (labels moved inside their rows, less padding), and two-step pickers were added.

## T1.5: the calendar on request (owner, 2026-10-08)

**Owner:**
- "An entire calendar picker should be opened by the user rather than appear unprompted. The natural language input has as few clicks to make as possible on purpose."
- "If the user already wrote 'tomorrow' there is no reason to add another date/time picker."

**Owner's answers:**
- **Tapping a highlighted date opens no picker.** To change it, the words are edited. (Revised below: it offers "Keep as text".)
- **The calendar opens from ⋯ › Date beside the line, and from the full page's Date row.**
- **It opens straight on the calendar, with no presets.** This supersedes decision 17's earlier "presets first".
- **Settled (owner, 2026-10-08):** "Tapping dates and times should still offer 'Keep as text', since in some inputs, like Journal, they might not have the same meaning as for a Calendar event." So rule 3 of the shorthand rules holds for every highlight, dates and times included: a tap offers "Keep as text" and nothing else.

**The picker's job is now choosing a day by looking at the month (day load on), then a time if wanted.** `tools/screens/picker3_opt.py` scores 60 variants:
- one view or two steps;
- a sheet, a page, or the keyboard's place;
- five time entries;
- duration presets or an end time.

**The tasks:** "Fri 16"; "Fri 16 at 14:30"; "an event Fri 16 at 15:00 for 1 h"; "the 3rd of next month". 35 of the 60 keep every needed control on screen; none in the keyboard's place does.

**One option leads on all three axes:** **two steps, in a sheet, with wheels and duration presets.**
- **Step 1** is the month and Done.
- **Step 2,** after a day is tapped, is the time and the end.
- **Each step covers about half the screen.**

**Every top option is a two-step sheet.** The time entries are close: time blocks are 8% behind, typed 9% and the dial 13%.

**Caveat:** a wheel drag counts as one action however far it spins, which slightly favours wheels.

**Windows:** the two-column drop-down, the month beside the time, now without presets.

**The calendar-first runs are kept as a record:** `picker-opt.json` (one view or two steps, presets included) and `picker2-opt.json` (a menu from the tapped word; stopped and superseded).

Mockups: `docs/screens/t1/picker-options.html`.

**Wheel cost corrected (owner, 2026-10-08):** "typing numbers or tapping on a clock shape is way faster than scrolling a wheel one hour and one minute at a time."
- **One wheel step is now one action.** From 09:00, 14:30 takes 11 steps and 15:00 takes 6. Before, each wheel counted one drag however far it spun.
- **The rank-sum also hid sizes.** A wheel last on drags by 17 to 1 cost the same as last by 1. Ease therefore uses one count of **actions** (taps + keystrokes + wheel steps), as the owner counts them (`docs/screens/t1/picker3-actions.json`).

Two-step sheet with duration presets:

| Time entry | Actions (4 tasks) | Reach | Clutter | Screen covered |
|---|---|---|---|---|
| **Clock dial** | **13** | 2.23 | **0.032** | 55% |
| Time blocks | 16 | 2.03 | 0.038 | 50% |
| Typed | 18 | **1.89** | 0.036 | **50%** |
| Wheels | 27 | 2.12 | 0.035 | 50% |

- **The dial is now the only front member.**
- **Typed has the best reach.** It brings up the keyboard, and its time view was checked to fit above it: the field, suggestions, end presets and Done all stay visible.
- **The owner narrowed the choice to typed or the dial.**

**The owner's proposal (2026-10-08): the dial and the typed field with its suggestions in one sheet, the keyboard only when the field is tapped** (entry `dialtyped`; the person takes the quicker of the two).

**Measured** (two steps, sheet, duration presets):
- **It ties the dial alone:** 13 actions, reach 2.23, 55% covered. Clutter is 0.0331 against 0.0317, under the 0.002 noise floor.
- **In both states** (normal, and with the field tapped and the keyboard up), the field, suggestions, end presets and Done stay visible, and so does the dial.

**The task set has no exact-minute time,** which is the one case where typing beats the dial (14:37). So the combination costs nothing measurable, and keeps typing for exact minutes and for anyone who prefers it.

Mockups: `docs/screens/t1/picker-options.html` (the steps, the keyboard state, and each entry alone for comparison).

**Approved (owner, 2026-10-08): the dial and the typed field in one sheet.** Two steps in a sheet: ⋯ › Date (or the full page's Date row) opens the month with its day load and Done; a day tapped opens the time view, with the typed field and its 09:00 and 21:00 suggestions, the dial under it, the duration presets and Done. The keyboard rises only when the field is tapped. On Windows, the two-column drop-down: the month beside the time. Tapping a highlighted date or time offers "Keep as text" and opens no picker. T1.5 is now a section of `docs/screens/t1/screens.html` (`tier_t1.py`, `OPTIONS_T15`).

**Measured again on the page** (`tier_t1.build_section`, the page's own clutter render):
- **The dial alone sits just beyond the noise floor:** clutter 0.030 against 0.033 for the combination (tolerance 0.002). The page marks the combination as dominated. Actions (13), reach (2.23) and coverage (55%) are equal. The combination is the owner's choice, held for typing.
- **A correction:** the earlier claim that "an exact minute (14:37) is where typing beats the dial" was not measured. The dial's minute ring can be tapped at any minute, but its one-minute targets are far under 48 dp. Typing costs the field plus four keys. Which is faster depends on how that ring is drawn, so the claim stands as a reason to keep typing, not as a measured win.
- **The control** (one view in the keyboard's place, with wheels and an end time) loses: three needed controls are not drawn, and it takes 32 actions.

## T1.6 Repeat builder: questions (owner, 2026-10-08)

**Owner's answers:**
- **Rules the builder reaches directly** (the rest through cron or typing): all four groups:
  - everyday intervals (every n days, weeks, months or years; chosen weekdays);
  - ordinals and month ends (second Tuesday, last Friday, the last day, the 31st clamped);
  - within a day (every 90 min, every 15 min from 9 to 17, 08:30 and 20:30);
  - random and after-done (random every 2–4 days, a random time in a window, n days after last done).
- **Cron:** score a raw field with its plain-language readout and next dates (the calculator), a five-field builder, and cron behind an Advanced row.
- **Presets:** score both presets first (then Custom) and the builder straight away (presets as its first row).
- **Next occurrences:** score with and without.
- **Axes:** harmony, ease, clutter, rule coverage (cases reached without cron or typing), the rule's legibility (read back in words before Done), and closeness to the references (measured geometry).
- **References:** include clock and timer apps ("some of these features are more akin to a clock or a timer"), and do not exclude open-source apps. Capture Todoist, TickTick, Google Tasks, Any.do, Google Calendar, Fossify Calendar, SimpleReminder, and the source apps' own screens.
- **Opens from:** ⋯ › Repeat beside the line and the full page's Repeat row. How T1.5 links to it is settled after this design.
- **Containers:** all four again (sheet, page, the keyboard's place, a pop-over).

**On the phone already:** Todoist, TickTick, Google Tasks, Any.do, Google Calendar, Fossify Calendar, Tasks.org and Loop Habit Tracker (both open source), the OnePlus clock, Notion Calendar, Chronicle and Mnemo. Tendril is not installed (only its test package), so its repeat screen is read from its code.

**References captured (2026-10-08)**, on the owner's phone, geometry and labels only. Screenshots are in the gitignored `_screens-sources/repeat/`; the features are in `docs/screens/t1/repeat-references.json`.
- **16 apps walked:** Todoist, TickTick, Google Tasks, Any.do, Fossify Calendar, Notion Calendar, Tasks.org, Loop, the OnePlus clock, Fossify Clock, SimpleReminder, Stochastic Reminder, MedTimer, reReminder, Chronicle, Mnemo, and Tendril (built from source and installed).
- **Installed via Droid-ify, with the owner's approval:** Fossify Clock, SimpleReminder, Stochastic Reminder, MedTimer, reReminder, Etar and Cyclic Alarms.
- **Skipped:**
  - Google Calendar, which is disabled on the phone;
  - Etar, whose calendar permission was declined;
  - Cyclic Alarms, which needs an overlay grant.
- **No reference reaches every rule group.** Random kinds appear only in Chronicle, Mnemo and Stochastic Reminder; windows only in MedTimer and reReminder; and cron is only typed (Mnemo).
- **Things created to reach an editor:** in Any.do and MedTimer, a "Sample" was saved to reach its editor, then deleted.

**Scored (`tools/screens/repeat_opt.py`):**
- **The space:** 234 variants plus a control:
  - form: freq, modes, sentence or typed;
  - start: presets first or the builder;
  - cron: an always-shown field, five fields, or behind Advanced;
  - preview: none, words or a month;
  - container: all four.
- **The tasks:** ten, from a preset to cron's OR rule.
- **The measures:**
  - actions are walked in order, and closing the keyboard counts when it hides a control;
  - visibility is hit-tested with and without the keyboard;
  - six axes: harmony, ease, clutter, rules reached without free text, the rule read back, and the distance from the 17 references.

**Results:**
- **125 of 234 pass the visibility and 48 dp rules.** Every keyboard-place variant fails, and all but 7 pop-overs fail.
- **The six-axis front holds 68,** and the control loses.
- **Settled by paired comparison** (variants differing in one choice only):
  - **The small month loses to the words line on every measure:** 2.5 more actions, more clutter, more covered, heavier, and no gain in legibility.
  - **Cron behind Advanced beats an always-shown cron field** (clutter +0.012 for the field), **and the five-field builder** (worse on everything).
  - **Typed words are off the front:** about 171 actions against 71–85, because each rule is typed out.
- **Left as trade-offs:**
  - **Form:**
    - modes takes the fewest actions (9.5 fewer than freq);
    - sentence is the calmest (11 controls against 25–29, covering 38% as a sheet);
    - freq is the closest to the references.
  - **Rule in words versus none:** words cost about 0.004 clutter and distance from the references, which mostly have no readout.
  - **Presets first versus builder:** presets cost 6.7 more actions, and their opening view is smaller and calmer.
  - **Sheet versus page:** a sheet has better reach (2.7 against 3.4); a page is calmer and covers everything.

Mockups: `docs/screens/t1/repeat-options.html` (`tools/screens/repeat_page.py`).

**Cron's reach (owner's question, 2026-10-08: "How many of the repeat options could cron cover?").** Read from `core/.../recurrence/Cron.kt`, which is Mnemo's five numeric fields with lists, ranges and steps, and no `L W #`.
- **3 of the 10 tasks today:**
  - every weekday (`0 9 * * 1-5`);
  - 08:30 and 20:30 (`30 8,20 * * *`);
  - the 1st or any Monday, the OR rule, which only cron reaches.
- **5 with Quartz's `L` and `#`:** the last day, and the 2nd Tuesday. A count ("6 times") is still out.
- **6 with several lines:** every 90 minutes, as `0 9,12,15 * * *` plus `30 10,13,16 * * *`.
- **Out of reach in any dialect:**
  - every n weeks, or n days across months (cron has no year and no week parity);
  - counts and end dates;
  - random schedules (a draw would have to be stored, which decision 04 rules out);
  - "after done".
- **Typed words translated into cron lines would not change this.** The limit is cron's grammar, not how the rule is entered. Typed words can still reach every kind, because the stored rule is RRULE plus the two random kinds, and cron is shown beside it whenever it can express the rule.

**Owner's answers:**
- **Cron accepts more than Mnemo's form:** `L` and `#` (Quartz), several lines as one rule (the data layer's RULE_SET), and names (MON, JAN). This is owed to the data layer, in `Cron.kt` with its cases, separately from the screen.
- **Score a merge:**
  - the sentence with the schedule types as its first chooser (`sentmodes`);
  - each form with one field that takes words or cron, with the calculator's cron line under it. Per task, the quicker path is counted: the builder or the field.
- **Narrowed by the first run:** sheet or page only; preview words or none; cron behind Advanced when there is no field.

**Merge round (`repeat_opt.py --merge`, `repeat-merge-rank.json`):** 72 variants plus the control; all pass, the front holds 61, and the control loses.
- **The words-or-cron field added to a builder barely helps:** 0.16 fewer actions, for +0.005 clutter and +1.6% covered. Typing a rule is longer than tapping it.
- **The sentence with the types as its first chooser (`sentmodes`) is the middle ground:**
  - against the sentence alone: 6.6 fewer actions, 4 more controls;
  - against the types alone: 6.4 more actions, 14 fewer controls, 13% less covered.
- **Slim (owner's idea: cron shown in the sheet, the builder thinned to what cron cannot do):**
  - 101 actions, against 81 for sentmodes;
  - covers 48%, so it is no thinner;
  - four tasks then need typing.

**Round 3 (owner, 2026-10-08): "hiding the full task sheet behind advanced or wrapping everything, including cron, inside the rule as a sentence of tappable words"** (`tools/screens/repeat3_opt.py`, `repeat3-opt.json`).

**Owner's answers:**
- **A** is scored with each builder behind More options.
- **B** is scored three ways: a read-only cron line, a two-way mirror, and an "as cron" toggle. The cron line is blank when cron cannot express the rule.
- **Text size:** the scoring decides.
- **Axes:** the six, plus density, legibility and learnability. "No cron-only actually exists": every task has a words, sentence or builder path, so learnability is the actions taken without cron syntax.

**The space:**
- 196 variants:
  - A: 4 builders × start × sheet or page × 7 type options;
  - B: 3 cron modes × start × sheet or page × 7 type options.
- The type options are designkit scale steps on the controls' 14 px base. The sentence sits at lg or xl; the small text at sm.

**Results:**
- **All 196 pass the rules; the front holds 81.**
- **B (everything in the sentence) against A (the slim field, the builder behind More options), paired:**
  - against A with the types builder: 7.75 fewer actions without cron, 4.25 more with it;
  - against A with sentmodes: 14.6 and 2.6 fewer;
  - clutter equal, 2% less covered, 2 more controls;
  - more crowded (0.8 more controls per 100 px), with a lighter heaviest element (A's field is the heaviest thing on its sheet);
  - closer to the references (−0.09).
- **Inside B, the cron path never beats the sentence's words on these ten tasks.** So read-only, toggle and mirror tie on actions:
  - the toggle costs 1 control;
  - the mirror costs 1 control and +0.003 clutter.

  Cron's value is then familiarity for people who know it, which these measures cannot see.
- **Type:**
  - The sentence's size (16–22 px) barely moves the measures.
  - craftkit's type-size sprawl counts the whole page, the Today screen behind included, so it does not separate the options.
  - **Only the Major Second options keep the small text at 12 px or more (12.5 px).** The other ratios drop it to 10.5–11.5 px.
  - Recommendation: the sentence one step above the controls, the small text at least 12 px; the exact sizes are settled in the type pass (decision 15).

Mockups: `docs/screens/t1/repeat3-options.html`.

**Round 4 (owner, 2026-10-08): the sentence sheet tidied** (`tools/screens/repeat4_opt.py`).

**The owner's review of round 3's B:**
- the presets and the unit chooser repeated the same options;
- an "every [n]" row repeated the sentence;
- the monthly chooser drew "day 16" and "3rd Friday" together. A monthly rule is one or the other: "I don't see why it matters that they coincide".

**The owner's design:**
- **Chips are the presets and set the unit:** Day, Week, Month, Year, plus Minutes, Hours, Weekdays and Weekend.
- **The sentence's words edit the rest,** and each word opens one chooser:
  - the unit word sets the number;
  - "on" sets the day;
  - "at" sets the time;
  - "forever" sets the end.
- **Monthly is a switch, then one picker:** the day of the month, or the weekday of the month.
- **The sheet opens with "Does not repeat".**

**The owner's answers:** score every one of the following.
- **Chip layouts:** all eight shown; 4 + More; two labelled rows; and the owner's own, the four presets on top with the sentence tapped to show the other four, placed above it (swapA) or below it (swapB).
- **The number:** typed inline, a stepper, or quick values.
- **The month day:** a grid, a typed number, or a list.
- **Random and After done:** as words in the sentence, as chips, or typed only.
- **The time:** typed, or T1.5's dial with the typed field.
- **The end:** chips, a list, or typed.
- **The cron line:**
  - read-only;
  - an "as cron" toggle;
  - a mirror;
  - the owner's addition: read-only until tapped, then edited in place, not in another sheet.
- **Containers:** the sheet and the page.

**Workflow:** about 6,500 combinations. The choices that touch only their own chooser were scored in two stages:
- **Stage 1** (the opening): chips × random × cron × container, 120 variants.
- **Stage 2** (the choosers): 54 combinations on stage 1's best sheet and best page, 108 variants.

Every state of the chosen design is drawn for review, because round 3's redundancy had gone unseen in its mockups.

**Defects fixed in the tooling:** the measure and render caches and the image crops raced between parallel workers. They now write aside, then swap the file in whole.

**Stage 1:** all 120 pass; the front holds 68.
- **Chips:**
  - swapping in the other four costs 2.7 more actions than showing all eight;
  - but it brings 4.6 fewer controls, −0.006 clutter and less crowding.
- **Random and After done:**
  - as chips: 81 actions;
  - as words: 84, and closer to the references;
  - typed only: 103, outside the sheet.
- **Cron:**
  - read-only is the calmest, but leaves cron to the capture line;
  - of the editable forms, the owner's "edit in place" has the least clutter (0.034, against the mirror's 0.038).
- **Best by the sum of the axis ranks, for both the sheet and the page:** swapB, random as words, cron read-only.

**Stage 2:** all 108 pass; the front holds 2, one per container.
- **The sheet's front member** (83 actions, reach 1.86, clutter 0.044, the tallest view 48% of the screen):
  - quick values for the number (the "…" chip types any other);
  - a typed month day, with a "Last day" chip;
  - a typed time with suggestions;
  - chips for the end.
- **The 1–31 grid** makes the month view taller than the screen; its header is cut off (the tallest view averages 71% against 61% for typed).
- **Caveat:** no task picks an arbitrary day of the month. There the grid costs 1 tap, and a typed day 3 actions with the keyboard up.

Mockups, every state: `docs/screens/t1/repeat4-options.html`.

## T1.5 + T1.6 merged: one "When" sentence (owner's workshop, 2026-10-08)

**Owner:**
- "'Does not repeat' is not necessary if we insert date and time picker vs repeat correctly… could the Repeat layout have a switch and become the only date and time and repeat pattern picker? 'Every' becomes a variable, tapping it switches to 'Once' (the last used option sticks as default for the next input). Tapping on 'at' switches to 'from-to' and 'random'."
- "Never ask 'exactly'": a specific time is exact, an interval is counted exactly, and a random time only respects its window.

**The grammar, workshopped:**
- **Once** on [date] [time].
- **Every** [n unit] [· at random (a range)] [· after it's done] [on days] [time] [starting date], [end].
  - **time:**
    - at [t, + more times];
    - from [a] to [b], read as "between [a] and [b]" when the unit is minutes or hours;
    - at a random time between [a] and [b];
    - no time (all day). After it's done, the time is optional.
  - **end:** forever · until [date] · [n] times.
    - Until opens the month, plus a calculator, "+ [n] [days, weeks, months]" from the start. It also covers "for [duration]" (merged, owner).
- **How the readings are chosen:** the time chooser offers At · From–to · Random time · No time, and the unit decides the wording. With days or longer, from–to reads as the item's span; with minutes and hours, as the window the repeats stay inside.
- **Combinations:**
  - random days take any time slot;
  - "at random" and "after it's done" can combine (a random gap counted from completion);
  - Once has no random time.
- **Both ways of saying twice a day stay:** several times, or an every-12-hours interval.

**To be scored:**
- "on [days]": Weekdays and Weekend as shortcuts in the weekday chooser, against Weekday and Weekend as units of the interval;
- how the start shows: only when changed, always, or carried over from Once's date;
- the entries: ⋯ › Date and ⋯ › Repeat opening the chooser already open, against one ⋯ › When opening on the last used.

**Owner asked for an interactive HTML page of the screen first, to see how it works in practice:** `docs/screens/t1/when-prototype.html`.

**Prototype v2 (owner, 2026-10-08):**
- **"The constant resizing of the sheet makes the user chase the sentence around the screen."** The sheet now keeps one height (640 px). The sentence and its readout are pinned to its foot, above the gesture bar. Choosers fill the space above them, scrolling when tall. Measured: the foot's bottom stays at the same pixel with every chooser open.
- **Undo and Redo** are in the header. Every change to the rule is one step, "so the user does not lose all progress for one misclick".
- **Contradictions the owner found:**
  - random gaps plus a random time;
  - an hourly interval plus a random time;
  - "every hour from 9 to 17, 6 times", which ends at 14:00 on the first day.

**Rules (owner's answers):** impossible options are hidden.
- **Minutes and hours** take a window ("between [a] and [b]") or all day; the interval sets the times.
- **At random (random gaps) needs a time bound** ("to avoid notifications or alarms firing during sleep hours"): a fixed time, or a window the random moment falls in, with no count. "On [days]" is hidden.
- **A random time takes a count per day** ("at [3] random times between 9:00 and 17:00"; owner: yes to several random times a day). This is separate from the end's count in all.
- **After it's done** hides "on [days]"; its time is optional.
- **Ends:** forever, until, [n] times in all, and, for minutes and hours, for [n] days (owner: both). A finite end reads back its last occurrence.
- **Edge cases, in the readout:**
  - until cannot be before the start (those days are not drawn);
  - a range typed backwards is swapped;
  - day 29–31 notes "the last day in shorter months";
  - 29 Feb notes "28 Feb in other years";
  - overnight windows read "the next day".
- **Recorded, not drawn:** times that fall in a clock change are a platform rule.

**Prototype v3 (owner, 2026-10-08):**
- **The sheet resizes upward only, and the sentence is held in place.** The foot is anchored above the gesture bar; measured, it stays at 712 px with every chooser.
- **The calendar fits without scrolling.** No chooser scrolls; Until's (the calculator plus the month) is the tallest, its top 8 px from the screen's.
- **Undo and Redo sit under the sentence,** opposite "As cron:".
- **Two times chosen in "at" are kept** when switching to from–to, and back.
- **Times are set on T1.5's approved entry, the dial with a typed field:** hour, then minutes. The prototype's native time inputs had brought back the scrolling the T1.5 scoring had ruled out (wheels 27 actions against the dial's 13).
- **The 24-hour dial follows SimpleReminder's** (Android's TimePicker, captured on the phone; geometry only):
  - 1–12 on the outer ring, 13–00 on the inner one;
  - a tap anywhere in an hour's wedge picks it.
  - Android's is about 224 dp across, with the inner ring at a 54 dp radius, so its inner hours are about 28 dp apart.
  - Here it is 312 dp across, with the inner ring at 92 dp, so the inner hours are 48 dp apart (the 48 dp rule).
  - This replaces the 12-position dial with a 00–11 | 12–23 switch.
  - The time chooser still fits.
- **Owner (2026-10-08): "I am comfortable with using a somewhat smaller tap size for this one purpose, not to devour the whole screen. 30-32dp could work? 35dp?"**
  - The dial is now sized from the inner ring's spacing (a tap still picks the whole wedge):

    | Inner spacing | Dial | Time chooser's top |
    |---|---|---|
    | 30 dp | 242 dp | 147 px from the screen's top |
    | **32 dp (default)** | 250 dp | 139 px |
    | 35 dp | 262 dp | 127 px |
    | 48 dp | 312 dp | 77 px |

  - The outer ring sits 40 dp further out, so its hours and the minutes stay above 48 dp (53 dp at 32).
  - The prototype has a selector, so the owner can try each by hand. **This is a recorded exception to the 48 dp rule for the dial's inner ring only.**
- **The dial at 32 dp inner spacing (250 dp across): owner's choice, 2026-10-08.**

**The start of a repeat (owner, 2026-10-08):**
- **"I don't know how to change it if it doesn't show."** As built, "shown only when changed" had no way to change the start: a defect, not an option. It is replaced.
- **A repeat's start defaults to Once's date.**
- **Three ways to change it, scored** (`tools/screens/when_start_opt.py`, `docs/screens/t1/when-start.json`). The prototype itself was measured: a script sets each state, then the render and the hit-tested DOM are read, the phone alone at 360 × 740.

| Variant | Actions (interval chooser open / sentence closed) | Drawn when closed | Sentence lines | Foot | Clutter, closed | Controls |
|---|---|---|---|---|---|---|
| The first Next date is tappable | 2 / 2 | yes | 1 | 151 px | 0.0297 | 6 |
| A Starting row in the interval's chooser | 2 / 3 | no | 1 | 121 px | 0.0290 | 5 |
| Always in the sentence | 2 / 2 | yes | 2 | 169 px | 0.0324 | 6 |

- **"Always" is dominated by the tappable Next date:** the same actions, with a line more, more height and more clutter.
- **Between the other two:** the tappable date is one action quicker from a closed sentence. The row is the shortest foot (30 px less, the date drawn at 12.5 px inside a 48 px target), the calmest, and has one control fewer. ⋯ › Repeat opens with the interval's chooser showing, where the row already is.
- **Once moved,** the start reads in the sentence ("…, starting [date]"), whichever way it was moved.
- **Owner's choices (2026-10-08):**
  - Weekdays and Weekend are shortcuts inside "on";
  - a repeat's start is changed from a Starting row in the interval's chooser;
  - the dial's inner ring is spaced 32 dp (250 dp across).

  These are the prototype's defaults now. Still open: two entries (⋯ › Date, ⋯ › Repeat) against one (⋯ › When).
- **Entries, counted** (the ⋯ short list from T1.3 holds Kind, Templates and Full form):

  | | Two entries | One entry |
  |---|---|---|
  | Items in ⋯ | 5 | 4 (Hick: 2.32 against 2.58 bits) |
  | The chooser | opens already showing | a tap more, every time |
  | Once or Every | set by the entry | a tap more whenever the last used is the wrong one |
  | Over T1.5's 4 tasks and T1.6's 10 | — | 14 to 27 taps more |

  **Owner's choice: two entries,** ⋯ › Date and ⋯ › Repeat, into the one merged sheet.

**Approved (owner, 2026-10-08): the When sheet as T1.5 + T1.6.**
- It supersedes:
  - T1.5's two-step picker (approved earlier the same day), now folded in `screens.html` as superseded;
  - T1.6's rounds 1–4.
- `screens.html` shows it as section `t1-5` (`tools/screens/when_page.py`), with its states rendered from the interactive prototype itself into `docs/screens/t1/when/`:
  - nine phone states;
  - Windows, the same sheet as a panel over the window.
- The prototype stays the reference for behaviour: `docs/screens/t1/when-prototype.html`.
- **Still owed:** the cron extensions in `Cron.kt` (`L`, `#`, several lines, names) and the data layer's support for the new kinds:
  - several random times a day;
  - random gaps bounded by a window;
  - "for n days";
  - the start row.
- **Fixed after the owner's report (2026-10-08): "T1.5 + T1.6 in screens.html did not render."**
  - **The cause:** the section's images were separate files, which a viewer that loads the page alone cannot reach.
  - **The images are now inlined,** as greyscale WebP, 40% of the PNGs' size.
  - **The page was then over the viewer's size limit.** The superseded explorations (the T1.5 picker, and T1.3's ✓/▤ sizes) moved to `superseded.html`, linked where they were. `screens.html` keeps the approved screens only (453 KB).
  - **Sections are newest first (owner):** T1.5 + T1.6, T1.4, T1.3, T1.2, T1.1.

**Cron extensions built (owner, 2026-10-08: "Cron work first").**
- **`core/.../recurrence/Cron.kt`** now takes, beyond Mnemo's five numeric fields:
  - names: `JAN`–`DEC` and `SUN`–`SAT`, any case, in lists and ranges;
  - `L`: the last day (`BYMONTHDAY=-1`), and `FRIL` / `5L`, the month's last Friday (`BYDAY=-1FR`);
  - `#`: `TUE#2` / `2#2`, the second Tuesday (`BYDAY=2TU`), 1 to 5;
  - several lines: one rule, their union (`RULE_SET`).
- **Plain and ordinal weekdays together** (`MON,FRI#2`) are a union, and the OR rule holds with an ordinal weekday.
- **Still refused:** `W`, `?`, a day no listed month has (`31 FEB`), and any bad line, which refuses the whole input.
- **Tests:** `CronTest`, 9 tests, with the dates checked against a calendar.
  - All 9 fail against the previous converter, and all pass now.
  - The core suite passes: 299 tests.
- `RecurrenceCasesTest`'s refusal list dropped the two forms that became valid.
- SPEC v0.37 §3.4 states the input.
- **Still owed to the data layer for the When sheet:**
  - several random times a day (RANDOM_WINDOW with a count);
  - random gaps bounded by a window;
  - "for n days" (an until computed from the start).

**The When sheet's data built (owner, 2026-10-08: "Build those in order of dependency").**
- **Order of dependency:**
  1. several random times a day, the window's draw generalised;
  2. random gaps bounded by a window, which reuses that window;
  3. ends for both.
- **Storage compatibility:** sync sends rows as named values, and an older version reads only the names it knows. A new column on an old kind would be dropped there, and written back without it. So each new form is a kind of its own:
  - **RANDOM_TIMES:** `window_count` times a day, one drawn in each equal part of the window, so they spread and never coincide; a window may run past midnight.
  - **RANDOM_GAPS:** `rand_unit` from MINUTE to MONTH, an optional window for the time (minutes and hours need one), and the gap restarts at the window's start each day.
  - **Both** take `rec_until` (inclusive) or `rec_count`.
  - **An older version cannot read the new kinds,** so their rows wait in its sync queue.
- **The plain forms keep RANDOM_WINDOW and RANDOM_DAYS,** with the same draw keys. Tests compare them with the old expansion verbatim, so stored items do not move.
- **"For n days"** is `untilForDays`, the last moment of the n-th day; a rule takes it as its UNTIL.
- **Schema 23** (an automatic migration adds four nullable columns). The triggers tie each kind to its columns.
- **A defect found and fixed before commit:** the first trigger draft compared the kind with IN. NULL IN (...) is NULL, which refused every row that does not repeat (140 tests failed). It now compares with IS, and the comment says why.
- **Tests:**
  - `RandomKindsTest`: 13, in the core;
  - `WhenKindsTest`: 5, round trips, kinds, sync values, reminders, triggers.
  - The core passes 312 tests and the data layer 378.
- SPEC v0.38 §3.4.

## T1.7 Labels: questions (owner, 2026-10-08)

**Already fixed** (decision 08, SPEC §3.8):
- one vocabulary, "Label": name, colour, scope (everything, activities, trackers), order;
- a page carries many; an activity, habit or tracker at most one;
- names are unique ignoring case, and duplicates merge on sync;
- a new label takes a name-derived colour, changeable later;
- the capture line's `#label` marker (T1.3).

**Owner's answers:**
- **Scope:** the chip, the picker, the suggestions while typing `#`, and management (Settings › Labels, behind ⚙).
- **To score:**
  - the chip's look in greys: text only, a dot and text (the dot takes the colour later), an outlined pill, a tinted pill, or text after #;
  - the picker: opened from ⋯ › Label and from the full page's Label row, as a sheet, a list with search and create-on-type, a chip grid, or in the keyboard's place;
  - more labels than fit: the first plus a count, as many as fit plus a count, or all of them wrapping;
  - the `#` suggestions: chips above the keyboard (in the hint line's place), a short list over the line, or inline completion;
  - management: direct controls, a menu per label, or a detail page.
- **Axes:**
  - harmony, ease, clutter;
  - legibility and telling labels apart without colour;
  - density on rows (width taken from the title, extra height, wrapping);
  - closeness to the references.
- **References:** Todoist, TickTick, Any.do, Tasks.org, Notion (new content only), Obsidian, and the source apps (Tendril's tags, Chronicle's categories).

**T1.7 scored (`tools/screens/label_opt.py`, `labels-{a,b,c,d}.json`, `labels-rank.json`).**

**References** (`docs/screens/t1/label-references.json`), captured on the phone with geometry and labels only:
- **Apps:** Todoist, TickTick, Any.do, Tasks.org, Notion and Obsidian (geometry only), Tendril, Chronicle.
- **Chips:** 7 of the 8 draw a tinted pill (Todoist's rows show grey text).
- **Pickers:** mostly sheets with a list, search, and create-while-typing.
- **`#` suggestions:** only Todoist and Any.do offer them.
- **Management:** mostly a page per label.
- **Left behind by the capture, to be cleared by the owner:**
  - Tendril's "Sample label" (Tendril cannot delete a label);
  - an empty Notion database in Notion's trash;
  - possibly a TickTick task in its trash.

**Results:**
- **A, the chip** (30 variants; all pass; the front holds 14):
  - **Inline**, after the title: no row lost, but titles get 125–160 px.
  - **Below** the title: titles get 208 px, but rows grow 11–18 px and one row is lost below the bar.
  - Plain text and #name are the calmest; outlines are the busiest.
  - The leaders are a tint, inline, as many as fit then +n (clutter and density), and a tint, below, the first then +n (closest to the references, 0.23).
- **B, the picker:**
  - A list in the keyboard's place, or in a pop-over, cuts off controls.
  - A grid in a sheet leads on ease and on labels shown (12, covering 42%).
  - A list in a sheet is the closest to the references, but covers 95% with 12 labels.
- **C, the `#` suggestions:** chips above the keyboard and a list over the line tie (14 actions). Inline completion fails the 48 dp rule.
- **D, management:**
  - direct controls: 17 actions, but 6 controls a row;
  - a page per label: 23 actions, 2 a row, calmer, closer to the references;
  - a menu per label is dominated by the page.

Mockups: `docs/screens/t1/labels-options.html`.

**T1.7, the owner's answers and the scoring that followed (2026-10-09):**
- **B, the picker (chosen):** a sheet with a grid; all labels shown, in alphabetical order; the search-and-create box below them.
- **A, the chip:** "depends on whether the label can be tapped to open a screen with all elements belonging to that label". Scored as part E: a label view, a filter, or a mark only, with the chip's target at 28 or 32 dp (owner's exception to 48 dp).
  - **A label view and the filter tie on every scored axis** (both take 2 actions, same reach, room and clutter). They differ only in what they show: the view gathers every kind, the filter only the screen it is on. That column is in the table but on no axis. (Corrected 2026-10-09: this line first said the view beat the filter "on every measure".)
  - **A label view against a mark only:** 2 actions against 10 (searching #health). The view's costs are mis-tap exposure (4.5–7.7% of a row's area) and reach to a small target (Fitts 3.6–3.8).
  - **32 dp against 28 dp:** reach 3.59 against 3.78, for 1 px more height and about 1% more exposure. On the rank sums 28 dp comes out ahead (inline text: 76.5 against 84.5), because exposure and height count against 32; 32 wins on reach alone.
- **Score tables (every variant of A–F, raw measures, rank-sum axes, the front, the gate):** `docs/screens/t1/labels-scores.html`, from `label_opt.py scores`. Part C's reach and line movement and part F's chosen dot are measured there, not copied.
- **Controls added at the owner's request (2026-10-09), one per part, scored like the rest (`label_opt.py controls`, `labels-controls.json`).** The table run fails if any control reaches the front.
  - A: heavy dark chips, every name wrapped below the title. Last of 31 (clutter 0.068, 26.5 px a row, 2 rows lost).
  - B: a page with rename, colour and delete on every row, and each pick confirmed. Last of 7 (23 actions, 42 controls).
  - C: a dialog over the line, with OK after each pick. Last of 4 (18 actions against 14, and the line is hidden).
  - D: nested pages, one page per property with Save, reorder behind Edit, and a confirmation before deleting. Last of 4 (33 actions; clutter 0.059 against 0.028–0.035). Its taller rows put Projects below the fold, so one scroll is counted.
  - E: 48 dp chips below the title, with a menu first. Off the front; 22 of 24 have a lower sum.
  - F: each dot with its name stacked under the time. On the first run it reached the front: it was the only tappable variant with every dot on one line, because the centred count had been measured on the chosen dot alone.
    - The centred count was then scored for all four count variants. The control fell off the front: 15 of 16 have a lower sum.
    - The chosen dot stays on the front, with the lowest sum.
  - **A tappable chip below the title** loses 2 rows below the bar; after the title, none.
- **C, the `#` suggestions:** the owner asked to score chips above the line against below it. With the same keyboard:
  - below: the line moves 25 px, reach 2.49;
  - above: the line stays put, reach 2.81;
  - a list over the line: stays put, reach 3.06.

  All take 14 actions.
- **D, management:** "Score both". Already scored:
  - direct controls: 17 actions, 6 controls a row, clutter 0.035;
  - a page per label: 23 actions, 2 a row, clutter 0.028, closer to the references.

**T1.7, the owner's proposal (2026-10-09):** "Could the label sit somewhere where it doesn't crowd the screen or increase rows height? Could it become a colored dot? The label color would then be decided by the user with an advanced color picker."
- **The caveat, recorded:** colour must not be the only way to tell labels apart (WCAG 1.4.1, colour-blind people). The name stays readable by a long press on the row, on the item's page, and in a filter bar of named dots (owner's answers). The colour comes from the guided picker that keeps colours apart for colour-blind vision (T0's series contest).
- **Scored as part F:**
  - place: under the time or mark, or by the action;
  - several labels: up to 3 dots, a dot and a count, or stacked;
  - the label view: from the item's page, or the dots as a 32 dp target.

  The filter bar is drawn in every variant.
- **Under the time, the view from the item's page:**
  - titles get 232 px (125–208 with name chips);
  - no row height is added and no row lost;
  - a dot and a count keeps the dots in a column (5 px stray; 21 for three side by side).
- **Tappable dots under the time** add 5 px a row and lose a row; they take 5% of a row as a target.
- **By the action:** titles get 162–184 px, nothing lost.
- **Opening the view:** 2 actions with tappable dots, 3 from the item's page.

Drawn: `docs/screens/t1/labels-dots.html` (`labels-f.json`).
- **Owner's choice (2026-10-09): "Under the time, dot + count, all exactly vertically centered."**
  - Every dot sits on one vertical line: the count hangs beside its dot without moving it (measured stray: 0 px, from 5 px).
  - The time or mark and its dot are centred together in the row.
  - Titles keep 232 px; no row height is added.
  - Drawn with the parts still open (the # chips above or below the line; Settings › Labels as direct controls or a page per label): `docs/screens/t1/labels-rest.html`.

**T1.7 approved (owner, 2026-10-09):** "C: above, the textbox stays fixed. D: filter on any screen, page per label in settings with Control, which serves as a legend for the colors as well." Asked what D takes from the control: "Its list rows only".
- **The label on a row:** a dot under the time or kind mark, as chosen earlier; one dot and its count, every dot on one vertical line.
- **Filtering:** the filter bar of named dots, on any screen. A tap shows only what carries that label there; the chip that is on comes first, with Clear beside it. A label's page shows what carries it.
- **The picker:** a sheet with every label in a grid, in alphabetical order, the search-and-create box below them. The drawing now puts the box below; the scored picker had it on top, and the 20 actions are unchanged.
- **The # suggestions:** chips above the capture line, which stays put (0 px, against 25 below; 14 actions, reach 2.81).
- **Settings › Labels:**
  - The control's list rows: each row has the label's dot, its name and a written line (scope · count), so the list is the colour legend.
  - Each row opens one page per label: name, colour, scope, what carries it, and Delete, with an undo toast. Reordering is behind Edit.
  - Scored as `legend`: 26 actions, 0.9 controls a row, clutter 0.045. It is on the front, with a rank sum of 12 against 10 for the plain page per label.
  - The cost of the legend is the written line (+0.017 clutter) and Edit (+3 actions with a scroll).
  - A ⋯ on each row (`legend_menu`) saves 1 action, doubles the controls a row, and falls off the front, so it is left out.
  - The reference distance counts `legend` as a page per label.
- **Drawn:** the T1.7 section of `docs/screens/t1/screens.html` (phone: Today with dots, Today filtered, capture with #, the picker, the legend list, a label's page; Windows: Today beside Settings › Labels).
  - Images are greyscale WebP at quality 50, so the page stays under 512 KB (505 KB).
  - The next tier's sections need a page of their own.

**T1.8 toasts and dialogs, the owner's answers (2026-10-09).** Already settled on 2026-10-07: deleting shows an Undo toast with no dialog; dialogs appear only for what Trash cannot bring back (emptying Trash, discarding an unsaved page).
- **Scope:**
  - the Undo toast and the two Trash dialogs;
  - the sync clash, when something changed on two devices (SPEC §3: keep one, or keep both);
  - notices and failures;
  - permission asks: notifications, exact alarms, battery.
- **The toast's place:** score all three, on phone and Windows: above the bar, above the capture line when it is open, and at the top under the header.
- **The Undo time:**
  - score the timings: 4, 7 and 10 s, against staying until the next action. WCAG 2.2.1 asks for an adjustable limit, so a setting is drawn either way;
  - score stacking: a new toast replaces the old, toasts stack, or they merge ("3 deleted · Undo all");
  - score a way back once the toast has gone: Undo in ⋯, a "Recently done" list, or Trash only.
- **The dialogs:**
  - score the forms: a centred dialog, a bottom sheet, or confirming in place;
  - score the button order;
  - score verb buttons against glyphs, icons and symbols. The owner changed the offered "verb buttons, always" into this;
  - score typing or holding to confirm as a real option.
- **The sync clash:** score every form (a mark on the item, a card on Today, a toast, a dialog when found), and the answer screen (side by side or stacked; words or marks).
- **Permission asks:** score the timing (when first needed, at first run, from Settings only).
- **Failures:** score the forms (a toast, a banner under the header until fixed, a mark in the bar or the Hub).
- **Axes (all four):**
  - ease and reach;
  - clutter and cover (including what the toast hides);
  - safety (how easily a destructive action is confirmed by mistake);
  - legibility and distance from the references.
- **References (all four groups):**
  - the four source apps;
  - the T1.7 label references;
  - more open-source apps (Fossify, Etar, Syncthing-Fork, others, via Droid-ify or Aurora);
  - Windows 11's own toasts and dialogs, and the desktop Notion and Obsidian.
  
  Placeholder data only. A destructive dialog is opened and cancelled, never confirmed.
- **The control:** one per part, built to lose; the run fails if a control reaches the front (as in T1.7).

**T1.8 first scoring (2026-10-09; the reference apps are not captured yet, so the reference distance is not on any axis).** `tools/screens/toast_opt.py`, tables `docs/screens/t1/toasts-scores.html`, drawings `toasts-options.html`. Six parts, each with a control.
- **A, where the toast sits:**
  - Above the capture line when it is open (anchored): hides nothing, reach 2.40, sum 25.5.
  - Above the bar: with the keyboard up it lands on the capture line and hides its ⋯.
  - At the top: reach 3.73.
  - **The control did not lose.** A notice in the middle over a shade hides 23 targets and needs a tap to carry on, but it sits closest to where the user acted (105 px, against 221–240), so it wins Notice and stays on the front. Reported as measured, not redesigned; how much nearness should count is the owner's call.
- **B, the Undo time:**
  - Merging several into one toast ("3 moved to Trash · Undo all", ▸ to pick one) is on the front at every timing.
  - The timings trade margin after reading (2.5 s at 4 s, 8.5 s at 10 s; Brysbaert 2019's 238 wpm) against how long the toast lingers.
  - Undo in a header ⋯ saves 4 actions over Trash and the folds, at one more header control.
  - Control (2 s, unlimited stack): off the front.
- **C, the dialogs** (17 of 54 on the front):
  - Confirming in place with a hold leads the sums: no overlay, backing out by tapping anywhere. It is the least safe, though: the confirm sits 8–33 px from the button just tapped.
  - A dialog or sheet keeps the destructive choice 52–345 px away.
  - Verbs read; glyphs are calmer.
  - In place, the button order has no effect (the rows repeat).
  - Control ("Are you sure?", Yes under the thumb): off the front.
- **D, the sync clash:**
  - A card at the top of Today, versions stacked, buttons in words: lowest sum (63.5).
  - A dialog answers in 1 action but interrupts and hides 23 targets.
  - Side by side always loses to stacked, because long titles wrap (184 px against 141).
  - Control: off the front.
- **E, permission asks:** asking when first needed wins (0 before use, with context). Settings only leaves a reminder to fail silently. Clutter is left out, as the three are different screens.
- **F, failures:**
  - A banner under the header and a dot on the Hub are both on the front.
  - A toast ranks below even the control: once it fades, nothing shows that anything failed.

**T1.8 references, the Windows desktop (2026-10-09).** In `docs/screens/t1/toast-references.json`, geometry and labels only.
- **Windows 11 notifications:** bottom right, above the taskbar. The user's setting is 5 s (`MessageDuration`). Repeats did not show, so stacking was not observed.
- **Notion desktop:** "Moved to Trash · Restore" at the bottom of the page area, up at 4 s and gone by 8 s. The way back is Trash.
- **Joplin desktop:**
  - Deleting needs no dialog. "La nota è stata spostata nel cestino · Annulla" ("The note was moved to the trash · Undo") sits bottom right and was up at about 5 s.
  - Emptying the trash opens a centred dialog, with the destructive command link on top: opened and cancelled.
- **Not captured:**
  - the phone: adb lost it, as wireless debugging refuses the connection;
  - Windows Explorer: the grant allows clicks only, and Recycle Bin would show the owner's files;
  - Obsidian desktop: its vault is the owner's.
- **Leftovers for the owner:** "Sample toast 1" in Notion's Trash and in Joplin's trash. Four test notifications sit in Windows' notification centre.
- **With the reference distance on the axes:** the controls of B to F lose. The C control first matched Joplin's dialog: its "Yes/No" had been described as verbs, so it is now "generic" and it loses. A's control still stays on the front, on nearness.

**T1.8 references, the phone (2026-10-09, USB).** Twelve apps, added to `toast-references.json` (`platform: android`). Geometry and labels only. Timing came from on-device hashes of the toast's screen rows every ~0.2 s; no images were kept.
- **Undo toasts:**
  - At the bottom: Tasks.org, and TickTick (an icon-only round button).
  - Anchored above the FAB: Todoist, Google Tasks, Keep.
  - None at all: Tendril, Chronicle, Mnemo, Any.do, MS To Do, Joplin Android, Notion Android, Loop.
- **Timings:** Google Tasks 3 s, Tasks.org 4 s, TickTick 5 s, Keep 8 s, Todoist 9.5 s.
- **Several in a row:** Tasks.org, TickTick and Keep replace the toast.
- **Way back:** mostly Trash or a completed section; Todoist has an activity list.
- **Dialogs:**
  - Every Android one is centred, with the destructive choice on the right (near the thumb), and confirmed by a tap.
  - Tasks.org ("OK") and Loop ("NO/SI") use generic labels, so they were recorded as `generic`, not verbs.
  - Joplin's desktop puts the destructive choice on top, its Android app on the right.
- **Permission asks:** Joplin Android asks for geolocation when the first note is made (need).
- **With every reference on the axes:**
  - **C's control reaches the front again.** "Yes/No" on a centred dialog under the thumb is what Tasks.org and Loop do, so it is nearest the references. The reference distance rewards it for being common practice; it loses on every other axis. Reported as measured.
  - A's control stays on the front (nearness).
  - B, D, E and F's controls lose.
  - The leaders do not change, except that C's dialogs now favour the destructive choice near the thumb, matching every Android reference.
- **Not captured, and why:**
  - Equipoise: no deletable items without making wellbeing data.
  - Fossify Calendar and Etar: samples would sync into the owner's Google calendars.
  - Fossify Clock: real alarms.
  - Track & Graph: its first-run tutorial.
  - Obsidian: an owner's note was open.
- **Incidents:**
  - Any.do deleted three samples permanently at once, through an in-row delete with no confirmation and no Undo.
  - The Tasks.org delete dialog was confirmed for the agent's own samples; Tasks.org shows no bin.
  - A stray "o" was typed into Chronicle's quick-add, then removed.
- **Leftovers for the owner to clear:**
  - Tendril: Sample toast 1–5 in Trash.
  - Chronicle: Sample toast 1 archived.
  - Tasks.org: 1–3 completed.
  - Todoist: 1–6 completed; they also counted toward the daily goal.
  - TickTick: 1–2 completed, 3–6 deleted.
  - Any.do: 4–5 active.
  - MS To Do: 1–2 completed, 3–5 active.
  - Google Tasks: 1–4 completed.
  - Keep: 1–5 in its bin, which Keep empties after 7 days.
  - Joplin Android: 1–3 in notes, 4–5 in its bin.
  - Loop: 1 archived.
  - Notion: 1–3 in Trash; with the desktop's, four sample pages in all.
  - Joplin desktop: 1 in its trash.
  - Windows: four test notifications.

**T1.8, the owner's choices (2026-10-09):**
1. **The toast sits anchored:** above the capture line when the sheet is open, otherwise above the bar.
   - Undoing an Add reopens the screen or sheet that was in use, with everything typed just before "done" put back.
2. **Undo:**
   - 7 s;
   - several in a row merge into one toast;
   - the toast can be swiped sideways to free the screen;
   - the way back once it has gone is Trash and "Done today" only.
3. **Destructive confirmation:**
   - In place, near the thumb, held.
   - **To rescore, for consistency across screens:** the header and button placement. The text in buttons should be shorter, or combined with glyphs.
   - The owner asked what "Discard changes" does. Answer: nothing in a page. A page saves as it is typed (the SPEC lets every keystroke write to the database), so leaving a page loses no edits; the dialog drawn for it was a state the data layer does not have. Unsaved text exists only in the capture sheet or the full form before Add.
   - Trash gets multi-select on its rows, to restore or delete forever the selection.
4. **Sync clash:** a card on Today, versions stacked, words.
5. **Failures:** a banner under the header.

**Asked next (2026-10-09):**
- **Unsaved capture text:** score it (keep a draft; discard with an Undo toast; hold to discard in place).
- **Screens that place their actions the same way:**
  - Trash, an item's page, a label's page, pages and databases;
  - "Hold to empty trash" belongs to Trash alone.
- **Placements to score, all four, with a control:**
  - in the header, top right;
  - a bottom action bar;
  - floating near the thumb;
  - behind a ⋯ belonging to the single element, aligned top right within the element's bounds (for example a row).
- **Button text, all three, with "Hold to empty trash" as the control:**
  - glyph and one word;
  - one word only;
  - glyph only, the word shown while held.

**T1.8, parts G and H scored (2026-10-09)** (`toast_opt.py g h`; tables `toasts-scores.html#g`, `#h`; drawings `toasts-options.html`).
- **G, where actions sit and their text:**
  - **The bottom action bar is the front leader with every text.** It takes 16 actions in all (against 20–26), reach 1.23 (against 1.9–3.9), and one way in. Delete sits 694 px from Back, against 273–292 in the header.
  - Its Delete strays 44 px across the four screens, because the screens carry different numbers of actions. The header strays 0–6 px.
  - Not measured: the bottom bar takes the nav bar's place on these pages, so going elsewhere needs Back first.
  - Glyph with word and word only tie (sum 28.5). Glyph only is calmer but carries no words (32.5).
  - The floating button is consistent (0 px) but needs 2 taps for everything (26 actions).
  - The header with glyphs is on the front; the element ⋯ is not.
  - Control (each screen its own way): 304 px stray and 3 ways in; 11 of 12 do better.
- **H, closing the capture sheet with text not added:**
  - The draft keeps the text (resuming takes 1 action against 29) but is off the front. Two flaws are named, not fixed:
    - each axis sums ranks, so a 1-against-29 gap counts as one rank step;
    - edge density reads the shaded dialog as calm.
  - **The control (a "Discard draft?" dialog) stays on the front:** it ties hold-in-place on every count, and its shade lowers clutter.
  - Undo (gone after 7 s) leads the sums, but loses the text unasked once the toast has gone.

**T1.8 G workshop, the owner's corrections (2026-10-09)** (`docs/screens/t1/actions-inventory.md`, draft 3):
- **One vocabulary:**
  - **Delete:** to Trash, with Undo.
  - **Restore** and **Delete forever:** in Trash only; Delete forever is held.
  - **Empty Trash:** held, fixed top right.
  - **Archive:** out of the lists, kept.
  - **Remove:** takes one thing off another.
  - "Move" is split into **When** (a time) and **Move** (a place).
  - **Snooze:** while ringing only.
  - **Skip** (Skip for today on a reminder or alarm that fires on several days).
- **Every deletable element has Delete, Restore and Delete forever** (tasks, events, reminders and alarms, habits, trackers, activities, checklists, pages, canvas cards and frames, labels, charts).
- **Labels:** tasks, events, reminders and checklists carry them too. This amends ADR 08.
- **Reminders and alarms:**
  - no Done;
  - label, date and time, repeat;
  - Skip for today when they fire on several days.
- **Tasks:** no timer.
- **A database row:** a reminder when its rows are tasks.
- **The work this creates** (listed in the inventory):
  - Restore for items and trackers;
  - Trash for activities, canvas cards and labels;
  - Delete forever for checklists and charts;
  - Delete forever for activities, reversing the 2026-10-02 rule;
  - `label_id` on items and checklists, with a schema bump;
  - a reminder on a database row;
  - a test of Skip on a standalone reminder.
- **Owner, 2026-10-09:**
  - Every "delete" moves to Trash.
  - Archive is unnecessary, since Trash keeps everything until Delete forever; it leaves the vocabulary.
  - Everything can be renamed except elements recorded on a tracker or for a chart.
  - Inventory draft 4. Open:
    - what becomes of activities Chronicle had archived;
    - whether a habit, linked to its tracker, is renamed on its own.
- **Owner, 2026-10-09:**
  - There is only placeholder data, so Chronicle's archived flag leaves the data layer (column, repository method, import).
  - Habits cannot be renamed, as they are attached to a tracker.
- **Owner, 2026-10-09:**
  - Score how a selection starts: long press selects; the long-press menu with Select; Select as a screen action; dragging down the left column; plus a control.
  - Score what a mixed selection offers: shared actions only, against each action where it applies; plus a control.
  - A database's properties, options and views go through Trash. Pages have their own section in Trash, so their elements are easier to find. Score per-page groups under the Pages section against one list under it.
  - Reminders and Pages get a sort.
- **G is rescored as where actions live:**
  - an element's own actions: long-press menu, selection bar, a ⋯ inside the element, or the element's page;
  - a screen's own actions: header, header ⋯, bottom bar, floating button.
  
  It is scored alongside the selection start, the mixed selection and the Trash's Pages section. The first G (a single placement for all four screens) is superseded.

**T1.8, where actions live, scored (2026-10-09)** (`tools/screens/actions_opt.py`; tables `toasts-scores.html#i`, `#n`, `#s`, `#m` and `#t`).
- **Two fixes to the ranking, made for every part:**
  - Fitts IDs within 0.05 bits are now a tie; a 0.002-bit gap had put M's control on the front.
  - The project's clutter tolerance (0.002) now applies under the keys these tables rank; it had been silently off for all of T1.8.
  - With them, H's and M's controls lose, and keeping a draft (H) joins the front.
- **I, an element's own actions:**
  - A long-press menu takes 8 actions, the same as a ⋯ in each row. The ⋯ costs 60 px of title room (147 against 207) but can be seen at rest.
  - The element's page takes 12 actions.
  - The selection bar takes 10 (When and Delete in the bar, Label and Reminder behind its ⋯) and is off the front.
  - **The control (a glyph strip on every row) stays on the front:** fewest actions (4), at 35 px of title room.
- **N, a screen's own actions:**
  - Bottom bar: reach 1.68, but 56 px less room.
  - Header: 4 controls.
  - Floating button and header ⋯: 2 taps each.
  - All four are on the front. Control: off the front; 4 of 4 do better.
- **S, how a selection starts:**
  - Dragging down the left column takes 5 actions but clashes with scrolling.
  - A long press takes 7.
  - The long-press menu's Select takes 9.
  - Select as a screen action takes 9, and can be seen at rest.
  - **The control (⚙ › Select) stays on the front:** its separate page is the calmest by edge density.
  - **Coupling:**
    - the selection bar (I) goes with a long press that selects (S): 10 + 7 = 17;
    - the long-press menu (I) goes with its Select (S): 8 + 9 = 17.
    
    The two models tie when taken together.
- **M, a mixed selection:** each action where it applies, with a count, takes 3 actions; only shared actions take 5. Both are on the front. Control (no counts, Done touching two of four silently): off.
- **T, Trash's Pages section:** one group per page takes 7 actions and reads 4 rows before the target, against 9 and 10 for one list. The control loses.
- **Controls still on a front:** A (nearness), C (nearest the references), I (fewest actions), S (calmest page). Each wins one axis and loses the rest.
- **Owner, 2026-10-09:**
  - **H: Undo.** Closing the capture sheet with text not added discards it, with a 7 s Undo toast.
  - **I is rescored with T1.7's label dots drawn on Today**, and the question "can a ⋯ live beside the circle, Log, Open and Add?" is measured:
    - With a ⋯, every row carries two targets. They overlap: the gap is −1 px, since the circle's 48 px target reaches past its drawing. Titles keep 147 px instead of 207.
    - Clutter rises 0.0007, inside the 0.002 tolerance.
    - So the ⋯ crowds the hand, not the eye. Keeping the usual 8 dp between targets would cost about 8 px more of title.
  - Front:
    - long-press menu (8 actions) and element page (12), sum 18.5;
    - ⋯ in the row (24.5);
    - control, still on the front by fewest actions (23.5).
    
    The selection bar is off the front (20).
- **X, which pairing of I and S works together** (owner's question, 2026-10-09; `actions_opt.py x`, from I's and S's measured rows):
  - **Two pairings fail by clash:**
    - a long press can't both open the menu and select (menu + long press);
    - nor both select and open a menu holding Select (selection bar + menu).
  - **The lowest sum is a long press that begins the selection, with the selection bar showing the actions (sum 57):**
    - one model for one element or many;
    - no gesture with two meanings, nothing reached two ways, no clash with scrolling;
    - 17 actions;
    - but nothing at rest shows the way in.
  - **Next:**
    - the element's page with the long-press menu's Select (58);
    - the long-press menu with Select in it (59): 17 actions, but two models, one for one element and one for several.
  - Pairing a ⋯ in the row with a long-press menu reaches the same actions two ways (68).
  - Dragging down the left column saves 2 actions but clashes with scrolling.
  - The control stays on the front, as do 10 of 14: with five axes the Pareto front barely discriminates here, so the sums carry the comparison.

**T1.8, every part decided (owner, 2026-10-09):**
- **I and S:** a long press begins a selection; one element selected shows its actions in the selection bar. Select is also a screen action.
- **M:** each action where it applies, with a count ("✓ 2", "● 4", "🗑 4").
- **N:** the top-right corner holds the Search glyph ⌕, the edit glyph ✎ and the Settings glyph ⚙.
  - ✎ starts a selection (checkboxes appear) and holds the screen's own edits: Sort on Pages and Reminders, Edit home on Today.
- **The selection's actions show in the header**, which reads "n selected" with ✕.
  - The owner's pasted note of a bottom bar for the menu is superseded by this answer.
- **T:** Trash's Pages section is grouped per page. Empty Trash is held, fixed top right.
- **Already decided:**
  - A: anchored;
  - B: 7 s, merged, swiped away, Trash and "Done today" as the way back;
  - C: in place, near, held;
  - D: a card on Today, versions stacked, words;
  - E: asked when first needed;
  - F: a banner;
  - H: discarded with Undo.
- **Data-layer work owed** (inventory draft 4):
  - Restore for items and trackers;
  - Trash for activities, canvas cards, labels and database parts;
  - Delete forever for checklists and charts;
  - labels on tasks, events, reminders and checklists (ADR 08 amendment, schema bump);
  - the archived flag removed;
  - a reminder on a database row;
  - a test of Skip on a standalone reminder;
  - a vocabulary gate test across every kind.

**T1.8 approved (owner, 2026-10-09):** "Approved, add this in the screens HTML file, then proceed in order of dependency."
- The T1.8 section is in `docs/screens/t1/screens.html`, at the top; the separate page is removed.
- To keep the page under the 512 KiB that viewers accept, `tier_t1.fit_size` first shrinks each inlined image to the width it is shown at, then lowers WebP quality in steps. It stopped at quality 20, which is still readable, at 513 KB.
- Next, in order of dependency: the data-layer work the T1.8 vocabulary owes, then T1.9.

**T1.9 empty and error states, the owner's answers (2026-10-09).** The rule from 2026-10-07 stands: one plain sentence and one action, with no illustration, no cheer and no guilt. Failures show a banner under the header (T1.8 F).
- **Scope (all four):**
  - empty screens;
  - screens filtered to nothing (search, a label filter, a selection, a Trash section);
  - errors and their words (banners and field errors);
  - first run and loading.
- **Empty form:** score all four with a control:
  - a sentence and a centred button;
  - a sentence where the first row would be, with the capture line as the action;
  - the capture line's placeholder alone;
  - a sentence and one greyed example row.
- **Today done against Today with nothing planned:** score one sentence against two, with the "Done today" fold kept or not.
- **Axes:**
  - the four axes, as in T1.8;
  - tone, measured: word count, reading grade, and a check for cheer, praise or blame;
  - references captured on the phone and the desktop (placeholder data only);
  - Windows scored too.

**T1.9 scored (2026-10-09)** (`tools/screens/empty_opt.py`, run through toast_opt's tables, now named per tier; `docs/screens/t1/empty-scores.html` and `empty-options.html`).
- **References:** 16 phone apps (`empty-references.json`).
  - Every source app puts a short sentence in the middle, with a small icon; most name the action ("Tap + to add one").
  - Tasks.org, Todoist, MS To Do, Google Tasks and TickTick use illustrations; Google Tasks praises ("Ben fatto!").
  - No app shows a field error, except Loop's "!" inside the field.
  - The desktop references wait: the owner was using the desktop.
- **Tone, measured:** words, a Flesch-Kincaid grade estimate, cheer (a word list, "!" and pictographic emoji) and blame (a word list). The lists are the assumption; they come from the 2026-10-07 rule.
  - A first run counted the interface glyphs ⚙ ✎ ☰ as emoji and the bar's labels as words; both were fixed before these numbers.
- **Empty screens:**
  - Placeholder alone leads (sum 19.5).
  - Then the sentence on a line where rows go (26) and the sentence with a centred button (26.5).
  - The example row is last (30.5).
  - **The control (an illustration with "All clear! 🎉") stays on the front:** its centred button is nearest the thumb (2.61). Every other axis is worst.
- **Today, done or nothing planned:** two sentences with the fold hidden lead (14). Keeping the fold costs a row.
- **Filtered to nothing:**
  - centred with a Clear button: plain 30, repeating the query 31.5;
  - inline forms off the front;
  - the control stays on the front by reach.
- **A field's error:** disabled Save (with its reason on a tap) 20.5; a line under the field 25; silent (Tendril's) 28.
- **The banner's words:** all three real wordings are on the front. "Sync folder unreachable. Changes are kept on this phone." + Fix is the only one that says the data is safe.
- **First run:** straight to an empty Today (0 taps), against one sheet (1 tap) and a tour (3 taps).
- **Loading:** what is already on the device at once (progressive), or skeleton rows. Both cause no layout shift.

**T1.9, the owner's choices (2026-10-09):**
- **Failure banner:** "what": "Sync folder unreachable." with Fix.
- **Today with nothing to show:** "nothing here". One sentence, "Nothing here.", whether everything is done or nothing was planned. The "Done today · n" fold stays, as decision 15 has it, when something was done.
- **Empty screens:** centred: one sentence and one button in the middle.
- **A field's error:** inline: a line under the field.
- **Filtered to nothing:** centred, naming what was looked for ('No pages match "zqxjw".'), with no button: the search field's ✕ or the filter chip clears it.
- **First run:** a three-card tour before Today.
- **Loading:** what is already on this device at once; newer rows slide in.

**The data-layer work the T1.8 vocabulary owed (done 2026-10-09, SPEC v0.39, schema 24):**
- **Commits:**
  - `2261987`: schema 24. Archive dropped (the activity and tracker `archived` columns, `setArchived`, archive in search); checklists carry a label; labels on every item kind; a property's Trash columns.
  - `5162a64`: Restore and Trash listings for items and trackers.
  - `bf35f00`: Trash for activities, labels, canvas cards and a database's properties, options and views.
  - `a322b60`: Delete forever for checklists and charts.
  - `f647d14`: `VocabularyTest`. The gate walks every kind through delete, Trash, restore, delete and purge; a mutant that emptied the charts' Trash listing failed it. It also checks a reminder on a row's task (it already worked) and Skip on a standalone reminder.
  - `0693fd3`: SPEC v0.39, including corrections to §3.7, §3.10 and §3.12, which had become false.
- **Tests:** core 312, data 378 → 390, all passing; the gate was rerun here: 4 of 4.
- **Not done:**
  - an Empty Trash call and a combined Trash listing (each kind has its own);
  - Delete forever for checklist lines;
  - time spans, readings and check-ins are untouched.
- **Open questions** (the agent made the smallest choice for each), in `decisions/17` until the owner answers:
  - restoring a part whose whole is in Trash is refused;
  - restoring a label or option whose name was taken since is refused;
  - the newly labelled kinds get "everything" labels, with no new scopes;
  - a labelled task's tracked time now counts in its label's total;
  - the old purges still accept a live row;
  - a deleted activity's running timer keeps running.

**The owner's answers to the data-layer questions (2026-10-10):**
1. Restoring a part whose whole is in Trash stays refused.
2. Restoring a label or option whose name was taken since stays refused.
3. "The user needs to be able to choose a label, which will be able to tie elements across different screens."
   - Read as: any label can be put on any element, so labels are global.
   - A label's scope (Everything / Activities / Trackers, ADR 08 and the owner's 2026-10-02 answer) is removed from the data layer.
   - The scope row on a label's page leaves the screens: T1.7's label page, and the inventory.
4. "Labels do not have trackers attached to them nor can they amount to a total, aside from how many elements have that label."
   - The label time total (ADR 08, owner 2026-10-02) is removed.
   - A label's only number is the count of what carries it.
