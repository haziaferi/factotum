# Screen inventory: the draft every navigation option is scored against

This is Step 0 and Step 0.5 of `design-optimization:app-register-layout`.
- **Step 0** groups the content into screens in one pass, from SPEC §2, §3 and §7.
- **Step 0.5** partitions the screens into modules **by purpose, not by topic**.

It is a **draft**: a one-pass grouping catches the obvious clusters and misses what real use would show. Nothing here is decided.
- The owner corrects the module boundaries, the screen list, or both.
- Tone values are placed per module, with a reason, in the tier that builds the module (Q9: one register per cluster).

| Module (purpose) | Screens | Source today | Register (to be placed in its tier) |
|---|---|---|---|
| **M1 Plan and do.** What is due, and when (external commitments, deadlines) | today/agenda; calendar (day, week, month); item editor (task, event, reminder; recurrence; reminders); a series' occurrence editor; ringing alarm (full screen) and missed-alarm list; the planner week (PLANNED, time blocks) | Tendril Calendar, Tasks, PlanView; Mnemo Home and Edit; Chronicle Remind, AlarmActivity | likely the highest tone of the five |
| **M2 Routines and tracking.** Doing things regularly, and seeing them over time (self-paced) | habits (Log, presence, no streak); trackers and readings; tracker detail and charts; saved charts; goals; activities and timers (several at once, the 12 h question); checklists | Tendril Tasks & Habits; Chronicle Track, Data and Charts | mid to low |
| **M3 Check-in and regulation.** Noticing how I am, and what helps (self-care, no judgement) | check-in (mood, energy, pleasantness; no numbers shown); regulate (direction, tools, the outcome at next open); ledger (masking scales); sensory log; burnout notice (a **triggered state**, not a screen) | Equipoise | ambient, plus the triggered state |
| **M4 Pages.** Keeping and finding what I know (reference) | page tree; page (blocks, images, labels); database (table, board and timeline views; formulas; rows as tasks); canvas and mind map; journal (one page per day); templates; links and the Road Map; History and notices | Tendril Pages, Road Map, Canvas | mostly **exempt** (reading and editing panes) |
| **M5 System.** Making the app work (infrastructure) | search (the quick switcher); settings ("On every device" and "On this device"); sync folder and its status; the sync clash question (ADR 01/11); trash; app lock; backup; onboarding; about (llama.cpp MIT notice); label manager | all four apps | **exempt** |

**Cross-module surfaces.** These pull from several modules into one view; the skill's Step 1d, trigger B, keeps each zone in its own module's register.
- **A home or "today"** joins M1 items, M2 habits and timers, and an M3 check-in prompt. Whether it exists at all is a navigation question.
- **Search** reaches every module (§3.10).
- **Labels** cut across M1, M2 and M4 (§3.8).

**Counts that navigation has to carry.**
- About 35 distinct screens and sheets.
- 5 modules.
- 2 form factors: a phone, and Windows at 840dp and up.
- 1 triggered state (burnout).
