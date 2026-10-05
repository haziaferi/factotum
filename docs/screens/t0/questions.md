# T0 questions: the frame

T0 is asked as one batch (owner, 2026-10-05). Evidence for every question is `docs/screens/t0/compare.html`, which reads from `tokens.json` and the screenshots in `_screens-sources/`. Answers are recorded in `decisions/15-screens.md` and SPEC §10.1.

| # | Question | Evidence | Blocks |
|---|---|---|---|
| Q1 | Are the tiers and their order right? (T0 frame, T1 shared parts, T2 items/calendar/alarms, T3 habits/trackers/time/goals/charts/checklists, T4 check-in/regulation, T5 pages/databases/canvas/journal/templates, T6 search/settings/sync/lock/backup/onboarding/about) | `docs/screens-workflow-prompt.md` | the order of every later tier |
| Q2 | Navigation pattern: Tendril's adaptive bar/rail at 840dp, Chronicle's bottom bar on every width, or Mnemo's single home with tabs | compare.html, Navigation row; tendril/00, chronicle/00, mnemo/01 | the frame mockup; where every later screen lives |
| Q3 | Top-level destinations: which modules get a place in the bar | compare.html, Navigation row (Tendril 5, Chronicle 4, Mnemo 4 tabs, Equipoise 3) | the frame mockup; T2–T6 entry points |
| Q4 | Palette system: Tendril's solved registers (10, contrast-solved at runtime), Chronicle's fixed palettes (6), Mnemo's skins (6, with motifs), or one fixed palette like Equipoise | compare.html, Default and Palette rows; tendril/04, chronicle/03, mnemo/04–09 | every token in every mockup |
| Q5 | Type: Tendril's Inter (with DM Sans and Serif as options), Chronicle's Space Grotesk display over the system face, Mnemo's Fraunces with Atkinson Hyperlegible, or Equipoise's Manrope | compare.html, Type row | every mockup's lettering |
| Q6 | Shapes: Tendril's small radii (4–12), Chronicle's Material 3 steps (4–28), Mnemo's asymmetric per-skin corners, or Material 3 defaults | compare.html, Shapes row | cards, sheets, chips in T1 |
| Q7 | Density: Tendril's three profiles (compact, comfortable, touch) scaled to the screen, Chronicle's width buckets, or none | compare.html, Density row; tendril/04 | row heights and spacing in T1 |
| Q8 | Icons: Material outlined (Tendril), filled when selected (Chronicle), or text-only tabs (Equipoise) | compare.html, Icons row | the navigation and every T1 control |
| Q9 | Wording register: Tendril's terse and exact, Chronicle's friendly-instructive, Mnemo's plain, or Equipoise's gentle second person | compare.html, Wording row | every string from T1 on |
| Q10 | Dark mode: system/light/dark, and whether Tendril's OLED "deeper blacks" comes along | compare.html, Dark mode row | the token set's dark half |
| Q11 | The settings marker for "follows you across devices" (§3.9): a word, an icon, or a section heading | SPEC §3.9; tendril/04 (Tendril has none) | T6 settings; T1 toggle row |

**Measured, for Q4.** These pairs in the source defaults fall below the WCAG minimum:
- Mnemo's primary on its background: 2.0:1 in light and 2.9:1 in dark, where a control needs 3:1.
- Tendril's outline: about 1.2:1 in light and 1.4:1 in dark. Tendril uses it as a hairline divider, not as a control's edge.

Whichever palette is chosen, its values are re-checked when the T1 parts are mocked.
