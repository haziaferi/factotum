# Factotum spec

Scope: the merged data model, sync and behaviour rules of Factotum, the one app that replaces Tendril, Chronicle, Mnemo and Equipoise. Screens are settled apart, tier by tier (R187); this spec holds only what R187 to R192 record of them.

History: `Factotum SPEC-history.md`, one line per change. It is never a source of current rules.

Kinds: O owner rule · D decided · I inherited · A assumed · Q open.

Standing answers: R05, R06, R07, R08, R09, R20, R81, R198 and R199 hold the owner's standing answers, and every other rule is filtered through them.

Evidence lives in `decisions/`: one ADR per decision, with the verified `file:line` facts, the scored options, the behaviour cases and the harness that measured them (`decisions/register.md` is the index). A rule states its decision once and cites its ADR; it never restates the evidence.

## Rule index

| ID | Name | Section |
|---|---|---|
| D-R01 | Source behaviour survives | 1. Purpose and jobs |
| D-R02 | One home per concept | 1. Purpose and jobs |
| D-R03 | Source defects fixed | 1. Purpose and jobs |
| D-R04 | Jobs and how often | 1. Purpose and jobs |
| D-R05 | Platforms | 2. Scope, platform and build |
| D-R06 | Every sole-owner module moves across | 2. Scope, platform and build |
| D-R07 | Visible choices are the owner's | 2. Scope, platform and build |
| D-R08 | App id and packages | 2. Scope, platform and build |
| O-R09 | Personal use, one signing key | 2. Scope, platform and build |
| I-R10 | Source apps | 2. Scope, platform and build |
| D-R11 | Modules split by layer | 2. Scope, platform and build |
| D-R12 | One write path | 2. Scope, platform and build |
| D-R13 | Corruption guard | 2. Scope, platform and build |
| D-R14 | Committed schema files | 2. Scope, platform and build |
| D-R15 | Upgrades drop the app's triggers first | 2. Scope, platform and build |
| D-R16 | Imports are hybrid and reviewed | 2. Scope, platform and build |
| D-R17 | Licensing | 2. Scope, platform and build |
| D-R18 | Synced tables | 3. Data model |
| D-R19 | Local stores, never synced | 3. Data model |
| D-R20 | Folder sync for one person | 4. Sync |
| D-R21 | Identity and stamps | 4. Sync |
| D-R22 | Group values | 4. Sync |
| D-R23 | When a person is asked | 4. Sync |
| D-R24 | Answers settle the clash everywhere | 4. Sync |
| D-R25 | The clock never goes back | 4. Sync |
| D-R26 | Old versions do not move the base | 4. Sync |
| O-R27 | A permanent purge registry | 4. Sync |
| D-R28 | A purge undone by a later edit | 4. Sync |
| D-R29 | One deletion vocabulary | 4. Sync |
| D-R30 | What Delete and Restore take | 4. Sync |
| D-R31 | Delete forever | 4. Sync |
| D-R32 | The device id | 4. Sync |
| D-R33 | The composition root | 4. Sync |
| D-R34 | Recovery re-reads its own files | 4. Sync |
| D-R35 | Device logs in the folder | 4. Sync |
| D-R36 | Folder requirements | 4. Sync |
| D-R37 | Conflict copies | 4. Sync |
| D-R38 | A local outbox decides what to export | 4. Sync |
| D-R39 | Imports in chunks | 4. Sync |
| D-R40 | Read positions | 4. Sync |
| D-R41 | Lines this version cannot read | 4. Sync |
| D-R42 | A row whose parent has not arrived waits | 4. Sync |
| D-R43 | A deleted row takes its merge state | 4. Sync |
| D-R44 | Tables reach the importer through RowTable | 4. Sync |
| D-R45 | Folder implementations | 4. Sync |
| D-R46 | One item table | 5. Items |
| D-R47 | Names in code | 5. Items |
| D-R48 | Item field groups | 5. Items |
| D-R49 | Kind rules are triggers | 5. Items |
| D-R50 | The completion log | 5. Items |
| D-R51 | Subtasks go with their parent | 5. Items |
| D-R52 | The capacity query | 5. Items |
| D-R53 | Reminders on any item | 6. Reminders |
| D-R54 | Reminder field groups | 6. Reminders |
| D-R55 | Standalone reminders on the day view | 6. Reminders |
| D-R56 | Fire time | 6. Reminders |
| D-R57 | Snooze syncs | 6. Reminders |
| D-R58 | A reminder needs a start date | 6. Reminders |
| D-R59 | A standalone reminder's last reminder | 6. Reminders |
| D-R60 | Alarms and missed occurrences | 6. Reminders |
| D-R61 | A force-stopped app says so | 6. Reminders |
| D-R62 | Recurrence kinds | 7. Recurrence |
| D-R63 | Random forms | 7. Recurrence |
| D-R64 | Seeded random draws | 7. Recurrence |
| D-R65 | DTSTART and set times | 7. Recurrence |
| D-R66 | Times are floating | 7. Recurrence |
| D-R67 | The expander | 7. Recurrence |
| D-R68 | Cron is input only | 7. Recurrence |
| D-R69 | One recurrence engine | 7. Recurrence |
| D-R70 | Reminders on a repeating item | 7. Recurrence |
| D-R71 | The occurrence-edit log | 8. Occurrence edits |
| D-R72 | What each scope reaches | 8. Occurrence edits |
| D-R73 | A clash on one occurrence asks | 8. Occurrence edits |
| D-R74 | Answers are edits | 8. Occurrence edits |
| D-R75 | Series edits | 8. Occurrence edits |
| D-R76 | Habit fields in an edit | 8. Occurrence edits |
| D-R77 | Edits reach reminders | 8. Occurrence edits |
| D-R78 | Every edit is kept | 8. Occurrence edits |
| D-R79 | Trackers move across as they are | 9. Habits and trackers |
| D-R203 | A choice tracker's choices | 9. Habits and trackers |
| D-R80 | A habit is an item over a tracker | 9. Habits and trackers |
| D-R81 | No streaks in Habits | 9. Habits and trackers |
| D-R82 | Presence | 9. Habits and trackers |
| D-R83 | Habit types and Logs | 9. Habits and trackers |
| D-R84 | Deleting a tracker | 9. Habits and trackers |
| D-R85 | Habit columns | 9. Habits and trackers |
| D-R86 | Pause | 9. Habits and trackers |
| D-R87 | Rolling habits | 9. Habits and trackers |
| D-R88 | Logged occurrences are quiet | 9. Habits and trackers |
| D-R89 | Time blocks | 9. Habits and trackers |
| D-R90 | The week planner | 9. Habits and trackers |
| D-R91 | A confirmed week | 9. Habits and trackers |
| D-R92 | PLANNED habits | 9. Habits and trackers |
| D-R93 | Placing an occurrence | 9. Habits and trackers |
| D-R94 | Timed and whole-day occurrences | 9. Habits and trackers |
| D-R95 | An occurrence's block and order | 9. Habits and trackers |
| D-R96 | Reminders on an "n a day" habit | 9. Habits and trackers |
| D-R97 | Activities | 10. Time |
| D-R98 | One span table, several timers | 10. Time |
| D-R99 | Span field groups | 10. Time |
| D-R100 | A span's end is checked where it is written | 10. Time |
| D-R101 | Day totals | 10. Time |
| D-R102 | Time is an activity's: spans and amounts | 10. Time |
| D-R103 | Goals on tracked time | 10. Time |
| D-R104 | Deleting an activity | 10. Time |
| D-R105 | What ends a running timer | 10. Time |
| D-R106 | A timer past its limit asks | 10. Time |
| Q-R107 | An activity's usual length | 10. Time |
| Q-R108 | The limit before any session | 10. Time |
| D-R109 | One label vocabulary | 11. Labels |
| D-R110 | Labels are global | 11. Labels |
| D-R111 | How many labels each element carries | 11. Labels |
| D-R112 | Label names are unique | 11. Labels |
| D-R113 | Same-name labels merge | 11. Labels |
| D-R114 | Label field groups | 11. Labels |
| D-R115 | No foreign key on a label | 11. Labels |
| D-R116 | A label in the Trash | 11. Labels |
| D-R117 | What a label counts | 11. Labels |
| D-R118 | Settings by scope | 12. Settings |
| D-R119 | A typed registry | 12. Settings |
| D-R120 | Setting keys | 12. Settings |
| D-R121 | Where each scope lives | 12. Settings |
| D-R122 | Repositories read settings on every call | 12. Settings |
| D-R123 | The settings part of a backup | 12. Settings |
| D-R124 | One search index | 13. Search |
| D-R125 | What search indexes | 13. Search |
| D-R126 | Kept current by triggers | 13. Search |
| D-R127 | What a search shows | 13. Search |
| D-R128 | Queries | 13. Search |
| D-R129 | One check-in table, mood on its own axis | 14. Check-in and regulation |
| D-R130 | No numbers on the check-in screen | 14. Check-in and regulation |
| D-R131 | A check-in about a past day | 14. Check-in and regulation |
| D-R132 | Check-in field groups | 14. Check-in and regulation |
| D-R133 | Check-in scales | 14. Check-in and regulation |
| D-R134 | Check-in engines | 14. Check-in and regulation |
| D-R135 | The direction engine | 14. Check-in and regulation |
| D-R136 | Outcome at the next open | 14. Check-in and regulation |
| D-R137 | The masking ledger | 14. Check-in and regulation |
| D-R138 | Sensory logs | 14. Check-in and regulation |
| D-R139 | The burnout index | 14. Check-in and regulation |
| D-R140 | Page parts are rows | 15. Pages |
| D-R141 | Page and block field groups | 15. Pages |
| D-R142 | Block order | 15. Pages |
| O-R143 | Later text wins, earlier is kept | 15. Pages |
| D-R144 | The replaced-by-a-sync notice | 15. Pages |
| O-R145 | Revive | 15. Pages |
| D-R146 | The app's own writes are marked | 15. Pages |
| D-R147 | Trash, restore and delete forever for pages | 15. Pages |
| D-R148 | What a merge can leave | 15. Pages |
| D-R149 | Page History | 15. Pages |
| D-R150 | Database tables | 15. Pages |
| D-R151 | Cell values and type changes | 15. Pages |
| D-R152 | A cell is kept when replaced | 15. Pages |
| D-R153 | A property in the Trash | 15. Pages |
| D-R154 | Select options | 15. Pages |
| D-R155 | Renames take the later name | 15. Pages |
| D-R156 | A database's rows | 15. Pages |
| D-R157 | Views | 15. Pages |
| D-R158 | Databases in pages | 15. Pages |
| D-R159 | Formulas and rollups | 15. Pages |
| D-R160 | A formula is checked when written | 15. Pages |
| D-R161 | Where formulas differ from Tendril | 15. Pages |
| D-R162 | Database rows as tasks | 15. Pages |
| D-R163 | A row task's life is its page's | 15. Pages |
| D-R164 | Row-task clashes | 15. Pages |
| D-R165 | Bound columns read the task | 15. Pages |
| D-R166 | Repeating rows and intervals | 15. Pages |
| D-R167 | Rows changed | 15. Pages |
| D-R168 | Pictures in pages | 15. Pages |
| D-R169 | Inserting a picture | 15. Pages |
| D-R170 | Pictures through the folder | 15. Pages |
| D-R171 | Collecting pictures | 15. Pages |
| D-R172 | Canvas tables | 15. Pages |
| D-R173 | Moving cards | 15. Pages |
| D-R174 | Deleting a card | 15. Pages |
| D-R175 | Page cards | 15. Pages |
| D-R176 | Canvas History | 15. Pages |
| D-R177 | The journal | 15. Pages |
| D-R178 | Road Map links | 15. Pages |
| D-R179 | Database relations | 15. Pages |
| D-R180 | Blocked-by | 15. Pages |
| D-R181 | Templates | 15. Pages |
| D-R182 | Copying a template | 15. Pages |
| D-R183 | Checklists | 16. Checklists and charts |
| D-R184 | Deleting a checklist | 16. Checklists and charts |
| D-R185 | Checklist order and text | 16. Checklists and charts |
| D-R186 | Saved charts | 16. Checklists and charts |
| D-R187 | Screens are settled tier by tier | 17. Screens |
| D-R188 | Dark mode | 17. Screens |
| D-R189 | Settings in two sections | 17. Screens |
| D-R190 | Fixed words | 17. Screens |
| Q-R191 | Navigation | 17. Screens |
| Q-R192 | Palette, type, shapes and density | 17. Screens |
| D-R193 | Build order | 18. Phasing and validation |
| D-R194 | Schema slices | 18. Phasing and validation |
| D-R195 | Sole-owner module order | 18. Phasing and validation |
| A-R196 | Triggers on the Android driver | 18. Phasing and validation |
| A-R197 | The search index on the phones | 18. Phasing and validation |
| D-R198 | Importing data from the source apps | Out of scope |
| D-R199 | A sync server, accounts or cloud storage | Out of scope |
| D-R200 | Source mechanisms not carried over | Out of scope |
| D-R201 | Waking a powered-off phone | Out of scope |
| D-R202 | Tendril's Claude text verbs | Out of scope |

## Glossary

| Term | Meaning |
|---|---|
| Source app | One of the four apps Factotum replaces: Tendril, Chronicle, Mnemo, Equipoise (R10) |
| Owner app | A source app that owns a concept being merged, in an ADR's behaviour cases |
| Sole-owner module | A module only one source app has, moved across whole (R06) |
| Item | A row of the `item` table: a task, event, reminder, habit or activity (R46) |
| Kind | An item's `kind`: TASK, EVENT, REMINDER, HABIT or ACTIVITY |
| Occurrence | One date-time of a repeating item, from its rule and its edits |
| Stamp | The `(hlc, device)` pair that orders writes to one field group |
| HLC | Hybrid logical clock: wall time that never goes backwards on one device (R25) |
| ULID | The primary key of every synced row; it begins with its creation time |
| Field group | Columns of a row written and merged together, under one stamp |
| Base stamp | The stamp of the other side's version a device last merged, per group |
| Peer | Another device of the same person, syncing through the same folder |
| Purge | Deleting a row for good; recorded in the purge registry (R27) |
| Trash | Where Delete puts an element until Restore or Delete forever (R29) |
| Revive | Bringing back a trashed page or part because a later edit touches it (R145) |
| Automatic write | A write the app makes itself, stamped from its cause and marked with `~` (R146) |
| Keep-loser group | A field group whose replaced version is kept in History, with a notice (R143) |
| Notice | The synced "replaced by a sync" notice, `page_notice` (R144) |
| Personal day | The day a moment belongs to under the person's day boundary (R120) |
| Tracker | A measured quantity, Chronicle's model (R79) |
| Reading | One value logged on a tracker, `TrackerReading` |
| Log | A reading made by marking a habit; the word on screen (R190) |
| Activity | An item of kind ACTIVITY that holds tracked time (R97) |
| Span | One timed interval on a task, habit or activity, a `time_span` row |
| Amount | Untimed time added to an activity on a picked day (R102) |
| Time block | A part of the day a habit can sit in, a `habit_block` row (R89) |
| Block | A part of a page: a paragraph, heading, image and so on, a `block` row |
| Doorway label | The label whose pages a database counts as rows (R156) |
| Check-in | A mood and energy record, a `check_in` row (R129) |
| Slice | One step of the data-layer build, named after the ADR it builds (R194) |
| Device log | A device's own segments and snapshots under `devices/<device-id>/` (R35) |
| Composition root | `com.hazia.factotum.data.Factotum`, which wires every repository and sync (R33) |

## 1. Purpose and jobs

One app that does what Tendril, Chronicle, Mnemo and Equipoise do, over one data model and one sync folder, so the same idea is never stored twice. It is for one person, on their own phone and computer (R09).

### D-R01 · Source behaviour survives

**Rule:** Every owner app's verified behaviour survives in Factotum, unless a decision records its loss and the owner accepted it.

**Evidence:** Each ADR in `decisions/` lists its owners' behaviour cases and any accepted loss (ADR 05 and ADR 09 were picked against the recommendation, and record what was lost).

**Acceptance:** Every case in `decisions/cases/*.jsonl` passes as a test against the real implementation (R194).

**Since:** 2026-10-01 · unrecorded · migrated

### D-R02 · One home per concept

**Rule:** Each concept has one home: one item table, one recurrence encoding, one label vocabulary, one search index and one sync model.

**Evidence:** R46, R62, R109, R124, R21.

**Acceptance:** The data model (R18) holds one table family per concept, and no second table stores items, rules, labels, search text or sync state.

**Since:** 2026-10-01 · unrecorded · migrated

### D-R03 · Source defects fixed

**Rule:** A defect found in a source app while the decisions were settled is fixed in Factotum, not carried over.

**Evidence:** Each ADR's fixes list in `decisions/`; their behaviour cases encode the fixed behaviour.

**Acceptance:** The ADR cases that encode a fix pass as tests (R194).

**Since:** 2026-10-01 · unrecorded · migrated

### D-R04 · Jobs and how often

**Rule:** Factotum serves the jobs below, as often and on the devices each row says. A job that arrives is pushed to the person (a notification, an alarm, a prompt at the next open), so navigation never carries it; a job that is sought is reached through navigation.

**Values:**

| Job | Covers | How often | Arrives or sought | Device |
|---|---|---|---|---|
| Catch something quickly | quick add from one line, one-tap readings, home-screen widgets | open; a tap or less away | sought, from anywhere | both; widgets phone only |
| See what's next | Today, the calendar's day, week and month | daily; weekly to plan | sought | both; week and month lean to desktop |
| Answer a prompt | alarms, reminders, missed alarms, sync clashes, notices, outcomes, the long-timer ask, burnout notice, app lock | per firing or rare; app lock every open | arrives | both |
| Do it and log it | habits, ticking tasks and occurrences, timers, readings, checklists | daily; several times a day for "n a day" habits and tasks | sought, or from the reminder | habits, readings, checklists phone |
| Check in with myself | check-in, regulation, ledger, sensory log | when something is noticed; the ledger once a day | sought; regulation arrives from the check-in | phone |
| Plan ahead | the item editor, one-occurrence edits, the week planner, time blocks, calendar links | per item; the planner weekly | sought | planner desktop |
| Write and think | journal, pages, canvas | daily, on both devices | sought | both; long writing and canvas lean to desktop |
| Organise and look things up | search, page tree, databases, templates, Road Map, labels | search several times a day | sought | both; tree, databases and Road Map lean to desktop |
| Look back over time | tracker detail, charts, goals, time totals, the stability trend, page History | a weekly review; can sit deeper than the daily jobs | sought | both |
| Look after the app | settings, sync folder, Trash, backup, onboarding, About | rare; onboarding once | sought; onboarding arrives | both |

**Evidence:** `docs/screens/t0/jobs.md` (owner's answers 2026-10-05, decision 15): pages, databases and canvas are daily on both devices; looking back is a weekly review; a check-in happens when something is noticed, not on Equipoise's several-a-day model.

**Acceptance:** The navigation and screens decisions in `decisions/15-screens.md` and later tiers cite this table for every cadence they rely on, and no screen puts a weekly job above a daily one.

**Since:** 2026-11-21 · owner · migrated

## 2. Scope, platform and build

### D-R05 · Platforms

**Rule:** Factotum runs on Android and Windows, as Tendril ships.

**Evidence:** Tendril is the only source app on both: a Kotlin Multiplatform `shared/` module with Room declared in common code (`shared/src/commonMain/kotlin/com/tendril/app/data/TendrilDatabase.kt`), plus `Tendril android/` and `Tendril windows/`. The other three apps are Android-only Kotlin.

**Acceptance:** `:android` and `:windows` build from the repository root (`./gradlew --offline`).

**Since:** 2026-10-01 · owner · migrated

### D-R06 · Every sole-owner module moves across

**Rule:** Every sole-owner module moves across, and no single-app feature is dropped, except Tendril's opt-in Claude text verbs (R202). Each moves as it is, with only R21's identity and sync columns added, unless one of its rules says otherwise. Android widgets, the on-device LLM, a Windows global quick-add and natural-language input where appropriate move across too.

**Values:**

| Module | Owner app | Tables | Rules |
|---|---|---|---|
| Pages and canvas | Tendril | the page tables of R18 | R140 to R182 |
| Trackers and goals | Chronicle | `tracker`, `tracker_choice`, `tracker_reading`, `goal`, `saved_chart`, `chart_source`, `checklist`, `checklist_item` | R79, R183, R186 |
| Regulation | Equipoise | `sensory_log`, `masking_entry`, `regulation_event`, `pending_outcome` | R135 to R139 |
| Time blocks, calendar links | Tendril | `habit_block`, `calendar_link` (device-local) | R89 |

**Evidence:** `docs/sole-owner-probe-2026-10-01.md`; `decisions/14-sole-owner-modules.md`; `decisions/15-screens.md:73` (features that move across, in the owner's words, 2026-10-05). Not checked: widgets, the LLM, the quick-add and natural-language input have no code (they come with the shells and screens).

**Acceptance:** Each module in the table has its rules built and their tests passing; the features in the second sentence each have a screen or entry point once their tier is settled.

**Since:** 2026-10-05 · owner · migrated

### D-R07 · Visible choices are the owner's

**Rule:** Every visible choice is the owner's: layout, wording, navigation and palette are settled with the owner before they are built (R187). So are names that outlive a build.

**Evidence:** Standing practice since 2026-09-30; on 2026-10-05 the owner corrected an app id the skeleton had set without asking (R08).

**Acceptance:** none: a working practice; each screen's approval is recorded in `decisions/` before its tier is built.

**Since:** 2026-10-01 · owner · migrated

### D-R08 · App id and packages

**Rule:** The app id and every package are `com.hazia.factotum`. Builds install with no `.debug` suffix.

**Evidence:** `android/build.gradle.kts:10` (`applicationId = "com.hazia.factotum"`) and its no-suffix note at line 31; the Room schema folder moved unchanged with the rename (f901399).

**Acceptance:** `applicationId` is `com.hazia.factotum` with no suffix, and every Kotlin package starts with `com.hazia.factotum`.

**Not:** `com.factotum`: the skeleton set it without asking, against R07.

**Since:** 2026-10-05 · owner · migrated

### O-R09 · Personal use, one signing key

**Rule:** Factotum is for personal use and never distributed. Every Android build is signed with Tendril's shared debug key (`keystores/my-shared-debug.keystore`, SHA-256 `20:FB:3E:76…`), committed on purpose. No store, release-signing or distribution concerns apply.

**Why:** The key can never change without an uninstall, which loses the app's data.

**Evidence:** `android/build.gradle.kts:21-33` signs every build with that keystore; `.gitignore` keeps it as the one committed keystore. Chronicle's "shared" key (`D0:5A…`) and the PC's `~/.android` key (`74:BF…`) are different keys.

**Acceptance:** The installed APK's signing certificate has SHA-256 starting `20:FB:3E:76`, and every build type uses `signingConfigs.debug`.

**Since:** 2026-10-05 · owner · migrated

### I-R10 · Source apps

**Rule:** The four source apps live under `Downloads/Builds/`, on the platforms and with the concepts each row gives.

**Values:**

| App | Path | Platform | Brings |
|---|---|---|---|
| Tendril | `Tendril/` (`shared/`, `Tendril android/`, `Tendril windows/`) | Android and Windows, Kotlin Multiplatform | calendar items, habits, reminders, check-ins, time logs, labels, pages and canvas |
| Chronicle | `chronicle-native-pending/chronicle-native/` | Android | trackers, goals, charts, activities and sessions, categories, checklists, reminders with alarms |
| Mnemo | `mnemo_pass4/mnemo/` (not git) | Android | reminders: cron and stochastic schedules, nag, modes and skins |
| Equipoise | `Personal assistant project/` | Android | check-in circumplex, regulation, burnout index, on-device LLM, capacity-ranked tasks |

**Since:** 2026-10-01 · unrecorded · migrated

### D-R11 · Modules split by layer

**Rule:** The code is Kotlin Multiplatform, split by layer into the modules below, each depending only on the modules its row names.

**Why:** The owner asked which option scored best for the app's size and data and picked from the front (R11 is option C).

**Values:**

| Module | Holds | Depends on |
|---|---|---|
| `:core` | pure common Kotlin with no Room: ULID, HLC, the field-group merge, the recurrence expander and seeded draw, occurrence edits, presence, the page-part merge | nothing |
| `:data` | the one Room database with every entity and DAO, the triggers, the corruption guard, the repositories and the sync importer | `:core` |
| `:llm` | llama.cpp with the build switches of R17 | nothing |
| `:ui` | shared Compose, once the screens are settled (R187) | `:data`, `:core` |
| `:android`, `:windows` | the app shells | all of the above |

**Evidence:** Measured 2026-10-01: the source apps hold 40.7k data and logic lines, 51.0k UI lines and 51 Room entities; Tendril's `shared` module alone has 55.4k main lines. `settings.gradle.kts` includes `:core`, `:data`, `:android` and `:windows`. Not checked: `:llm` and `:ui` do not exist yet; `:llm` is created when Equipoise's LLM code lands.

**Acceptance:** `:core` has no Room dependency, `:data` depends only on `:core`, and the build passes (`./gradlew --offline`).

**Not:** A, one `shared` module as Tendril has: on the front with C, but every engine edit recompiles everything and reruns Room's code generation. B, split by feature: dominated by C, since the hub tables (sync stamps, search triggers, labels, habit to tracker) would cross module lines. D, Android first: fails R05.

**Since:** 2026-10-01 · owner · migrated

### D-R12 · One write path

**Rule:** Every local write goes through one repository layer in `:data`, as one transaction through the same staged merge as an import, which stamps the groups it changes and saves the clock with them; answers to a pending question go the same way. DAOs are `internal`, so only `:data` writes rows. The sync importer is the only code that writes remote rows, applying R21's merge per field group and R140's per-row rule for page parts.

**Evidence:** `LocalWrites.kt` (every repository writes through it); `ItemRepository.kt`. The search index stays correct even on a path that bypasses the layer, through its triggers (R126).

**Acceptance:** Every DAO in `:data` is `internal`, and the two-device tests through the composition root (R33) pass.

**Since:** 2026-10-02 · builder · migrated

### D-R13 · Corruption guard

**Rule:** Both database drivers carry a guard that keeps a corrupt database file instead of deleting it, recovering only from `SQLITE_CORRUPT` and `SQLITE_NOTADB`. A locked or full database is rethrown, and its file left in place. The guard moves the `-journal`, `-wal` and `-shm` files with the database.

**Why:** Room's corruption handler deletes the database file before any recovery code runs.

**Evidence:** All three syncing source apps guard against it: Tendril with `shared/src/androidMain/.../KeepFileOnCorruptionDriver.kt` (the starting point, already KMP), Chronicle and Mnemo each with a `DatabaseRecovery.kt`. The guard is wired into Room's open path (slice 01).

**Acceptance:** `KeepFileOnCorruptionDriverTest` and `BundledDriverCorruptionTest` cover the two drivers, with a control showing that the stock Android driver deletes a corrupt file; `DatabaseRecoveryTest` checks the order of build, probe and set-aside.

**Since:** 2026-10-01 · builder · migrated

### D-R14 · Committed schema files

**Rule:** A committed Room schema file never changes; `tools/schema_check.py` fails when one differs from HEAD.

**Why:** A KSP build run before `SCHEMA_VERSION` was raised rewrote the committed schema file, so the next AutoMigration skipped columns; an upgrade test built from that same file cannot catch it.

**Acceptance:** `tools/schema_check.py` passes.

**Since:** 2026-10-04 · builder · migrated

### D-R15 · Upgrades drop the app's triggers first

**Rule:** Before Room upgrades an older database file, the app drops its own triggers, which it makes again on every open.

**Why:** A Room upgrade that rebuilds a table dies when SQLite checks every trigger at the rename: the span rule, which names `item`, stopped the upgrade that added the label columns.

**Acceptance:** A test upgrades a version 9 file holding the triggers and its child rows (`OldSchema.kt`).

**Since:** 2026-10-02 · builder · migrated

### D-R16 · Imports are hybrid and reviewed

**Rule:** Self-contained units of the source apps are ported, then cleaned; code bound to the old schemas is rewritten against this spec, reading the source only for behaviour. Every import passes, in order, `code-verification-core`, `/code-review`, `/simplify` and a sweep that removes AI slop before it is committed.

**Values:**

| Ported as units | From |
|---|---|
| `KeepFileOnCorruptionDriver` | Tendril |
| `HabitPresence` | Chronicle |
| the seeded draw | the spike's Java (R64) |
| the RRULE expander | Tendril's `RecurrenceSpec` (R67) |

**Evidence:** AI slop here means comments that restate the code, dead branches, speculative generality and invented APIs.

**Acceptance:** none: a working practice, checked in review rather than in code.

**Since:** 2026-10-01 · owner · migrated

### D-R17 · Licensing

**Rule:** The four source apps are the owner's own. Of Equipoise's vendored `third_party/llama.cpp`, only the MIT-licensed `llama` and `ggml` are built, with `common` and `tools` off, on Android and on Windows. Factotum shows llama.cpp's MIT notice in the app.

**Evidence:** Spike 6 (`docs/spikes-2026-10-01.md`): the vendored extras aren't linked. Not checked: no `:llm` build and no About screen exist yet.

**Acceptance:** The `:llm` build links only `llama` and `ggml` on both platforms, and the About screen shows llama.cpp's MIT notice.

**Since:** 2026-10-01 · builder · migrated

## 3. Data model

### D-R18 · Synced tables

**Rule:** Every synced table carries R21's columns: a ULID id, a stamp per field group, and `deleted_at` in the group that decides whether the row exists. The synced tables are those below, each in the area whose rules own it.

**Values:**

| Area | Tables | Rules |
|---|---|---|
| Items | `item` (TASK, EVENT, REMINDER, HABIT, ACTIVITY), `completion`, `reminder`, `occurrence_edit`, `time_span` | R46, R53, R71, R98 |
| Trackers | `tracker`, `tracker_choice`, `tracker_reading`, `goal`, `saved_chart`, `chart_source` | R79, R186, R203 |
| Check-in and regulation | `check_in`, `sensory_log`, `masking_entry`, `regulation_event` | R129, R135 |
| Pages | `page`, `block`, `page_database`, `property`, `property_option`, `property_value`, `value_pick`, `page_view`, `page_canvas`, `canvas_node`, `canvas_edge`, `page_relation`, `relation_link` | R140, R150, R172, R178, R179 |
| Labels | `label`, `page_label` | R109 |
| Page notices | `page_notice` | R144 |
| Other | `checklist`, `checklist_item`, `habit_block`, `setting` (PERSONAL keys only), `purge_registry` | R183, R89, R121, R27 |

**Evidence:** `FolderSyncTest.everySyncedTableIsQueuedForExportAndRoundTrips` kills mutant `a synced table with no export trigger` (`tools/mutants.py`, slice `gapA`), 2026-11-21. The test makes its `tracker_choice` row with `TrackerRepository.addChoice` (R203).

**Acceptance:** `FactotumDatabase.kt:222` checks at open that every synced table has its `RowTable`, and `FolderSyncTest.everySyncedTableIsQueuedForExportAndRoundTrips` makes a row in every synced table, finds each table in the outbox, and reads the same rows on a peer after sync.

**Since:** 2026-11-25 · builder · migrated

### D-R19 · Local stores, never synced

**Rule:** The stores below stay on their device and are never exported to the folder.

**Values:**

| Store | Holds | Rules |
|---|---|---|
| `page_revision`, `sync_lost` | a page's History and the versions a merge replaced | R149, R143 |
| `calendar_link` | links to external calendars | R06 |
| `pending_outcome` | the regulation outcome this device still owes | R136 |
| `search_fts`, `search_key` | the search index | R124 |
| `sync_waiting` | imported lines whose parent has not arrived | R42 |
| `clock` | the HLC's high-water mark | R25 |
| `device_setting` | DEVICE_PREF and DEVICE_STATE keys | R121 |
| the secret store | SECRET keys, in the Keystore or DPAPI | R121 |
| the device id file | this device's identity | R32 |

**Acceptance:** No export trigger names a store in this table, and a peer that imports a device's folder never receives one of them.

**Since:** 2026-10-04 · builder · migrated

## 4. Sync

### D-R20 · Folder sync for one person

**Rule:** One person syncs several devices through one folder they choose, with no server. Factotum is not compatible with the source apps' sync files.

**Acceptance:** `FolderSyncTest` syncs two devices through a shared folder and nothing else.

**Since:** 2026-09-30 · owner · migrated

### D-R21 · Identity and stamps

**Rule:** Every synced row has a ULID primary key and one `(hlc, deviceId)` stamp per field group; the whole row is one group unless its rule names more. `deleted_at` sits in the group that decides whether the row exists. A `Row` names its table, and ids stay unique across tables.

**Why:** The three syncing source apps disagree on identity, deletion and conflict: Tendril's purge registry never expires, Chronicle garbage-collects tombstones after 90 days, and Mnemo raises a conflict on any `updatedAt` difference.

**Evidence:** ADR 01 (`decisions/01-sync.md`), hybrid+; `tools/sync_sim.py` is the reference model. The merge engine is in `:core` (`com.hazia.factotum.core.sync`) behind a `SyncStore` interface; `tools/mutants.py 01` shows each rule is needed.

**Acceptance:** The 10 cases of `decisions/cases/01-sync.jsonl` pass as tests on both targets (`SyncCasesTest`): 8 hold and 2 ask a person, as hybrid+ scored.

**Since:** 2026-10-01 · owner · migrated

### D-R22 · Group values

**Rule:** A group value is a String, Long, Boolean, finite Double or null. Clashes compare values with `==`.

**Why:** 5 and 5L would otherwise differ; NaN never equals itself, and JSON cannot carry it.

**Evidence:** Decoding goes through `Group` (`Row.kt:17`); `RecordCodecTest.aLineCarryingANaNOrAnInfiniteDoubleIsRefused` kills mutant `a group takes an infinite Double` (`tools/mutants.py`, slice `gapA`), 2026-11-21.

**Acceptance:** `RecordCodecTest.aLineThatIsNotARecordIsRefused` refuses a value of another type, `ClockAndIdTest.aGroupRefusesADoubleThatNeverEqualsItself` a NaN, and `RecordCodecTest.aLineCarryingANaNOrAnInfiniteDoubleIsRefused` a line carrying NaN or an infinite Double.

**Since:** 2026-11-21 · builder · migrated

### D-R23 · When a person is asked

**Rule:** A person is asked (keep mine, take theirs, keep both) only when an item's schedule group changed on both sides since its base stamp, or an occurrence clashes (R73). Everything else merges silently.

**Evidence:** ADR 01; ADR 02 assigns the schedule group (R48).

**Acceptance:** The two asking cases of `decisions/cases/01-sync.jsonl` ask, and the other eight merge without a question (`SyncCasesTest`).

**Since:** 2026-10-01 · owner · migrated

### D-R24 · Answers settle the clash everywhere

**Rule:** An answered group carries `settles`, the other side's stamp the answer saw, and it syncs, so the other device that was asked takes the answer instead of asking again. Each answer does what its row says. Two devices that answer differently are asked again, as both sides changed the schedule since their base.

**Values:**

| Answer | Effect |
|---|---|
| Keep mine | re-stamps the local group; its base becomes the stamp it settled, so a later edit on the other side is asked again |
| Take theirs | adopts their group, stamp and all |
| Keep both | keeps mine, and makes their version a new row with a new ULID |

**Evidence:** Each asking group carries one more synced `(hlc, device)` pair.

**Acceptance:** `ResolutionTest` checks each answer, and `FolderSyncTest.anAnswerSettlesTheQuestionOnBothDevices` an answer settling the question on both devices.

**Since:** 2026-10-01 · builder · migrated

### D-R25 · The clock never goes back

**Rule:** The clock resumes from its stored high-water mark (table `clock`), so a wall clock set backwards cannot reissue an older stamp. Each write saves the clock in the same transaction.

**Acceptance:** `ClockAndIdTest` sets the wall clock back and gets a newer stamp.

**Since:** 2026-10-02 · builder · migrated

### D-R26 · Old versions do not move the base

**Rule:** A version no newer than the base is ignored, and a pending question is not replaced by an older replay of the other side's version.

**Why:** A device log replays old versions. Merging one moved the base up to this device's own newer stamp, so the other side's next change looked uncontested and replaced this device's change without asking; the in-memory cases never replay, so only the folder tests found it.

**Acceptance:** Replaying an older version of the other side through the folder leaves the base and any pending question as they were, and the next change on the other side is still asked.

**Since:** 2026-10-02 · builder · migrated

### O-R27 · A permanent purge registry

**Rule:** A purge is recorded in one `purge_registry` table that never expires. An import re-checks only the registry entries it added or lowered, and the registry is looked up by id (`SyncStore.purge(id)`), never loaded whole; only a snapshot reads all of it.

**Why:** A device away longer than any expiry would bring a purged row back, as Chronicle's 90-day collection does. The registry never shrinks, so it is read by id.

**Evidence:** ADR 01; the lookup by id is `StagedStore.kt:151`. `FolderSyncTest.anImportTouchingOnePurgedIdReadsOneRegistryRow` counts the rows read through the driver (`RegistryReads`) and kills mutant `the registry loaded whole` (`tools/mutants.py`, slice `gapA`), 2026-11-21. The import skips a purge it holds at the same or an earlier stamp (`Merge.kt:66`); `FolderSyncTest.aPurgeAlreadyHeldChangesNothingAndAnEarlierOneLowersIt` kills mutants `a held purge is re-checked` and `a held purge is never lowered` (slice `gapA`), 2026-11-24.

**Acceptance:** The purge case of `decisions/cases/01-sync.jsonl` passes (`SyncCasesTest.tendrilPurgeHolds`), `FolderSyncTest.anImportTouchingOnePurgedIdReadsOneRegistryRow` reads one registry row for an import touching one of 30 purged ids, and `FolderSyncTest.aPurgeAlreadyHeldChangesNothingAndAnEarlierOneLowersIt` imports a purge already held, at its stamp and at a later one, with nothing changed, and an earlier one that lowers the entry.

**Since:** 2026-11-24 · owner · agreed rewording

### D-R28 · A purge undone by a later edit

**Rule:** An import that takes back a purge clears the read positions and reads every folder file again from its start, this device's own included. The merge takes what it holds without change, and the rows under the purged one come back.

**Why:** ADR 01 lets a row edited after its purge come back, but the device that purged it also lost, through foreign-key cascades, the rows under it (a page's blocks, a database's schema and cells, a canvas's cards, a task's completions); the peer that edited keeps them and never sends them again, since they did not change.

**Evidence:** Found by the slice 12c review.

**Acceptance:** After a purge is undone by a peer's later edit, both devices hold the same rows under the revived one.

**Since:** 2026-10-03 · builder · migrated

### D-R29 · One deletion vocabulary

**Rule:** Every kind that can be deleted has the same verbs: Delete moves it to the Trash, Restore brings it back, Delete forever purges it from the Trash only, and Empty Trash purges everything in the Trash. The Trash keeps everything until Delete forever.

**Values:**

| Kinds | Rules |
|---|---|
| tasks, events, standalone reminders, habits, trackers, activities | R51, R59, R84, R104 |
| checklists | R183 |
| pages, databases and their rows | R147, R156 |
| a database's properties, options and views | R153, R154, R157 |
| canvas cards and frames | R174 |
| labels | R116 |
| charts | R186 |

**Evidence:** `docs/screens/t1/actions-inventory.md` draft 4 (owner, 2026-10-09).

**Acceptance:** `VocabularyTest` walks every kind through Delete, its Trash, Restore, Delete again and Delete forever; a kind missing one does not compile or fails.

**Not:** Archive: dropped, since the Trash keeps everything until Delete forever.

**Since:** 2026-10-09 · owner · migrated

### D-R30 · What Delete and Restore take

**Rule:** Delete sets `deleted_at` in the existence group, and what the deletion takes with it shares its one stamp. Restore is an edit with a new stamp: it brings back what that one stamp took, and nothing deleted by hand before. A part waits for its whole: a subtask for its parent, a habit for its tracker.

**Values:**

| Deleted | Takes with it |
|---|---|
| a task | its subtasks |
| a standalone reminder | its reminders |
| a tracker | its habits and goals |
| an activity | its spans and goals |
| a canvas card | its frames and lines |
| a relation column | its pair |

**Acceptance:** `VocabularyTest` restores each kind and checks that exactly what its deletion took comes back.

**Since:** 2026-10-09 · owner · migrated

### D-R31 · Delete forever

**Rule:** Delete forever is the purge of R27, and it travels; what hangs off a row by a foreign key goes with it. Delete forever refuses a live row, for every kind. A purge from a peer is the import's own and applies to a row live here too.

**Acceptance:** `VocabularyTest` checks that Delete forever of a live row of each kind is refused.

**Since:** 2026-10-10 · owner · migrated

### D-R32 · The device id

**Rule:** The device id lives in its own file, written atomically, and is not a setting. An unreadable file is set aside and a new id made. The file is excluded from Android Auto Backup and device transfer, so two devices never share an identity.

**Evidence:** ADR 09; ADR 13 requirement 5 (`decisions/verify/13-folder/workload.md`). Not checked: the Auto Backup exclusion needs the Android shell, which has no code. `android/src/main/AndroidManifest.xml` declares no backup rules.

**Acceptance:** `SyncStorageTest.anUnreadableDeviceIdIsSetAsideAndReplaced` sets an unreadable id file aside and makes a new id; the Android manifest's backup rules exclude the file.

**Since:** 2026-10-01 · builder · migrated

### D-R33 · The composition root

**Rule:** `com.hazia.factotum.data.Factotum` builds every repository over one database and sync over one folder, and runs the after-import rules in the order below. It publishes pictures before an export and fetches them after an import (R170), and offers `rowsChanged()` (R167).

**Values:**

| Order | After-import rule |
|---|---|
| 1 | labels merge (R113) |
| 2 | finished timers end (R105) |
| 3 | row-task clashes settle (R164) |
| 4 | pages keep their replaced text and revive (R143, R145) |
| 5 | options and cards settle (R154, R174) |
| 6 | rows' tasks follow (R163) |

**Acceptance:** Every two-device test runs through `Factotum` (`World.Device` delegates to it).

**Since:** 2026-10-04 · builder · migrated

### D-R34 · Recovery re-reads its own files

**Rule:** A database made anew after a corrupt one was set aside reads this device's own folder files on its first import, so its data and settings come back with no peer. Its DEVICE settings go back to their defaults.

**Evidence:** ADR 09; `FolderSync` takes `recovered=true` after a recovery, and `DatabaseRecoveryTest` checks the recovery order. `SettingsCasesTest.aRecoveredDeviceGetsItsRowsBackFromItsOwnFilesAndItsDeviceSettingsStartAtTheirDefaults` kills mutant `a recovery reads only peers` (`tools/mutants.py`, slice `gapA`), 2026-11-21.

**Acceptance:** `SettingsCasesTest.aDeviceWhoseDatabaseWasRecoveredGetsItsSettingsBackFromItsOwnFiles` recovers a device alone and finds its PERSONAL settings again, and `aRecoveredDeviceGetsItsRowsBackFromItsOwnFilesAndItsDeviceSettingsStartAtTheirDefaults` finds its rows again and its DEVICE settings at their defaults.

**Since:** 2026-11-21 · builder · migrated

### D-R35 · Device logs in the folder

**Rule:** Each device writes only under `devices/<device-id>/`, so ordinary use makes no conflict copies. An export appends the versions written since the last export, including versions imported from peers, to log segments, and every few segments the device writes a snapshot and deletes its older segments, with the values below. Every folder write replaces the whole file atomically (R36).

**Why:** With ADR 01's merge every layout that delivers every version is lossless, so the layouts differ in cost and risk. At one year of data, rewriting each device's whole state costs hundreds of MB of writes a day (Chronicle's snapshot 900 MB/day, Tendril's per-area files 411 MB/day); shared files produce conflict copies and lose a wiped device's losing edit; one file per row passes Android's 10,000-file slowdown within a year.

**Values:**

| Parameter | Value |
|---|---|
| segment | `log-<seq>.jsonl`, up to 16 KiB |
| snapshot | `snapshot-<seq>.jsonl`, one record per line, every 64 segments |
| export delay | 30 s after the last local write |

**Evidence:** ADR 13 (`decisions/13-folder.md`): the simulator `tools/folder_sim.py`, a reviewed model and the scores. `FolderSync` in `com.hazia.factotum.data.sync`; `tools/mutants.py 13` shows each rule is needed.

**Acceptance:** The 4 cases of `decisions/cases/13-folder.jsonl` pass through the real importer and exporter under a Syncthing double (`FolderSyncTest`).

**Not:** `snapshot.json`, ADR 13's name: the sequence number in the name tells a reader a snapshot is new without opening it.

**Since:** 2026-10-01 · owner · migrated

### D-R36 · Folder requirements

**Rule:** Whatever is synced, the folder meets the five requirements below.

**Values:**

| Requirement | Detail | Rules |
|---|---|---|
| Firing a reminder writes nothing that syncs | fire bookkeeping is device state; occurrences come from the rule | R56 |
| Exports are debounced | the database may be written on every keystroke | R35 |
| Every folder write is an atomic replace | temp file, then rename; where Android's SAF cannot, the reader tolerates a torn file | R40 |
| Synced files are compact JSON | never pretty-printed | R35 |
| The device-id file is excluded from Android Auto Backup and device transfer | two devices never share an identity | R32 |

**Evidence:** `decisions/verify/13-folder/workload.md`. `firings()` only reads; `FolderSyncTest.aReminderFiringLeavesTheOutboxEmpty` kills mutant `a firing writes its reminder` (`tools/mutants.py`, slice `gapA`), 2026-11-21. Not checked: `exportAfterQuiet` has no production caller (R38), and the Auto Backup exclusion is not built: `android/src/main/AndroidManifest.xml` holds an empty `<application />` (checked 2026-11-24).

**Acceptance:** `ExportTimingTest.aBurstOfWritesExportsOnceThirtySecondsAfterTheLast` (debounce), `DirectorySyncFolderTest.aReplaceLandsWholeAndLeavesNoTemporaryFile` (atomic replace), `RecordCodecTest.aRecordIsOneCompactLine` (compact JSON) and `FolderSyncTest.aReminderFiringLeavesTheOutboxEmpty` (a firing writes nothing) pass. In each shell, every export starts through `exportAfterQuiet` (R38), with no other production call to the export. The Android manifest's `dataExtractionRules` and `fullBackupContent` both exclude the device-id file (R32).

**Since:** 2026-11-24 · owner · agreed rewording

### D-R37 · Conflict copies

**Rule:** Readers merge, then delete, any `.sync-conflict-` copy. A copy in a device's own folder also makes it re-read its own files, because the side that won the clash is not its own writing, and leaves it owing a new id, held in its database from before the copy is deleted until the device runs under another id. The shell then writes a new id and builds the data layer again over the same database and folder, and the first export under the new id is a snapshot of everything the device holds.

**Why:** A conflict copy in a device's own folder means a cloned device id, and only a new id for one of the two devices ends the clashes. The debt is held, not only reported, so stopping between the clash and the new id cannot lose it once the copy is gone. The snapshot is needed because what the device wrote under its old id is in no file a peer reads: the clone's writing won the clash, and the copy is deleted.

**Values:**

| Step | Where |
|---|---|
| The debt, one local row of the device id given up | `sync_id_owed` (`IdOwedEntity`, Schema 26) |
| Held before any copy in its own folder is deleted | `FolderSync.kt:99` |
| Asked by the shell at start and after each import | `Factotum.newIdOwed` (`FolderSync.kt:84`): owed only while the row names this device's id |
| A new id, moved over the old file in one step | `renewDeviceId` (`DeviceId.kt:39`) |
| The first export under another id: a snapshot of everything, then the debt cleared | `FolderSync.kt:256`, `publishAllUnderNewId` |

**Evidence:** The data layer is built as in Values (2026-11-25). Not checked: no shell exists yet to ask `newIdOwed`, renew and build again, so the test does that step by hand.

**Acceptance:** `FolderSyncTest.aClonedDeviceIdsClashIsMergedAndTheCopyRemoved` merges and deletes a conflict copy. `FolderSyncTest.aClonedIdIsOwedANewOneUntilTheDeviceRunsUnderAnother`: after one in its own folder the device owes a new id across imports; built again under a new id it owes none, its folder starts with a snapshot, and the clone and a third device hold every row with no further clash. `FolderSyncTest.aClonedIdIsOwedBeforeItsConflictCopyIsDeleted`: an import stopped at the copy's delete leaves the debt held. `SyncStorageTest.anOwedIdOutlivesAReopen` and `SyncStorageTest.aRenewedDeviceIdReplacesTheOldOneForGood` cover the debt and the id file. Each shell asks `newIdOwed` at start and after each import and, while owed, renews and builds again.

**Not:** Factotum swapping its own id, clock and sync in place: every repository's writer would need a replaceable clock. Only reporting the clash: a stop before the new id would forget it until the next clash.

**Since:** 2026-11-25 · owner · agreed rewording

### D-R38 · A local outbox decides what to export

**Rule:** Every local write, and every import that changes a row, queues the row in a local outbox. Triggers on every synced table and on the purge registry queue it, so no write path can forget the outbox. The export starts from the queue through `exportAfterQuiet`.

**Evidence:** Not checked: starting the export from the queue needs the app's process wiring.

**Acceptance:** A write through any repository, and an import that changes a row, each leave the row queued for export.

**Not:** A stamp cursor: a version imported from a peer can carry an older stamp than anything this device has exported.

**Since:** 2026-10-02 · builder · migrated

### D-R39 · Imports in chunks

**Rule:** An import commits in chunks of at most 2,000 lines, each one transaction holding the merge, the read position it reached and the clock. What a chunk can touch is loaded first, merged in memory by the synchronous merge in `:core`, and written back.

**Why:** A peer's 16 MB snapshot then neither fills memory nor holds the write lock for long, and a crash only means the rest is read again.

**Acceptance:** `FolderSyncTest` imports a snapshot larger than one chunk and stops and resumes it at a chunk boundary.

**Since:** 2026-10-01 · builder · migrated

### D-R40 · Read positions

**Rule:** Read positions are per file, in bytes, and local to the device. A peer file is read only once it has grown, a last line with no newline is left for a later read, and a file that shrank (a torn SAF write) is read again from the start.

**Evidence:** `FolderSync.kt:103` reads a shorter file from its start; `FolderSyncTest.aFileThatShrankIsReadAgainFromTheStart` kills mutant `a shrunk file read from the old position` (`tools/mutants.py`, slice `gapA`), 2026-11-21.

**Acceptance:** `FolderSyncTest.aPeerFileIsReadOnlyWhenItHasGrown`, `aLineStillBeingWrittenWaitsForItsNewline` and `aFileThatShrankIsReadAgainFromTheStart` pass.

**Since:** 2026-11-24 · owner · agreed rewording

### D-R41 · Lines this version cannot read

**Rule:** A line this version cannot read, or a row that does not fit its table (missing groups, wrong value types), is skipped. When the set of synced tables changes in an upgrade, the read positions are dropped and every peer file is read once more. A line the database refuses is applied again one line at a time; one refused with its parents present is dropped and counted as skipped, never kept waiting.

**Why:** Peers' snapshots and segments hold their whole state, so a record for a table this version lacked is applied after the upgrade, and nothing skipped is lost.

**Acceptance:** `FolderSyncTest` skips an unreadable line, applies it after the table set changes, and drops a line that breaks its table's rules.

**Since:** 2026-10-02 · builder · migrated

### D-R42 · A row whose parent has not arrived waits

**Rule:** Each table names the parents a row needs (`RowTable.parents`); before a chunk is applied, a line whose parent is neither here nor in the chunk is kept once in `sync_waiting`. After every import the waiting lines whose parents have arrived are applied, and a line whose parent was purged is dropped. Foreign keys are deferred, and a snapshot lists parents first.

**Why:** Sync gives no order between files, so a subtask or a completion can arrive before its parent; a purge of the parent already meant the cascade.

**Acceptance:** A completion imported before its item waits, then applies once the item arrives; one whose item was purged is dropped.

**Since:** 2026-10-02 · builder · migrated

### D-R43 · A deleted row takes its merge state

**Rule:** A trigger clears a deleted row's local merge state (its base and pending questions), whether the merge removed it or a foreign key's cascade did.

**Acceptance:** Purging a row with a pending question leaves no base or question behind.

**Since:** 2026-10-02 · builder · migrated

### D-R44 · Tables reach the importer through RowTable

**Rule:** Each synced table reaches the importer through one `RowTable`. A snapshot is written while paging `RowTable.all()`, without holding every row at once.

**Evidence:** Not checked: paging `RowTable.all()` is not built.

**Acceptance:** Every synced table of R18 has its `RowTable`, and a snapshot of a large table is written with bounded memory.

**Since:** 2026-10-01 · builder · migrated

### D-R45 · Folder implementations

**Rule:** The folder is `DirectorySyncFolder` on Windows and in app storage. A SAF folder on Android's shared storage comes with the Android shell.

**Evidence:** Not checked: the SAF folder is not built.

**Acceptance:** `DirectorySyncFolderTest` passes; the SAF folder passes the same tests on a device.

**Since:** 2026-10-01 · builder · migrated

## 5. Items

### D-R46 · One item table

**Rule:** Tasks, events, standalone reminders, habits and activities are rows of one `item` table, told apart by `kind`: TASK, EVENT, REMINDER (R53), HABIT (R80) and ACTIVITY (R97). Rules keep each kind's columns on that kind.

**Evidence:** ADR 02 (`decisions/02-task.md`); `com.hazia.factotum.data.item`.

**Acceptance:** The 9 cases of `decisions/cases/02-task.jsonl` pass as tests against the real database: eight in `ItemCasesTest`, and `tendril-reminder-fk` in `ReminderCasesTest`.

**Since:** 2026-10-02 · owner · migrated

### D-R47 · Names in code

**Rule:** The code calls a row of `item` an `Item`, and Chronicle's logged value a `TrackerReading`. Nothing is called "Entry".

**Evidence:** ADR 02. Chronicle's `EntryEntity` became `tracker_reading`.

**Acceptance:** No class, table or column in `core/` or `data/` is named Entry.

**Since:** 2026-10-01 · owner · migrated

### D-R48 · Item field groups

**Rule:** An item's columns merge in the four groups below, and only the schedule group asks a person on a clash (R23). Every other group merges silently, the later write standing.

**Values:**

| Group | Columns | On a clash | Rules |
|---|---|---|---|
| schedule | dates, times, `due_date`, `deleted_at`, recurrence, `pause_from`, `pause_until`, `duration_min` | asks | R62, R85 |
| status | `status`, `importance`, `capacity_rank` | merges silently | R52 |
| details | `kind`, `title`, `parent_id`, `tracker_id`, `block_id`, `icon`, `color`, `sort_order` | merges silently | R85, R97 |
| labelled | `label_id` | merges silently | R111 |

**Evidence:** ADR 02 names schedule and status; the details group was the builder's, confirmed by the owner on 2026-11-24. Columns checked against `ItemTables.kt:48` on 2026-11-24. `FolderSyncTest.theDetailsAndStatusGroupsChangedOnTwoDevicesMergeWithNoQuestion` kills mutant `details and status ask` (`tools/mutants.py`, slice `gapA`), 2026-11-21.

**Acceptance:** `FolderSyncTest.anAnswerSettlesTheQuestionOnBothDevices` asks for a schedule clash, and `theDetailsAndStatusGroupsChangedOnTwoDevicesMergeWithNoQuestion` merges the details and status groups changed on two devices with no question, the later write standing.

**Not:** Keeping a replaced item title in History with a notice, as a page title is kept (R143): the owner chose the silent merge on 2026-11-24. Asking a person on a title clash: a question for a rare, small clash.

**Since:** 2026-11-24 · owner · agreed rewording

### D-R49 · Kind rules are triggers

**Rule:** The rules that keep each kind's columns on its kind are BEFORE INSERT and BEFORE UPDATE triggers (`SchemaTriggers`) that refuse a row breaking them; a missing value breaks a rule, as the rules sit in `COALESCE`, so a task with no status is refused. They are dropped and made again on every open, so an upgrade never keeps an old body.

**Why:** Room cannot declare a CHECK constraint.

**Acceptance:** `ItemCasesTest.sharedEventHasNoTaskState_theDatabaseRefusesIt` and `theKindRulesHoldAfterAReopen` (updates), `PlannerCasesTest.plannedAndBlockRulesHold` (inserts), `HabitCasesTest.aTaskWithoutAStatusIsRefused`, `ReminderCasesTest.aStandaloneReminderNeedsATime` and `TimeCasesTest.activitiesKeepTheirOrderAndTheirColumnsStayTheirs` pass.

**Since:** 2026-10-02 · builder · migrated

### D-R50 · The completion log

**Rule:** Resolving an occurrence writes a `completion` row, DONE or SKIPPED, naming the occurrence by its date-time (the series' own, or an added one's), so two occurrences on one day are resolved apart. Two devices resolving one occurrence leave two rows, and reads take the later stamp per occurrence.

**Evidence:** Reads take the later stamp in `ItemRepository.kt:216`; `FolderSyncTest.oneOccurrenceResolvedOnTwoDevicesReadsOneResultTheLater` kills mutant `the earlier completion read` (`tools/mutants.py`, slice `gapA`), 2026-11-21.

**Acceptance:** `FolderSyncTest.oneOccurrenceResolvedOnTwoDevicesReadsOneResultTheLater` resolves one occurrence on two devices, keeps two log rows and reads one result, the later.

**Not:** A unique key per occurrence: the second device's row would fail to import.

**Since:** 2026-11-24 · owner · agreed rewording

### D-R51 · Subtasks go with their parent

**Rule:** Deleting a parent deletes its subtasks, in the same stamp (R30). Deleting it forever removes them through the foreign key, with the parent's completions.

**Acceptance:** `ItemCasesTest` and `VocabularyTest` delete, restore and purge a parent with subtasks.

**Since:** 2026-10-02 · builder · migrated

### D-R52 · The capacity query

**Rule:** Equipoise's capacity-ranked query uses the index `item_kind_date` and never scans the `item` table.

**Evidence:** Checked from the query plan (2026-10-01).

**Acceptance:** The query plan of the capacity query names `item_kind_date` and no table scan.

**Since:** 2026-10-02 · builder · migrated

## 6. Reminders

### D-R53 · Reminders on any item

**Rule:** Reminder rows hang off any item, and a standalone reminder is an item of kind REMINDER. A reminder row carries `alert_kind` (NOTIFICATION or ALARM), nag count and duration, sound, vibration, mode, skin and `exact`.

**Evidence:** ADR 03 (`decisions/03-reminder.md`); `com.hazia.factotum.data.reminder`.

**Acceptance:** The 11 cases of `decisions/cases/03-reminder.jsonl` pass: ten in `ReminderCasesTest`, and `chronicle-standalone-repeats` in `RecurringItemTest`, where `shared-one-recurrence-home` is also checked across every synced table.

**Since:** 2026-10-01 · owner · migrated

### D-R54 · Reminder field groups

**Rule:** A reminder row has two groups, neither of which asks a person: `alert` (the offset, anchor, alert settings and `deleted_at`) and `status` (only the snooze, `snoozed_until` and `snoozed_from`). Retiming a standalone reminder is a change to its item's schedule, which does ask.

**Acceptance:** `FolderSyncTest.aSnoozeOnOneDeviceAndAnAlertChangeOnAnotherBothStayWithoutAQuestion` passes.

**Since:** 2026-10-02 · builder · migrated

### D-R55 · Standalone reminders on the day view

**Rule:** Standalone reminders show on the day view only while the DEVICE_PREF setting `show_reminders_on_day` is on, and it is off by default. The day query takes it from its caller, with no default of its own.

**Evidence:** ADR 03; ADR 09 (owner answer 2026-10-02: DEVICE_PREF).

**Acceptance:** `ReminderCasesTest` reads the day with the setting off and on.

**Since:** 2026-10-02 · owner · migrated

### D-R56 · Fire time

**Rule:** A reminder fires on its item's start date, at the start time (else the reminder's anchor, else midnight), moved by its offset in wall-clock minutes. A reminder is quiet once its item is done, skipped or deleted. Computing firings writes nothing; which firings have rung is device state, kept by the shells.

**Values:**

| Case | Fires at |
|---|---|
| five minutes before 14:00 | 13:55 on any day, whatever the time zone does |
| a repeating item | R70 |
| an "n a day" habit | R96 |
| an edited occurrence | R77 |

**Evidence:** Not checked: the record of rung firings is not built; it comes with the Android and Windows shells.

**Acceptance:** `ReminderCasesTest` computes fire times across a DST change and after an item is done, skipped and deleted, and a firing writes no synced row.

**Since:** 2026-10-02 · builder · migrated

### D-R57 · Snooze syncs

**Rule:** A snooze is stored as `snoozed_until` in the reminder's status group, and it syncs. It holds for the firing it snoozed and never overwrites the next occurrence or changes the item's schedule; once the item is rescheduled or the reminder retimed, the reminder fires at its new time.

**Evidence:** ADR 03; Mnemo's reminders behave the same when a reschedule replaces the next fire.

**Acceptance:** `ReminderCasesTest` snoozes on one device, reads the snooze on the other, then reschedules and gets the new time.

**Since:** 2026-10-02 · owner · migrated

### D-R58 · A reminder needs a start date

**Rule:** The repository refuses a reminder on an item with no start date, taking the start date away from an item with live reminders, and adding a reminder to a deleted item. A synced reminder whose item lost its date on another device is kept, and does not fire.

**Acceptance:** `ReminderCasesTest` is refused in each of the three cases and keeps the synced reminder silent.

**Not:** A trigger: it would drop a synced reminder whose item lost its date on another device.

**Since:** 2026-10-02 · owner · migrated

### D-R59 · A standalone reminder's last reminder

**Rule:** Deleting a standalone reminder's last reminder deletes its item, which would otherwise sit unseen, never firing. "Keep both" on a clash over a standalone reminder copies its reminders onto the new item, so both times fire.

**Acceptance:** `ReminderCasesTest` deletes the last reminder and keeps both on a clash.

**Since:** 2026-10-02 · builder · migrated

### D-R60 · Alarms and missed occurrences

**Rule:** Each kind of alert rings and is caught up as its row says on each platform.

**Values:**

| Platform | ALARM | NOTIFICATION | A missed one |
|---|---|---|---|
| Android | held by the OS through `setAlarmClock`; rings even while the app is dead | fires at its time | an ALARM rings; a NOTIFICATION fires once, late, then continues |
| Windows | the app lives in the tray; a toast keeps ringing, as its nag settings say, until dismissed | not ruled on | an ALARM missed while the app was not running is shown once at the next start, since nothing holds an alarm then |

**Evidence:** ADR 04; owner's answer 2026-10-04 for Windows, as Tendril's desktop does. Not checked: both shells' alarm code is not built.

**Acceptance:** On each platform an alarm set before the app is closed rings (Android) or is shown at the next start (Windows), and a missed NOTIFICATION fires once.

**Since:** 2026-10-04 · owner · migrated

### D-R61 · A force-stopped app says so

**Rule:** On the next start after a force-stop, the app detects that the OS cancelled its alarms and says so.

**Why:** A force-stopped app loses its alarms until it is next opened; this is a platform limit, not a defect.

**Evidence:** Spike 5 (`docs/spikes-2026-10-01.md`). Not checked: detection needs the Android shell and a device.

**Acceptance:** On a device, force-stopping the app and opening it again shows the notice, and the alarms are set again.

**Since:** 2026-10-02 · owner · migrated

## 7. Recurrence

### D-R62 · Recurrence kinds

**Rule:** An item's recurrence is stored on `item`, in its schedule group, as one of the kinds below. A clashing rule change asks a person (R23), and triggers tie each kind to its columns and require a start date.

**Values:**

| `recurrence_kind` | Meaning | Rules |
|---|---|---|
| RRULE | an RFC 5545 rule, read strictly | R67 |
| RULE_SET | several rules as one, such as several set times a day | R65 |
| RANDOM_DAYS | random days, drawn per R64 | R63 |
| RANDOM_WINDOW | a random time in a window | R63 |
| RANDOM_TIMES | several drawn times a day | R63 |
| RANDOM_GAPS | random gaps between occurrences | R63 |
| PLANNED | a habit laid out by the planner | R92 |
| ROLLING | due a period after the last Log | R87 |

**Evidence:** ADR 04 (`decisions/04-recurrence.md`), rrule+ext; `com.hazia.factotum.core.recurrence`.

**Acceptance:** The 11 cases of `decisions/cases/04-recurrence.jsonl` pass (`RecurrenceCasesTest`): the 9 fixed rules match, occurrence by occurrence, the truth `tools/recurrence_sim.py` computes from the owner apps' rules (written as a fixture by `tools/recurrence_fixtures.py`), Mnemo's three through the cron converter.

**Since:** 2026-10-08 · owner · migrated

### D-R63 · Random forms

**Rule:** The When sheet's random forms are kinds of their own, with the columns below, and each takes an end, `rec_until` (inclusive) or `rec_count`. "For n days" is an until: the last moment of the n-th day. The plain forms RANDOM_WINDOW and RANDOM_DAYS keep their draws.

**Why:** A version that cannot read a new form leaves the row waiting, instead of reading it as an old kind and dropping what it does not know.

**Values:**

| Kind | Draws |
|---|---|
| RANDOM_TIMES | `window_count` times a day, one in each equal part of the window, which may run past midnight |
| RANDOM_GAPS | gaps counted in `rand_unit`, minutes to months, with an optional window for the time; minutes and hours need one |

**Evidence:** Decision 17 (owner, 2026-10-08); schema 23.

**Acceptance:** `RandomKindsTest` and `WhenKindsTest` pass.

**Since:** 2026-10-08 · owner · migrated

### D-R64 · Seeded random draws

**Rule:** A random draw is seeded with FNV-1a 64 of `itemId|occurrenceDate|kind` and drawn with SplitMix64, cut at the spike's bound, so every device computes the same time and nothing drawn is stored. A drawn time in a DST gap moves forward by the gap.

**Evidence:** Spike 4 (`docs/spikes-2026-10-01.md`): the draws are identical across 18 Kotlin versions and 4 time zones, and both generators pass a uniformity test; Chronicle's seed made two items draw in lockstep 1000/1000 times, the item-keyed seed does not. `SeededDraw.kt`.

**Acceptance:** `RecurrenceCasesTest` compares the draws with the spike's own SplitMix64 in Python and in its Java, and checks the random kinds' properties.

**Since:** 2026-10-02 · owner · migrated

### D-R65 · DTSTART and set times

**Rule:** DTSTART is the first date the rule's own anchor allows, on or after the active start, and it is an occurrence only when it matches the rule. Several set times a day are a RULE_SET. Month ends anchor to the original date.

**Why:** Unlike RFC 5545, a DTSTART that does not match is no occurrence: a converted cron rule starts at midnight, which must not ring.

**Evidence:** Spike 2: all 8 RRULE-form rules match once DTSTART is aligned and set times use a RULE_SET.

**Acceptance:** `RecurrenceCasesTest.theNineFixedRulesGiveTheOwnerAppsOccurrences` and `aStartTheRuleDoesNotMatchIsNotAnOccurrence` cover an unaligned start, a cron rule from midnight and a month end, and `CronTest.severalLinesAreOneRuleTheirUnion` a rule set.

**Since:** 2026-10-02 · owner · migrated

### D-R66 · Times are floating

**Rule:** Every time in Factotum is a floating local date-time, and an `UNTIL` with a `Z` is read as local like every other time. Turning a time into an instant, with the DST-gap rule of R64, belongs to the shells' alarm code.

**Evidence:** `RRule.kt:57` takes the optional `Z`.

**Acceptance:** `RecurrenceCasesTest.anUntilEndingInZIsReadAsLocal_SPEC_R66` reads an `UNTIL` ending in `Z` as the same local time without it, and expands it to that day.

**Since:** 2026-11-21 · builder · migrated

### D-R67 · The expander

**Rule:** The expander is Tendril's `RecurrenceSpec`, ported and extended to local date-times, `MINUTELY`, `HOURLY`, `BYHOUR`, `BYMINUTE`, `BYSETPOS` and `UNTIL` to the second. It is strict: a rule with a part it lacks, or one that would mislead, is refused, never half-read. A minutely or hourly rule skips the days its limits exclude, so a rare one costs no more than a frequent one.

**Values:**

| Refused | Why |
|---|---|
| a part the expander lacks | half-reading it would make wrong occurrences |
| YEARLY day selection without `BYMONTH` | not implemented |
| `BYMONTHDAY` under WEEKLY | it would mislead |
| a day no listed month has | it would mislead |
| an INTERVAL over 10,000 | it would mislead |

**Evidence:** Porting found a bug in the original: a YEARLY period began at the start's month, so a `BYMONTH` earlier in the year was missed in the last year of a window.

**Acceptance:** `RecurrenceCasesTest` and the expander's ported tests refuse each row's rule and pass the fixed rules.

**Since:** 2026-10-02 · builder · migrated

### D-R68 · Cron is input only

**Rule:** Raw cron is accepted as input, converted to a rule, and never stored. Beyond Mnemo's five numeric fields it takes names (`MON`, `JAN`), `L` (the last day; `FRIL`, the last Friday), `#` (`TUE#2`, the second Tuesday) and several lines as one rule, their union. `W`, `?`, seconds and years are refused.

**Evidence:** Decision 17 (owner, 2026-10-08).

**Acceptance:** `CronTest` passes.

**Since:** 2026-10-08 · owner · migrated

### D-R69 · One recurrence engine

**Rule:** Recurrence expansion is one engine for every item kind, and it reads `occurrence_edit` (R71).

**Acceptance:** Tasks, events, reminders and habits all expand through `com.hazia.factotum.core.recurrence`, with no second expander in `core/` or `data/`.

**Since:** 2026-10-01 · unrecorded · migrated

### D-R70 · Reminders on a repeating item

**Rule:** A reminder on a repeating item fires at its next occurrence after a given moment that the completion log has not resolved; the search starts at the beginning of the day before that moment, earlier by a positive offset. A whole-day item's reminder fires at the reminder's anchor, unless its rule sets times (`BYHOUR`, a random window, cron). A rule this version cannot read, from a newer peer, silences only its own item's reminders.

**Why:** A whole-day occurrence sits at midnight and fires hours later; a search starting at the given moment missed the rest of a day for a reminder set before its anchor (fixed 2026-10-02).

**Acceptance:** `RecurringItemTest` passes, including a whole-day item reminded before its anchor after a firing has passed.

**Since:** 2026-10-02 · builder · migrated

## 8. Occurrence edits

### D-R71 · The occurrence-edit log

**Rule:** Every repeating item has one insert-once `occurrence_edit` log, with the scopes OCCURRENCE, DAY, WEEK, FROM and EXTRA. An edit's `changes` holds only the fields it sets, and edits apply in stamp order, field by field. A move is one OCCURRENCE edit with `moved_to`.

**Evidence:** ADR 11 (`decisions/11-occurrence-edits.md`); the engine in `com.hazia.factotum.core.recurrence` (`OccurrenceEdits.kt`), the log in `com.hazia.factotum.data.item`.

**Acceptance:** The 10 cases of `decisions/cases/11-occurrence-edits.jsonl` pass on the engine (`OccurrenceEditsTest`, with `tools/occurrence_sim.py`'s fixture) and across two syncing devices (`OccurrenceEditSyncTest`).

**Not:** Tendril's Entry exception columns and `HabitScheduleEdit`: replaced by this log.

**Since:** 2026-10-01 · owner · migrated

### D-R72 · What each scope reaches

**Rule:** An OCCURRENCE edit names the series' own date-time; DAY, WEEK and FROM reach occurrences where they are at that point, moved and added ones too. A new pattern for a day or week is a FROM edit with `week_days` or a rule, which repeats the item differently from its date, starting afresh there; each day follows the latest-created pattern dated on or before it. An added occurrence is keyed by its edit, so it never replaces the series' occurrence at the same time.

**Evidence:** Tendril's split series and its "weekly" move behave the same.

**Acceptance:** `OccurrenceEditsTest` applies each scope over moved and added occurrences, as `tools/occurrence_sim.py` does.

**Since:** 2026-10-02 · builder · migrated

### D-R73 · A clash on one occurrence asks

**Rule:** Two live OCCURRENCE or FROM edits on one place, from two devices, neither having seen the other, that set a same schedule field to different values make a question, until an edit that has seen both settles it. The clash is computed from the ids of the edits on the same place each author had seen, live or undone, never stored.

**Evidence:** ADR 11 (owner answer 2026-10-01: a same-occurrence clash asks, like ADR 01).

**Acceptance:** `OccurrenceEditSyncTest` makes the clash on two devices and a third that saw only one, and asks exactly once.

**Not:** A base stamp, as ADR 11 said: one stamp cannot tell that a third device never saw an edit.

**Since:** 2026-10-02 · owner · migrated

### D-R74 · Answers are edits

**Rule:** An answer is a new edit that has seen both: keeping one re-sets its schedule fields, while the other's title still merges, and keeping both (one occurrence only) also adds an occurrence where the earlier edit had put it, under an id made from that edit, so two devices keeping both make one. Two devices answering differently make two corrections that clash in turn. A trigger refuses any change to an edit but the one undo.

**Acceptance:** `OccurrenceEditSyncTest` answers each way, answers differently on two devices, and is refused an update.

**Since:** 2026-10-02 · builder · migrated

### D-R75 · Series edits

**Rule:** Renaming a series renames its moved occurrences. Tasks gain "this week" and "from now on" edits.

**Evidence:** ADR 11.

**Acceptance:** `OccurrenceEditsTest` renames a series with a moved occurrence.

**Since:** 2026-10-01 · owner · migrated

### D-R76 · Habit fields in an edit

**Rule:** An edit's `block` field is read and merges silently (R95). The habit fields `sort_order`, `rule_patch` and `pause` stay in `changes` as raw JSON, as written, so nothing a newer peer wrote is lost on a round trip.

**Why:** Factotum edits a rule with a FROM edit and pauses on the item.

**Acceptance:** An edit carrying `sort_order`, `rule_patch` and `pause` round-trips through the folder unchanged.

**Since:** 2026-10-02 · builder · migrated

### D-R77 · Edits reach reminders

**Rule:** Reminders fire on the edited occurrences: a skipped one is quiet, a moved or retimed one fires at its new time, and an added occurrence on a whole-day item fires at the anchor unless it was given a time.

**Acceptance:** `OccurrenceEditSyncTest.aSkippedOccurrenceDoesNotFireAndAMovedOneFiresAtItsNewTime`, `anAddedOccurrenceOnAWholeDayItemFiresAtTheAnchor`, `aRetimedOccurrenceFiresAtItsNewTimeWithoutBeingMoved` and `anAddedOccurrenceGivenATimeOnAWholeDayItemFiresAtThatTime` pass.

**Since:** 2026-11-21 · builder · migrated

### D-R78 · Every edit is kept

**Rule:** Every occurrence edit is kept, however old, so past days keep showing what happened. A policy for the log's growth waits for a measurement that it has grown too large.

**Acceptance:** none: nothing deletes an edit, and a test of a growth policy waits for that measurement.

**Since:** 2026-10-04 · owner · migrated

## 9. Habits and trackers

### D-R79 · Trackers move across as they are

**Rule:** Chronicle's trackers move across as they are, in `tracker`, `tracker_choice`, `tracker_reading` and `goal`, one field group per row, as Chronicle stamps whole rows. Their domain rules are triggers, listed below. A reading's time is a floating local date-time (R66), and a tracker's category is a label (R111).

**Values:**

| Domain rule | Kept by |
|---|---|
| one value per reading | trigger |
| a rating from 1 to 5 | trigger |
| a unit only on a number tracker | trigger |
| a CHOICE tracker has no default | trigger |

**Evidence:** `TrackerRepository.kt:21` (`TrackerType`: NUMBER, BOOLEAN, RATING, CHOICE); `com.hazia.factotum.data.tracker`; the triggers are in `SchemaTriggers.kt`.

**Acceptance:** `HabitCasesTest.trackerAndReadingRulesHold` refuses a row breaking each rule: a reading with two values or none, a rating of 0 or 6 on a reading or a default, a unit on a yes/no or rating tracker, and a default of any kind on a CHOICE tracker.

**Since:** 2026-11-21 · builder · migrated

### D-R203 · A choice tracker's choices

**Rule:** A CHOICE tracker's choices are added, renamed, recoloured, moved, deleted to the Trash, restored and deleted forever as a database's Select options are (R154), each name taken once per tracker, ignoring case; unlike a deleted option, which reads as none, a deleted choice still reads on the Logs that picked it. A Log picks a live choice of its own tracker and keeps the id it picked, read through merges. After every import, a choice in the Trash comes back when a device that had not seen its delete Logged it, or a choice merged into it, after the delete, and live choices a sync left with one name merge into the lowest id, the one made first.

**Why:** A CHOICE tracker had no way to get its choices, and one person's choices are a list they reorder and prune like any Select.

**Values:**

| Case | What happens |
|---|---|
| a name a live choice of the tracker has, ignoring case | refused on add, rename and restore |
| a choice on a trashed tracker or one that is not CHOICE | refused |
| a move | writes the moved choice only, between its neighbours' places; all are renumbered only when no place is left between two |
| a deleted choice | leaves the list, and a device that has seen the delete refuses a new Log of it; the Logs that picked it still read it |
| a Log of a trashed choice, or of a choice merged into it, by hand, on a device that had not seen the delete, stamped after it | the choice comes back, stamped automatically from its delete |
| two live choices of one tracker and one name after a sync | the one with the higher id goes, `merged_into` the first, stamped automatically; its Logs read as the first |
| a merged choice | not in the Trash, so neither restored nor deleted forever; a new Log naming it picks the choice it went into |
| a choice deleted forever | the purge travels; its Logs keep its id, which names no choice from then on |

**Evidence:** `TrackerRepository.kt` (`addChoice` to `settleChoices`), run after each import by `Factotum.kt`; `merged_into` added in Schema 27. A choice is one field group (R79), so a rename and a move of one choice on two devices keep the later of the two. Owner's answers 2026-11-25: the Select options' set of writes, and duplicates merge into the first.

**Acceptance:** `TrackerChoicesTest` adds, renames, recolours and moves choices and refuses a taken name, a blank one and a choice on a NUMBER tracker, and on a trashed tracker until its restore; refuses a Log of a deleted choice or another tracker's; restores and deletes forever from the Trash, with Logs keeping the id; merges two choices of one name made on two devices into the first on both, refuses to restore or delete forever the merged one, and Logs it as the first; brings back a choice Logged after its delete, directly or through a choice merged into it, but not one Logged before it or Logged and undone; keeps a rename made elsewhere when a move lands; and renumbers when a move falls between two tied places.

**Not:** Merging duplicates by rewriting the Logs' `choice_id`: every device would write the Logs again, and a Log keeps the id it picked. Keeping both duplicates: the owner chose the merge (2026-11-25). Reading a deleted choice as none on its Logs, as a deleted option reads (R154): a Log records what was picked then, and without its choice it would hold no value.

**Since:** 2026-11-25 · owner · agreed rewording

### D-R80 · A habit is an item over a tracker

**Rule:** A habit is an item of kind HABIT with a required `tracker_id`, and Logging it is a reading on that tracker. A habit and its tracker are made in one write, or the habit uses an existing tracker and shares its Logs, which belong to the tracker. Deleting a habit leaves the tracker and its Logs.

**Evidence:** ADR 06 (`decisions/06-habit.md`); owner's answers 2026-10-02; `HabitRepository` in `com.hazia.factotum.data.item`.

**Acceptance:** The 8 cases of `decisions/cases/06-habit.jsonl` pass (`HabitCasesTest`), with the owner's answers.

**Since:** 2026-10-02 · owner · migrated

### D-R81 · No streaks in Habits

**Rule:** Inside Habits, nothing stores or shows a streak, a chain or a missed-day count. Nothing outside Habits inherits the rule.

**Evidence:** `decisions/06-habit.md` records it as the owner's rule of 2026-09-30, citing the source constraint `0.14`. `HabitPresence.kt:46` keeps no count of misses.

**Acceptance:** No table or column stores a streak or missed-day count, and presence (R82) returns none.

**Not:** Tendril's stored streak columns and its `show_habit_streaks` setting: not carried over.

**Since:** 2026-09-30 · owner · migrated

### D-R82 · Presence

**Rule:** A habit's presence is derived as in `HabitPresence`: the days this month, the last date, and the usual time, withheld below 3. Presence counts a "yes", any rating and a number above 0, and a number habit shows today's and this month's amounts. A choice tracker has no presence.

**Evidence:** ADR 06; owner's answer 2026-10-02; `HabitPresence` ported from Chronicle.

**Acceptance:** `HabitPresenceTest` and `HabitCasesTest` pass.

**Since:** 2026-10-02 · owner · migrated

### D-R83 · Habit types and Logs

**Rule:** A habit is a yes/no, rating or number habit, and a Log must be of its tracker's kind. A Log with no value is a "yes", or the habit's amount per Log, which is the tracker's default value. A number habit's daily amount is Chronicle's recurring, automatic DAY goal, one per tracker.

**Acceptance:** `HabitCasesTest` Logs a number habit with and without a value, a rating habit (refused without one) and a yes/no habit without one, and `aYesNoHabitLoggedWithAnExplicitValueKeepsIt` keeps an explicit no and an explicit yes.

**Since:** 2026-11-21 · builder · migrated

### D-R84 · Deleting a tracker

**Rule:** Deleting a tracker deletes its habits and goals; a purge takes its goals too, which name it without a foreign key. A habit another device made on it meanwhile reads as deleted. Undo takes the Log made last.

**Evidence:** Owner's answer 2026-10-02 (a habit whose tracker is deleted goes with it).

**Acceptance:** `HabitCasesTest` and `VocabularyTest` delete, restore and purge a tracker with habits and goals.

**Since:** 2026-10-02 · owner · migrated

### D-R85 · Habit columns

**Rule:** A habit's own columns sit in the item groups below.

**Values:**

| Column | Group |
|---|---|
| `tracker_id`, `block_id` | details (a block merges silently) |
| `pause_from`, `pause_until` | schedule |
| `duration_min` | schedule |
| `roll_every`, `roll_unit` | schedule |
| `plan_n`, `plan_per`, `plan_days`, `plan_blocks` | schedule (R92) |

**Evidence:** Spike 2: the planner needs `block_id` (the habit's default time block) and `duration_min`. `RecurrenceColumns` is embedded in `ItemEntity`.

**Acceptance:** `HabitCasesTest.habitColumnsChangedOnTwoDevicesAskOnlyForTheSchedule` changes a details column on two devices with no question, then a schedule column on two devices with one.

**Since:** 2026-11-21 · builder · migrated

### D-R86 · Pause

**Rule:** A habit pauses with `pause_from` and `pause_until`; no `pause_until` means until resumed, as in Tendril. Pause is kept per habit, and goes by the personal day.

**Evidence:** Found in slice 06b: habits sharing a tracker shared one pause, as their state was keyed by tracker.

**Acceptance:** `PlannerCasesTest.twoHabitsOnOneTrackerPauseOnTheirOwn` passes.

**Since:** 2026-10-02 · owner · migrated

### D-R87 · Rolling habits

**Rule:** A rolling habit ("due again N days after the last Log", Tendril's default) has the recurrence kind ROLLING. It falls due a period after the day of its last Log that counts as presence, or at its start before any, and stays due every day until a Log. A month is a calendar month.

**Evidence:** Owner's answer 2026-10-02.

**Acceptance:** `HabitCasesTest` rolls a habit by days and by a month.

**Not:** Tendril's 30-day month.

**Since:** 2026-10-02 · owner · migrated

### D-R88 · Logged occurrences are quiet

**Rule:** A Log naming an occurrence silences that one. A Log naming none silences the first other occurrence of its personal day, so one dose of three leaves two. Logs go by the personal day.

**Acceptance:** `HabitCasesTest.aLogNamingNoOccurrenceQuietsOnlyOneOfTheDays` Logs one dose of three, the other two still fire that day, and the next day's first fires as usual.

**Since:** 2026-11-21 · builder · migrated

### D-R89 · Time blocks

**Rule:** Time blocks are Tendril's rows in `habit_block`, one group each, with a block's weekday times in its own text (`SAT,SUN@480-630`). The five defaults are written when a database is made or upgraded to blocks, under fixed ids and one fixed stamp, so two devices hold the same five and any real edit is newer. A habit names its block without a foreign key, so a deleted block leaves its habits at any time of day.

**Evidence:** `com.hazia.factotum.core.plan`, ported from Tendril's `CalendarSchedule.kt`; the 7 to 8 `AutoMigrationSpec` seeds the defaults.

**Acceptance:** `PlannerCasesTest` makes a database on two devices and finds the same five blocks.

**Since:** 2026-10-02 · builder · migrated

### D-R90 · The week planner

**Rule:** Each habit's occurrences come from the expander with the occurrence edits applied, less its paused days; the planner only places them and suggests. The load a suggestion balances is the week after its edits, and each day follows the rule in force on it, the item's own or one a FROM edit set.

**Evidence:** Tendril's planner tests that still apply pass (`PlannerTest`).

**Acceptance:** `PlannerTest` and `PlannerCasesTest` pass.

**Not:** Tendril's planner counted the week before its edits.

**Since:** 2026-10-02 · builder · migrated

### D-R91 · A confirmed week

**Rule:** A confirmed week is laid out before the other edits, so every DAY, WEEK and FROM edit reaches its days whenever it was written, and a moved or added entry in that week stays. Confirmed days count only from the habit's start and on its own days. The days suggested leave out paused and skipped ones.

**Acceptance:** `PlannerCasesTest` confirms a week, then applies an earlier skip and a later time, and both reach it.

**Not:** Clearing whatever was in the week on confirmation (slice 11's rule).

**Since:** 2026-10-02 · builder · migrated

### D-R92 · PLANNED habits

**Rule:** PLANNED is `plan_n`, `plan_per` (DAY or WEEK), `plan_days` and `plan_blocks`, on a HABIT only. "n a day" has no set time: the i-th occurrence of a day is at i seconds past midnight, an ordinal no real time uses, and it sits in the block it names or is spread evenly over the blocks in their order. "n a week" places nothing until a WEEK edit confirms the week's days; until then the planner suggests them as Tendril does (evenly spaced, rotated to keep the busiest day lightest, then the load even), each habit on the load the earlier ones left.

**Evidence:** Spike 2: PLANNED round-trips to Tendril's plans on 500/500 random weeks.

**Acceptance:** `PlannerTest` and `PlannerCasesTest` pass.

**Since:** 2026-10-02 · owner · migrated

### D-R93 · Placing an occurrence

**Rule:** An occurrence goes in the first block that applies, in the order below. Blocks that overlap on a day are reported. With every block deleted, "n a day" occurrences are at any time, and still exist to be Logged.

**Values:**

| Order | Block |
|---|---|
| 1 | a set time: the block holding it (start in, end out), else outside every block, kept and shown |
| 2 | the block an edit gave the occurrence, or none |
| 3 | its slot's block |
| 4 | the habit's block |

**Acceptance:** `PlannerCasesTest` (a set time in a block, an edit's block, a slot's block) and `PlannerTest` (a set time outside every block, the habit's block, `overlappingBlocksAreReportedOncePerOverlappingPair`) pass.

**Not:** Tendril placed no "n a day" occurrence once every block was deleted.

**Since:** 2026-10-02 · builder · migrated

### D-R94 · Timed and whole-day occurrences

**Rule:** The personal day of a whole-day occurrence is its own date; only a timed one moves to the day before when the day starts after midnight. An occurrence is timed when the item has a set time, its day's rule sets a time, or an edit gave it one, and this one rule serves the planner, pause, Logs and reminders.

**Evidence:** Not checked: the planner's placement and a Log of a timed occurrence before the day start.

**Acceptance:** `PlannerCasesTest.aWholeDayOccurrenceIsPausedOnItsOwnDateWhenTheDayStartsLater` and `aTimedOccurrenceBeforeTheDayStartBelongsToTheDayBefore` (a pause and its reminder read an occurrence before the day start as the day before's) pass.

**Since:** 2026-11-21 · builder · migrated

### D-R95 · An occurrence's block and order

**Rule:** An occurrence's block is ADR 11's `block` field, read and merged silently. An occurrence keeps its habit's manual order: `sort_order` on the item, then the item.

**Evidence:** `block` is outside an edit's schedule fields (`OccurrenceEdits.kt:34`).

**Acceptance:** `OccurrenceEditSyncTest.anOccurrencesBlockMovedOnTwoDevicesMergesWithoutAQuestion` moves an occurrence's block on one device while the other retimes it, and moves another's block on both, with no question and one result on both devices; `PlannerTest.habitsInABlockFollowTheirManualOrderThenTheirId` passes.

**Since:** 2026-11-21 · builder · migrated

### D-R96 · Reminders on an "n a day" habit

**Rule:** A reminder on an "n a day" habit fires once per unlogged occurrence, at the start of its block that day (weekday times included), moved by the reminder's offset. An occurrence with no block left fires at the reminder's anchor. The next firing is the earliest due, not the next occurrence's, as blocks need not follow the occurrences' order.

**Evidence:** Owner's answer 2026-10-02. Tendril gave such habits no reminder at all.

**Acceptance:** `PlannerCasesTest` fires each occurrence at its block's start and an unblocked one at the anchor.

**Since:** 2026-10-02 · owner · migrated

## 10. Time

### D-R97 · Activities

**Rule:** An activity is an item of kind ACTIVITY, with no dates and optionally an icon and a colour. An activity or a habit has a manual `sort_order`, fractional as Tendril's, in the details group (R48). Activities are listed in it; the planner follows a habit's inside a block, then its id.

**Evidence:** ADR 07 (`decisions/07-timelog.md`), activity-item; `com.hazia.factotum.data.time`. The planner places habits only (`Planner.kt:114`); activities list by `sort_order`, an empty one last, then id (`ItemDao.kt:184`); checked 2026-11-24.

**Acceptance:** `TimeCasesTest.activitiesKeepTheirOrderAndTheirColumnsStayTheirs` makes and orders activities, `reorderingAnActivityMovesItBetweenItsNewNeighbours` moves one to a fractional key between two others, and `PlannerTest.habitsInABlockFollowTheirManualOrderThenTheirId` orders a block's habits by `sort_order`, then id.

**Not:** An `archived` flag: dropped with schema 24 (owner, 2026-10-09), as the Trash replaces archiving (R29). The planner placing activities: an activity has no dates to place (owner, 2026-11-24).

**Since:** 2026-11-24 · owner · agreed rewording

### D-R98 · One span table, several timers

**Rule:** All tracked time is in one `time_span` table on `item_id`, and several timers can run at once. Manual entry and editing of spans apply to every owner.

**Evidence:** ADR 07.

**Acceptance:** The 9 cases of `decisions/cases/07-timelog.jsonl` pass (`TimeCasesTest`), two of them as later rulings changed them: `chronicle-activity-delete-refused` as R104, and `chronicle-activity-and-category-totals` without its category half (R117).

**Since:** 2026-10-01 · owner · migrated

### D-R99 · Span field groups

**Rule:** A span has five field groups, one per thing written apart: its start (with its owner and planned run), its end, its deletion, when a long run was last kept, and its comment. Times are kept to the second, and a span stays on its owner, which is a task, habit or activity. A deleted span, or one on a deleted owner, is not edited again, and deleting twice changes nothing.

**Why:** Each write touches only what it changes, so a stop, a deletion, a keep, a start time and a comment made on different devices all survive the merge, and nothing reopens or revives a span.

**Acceptance:** `TimeCasesTest.aCommentWrittenOnOneDeviceDoesNotReopenATimerStoppedOnAnother`, `aStaleKeepOrStartEditDoesNotReopenOrReviveASpan` and `eachOfASpansFiveGroupsWrittenOnADifferentDeviceSurvives` (five devices, one group each) pass.

**Since:** 2026-11-21 · builder · migrated

### D-R100 · A span's end is checked where it is written

**Rule:** That a span ends no earlier than it starts is checked where it is written, not in the database. Totals count a span that breaks it as nothing.

**Why:** Start and end merge apart, and a row the database refused would stop every later import.

**Acceptance:** `TimeCasesTest.tendrilExactlyOneOwner_aSpanHasOneOwnerOfAKindThatIsTimed` refuses an end before the start locally, and `aMergedSpanEndingBeforeItStartsCountsAsNothing` counts a span merged to end before its start as nothing.

**Since:** 2026-11-21 · builder · migrated

### D-R101 · Day totals

**Rule:** A span counts wholly for the personal day it started, and a running span counts up to the moment the total is read. A day's total is the union of the spans started that day plus the sum of its amounts (R102); a week's total is the sum of its days. A span whose owner is deleted, or a habit's whose tracker is deleted, does not count; seconds are kept and minutes shown rounded down, once at the end.

**Evidence:** ADR 07; decision 19 T3b.5e (owner, 2026-10-16) adds the amounts.

**Acceptance:** `TimeTotalsTest` and `TimeCasesTest` pass. Not checked: amounts in the total wait for the amount table.

**Since:** 2026-10-16 · owner · migrated

### D-R102 · Time is an activity's: spans and amounts

**Rule:** An activity holds spans and untimed amounts ("+1 h 45", on a picked day, today by default). Time is always an activity's, so there is no Duration tracker, and a tracker's typed unit is never time.

**Evidence:** Decision 19 T3b.5e (owner, 2026-10-16). Not checked: not built; the amount table and its sync are owed. The tracker unit list in code (`TrackerDao.kt:25`) still includes `HOURS`.

**Acceptance:** An amount added on a picked day syncs to a peer and counts in that day's total, and no tracker accepts a time unit.

**Since:** 2026-10-16 · owner · migrated

### D-R103 · Goals on tracked time

**Rule:** A goal on an activity names the activity item. Its windows are Chronicle's, built from day totals: the day, the week from Monday, the month from the 1st, and a milestone over the last 400 days.

**Acceptance:** `TimeTotalsTest.goalWindowsAreTheDayTheWeekFromMondayTheMonthFromThe1stAndAMilestones400Days` checks each window's bounds, and `TimeCasesTest.aGoalIsReachedInEachWindowThroughTheRepository` reaches a day, week, month and milestone goal through `ActivityRepository`, each counting only its window.

**Since:** 2026-11-21 · builder · migrated

### D-R104 · Deleting an activity

**Rule:** Deleting an activity moves it to the Trash with its live spans and goals, in one write and one stamp, after its running timers stop; a restore brings them back, ended. Delete forever purges it and its goals, and its spans go by the foreign key, including a span another device logged before they synced.

**Evidence:** Owner, 2026-10-09: the owner chose Delete forever over the rule of 2026-10-02.

**Acceptance:** `VocabularyTest` and `TimeCasesTest` delete, restore and purge an activity with a running timer.

**Not:** An activity never deleted forever, and a trigger refusing to delete one with spans (owner, 2026-10-02): replaced on 2026-10-09.

**Since:** 2026-10-10 · owner · migrated

### D-R105 · What ends a running timer

**Rule:** The events below end the owner's running timers in the same write. A device that learns of a finished task or a deleted owner from a peer ends its timers when it imports it (`endFinished`, run after each import).

**Values:**

| Event | Ends its running timers |
|---|---|
| a task marked done or skipped | yes |
| an occurrence resolved | yes; a past occurrence of a repeating task leaves a timer started after it running |
| a task or habit deleted | yes |
| a habit's tracker deleted | yes |
| an activity deleted | yes |
| a database row trashed from the page side | yes, its row task's timer (R163) |
| a habit's Log | no |

**Evidence:** Owner's answers 2026-10-02.

**Acceptance:** `TimeCasesTest` and `RowTasksTest` run each event with a timer running, locally and through an import.

**Since:** 2026-10-10 · owner · migrated

### D-R106 · A timer past its limit asks

**Rule:** A span running past its limit, since it started or since the person last kept it, asks the person to keep it, end it at a time they pick, or end it at the limit, and counts as running until answered. The ask is made on Today the next time the app opens, and the limit is 3x the activity's usual length (R107, R108).

**Evidence:** Owner's answers 2026-10-02; decision 19 T3b.3 (owner, 2026-10-16). Not checked: `TimeRepository.runningLong` reads the PERSONAL `longRun` setting (`Settings.kt:41`), not 3x the usual length.

**Acceptance:** A span past 3x its activity's usual length is listed by `runningLong`, and each answer ends or keeps it as its words say (`TimeCasesTest`).

**Not:** One PERSONAL limit of 12 hours (owner, 2026-10-02): reversed by the owner on 2026-10-16.

**Since:** 2026-10-16 · owner · migrated

### Q-R107 · An activity's usual length

**Rule:** How is an activity's usual length computed, for the limit of R106?

**Default:** none proposed: decision 19 T3b.3 leaves it owed to the data layer, with no formula.

**Since:** 2026-10-16 · owner · migrated

### Q-R108 · The limit before any session

**Rule:** What limit applies to an activity's timer before the activity has any sessions to take a usual length from?

**Default:** none proposed: decision 19 T3b.3 leaves it owed to the data layer, with no value.

**Since:** 2026-10-16 · owner · migrated

## 11. Labels

### D-R109 · One label vocabulary

**Rule:** Labels are one vocabulary, the `label` table (name, colour, `sort_order`), and they sync as rows. A new label takes Tendril's colour for its name, which can then be changed.

**Evidence:** ADR 08 (`decisions/08-tagging.md`), one-vocab; `com.hazia.factotum.core.label`, `com.hazia.factotum.data.label`.

**Acceptance:** The 10 cases of `decisions/cases/08-tagging.jsonl` pass: six in `LabelCasesTest`, `chronicle-applies-to-scope` as R110 changed it (`anyLabelGoesOnAnyElementAndEveryLiveLabelIsOffered`), and the page cases (`tendril-page-many-labels`, `tendril-page-delete-no-orphans`, the members half of `tendril-database-doorway`) in `PageCasesTest`.

**Since:** 2026-10-01 · owner · migrated

### D-R110 · Labels are global

**Rule:** The person chooses a label, and it ties elements across screens: any label goes on any element, and every live label is offered everywhere. Setting a label checks only that it is live.

**Evidence:** Owner, 2026-10-10; schema 25 drops `applies_to`, its stamp columns and the trigger that checked it.

**Acceptance:** `LabelCasesTest.anyLabelGoesOnAnyElementAndEveryLiveLabelIsOffered` passes.

**Not:** A label scope (`applies_to`, owner 2026-10-02): dropped by the owner on 2026-10-10.

**Since:** 2026-10-10 · owner · migrated

### D-R111 · How many labels each element carries

**Rule:** Each element carries labels as its row says.

**Values:**

| Element | Labels | Stored as |
|---|---|---|
| a page | many | `page_label` rows |
| any item kind | at most one | `label_id`, a group of its own |
| a tracker | at most one | `label_id`, a group of its own |
| a checklist | at most one | `label_id`, a group of its own, absent until a label is put on it |
| a page database | one, its doorway label | R156 |

**Evidence:** ADR 08; owner, 2026-10-09 (tasks, events, standalone reminders and checklists carry one too); schema 24.

**Acceptance:** `LabelCasesTest` (one label on a habit, activity, task, event, standalone reminder, tracker and checklist, a second replacing the first; `aStandaloneReminderCarriesOneLabelAndASecondReplacesTheFirst_SPEC_R111`), `PageCasesTest` (many on a page) and `DatabaseCasesTest` (the doorway) pass.

**Since:** 2026-11-24 · owner · agreed rewording

### D-R112 · Label names are unique

**Rule:** Label names are unique ignoring case, kept by the repository, not by an index. Names are compared trimmed, in one Unicode form (NFC), ignoring case.

**Why:** Two devices make the same name apart, and a database rule a merged row broke would stop every later import.

**Acceptance:** `LabelCasesTest` refuses a second label differing only in case or form.

**Since:** 2026-10-02 · owner · migrated

### D-R113 · Same-name labels merge

**Rule:** After every import, of the live labels with one name, all but the one with the lowest id (the one made first) are deleted with `merged_into` naming it, and it keeps its colour. Nothing that carried them is rewritten: readers take a merged label as the label it went into.

**Why:** A merge then never overwrites a label a person chose meanwhile on another device.

**Evidence:** Owner's answer 2026-10-02. ULIDs begin with the time.

**Acceptance:** `LabelCasesTest` makes one name on two devices, syncs, and reads one label everywhere.

**Since:** 2026-10-02 · owner · migrated

### D-R114 · Label field groups

**Rule:** A label has four field groups: name, colour, order and deletion. A rename and a recolour made apart both stand, and a label deleted on one device never brings back a tracker deleted on another.

**Acceptance:** `LabelCasesTest` renames and recolours on two devices and both stand.

**Not:** A fifth group for scope: gone with schema 25.

**Since:** 2026-10-10 · builder · migrated

### D-R115 · No foreign key on a label

**Rule:** No `label_id` has a foreign key, on an item, a tracker, a checklist or a `page_label` row; readers take a missing or deleted label as none. `page_label` has a key to its page, which a purge of the page cascades through, and its id names both, so two devices putting one label on one page write one row. Deleting a label leaves the page rows as they are, read as none.

**Why:** A key would only add a table rebuild (Tendril's habit label had none either); taking the page rows off would count as an edit to every trashed page carrying the label, and bring each one back (R145).

**Acceptance:** `PageCasesTest` deletes a label carried by a trashed page, and the page stays trashed.

**Since:** 2026-10-03 · builder · migrated

### D-R116 · A label in the Trash

**Rule:** A deleted label goes to the Trash, and its deletion takes it, and any label merged into it, off what carried them in an automatic stamp just above its own, so a restore gives it back to exactly those, unless they were labelled otherwise since. A restore is refused while a live label has its name. After Delete forever, whatever still names it (an item, a page's label row, a doorway) reads it as none.

**Evidence:** Owner, 2026-10-09.

**Acceptance:** `LabelCasesTest.aRestoredLabelIsBackOnWhatItsDeletionTookItOffAndOneDeletedForeverReadsAsNone`, `deletingASurvivorClearsWhatCarriedTheLabelsMergedIntoItAndADeadLabelIsNotEdited` and `VocabularyTest` pass.

**Since:** 2026-10-09 · owner · migrated

### D-R117 · What a label counts

**Rule:** A label counts the live elements carrying it, or carrying a label merged into it, each once: items, trackers, checklists, pages (not a template) and databases by their doorway (`LabelRepository.carrying`). It adds up to nothing else.

**Evidence:** Owner, 2026-10-10.

**Acceptance:** `VocabularyTest.aLabelCountsTheLiveElementsCarryingItEachOnce` counts each kind once, `LabelCasesTest` reads a merged label's elements, and `VocabularyTest.aTemplateCarryingALabelIsNotCounted_SPEC_R117` leaves a template out.

**Not:** A label time total, and the category half of `chronicle-activity-and-category-totals`: removed by the owner on 2026-10-10.

**Since:** 2026-11-24 · owner · agreed rewording

## 12. Settings

### D-R118 · Settings by scope

**Rule:** Every setting key is declared once with one of the scopes below. The device id is not a setting (R32).

**Values:**

| Scope | Stored | In the backup |
|---|---|---|
| PERSONAL | synced live through the `setting` table | yes |
| DEVICE_PREF | local | yes |
| DEVICE_STATE | local, never leaves the device | no |
| SECRET | the Keystore or DPAPI | not in the settings part (R123); a full backup is not ruled on |

**Evidence:** ADR 09 (`decisions/09-settings.md`), scoped-live, the owner's pick against the recommendation; `com.hazia.factotum.core.settings`, `com.hazia.factotum.data.settings`.

**Acceptance:** The 9 cases of `decisions/cases/09-settings.jsonl` pass (`SettingsCasesTest`): A and B share a folder, and C is a phone restored from A's backup.

**Not:** The four source apps' settings stores: replaced by this one.

**Since:** 2026-10-01 · owner · migrated

### D-R119 · A typed registry

**Rule:** A typed registry names each setting's key, scope, default and the values it takes. A value that does not read (unreadable, or one no version could mean) reads as the default, and no upper bound is invented. Setting a value to its default clears it, so a later default reaches it.

**Acceptance:** `SettingsCasesTest` reads an unreadable value as the default and clears a value set to its default.

**Since:** 2026-10-02 · builder · migrated

### D-R120 · Setting keys

**Rule:** The settings below are declared with the scope and default their row gives.

**Values:**

| Setting | Key | Scope | Default | Rules |
|---|---|---|---|---|
| the personal day boundary | `day_start` | PERSONAL | midnight | R94 |
| standalone reminders on the day view | `show_reminders_on_day` | DEVICE_PREF | off | R55 |
| app lock | `app_lock` | DEVICE_PREF | off | R123 |
| app lock grace | `app_lock_grace_seconds` | DEVICE_PREF | 0 s | R123 |
| the app lock PIN | `app_lock_pin` | SECRET | none | R123 |
| the regulation onboarding answer | `onboarding_answer` | PERSONAL | `MIXED` | R135 |
| Mixed mode | `mixed_mode` | PERSONAL | `EVERY_TIME` | R135 |
| the sleep tracker | `sleep_tracker` | PERSONAL | none | R139 |
| Tendril's AI key | `ai_key` | SECRET | none | R121 |
| Equipoise's endpoint key | `llm_endpoint_key` | SECRET | none | R121 |
| the burnout threshold, 0 to 1 | `burnout_threshold` | PERSONAL | 0.5 | R139 |
| crisis contacts, as written | `crisis_contacts` | PERSONAL | none | R20 |
| a new reminder's alert mode | `default_alert_mode` | DEVICE_PREF | `SCHEDULE` | R53 |
| first-run questions asked here | `first_run_done` | DEVICE_STATE | off | R121 |
| this device's sync folder | `sync_folder` | DEVICE_STATE | none | R45 |
| the desktop window's place and size | `window_frame` | DEVICE_STATE | none | R121 |
| this device's language model | `llm_model` | DEVICE_STATE | none | R06 |

**Evidence:** Owner's answers 2026-10-02 (day boundary, reminders switch, app lock); decision 14 (regulation); owner, 2026-11-24 (the last seven rows as coded, crisis contacts syncing to every device). Keys and defaults checked against `core/src/commonMain/kotlin/com/hazia/factotum/core/settings/Settings.kt` on 2026-11-24, which also declares `long_run_hours`, the PERSONAL timer limit R106 replaced; it goes when R106's limit is built. `SettingsCasesTest.eachSettingKeyHasItsScopeAndDefaultAndThePersonalOnesSync` kills mutants `Mixed mode kept per device` and `the app lock grace defaults to 5 s` (2026-11-21), and `crisis contacts kept per device`, `the burnout threshold defaults to 0.6`, `the default alert mode synced` and `the sync folder rides in a backup` (2026-11-24; `tools/mutants.py`, slice `gapA`).

**Acceptance:** `SettingsCasesTest.eachSettingKeyHasItsScopeAndDefaultAndThePersonalOnesSync` reads each key's scope and default in the table and syncs the PERSONAL ones to a second device.

**Not:** Crisis contacts kept per device, out of the folder: the owner chose to have them on every device (2026-11-24); the folder reaches only the person's own devices (R20).

**Since:** 2026-11-24 · owner · agreed rewording

### D-R121 · Where each scope lives

**Rule:** PERSONAL settings are rows of the synced `setting` table, one field group each, later stamp first, with the id `setting:<key>`, so two devices that set one key apart write one row; a key this version does not know travels as it came. DEVICE_PREF and DEVICE_STATE live in a local `device_setting` table no export reads. SECRET keys go to a `SecretStore`, backed by the Keystore and DPAPI in the shells.

**Evidence:** Tendril's `SecretStore` and `FileAiKeyStore` are the code to port; Tendril's AI key and Equipoise's endpoint key are two secrets. `SettingsCasesTest.aDevicePreferenceNeverReachesTheFolder` kills mutant `a device preference written to the synced table` (`tools/mutants.py`, slice `gapA`), 2026-11-21. Not checked: the Keystore and DPAPI stores come with the shells.

**Acceptance:** `SettingsCasesTest.aPersonalSettingChangedOnTwoDevicesKeepsTheLaterAndTheDefaultClearsIt` sets one key on two devices and reads one row, and `aDevicePreferenceNeverReachesTheFolder` finds no DEVICE_PREF value in the folder or the `setting` table.

**Since:** 2026-11-21 · builder · migrated

### D-R122 · Repositories read settings on every call

**Rule:** Repositories read the day boundary on every call, through a required `PersonalSettings` constructor parameter.

**Why:** A change imported from another device then applies at once, and no repository can be built that ignores them.

**Evidence:** The source also named the timer limit, which stopped being a setting on 2026-10-16 (R106). `LedgerRepository.kt:40` and `RegulationRepository.kt:40` take the concrete `SettingsRepository`, also required; no test checks the constructors.

**Acceptance:** `SettingsCasesTest.theDayStartSetOnOneDeviceDecidesTheDayOnAnotherAtOnce` passes, and every repository that reads the day boundary takes it through a required parameter.

**Since:** 2026-10-02 · builder · migrated

### D-R123 · The settings part of a backup

**Rule:** The settings part of a backup carries the PERSONAL rows with their stamps, and the DEVICE_PREF values. A restore writes only settings this version knows, of those two scopes, with values they take, so an old backup never outranks a newer value here or on a peer. App lock is never turned on by a restore, nor at all before this device has its PIN.

**Evidence:** Owner's answers 2026-10-02: app lock per device; this slice builds the settings part only. Not checked: a full backup comes with the shells.

**Acceptance:** `SettingsCasesTest` restores an old backup on a phone and keeps the newer values; a backup with app lock on leaves it off.

**Since:** 2026-10-02 · owner · migrated

## 13. Search

### D-R124 · One search index

**Rule:** Search is one local, rebuildable FTS4 index, `search_fts(text)`, beside a plain `search_key(doc, kind, row_key)` whose `doc` is each entry's FTS document id. It uses the `unicode61` tokenizer with `remove_diacritics=2`, which folds case and accents.

**Why:** A trigger removes an entry by its key in about 0.04 ms, where finding it by a column FTS4 does not index scanned the index (13 ms at 50,000 entries).

**Evidence:** ADR 10 (`decisions/10-search.md`); `com.hazia.factotum.data.search`. Spike 1, desktop (2026-10-03): the bundled SQLite is 3.50.1, has FTS5, and makes the FTS4 index with `remove_diacritics=2`.

**Acceptance:** The 7 cases of `decisions/cases/10-search.jsonl` pass: the item, tracker and Log cases in `SearchCasesTest`, the page and block halves in `PageCasesTest`.

**Not:** Tendril's and Chronicle's separate FTS tables. FTS5: Room's annotations do not generate it, and it could replace FTS4 only if every target SQLite build has it (R197).

**Since:** 2026-10-03 · owner · migrated

### D-R125 · What search indexes

**Rule:** The index holds the texts below. A deleted row and a blank text leave it by trigger.

**Values:**

| Source | Text |
|---|---|
| an item | its title |
| a tracker | its name |
| a Log | its label and note |
| a session | its comment |
| a page | its title; a journal day with no title under its date |
| a block | its text |
| a checklist | its name, then its items' text |

**Evidence:** Owner's answers 2026-10-03; decision 14 (checklists).

**Acceptance:** `SearchCasesTest`, `PageCasesTest` and `ChecklistChartTest` find each source.

**Not:** Check-in notes: kept out of search (owner, 2026-10-03).

**Since:** 2026-10-04 · owner · migrated

### D-R126 · Kept current by triggers

**Rule:** Triggers on every source table keep the index current, import writes included, and they are made again on every open. The index is rebuilt on open when it holds a different number of entries than rows belong in it: after an upgrade (whose triggers were dropped for it), a restore or a recovery.

**Acceptance:** `SearchCasesTest` finds a row written by an import, and an index emptied by hand is rebuilt at the next open.

**Since:** 2026-10-03 · owner · migrated

### D-R127 · What a search shows

**Rule:** Nothing deleted, or under something deleted, shows: a page or block only while the page and every page above it are live, and a deleted tracker's Logs, a deleted task's sessions, a subtask under a deleted parent or a habit whose tracker is deleted are read as deleted when searching. Done or skipped tasks and reminders, and one-off events that have ended, show marked as finished. Templates are kept out (R181).

**Evidence:** Owner's answers 2026-10-03.

**Acceptance:** `SearchCasesTest` and `PageCasesTest` search under each deleted parent and find nothing, and find a done task marked.

**Since:** 2026-10-03 · owner · migrated

### D-R128 · Queries

**Rule:** A query is words of letters and digits (an accent typed apart included), each a prefix, all required, from two letters on. Names come first, then text inside, newest first by its own time; a name's time is its item's date, and block hits get snippets. Hits are read in chunks under SQLite's 999 variables.

**Evidence:** Owner's answers 2026-10-03 (two letters; names first, then newest).

**Acceptance:** `SearchCasesTest` orders names before text, ignores one letter, and finds a word with its accent typed apart mid-word.

**Since:** 2026-10-03 · owner · migrated

## 14. Check-in and regulation

### D-R129 · One check-in table, mood on its own axis

**Rule:** Check-ins are one `check_in` table with mood as its own axis: `mood` is 1 to 5, `energy` and `pleasantness` are 0 to 1 and nullable, and `source_levels`, `stability` and `note` are stored too.

**Evidence:** ADR 05 (`decisions/05-checkin.md`), own-axis: the owner chose it against the recommendation, and ADR 05 records the loss accepted. `com.hazia.factotum.core.checkin`, `com.hazia.factotum.data.checkin`.

**Acceptance:** The 7 cases of `decisions/cases/05-checkin.jsonl` pass (`CheckInCasesTest`).

**Since:** 2026-10-01 · owner · migrated

### D-R130 · No numbers on the check-in screen

**Rule:** The check-in screen shows no numbers: no averages, counts or curves. Equipoise's engines still compute on demand.

**Evidence:** ADR 05. Not checked: the check-in screen is not built.

**Acceptance:** The check-in screen's mockup and build show no number, average, count or curve.

**Since:** 2026-10-01 · owner · migrated

### D-R131 · A check-in about a past day

**Rule:** A check-in may be about a past day: it keeps the moment it was made and, optionally, the day it is about, which is no later than the personal day it was made on. It counts for the day it is about, else the personal day it was made on.

**Evidence:** Owner's answer 2026-10-03.

**Acceptance:** `CheckInCasesTest` makes a check-in about yesterday and finds it on yesterday, and refuses one about tomorrow.

**Since:** 2026-10-03 · owner · migrated

### D-R132 · Check-in field groups

**Rule:** A check-in has three field groups: what it says (its moment, the day it is about, its values), written once; its note; and its deletion. A check-in is undone, not changed, and several a day are kept.

**Why:** A note edited on another device then never brings back a check-in undone here (Tendril: delete wins).

**Acceptance:** `CheckInCasesTest` edits a note on one device while the other undoes the check-in, and it stays undone.

**Since:** 2026-10-03 · builder · migrated

### D-R133 · Check-in scales

**Rule:** Each source's taps are stored on the scales below, and the rules (a whole mood from 1 to 5, axes from 0 to 1, a whole step count on an axis, a well-formed moment and day) sit on the group written once.

**Values:**

| Source | Energy values | `source_levels` |
|---|---|---|
| a Tendril energy tap | (k − 0.5) / 5 | 5 |
| Equipoise's widget | 0.15, 0.5, 0.85, the values it has always stored | 3 |

**Acceptance:** `CheckInScalesTest` passes.

**Since:** 2026-10-03 · builder · migrated

### D-R134 · Check-in engines

**Rule:** Equipoise's LowMoment and StabilityTrend are ported unchanged, with their tests, and the stability trend is said in words only. An engine reads the moment a check-in was made, not the day it is about: its history is every two-axis check-in made before the one judged, by its personal day.

**Evidence:** Owner's answer 2026-10-03 (the trend in words only). Not checked: the check-in shapes are not ported; they come with the screens.

**Acceptance:** `LowMomentTest`, `StabilityTrendTest` and `CheckInCasesTest.aCheckInMayBeAboutAPastDayButNotAFutureOneAndTheEnginesReadTheMoment` pass.

**Since:** 2026-10-03 · owner · migrated

### D-R135 · The direction engine

**Rule:** Which way to regulate is worked out on demand from the live outcomes on live two-axis check-ins, so an undone check-in stops teaching, and outcomes are taken only for a check-in with both axes. Equipoise's direction engine is ported with its tests and simulators. The onboarding answer and Mixed mode are PERSONAL settings (R120).

**Evidence:** Decision 14 (`decisions/14-sole-owner-modules.md`); built 2026-10-04 in `com.hazia.factotum.core.checkin` and `com.hazia.factotum.data.checkin`.

**Acceptance:** `DirectionEngineSpikeTest`, `OnboardingTest`, `MixedModeTest` and `RegulationLedgerTest` pass.

**Since:** 2026-10-04 · builder · migrated

### D-R136 · Outcome at the next open

**Rule:** A tool done away from the phone is owed on this device alone (`pending_outcome`, never synced), asked once at the next open, and lapsed as "not now" after that or when another tool is chosen. Each step is one transaction. One owed for a check-in since undone is dropped without a word.

**Acceptance:** `OutcomeAtNextOpenTest` passes.

**Since:** 2026-10-04 · builder · migrated

### D-R137 · The masking ledger

**Rule:** A ledger day is one row, `masking:<day>`, made with one fixed app stamp, so two devices write one row and making it never undoes a clearing. Its three scales are field groups, empty until tapped; a clearing empties them, and a tap brings the day back afresh.

**Acceptance:** `RegulationLedgerTest` makes one day on two devices, clears it on one, and taps it back.

**Since:** 2026-10-04 · builder · migrated

### D-R138 · Sensory logs

**Rule:** A sensory log is five channels from 0 to 1, said once and undone, not changed.

**Acceptance:** `RegulationLedgerTest` writes and undoes a sensory log.

**Since:** 2026-10-04 · builder · migrated

### D-R139 · The burnout index

**Rule:** The burnout index is never stored: `LedgerRepository.burnout` works it out on demand over the fourteen personal days up to the one being read, reweighing over the terms present. Its terms are those below.

**Values:**

| Term | A day's value |
|---|---|
| energy | the mean of its energy values, one-axis taps included |
| masking load | counted only when all three scales are set |
| sensory load | the mean of its logs' channel means |
| sleep | the sum of that day's readings of the live tracker named in `sleep_tracker` |

**Evidence:** Decision 14 (2026-10-03): computed on demand, never synced, sleep from a tracker the person names, a missing input reweighs the rest. Not checked: a day partly answered adds no masking load provisionally; the screens may ask for all three scales at once. A person who tracks only masking can reach the top, so one ledger day or one sensory log can cross an alert threshold alone; the once-only alert is not wired.

**Acceptance:** `BurnoutIndexSpikeTest`, `MaskingLoadSpikeTest` and `RegulationLedgerTest` pass.

**Since:** 2026-10-04 · owner · migrated

## 15. Pages

### D-R140 · Page parts are rows

**Rule:** Pages, blocks, property values, canvas cards and lines, and database views are rows with R21's stamps and tombstones, merged per row and per field group. The property schema is upserted by its id.

**Evidence:** ADR 12 (`decisions/12-page-merge.md`), per-row+revive; `com.hazia.factotum.core.page`, `com.hazia.factotum.data.page`.

**Acceptance:** The 8 cases of `decisions/cases/12-page-merge.jsonl` pass: five in `PageCasesTest`, the two cell cases in `DatabaseCasesTest`, and `shared-canvas-nodes` in `CanvasCasesTest`.

**Since:** 2026-10-01 · owner · migrated

### D-R141 · Page and block field groups

**Rule:** A page and a block merge in the field groups below, so edits to different parts of one block both stand.

**Values:**

| Row | Groups |
|---|---|
| page | its making; its title and icon; its place under a parent; its deletion |
| block | its making (which page; a trigger keeps it there); its type; its text with Tendril's formatting spans; its place (parent block and sort key); its attributes; its deletion |

**Acceptance:** `PageCasesTest.twoGroupsOfOneBlockEditedOnTwoDevicesBothStand_SPEC_R141` changes a block's type and text on one device and its attributes and place on another, and all four stand.

**Since:** 2026-11-21 · builder · migrated

### D-R142 · Block order

**Rule:** A block's sort key is text: base-36 digits compared character by character (fractional indexing after Greenspan). There is always a key between two neighbours, so placing a block never re-keys its siblings, and two blocks placed at one key read in id order.

**Acceptance:** `PageCasesTest.blocksNestAndKeepTheirOrderAfterTheKeysRunOutOfRoom`, `placingBlocksNeverWritesOverAMoveOrADeletionMadeElsewhere` and `OutlineTest` pass.

**Not:** A Double key: it ran out of room after about fifty inserts at one spot, and re-keying the siblings wrote over moves and deletions made on other devices.

**Since:** 2026-10-03 · owner · migrated

### O-R143 · Later text wins, earlier is kept

**Rule:** On a clash within one keep-loser group (a page's title, a block's text, a cell, a card's text, a line's label, a picture), the later version wins and the replaced one is kept. The merge hands every version that both sides changed since their base to a local `sync_lost` table, its base being the newest version read from a peer, not the winner. After every import, each becomes a MERGE version in that device's History and a synced notice (R144), unless the text it lost to says the same.

**Why:** Nothing typed is lost to a sync: the replaced text stays in History, and a notice says so. With the base read from a peer, every replaced text is kept on at least one device, with three devices too.

**Acceptance:** `PageCasesTest.theLaterTextWinsAndTheEarlierIsKeptInHistoryWithOneNoticeDismissedEverywhere` (two devices), `KeepLoserMergeTest.withThreeDevicesEveryReplacedTextIsLostSomewhereWhateverTheOrder` (three, in memory) and `PageCasesTest.withThreeDevicesEveryReplacedTextIsKeptInAHistoryAndNoticedEverywhere_SPEC_R143` (three, on the real database, read from History) pass.

**Since:** 2026-11-24 · owner · agreed rewording

### D-R144 · The replaced-by-a-sync notice

**Rule:** A "replaced by a sync" notice (`page_notice`) syncs, shows everywhere until it is dismissed once, and counts a title clash. It carries the replaced text, so a device that never held it can bring it back, and it is stamped with the replaced version's own stamp, so two devices write one notice and the second never undoes a dismissal.

**Evidence:** Owner's answers 2026-10-03.

**Acceptance:** `PageCasesTest` makes a clash on two devices, dismisses the notice on one, and it stays dismissed on both.

**Not:** Tendril's `.tendril-lost` folder files (R200).

**Since:** 2026-10-03 · owner · migrated

### O-R145 · Revive

**Rule:** A later edit to any part of a trashed page brings it back, for pages only. After every import, a trashed page comes back when its title, its place, a block, a label, or a live sub-page moved or made under it carries a stamp later than its deletion, and brings back its trashed parents; a deleted block comes back when one of its groups does. A revival is stamped just above the deletion it undoes (that stamp's time, its device followed by `~`).

**Why:** A later edit brings a page back from the Trash, as Tendril does, and nothing typed is lost; it can be trashed again. The revival's stamp makes every device write the same row, and a purge made after the edit still holds.

**Evidence:** Owner's answers 2026-10-03 (a later edit brings back a deleted block; revive brings back trashed parents).

**Acceptance:** `PageCasesTest.aLaterEditBringsATrashedPageBackAndAnEarlierOneDoesNot`, `aLaterEditToASubPageBringsBackItsTrashedParents` and `aLaterEditBringsADeletedBlockBack` pass, and `aMoveALabelOrASubPageMadeUnderItAfterTheTrashBringsAPageBackStampedJustAboveTheTrash_SPEC_R145` brings pages back by a place, a label and a sub-page and reads each revival's stamp as the trash's time and device followed by `~`.

**Not:** A deletion beating a later edit to another part of the page, as R21's group rule has it for other rows: the edit would sit in the Trash.

**Since:** 2026-11-24 · owner · agreed rewording

### D-R146 · The app's own writes are marked

**Rule:** Every write the app makes itself (a revival, a merge of options, the lift of a deleted card's children, a carried card's move, a tidy) is stamped with the stamp of what caused it and `~` after its device. Revive reads only by-hand stamps, for pages, blocks, cells, options, cards and lines.

**Why:** Every device then writes the same row, it outranks what it replaces, and it is never read as a person's edit; without the mark, two devices deleting a card and its parent always brought one back.

**Acceptance:** `CanvasCasesTest` deletes a card and its parent on two devices and neither comes back.

**Since:** 2026-10-03 · builder · migrated

### D-R147 · Trash, restore and delete forever for pages

**Rule:** Trashing a page trashes its live sub-pages with one stamp, and restoring it brings back the pages trashed with it. Delete forever works only from the Trash and purges the page and the trashed pages under it; a live page a sync left under them moves to the top.

**Evidence:** Owner's answers 2026-10-03.

**Acceptance:** `PageCasesTest` and `VocabularyTest` trash, restore and purge a page tree.

**Since:** 2026-10-03 · owner · migrated

### D-R148 · What a merge can leave

**Rule:** A page left under a trashed page, or two pages moved under each other on two devices, is shown at the top of the tree. A trashed cycle is listed once in the Trash, by its lowest id.

**Acceptance:** `PageCasesTest` makes a cycle on two devices and reads both pages at the top.

**Since:** 2026-10-03 · builder · migrated

### D-R149 · Page History

**Rule:** A page's History is this device's own (`page_revision`), with the versions below, fifty kept per page. Restoring a version sets the title and each block by its id, and deletes the blocks it did not have.

**Values:**

| Version | Written |
|---|---|
| EDIT | before a change, at most one every ten minutes |
| MERGE | for a version a sync replaced, linked to its notice |
| RESTORE | when a version is brought back |

**Acceptance:** `PageCasesTest` writes, merges and restores versions and keeps fifty.

**Since:** 2026-10-03 · builder · migrated

### D-R150 · Database tables

**Rule:** A database is a page with the tables below, each of their groups written apart. Properties and views name the database page.

**Why:** Every synced row's id is unique across tables, since the merge stages rows by id alone.

**Values:**

| Table | Holds | Id |
|---|---|---|
| `page_database` | the shell: doorway label and hue | `database:<page>` |
| `property` | name, type, place, deletion | its own |
| `property_option` | name, colour, place, deletion with `merged_into` | its own |
| `property_value` | one per page and property | `pv:<page>:<property>` |
| `value_pick` | one per Multi-select pick | `pick:<page>:<property>:<option>` |
| `page_view` | name, layout, shown, sort, filter, place, deletion | its own |

**Evidence:** `DatabaseRepository` in `com.hazia.factotum.data.page`.

**Acceptance:** `DatabaseCasesTest` (`shared-cell-and-body`, `shared-cell-loser-recoverable`) passes.

**Since:** 2026-10-03 · builder · migrated

### D-R151 · Cell values and type changes

**Rule:** A value is text in one form per type: a decimal, `true` or `false`, an ISO date, a Select's option id. A type change writes no value; the stored value is read for what it can be under the new type (an option's id or name for a Select, the first pick of a Multi-select changed into a Select, a number, a date). A change to a Select or a Multi-select makes an option for each text no live option names.

**Evidence:** Owner's answers on databases 2026-10-03 (a type change keeps the stored values).

**Acceptance:** `DatabaseCasesTest` changes a column's type both ways and reads the same stored values.

**Since:** 2026-10-03 · owner · migrated

### D-R152 · A cell is kept when replaced

**Rule:** A cell is a keep-loser group (R143): History holds the page's cells and picks, and the notice names a Select's option. A cell row made on two devices meets as a clash, so it starts with no merge base, and clearing a cell nobody filled here writes nothing. A Multi-select cell merges its picks, one `value_pick` row each.

**Evidence:** Owner's answers on databases 2026-10-03.

**Acceptance:** `DatabaseCasesTest` (`shared-cell-loser-recoverable`) passes, and two picks made apart both stand.

**Since:** 2026-10-03 · owner · migrated

### D-R153 · A property in the Trash

**Rule:** A deleted property goes to the Trash: it reads as gone everywhere but the Trash, and keeps its values, options and links, which a restore brings back. A relation goes with its pair, in one stamp, and a by-hand edit made elsewhere after the deletion brings it back after an import. Delete forever purges it with its pair, and its values, options and links go by the foreign keys.

**Evidence:** Owner, 2026-10-09; schema 24 gives `property` a deletion group, absent on a column never deleted.

**Acceptance:** `VocabularyTest` and `DatabaseCasesTest` delete, restore and purge a column and a relation pair.

**Since:** 2026-10-09 · owner · migrated

### D-R154 · Select options

**Rule:** A deleted option reads as none and keeps its picks; a later pick of it, or of an option merged into it, brings it back, and Restore and Delete forever come from the Trash. Options of one property with one name merge into the lowest id, the one made first, and a restore is refused while a live option of the property has its name. A merge or a revival is stamped just above the option's own stamps, so it is never an edit that brings back a trashed database.

**Evidence:** Owner's answers on databases 2026-10-03; owner, 2026-10-09 (the Trash).

**Acceptance:** `DatabaseCasesTest` deletes, picks again, merges and restores options.

**Since:** 2026-10-09 · owner · migrated

### D-R155 · Renames take the later name

**Rule:** A renamed property, option or view takes the later name silently, and a view's sort, filter and visible columns sync.

**Evidence:** Owner's answers on databases 2026-10-03.

**Acceptance:** `DatabaseCasesTest.aPropertyOptionAndViewRenamedOnTwoDevicesTakeTheLaterNameSilentlyAndShownColumnsSync_SPEC_R155` (the later names, with no notice or question, and the shown columns synced) and `aSortAndAFilterChangedApartBothStand` pass.

**Since:** 2026-11-24 · owner · agreed rewording

### D-R156 · A database's rows

**Rule:** A database's rows are its page's sub-pages and the live pages carrying its doorway label. Trashing a database trashes its rows, a revived page brings back the pages trashed with it, and a cell, a pick or an edit to the database's schema counts as an edit to its page. A trashed database's schema is not edited.

**Evidence:** Owner's answers on databases 2026-10-03 (members are the rows made in it and the pages carrying its label).

**Acceptance:** `DatabaseCasesTest` and `PageCasesTest` read the members, trash and revive a database.

**Since:** 2026-10-03 · owner · migrated

### D-R157 · Views

**Rule:** A view keeps Tendril's single sort and single filter, compared by type: numbers as numbers, dates as dates, a Select by its options' order, text ignoring case, an empty cell last either way. A filter naming an option merged since reads as the option it went into, and a setting naming a deleted property reads as none. A Board shows a column for no option first, then the live options in order, and is empty without a Select to group by; a database keeps at least one view, and a deleted view is restored or deleted forever from the Trash.

**Evidence:** Text sorts compare in lower case (`DatabaseRepository.kt:973`), and "is" and "contains" ignore case (`:986`, `:996`); the test kills mutants `a text sort minds case`, `a text filter minds case` and `a text contains filter minds case` (`tools/mutants.py`, slice `gapC`), 2026-11-24.

**Acceptance:** `DatabaseCasesTest.aViewSortsByTypeWithEmptyLastAndFiltersByType`, `aSelectSortsByItsOptionsOrderTextIgnoresCaseAndADateFilterReadsDates_SPEC_R157` and `aDatabaseKeepsOneViewAndATrashedOnesSchemaIsNotEdited` pass; the second sorts text in mixed case and filters it with "is" and "contains" typed in capitals.

**Since:** 2026-11-24 · owner · agreed rewording

### D-R158 · Databases in pages

**Rule:** Besides the database page, a page can hold a DATABASE block (a database made inside a page, its sub-page, shown in place and moving and trashing with it) and a VIEW block (a view of any database, owned by the block, with its own layout, sort and filter, including this page; removing it never touches its pages). A saved query on properties sits beside the doorway label, and views over items (tasks, events, habits) select by label.

**Evidence:** Decision 16 (`decisions/16-databases.md`, owner 2026-10-05): O6; `tools/dbview_sim.py` and `decisions/16-databases-survey.json`. Growth: 2 block kinds and 3 columns; nothing built changes. Not checked: not built; a data-layer slice is owed before the T5 screens.

**Acceptance:** The cases of `decisions/cases/16-databases.jsonl` pass against the real database.

**Since:** 2026-10-05 · owner · migrated

### D-R159 · Formulas and rollups

**Rule:** A COMPUTED column holds, in a field group of its own taking the later stamp, a formula stored with property ids for keys (typed and shown with names, so a rename never breaks it) or a rollup (a relation of its database, a value property of the related one, an aggregation). Computed values are worked out when rows are read, so a view sorts and filters on them, numbers before dates before text. A rollup reads the live related rows only, and the related rows without their own rollups, so two databases reading each other never loop.

**Evidence:** Tendril's formula engine (lexer, parser, type checker, dependency graph, evaluator) in `com.hazia.factotum.core.formula`, its 73 tests ported; decision 14.

**Acceptance:** `FormulaLexerTest`, `FormulaParserTest`, `FormulaTypeCheckerTest`, `FormulaDependencyGraphTest`, `FormulaEvaluatorTest`, `FormulaKeysTest` and `FormulaColumnsTest` pass.

**Since:** 2026-10-04 · owner · migrated

### D-R160 · A formula is checked when written

**Rule:** A formula is checked with every other formula of its database when it is written. A name two columns share, an error, a cycle (the formula's own or one a sync made), or an edit that breaks a formula naming it is refused, with the message in names, pointing at what was typed.

**Acceptance:** `FormulaColumnsTest` is refused in each case.

**Since:** 2026-10-04 · builder · migrated

### D-R161 · Where formulas differ from Tendril

**Rule:** Formulas follow Tendril's engine except in the cases below, which Factotum changed.

**Values:**

| Case | Factotum |
|---|---|
| a box never ticked | reads unchecked (Tendril read it blank) |
| a formula reading a rollup | allowed |
| a rollup reading a rollup or a relation | refused |
| a template's copy | keeps its formulas working |

**Acceptance:** `FormulaColumnsTest` covers each row.

**Since:** 2026-10-04 · builder · migrated

### D-R162 · Database rows as tasks

**Rule:** A database's rows-as-tasks switch is a field group on its shell, and the task field a column shows (done, date, due date, repeat) is a group on the column, the latest binding winning when a sync leaves two. While the switch is on, every row is a task, `rowtask:<page>`, one per page whatever databases it is a row of, seeded with one fixed app stamp so two devices seeding it make one. The title is one: a rename of the page or the task renames both in one write.

**Evidence:** Decision 14, the owner's answers 15 to 30; `RowTasks.kt` in `com.hazia.factotum.data.page`.

**Acceptance:** `RowTasksTest` passes.

**Since:** 2026-10-04 · owner · migrated

### D-R163 · A row task's life is its page's

**Rule:** Deleting a row's task trashes the row; trashing, restoring or deleting a page for good does the same to its rows' tasks, and a database's Trash takes its rows' tasks. A task edit made after its row was trashed elsewhere brings the row back. A page that stops being a row has its task trashed, and a row trashed from the page side stops its task's running timer.

**Acceptance:** `RowTasksTest` trashes, restores and purges from each side.

**Since:** 2026-10-04 · owner · migrated

### D-R164 · Row-task clashes

**Rule:** A clash between a trash or restore and a person's schedule edit asks nothing: the person's fields stand, and the later of the two says whether the task is deleted (`Merger.settle`). Two people's edits still ask, with no "keep both". A task whose page is deleted for good goes on each device alone, with no purge of its own, so a page a later edit brings back finds its task again.

**Acceptance:** `RowTasksTest` makes each clash on two devices.

**Since:** 2026-10-04 · owner · migrated

### D-R165 · Bound columns read the task

**Rule:** Bound columns read the task, so formulas, rollups, sorts and filters see it, and they are set through the task. Binding a column gives the tasks its values, and unbinding it (or turning the switch off) leaves the task's values in the cells, all stamped as the app's, so none of it brings back a row trashed elsewhere.

**Acceptance:** `RowTasksTest.bindingOnADeviceThatHadNotSeenATrashDoesNotBringTheRowBack` and `unbindingOrTurningTasksOffOnADeviceThatHadNotSeenATrashDoesNotBringTheRowBack_SPEC_R165` pass.

**Since:** 2026-11-24 · owner · agreed rewording

### D-R166 · Repeating rows and intervals

**Rule:** A repeating row shows its next open occurrence, and ticking resolves it; its date moves the series or the next occurrence, as the screen asks every time. An interval is "every n days, weeks or months" (`n:UNIT`, n from 1), the plain rule `FREQ=…;INTERVAL=n`, so a monthly one begun on the 31st skips the months without one; a richer rule shows read-only and freezes empty. Setting an interval on an undated row starts it today.

**Evidence:** `com.hazia.factotum.core.recurrence.Interval`.

**Acceptance:** `IntervalTest` and `RowTasksTest` pass.

**Not:** Tendril's monthly interval, which drifted to the 28th.

**Since:** 2026-10-04 · owner · migrated

### D-R167 · Rows changed

**Rule:** The composition root's `rowsChanged()` runs after a local write that changes which pages are rows, and the screens call it. A row's own edits seed its task first, so nothing is refused meanwhile.

**Evidence:** Not checked: no screen calls `rowsChanged()` yet.

**Acceptance:** A write that adds a page to a database through the screens is followed by `rowsChanged()`, and the new row has its task.

**Since:** 2026-10-04 · builder · migrated

### D-R168 · Pictures in pages

**Rule:** An image block's caption is its text, and its picture is a keep-loser group of its own (`block_image`: the blob's name and size), so a picture replaced on two devices keeps the later and puts the earlier in History with a notice. A picture is stored once by the SHA-256 of its bytes as stored (`<sha256>.jpg` or `.png`), so the same picture inserted twice, or on two devices, is one file, and a template's copy names the same one. A picture taken away that loses offers nothing back.

**Evidence:** Decision 14, the owner's answers 24-25 and 31-34; `com.hazia.factotum.core.image`, `com.hazia.factotum.data.image`.

**Acceptance:** `ImagesTest` passes.

**Since:** 2026-10-04 · owner · migrated

### D-R169 · Inserting a picture

**Rule:** On insert, a picture is turned upright as its EXIF says, scaled to at most 2048 px on its longest edge, and re-encoded with no metadata, location included: a JPEG at quality 85, or a PNG when a pixel is transparent; an animation keeps its first frame. Scaling is platform code behind `ImageScaler`, reading the formats in the values below.

**Values:**

| Platform | Reads | Refuses |
|---|---|---|
| desktop | what the JDK's ImageIO reads: JPEG, PNG, GIF, BMP, TIFF, WBMP; its size before its pixels | WebP, HEIC, CMYK JPEGs, over 100 million pixels |
| Android | what `ImageDecoder` reads | not listed in the source |

**Evidence:** Not checked: Android's scaler needs a device check of orientation with a target size, and of HEIF with transparency. JDK 21's ImageIO reads a CMYK JPEG without turning it into RGB, so it would be stored black; `DesktopImageScaler` refuses a JPEG whose frame header names four channels, CMYK or YCCK (checked 2026-11-22). It takes the first ImageIO reader that accepts the bytes (`DesktopImageScaler.kt:62`), so TIFF and WBMP are read too; a peer never reads them, as every picture is stored as a JPEG or PNG. The test's TIFF and WBMP cases kill mutants `TIFF and WBMP are refused` and `a WBMP is refused` (`tools/mutants.py`, slice `gapC`), 2026-11-24.

**Acceptance:** `ImagesTest.aPictureIsScaledToAt2048TurnedUprightAndStrippedOfItsMetadata` and `aGifABmpAndAnAnimationAreReadWebpHeicAndCmykRefusedAndAJpegIsWrittenAtQuality85_SPEC_R169`, which also reads a TIFF and a WBMP, pass on the desktop; the device check passes on Android.

**Since:** 2026-11-24 · owner · agreed rewording

### D-R170 · Pictures through the folder

**Rule:** Each device keeps its own copy of a picture (`BlobStore`); the folder only carries them, in `blobs/` beside `devices/`. A picture is published before the logs that name it are exported and fetched after an import (`BlobSync.exchange`), and kept only when its bytes match its name; a damaged copy, here or in the folder, is replaced from a device holding a good one, and Syncthing's conflict copies are removed. Until its bytes arrive a picture reads as waiting, with its size for a placeholder.

**Acceptance:** `ImagesTest` syncs a picture to a peer, damages a copy, and reads a waiting placeholder.

**Since:** 2026-10-04 · owner · migrated

### D-R171 · Collecting pictures

**Rule:** The folder's copy of a picture goes once a device has named it in no live block or open notice for 30 days, so a block revived within them keeps its picture. A device's own copy stays while anything there names it, History and deleted blocks included.

**Evidence:** Decision 14, answers 31 and 32. Known limit: a picture that only History or a deleted block names travels no more once its folder copy is collected, so a device away longer than 30 days restores that version without it until a device holding it names it live again.

**Acceptance:** `ImagesTest` collects the folder copy after 30 days unnamed and keeps the device copy History names.

**Since:** 2026-10-04 · owner · migrated

### D-R172 · Canvas tables

**Rule:** `page_canvas` makes a page a canvas (`canvas:<page>`, the board's layout). A `canvas_node` is a text card, a page card or a frame, with its position, size (a card's width only; its height follows its text), text, hue, mind-map parent, fold, layout and stacking key each a field group; a `canvas_edge` is a line with an id of its own, its direction and its label. Neither a page card's page nor a card's parent has a foreign key, so a purge never deletes a card, and a card read under a missing, deleted or cycled parent is a root.

**Evidence:** `CanvasRepository` in `com.hazia.factotum.data.page`.

**Acceptance:** `CanvasCasesTest` (`shared-canvas-nodes`) passes.

**Since:** 2026-10-03 · builder · migrated

### D-R173 · Moving cards

**Rule:** A card moved on two devices takes the later position, and a frame and a card in it moved apart each keep their own later position. A move is written when a card is dropped, carrying its mind-map subtree; frames do not ride along. Frame membership is geometric, worked out by the screen that draws the boxes, so carrying a frame's contents is a bulk move of the cards it holds.

**Evidence:** Owner's answers on the canvas 2026-10-03, confirmed 2026-11-24. `CanvasRepository.kt:108` (`moveNode`) carries only the mind-map subtree; `CanvasRepository.kt:129` (`moveNodes`) is the bulk move. Not checked: no screen works out frame membership yet; `moveNodes` is the bulk move it calls.

**Acceptance:** `CanvasCasesTest.aCardMovedOnTwoDevicesTakesTheLaterPosition` and `aFrameAndACardInItMovedApartEachKeepTheirOwnLaterPosition_SPEC_R173` pass. Dragging a frame on the canvas screen moves the cards inside its box through one `moveNodes` call.

**Since:** 2026-11-24 · owner · agreed rewording

### D-R174 · Deleting a card

**Rule:** Deleting a card deletes, in one stamp, its lines, the frames that follow it and their lines, and lifts its children to its parent. A later edit to it on any device, a line drawn to it, or a child put under it brings it back with all of that, its children moved back under it; so does a restore from the Trash. Delete forever purges the card, the frames deleted with it, and every line touching them, and its lifted children stay.

**Evidence:** Owner's answers on the canvas 2026-10-03; owner, 2026-10-09 (the Trash).

**Acceptance:** `CanvasCasesTest` and `VocabularyTest` delete, revive, restore and purge a card with lines and children.

**Since:** 2026-10-09 · owner · migrated

### D-R175 · Page cards

**Rule:** A page card keeps showing its page: live, marked as in the Trash, as a placeholder when it is deleted for good (in the purge registry), or as not on this device yet. A purge never deletes a card.

**Evidence:** Owner's answers on the canvas 2026-10-03.

**Acceptance:** `CanvasCasesTest` reads a page card in each of the four states.

**Since:** 2026-10-03 · owner · migrated

### D-R176 · Canvas History

**Rule:** History holds a canvas's cards and lines, each group as a record line encodes it, and gives them back by id. A card's text and a line's label are kept when replaced, with a notice.

**Evidence:** Owner's answers on the canvas 2026-10-03. The viewport, the stacking verbs and re-tidying after a sync wait for the screens.

**Acceptance:** `CanvasCasesTest` replaces a card's text on two devices and restores it from History.

**Since:** 2026-10-03 · owner · migrated

### D-R177 · The journal

**Rule:** The journal is one page, `journal:root` ("Journal"), with one page per personal day under it, `journal:<date>`, titled with the date until renamed; a day is found by its id, whatever its title, and starts empty. Both are made with one fixed app stamp, the lowest there is, so two devices that open a day write the same rows and opening a day never outranks a trash, a move or a rename made elsewhere. A day this device knows was deleted for good is made again with a fresh stamp, and a purge it has not heard of holds against what it writes there meanwhile, as for any page.

**Evidence:** Owner's answers on the journal 2026-10-03 (one page per personal day, one page however many devices open it). Writing in a day trashed elsewhere brings it back (R145); a day this device knows is in the Trash is restored from the Trash, by the screen.

**Acceptance:** `JournalLinksTemplatesTest` opens one day on two devices and finds one page.

**Since:** 2026-10-03 · owner · migrated

### D-R178 · Road Map links

**Rule:** A Road Map link is one undirected `page_relation` row per pair (`relation:<lower>:<higher>`), removed and made again by its deletion. A link made, or made again, counts for both pages in revive, so a link made to a trashed page brings it back; one taken off does not. A link to a trashed page shows it marked, and to a purged one a placeholder.

**Evidence:** Owner's answers 2026-10-03.

**Acceptance:** `JournalLinksTemplatesTest` removes and remakes a link and links a trashed page.

**Not:** Add-only relations, as ADR 12 had them: the owner chose removable links on 2026-10-03.

**Since:** 2026-10-03 · owner · migrated

### D-R179 · Database relations

**Rule:** A database relation is always two-way: two RELATION columns, each naming its database and its pair, made in one write, the reverse named after the source. Their links are `relation_link` rows held under the pair's lower-id column, from its side (`link:<column>:<row>:<target>`), so the two columns read one row and never disagree; a column whose pair was deleted on another device keeps its links under its own id; a link is removed and made again by its deletion, as a Road Map link is. Neither page of a link has a foreign key, so a page deleted for good reads as a placeholder from either side and a trashed one shows marked; a type never changes to or from a relation, and deleting either column deletes both.

**Evidence:** Owner's answers 2026-10-03.

**Acceptance:** `JournalLinksTemplatesTest` and `DatabaseCasesTest` link rows from either side, remove and remake a link, and delete one column.

**Not:** Add-only links, as ADR 12 had them: the owner chose removable links on 2026-10-03.

**Since:** 2026-10-03 · owner · migrated

### D-R180 · Blocked-by

**Rule:** A database's blocked-by is a relation within it; a row is blocked while a linked row is live, and a trashed blocker does not block. Choosing it is a schema edit for revive.

**Evidence:** Owner's answers 2026-10-03.

**Acceptance:** `JournalLinksTemplatesTest` blocks a row and unblocks it by trashing the blocker.

**Since:** 2026-10-03 · owner · migrated

### D-R181 · Templates

**Rule:** A template carries `is_template` in its page's making. It is kept out of the tree, rows, links, pickers and search, can be no page's parent, and is listed apart (`templates()`); the Trash shows it.

**Evidence:** Owner's answers 2026-10-03.

**Acceptance:** `JournalLinksTemplatesTest.aTemplateIsNotFoundNorAParentAndATrashedOneIsInTheTrash` makes a template and finds it only in `templates()` and the Trash, and `aTemplateIsNoDatabaseRowAndNoBoardOffersIt_SPEC_R181` keeps it out of a database's rows and a board's page picker.

**Since:** 2026-11-24 · owner · agreed rewording

### D-R182 · Copying a template

**Rule:** A copy is made in one write, with new ids throughout, and is independent of its template; it takes the structure below. A relation column's copy relates to the same database with a new matching column there, made only for a page, never for a template, which stays out of every database. A new database row starts empty.

**Values:**

| From | Copied |
|---|---|
| a page | its blocks, their nesting and the references inside them |
| a database | its shell colour, properties, live options and views, their settings; a filter naming source rows is dropped |
| a canvas | its board, with its mind-map links |

**Evidence:** Owner's answers 2026-10-03 (structure only; days and new rows start empty).

**Acceptance:** `JournalLinksTemplatesTest` copies each kind and edits the copy without touching the template.

**Since:** 2026-10-03 · owner · migrated

## 16. Checklists and charts

### D-R183 · Checklists

**Rule:** A checklist's name, place, last reset and deletion are field groups, and so are an item's text, tick, place and deletion. A reset is one stamp, and an item reads ticked only when ticked after it, so a tick made before a reset is cleared whenever it syncs. A deletion wins over an edit made apart.

**Evidence:** Chronicle's checklists; decision 14; `com.hazia.factotum.data.checklist`.

**Acceptance:** `ChecklistChartTest` passes.

**Since:** 2026-10-04 · owner · migrated

### D-R184 · Deleting a checklist

**Rule:** A list's deletion takes its items with a stamp just above each one's own, so a restore brings back exactly the items the deletion took, on any device, and an item deleted by hand meanwhile stays deleted. An item deleted by hand comes back from the list's Trash.

**Acceptance:** `ChecklistChartTest` and `VocabularyTest` delete a list with an item deleted by hand, restore it, and find that item still deleted.

**Since:** 2026-10-04 · builder · migrated

### D-R185 · Checklist order and text

**Rule:** Lists and charts have a manual order, a new one first; items are added last. Names and item text are never blank.

**Acceptance:** `ChecklistChartTest` adds lists, charts and items and refuses a blank name.

**Since:** 2026-10-04 · owner · migrated

### D-R186 · Saved charts

**Rule:** A chart's type is written once, its name, range and place are field groups, and its sources are rows (`chart_source:<chart>:<kind>:<source>`), so two devices adding one each keep both, and one taken off comes back when added again. A chart's series run over the personal days up to the one being read, per source as below. Chronicle's moving average and goal line are in `:core`.

**Values:**

| Source | A day's value |
|---|---|
| an activity | its whole minutes, each span on the day it started (R101); 0 when none |
| a tracker | its mean reading; none when it had no reading (how to draw that waits for the screens) |
| a deleted source | nothing drawn |
| a live recurring goal | a daily line |

**Evidence:** `com.hazia.factotum.data.chart`, `com.hazia.factotum.core.chart`.

**Acceptance:** `ChecklistChartTest` and `ChartsTest` pass.

**Not:** Chronicle cut sessions at midnight.

**Since:** 2026-10-04 · owner · migrated

## 17. Screens

### D-R187 · Screens are settled tier by tier

**Rule:** Screens are settled with the owner tier by tier, from the T0 frame to T6, mocked in HTML beside the source apps, and built only once agreed. Each cluster of screens gets its own wording register, set in its tier.

**Evidence:** Decision 15 (`decisions/15-screens.md`, owner 2026-10-05); the brief `docs/screens-workflow-prompt.md`. Not checked: no `:ui` code exists.

**Acceptance:** Every screen built in `:ui` has its approval recorded in `decisions/` and a mockup under `docs/screens/`, and a screenshot of the running app matches it.

**Since:** 2026-10-05 · owner · migrated

### D-R188 · Dark mode

**Rule:** The theme is System, Light or Dark, plus an OLED option on the phone only.

**Evidence:** Decision 15 (owner, 2026-10-05). Not checked: not built.

**Acceptance:** The settings offer the four choices on the phone and three on Windows.

**Since:** 2026-10-05 · owner · migrated

### D-R189 · Settings in two sections

**Rule:** Settings that follow the person are one section, "On every device", and this device's are another, "On this device".

**Evidence:** Decision 15 (owner, 2026-10-05). The sections follow the scopes of R118. Not checked: not built.

**Acceptance:** Every PERSONAL setting appears under "On every device" and every DEVICE_PREF setting under "On this device".

**Since:** 2026-10-05 · owner · migrated

### D-R190 · Fixed words

**Rule:** The words below are fixed, and their meanings are not used for anything else.

**Values:**

| Word | Means | Not used for |
|---|---|---|
| "Label" | the one label vocabulary (R109) | Tendril's Select property, which keeps "Tag" |
| "Log" | marking a habit (R80) | a check-in |
| "check-in" | a mood and energy record (R129) | a habit |

**Evidence:** ADR 05, ADR 06, ADR 08; decision 15.

**Acceptance:** The screens' wording uses each word only in its meaning.

**Since:** 2026-10-01 · owner · migrated

### Q-R191 · Navigation

**Rule:** What is the navigation pattern, and what are its destinations and icons?

**Default:** none proposed: the source leaves it to be scored with the design skills against real-world examples before the frame is mocked. `decisions/15-screens.md` records later rulings on it (the bar and the Hub, owner 2026-10-07) that this spec does not hold.

**Since:** 2026-10-05 · owner · migrated

### Q-R192 · Palette, type, shapes and density

**Rule:** What are the palette, type, shapes and density?

**Default:** none proposed: the source leaves each to be scored with the design skills against real-world examples before the frame is mocked; `decisions/15-screens.md` records palette slates with no pick.

**Since:** 2026-10-05 · owner · migrated

## 18. Phasing and validation

Background, not a rule: Equipoise runs llama.cpp on Android only, and only in the foreground, so the on-device LLM on Windows is a risk for the move of R06.

### D-R193 · Build order

**Rule:** The data layer goes first, in the steps below, in order; no screens are built before step 4.

**Values:**

| Step | Builds | Done when |
|---|---|---|
| 1 | the skeleton: the modules of R11 building on Android and Windows, and the corruption guard (R13) | the modules build on both platforms, and the guard's tests cover both drivers |
| 2 | the schema slices of R194 | each slice's ADR cases pass as tests |
| 3 | the sole-owner modules, in the order of R195 | not stated |
| 4 | the screens, after R187 settles each tier | not stated; a tier is built only once agreed |

**Evidence:** Owner, 2026-10-01. Steps 1 to 3 were built by 2026-10-04; the device halves of spikes 1, 3 and 5 wait for the Android shell (R197, R196, R61).

**Acceptance:** No `:ui` screen code exists before step 4 begins, and every slice of step 2 has its cases passing (R194).

**Since:** 2026-10-04 · owner · migrated

### D-R194 · Schema slices

**Rule:** The schema is built in ADR dependency order: 01, 02, 03, 04, 11, 06, 07, 08, 09, 10, 05, 12. A slice is done when its ADR's behaviour cases (`decisions/cases/<nn>-*.jsonl`) pass as tests against the real implementation.

**Evidence:** Three fresh-eyes audits checked the decision records: `docs/fresh-eyes-2026-09-30.md`, `docs/fresh-eyes-2026-10-01.md` and `docs/fresh-eyes-2026-10-01b.md`. Every decision was scored against its owners' behaviour cases, with a control option that failed as expected, and picked by the owner. `python tools/mutants.py` is the fail-before gate, with named kills.

**Acceptance:** Every case of every `decisions/cases/*.jsonl` file has a passing test, counted fresh from the JUnit XML (`tools/test_summary.py`).

**Since:** 2026-10-01 · owner · migrated

### D-R195 · Sole-owner module order

**Rule:** The sole-owner modules are built simplest first: formulas and rollups, then checklists and saved charts, regulation, database rows as tasks, and images.

**Evidence:** Decision 14 (`decisions/14-sole-owner-modules.md`, owner 2026-10-03).

**Acceptance:** none: an order of work, met by 2026-10-04 (history rows of R159, R183, R135, R162, R168).

**Since:** 2026-10-04 · owner · migrated

### A-R196 · Triggers on the Android driver

**Rule:** The app's triggers, installed from a database callback as Chronicle does on Android, install and fire on the Android driver as they do on the desktop one.

**Evidence:** Spike 3: on the desktop it holds (every trigger test runs on the bundled driver). Not checked: the device half runs with the Android shell, which has no code.

**Since:** 2026-10-03 · builder · migrated

### A-R197 · The search index on the phones

**Rule:** The phones' own SQLite (3.28 on Android 11, the minimum) makes the FTS4 index with `remove_diacritics=2`.

**Evidence:** Spike 1, desktop half (2026-10-03). Not checked: the phones' half, and whether they have FTS5, are measured with the Android shell.

**Since:** 2026-10-03 · builder · migrated

## Acceptance list

- R01 · Source behaviour survives: Every case in `decisions/cases/*.jsonl` passes as a test against the real implementation (R194).
- R02 · One home per concept: The data model (R18) holds one table family per concept, and no second table stores items, rules, labels, search text or sync state.
- R03 · Source defects fixed: The ADR cases that encode a fix pass as tests (R194).
- R04 · Jobs and how often: The navigation and screens decisions in `decisions/15-screens.md` and later tiers cite this table for every cadence they rely on, and no screen puts a weekly job above a daily one.
- R05 · Platforms: `:android` and `:windows` build from the repository root (`./gradlew --offline`).
- R06 · Every sole-owner module moves across: Each module in the table has its rules built and their tests passing; the features in the second sentence each have a screen or entry point once their tier is settled.
- R08 · App id and packages: `applicationId` is `com.hazia.factotum` with no suffix, and every Kotlin package starts with `com.hazia.factotum`.
- R09 · Personal use, one signing key: The installed APK's signing certificate has SHA-256 starting `20:FB:3E:76`, and every build type uses `signingConfigs.debug`.
- R11 · Modules split by layer: `:core` has no Room dependency, `:data` depends only on `:core`, and the build passes (`./gradlew --offline`).
- R12 · One write path: Every DAO in `:data` is `internal`, and the two-device tests through the composition root (R33) pass.
- R13 · Corruption guard: `KeepFileOnCorruptionDriverTest` and `BundledDriverCorruptionTest` cover the two drivers, with a control showing that the stock Android driver deletes a corrupt file; `DatabaseRecoveryTest` checks the order of build, probe and set-aside.
- R14 · Committed schema files: `tools/schema_check.py` passes.
- R15 · Upgrades drop the app's triggers first: A test upgrades a version 9 file holding the triggers and its child rows (`OldSchema.kt`).
- R17 · Licensing: The `:llm` build links only `llama` and `ggml` on both platforms, and the About screen shows llama.cpp's MIT notice.
- R18 · Synced tables: `FactotumDatabase.kt:222` checks at open that every synced table has its `RowTable`, and `FolderSyncTest.everySyncedTableIsQueuedForExportAndRoundTrips` makes a row in every synced table, finds each table in the outbox, and reads the same rows on a peer after sync.
- R19 · Local stores, never synced: No export trigger names a store in this table, and a peer that imports a device's folder never receives one of them.
- R20 · Folder sync for one person: `FolderSyncTest` syncs two devices through a shared folder and nothing else.
- R21 · Identity and stamps: The 10 cases of `decisions/cases/01-sync.jsonl` pass as tests on both targets (`SyncCasesTest`): 8 hold and 2 ask a person, as hybrid+ scored.
- R22 · Group values: `RecordCodecTest.aLineThatIsNotARecordIsRefused` refuses a value of another type, `ClockAndIdTest.aGroupRefusesADoubleThatNeverEqualsItself` a NaN, and `RecordCodecTest.aLineCarryingANaNOrAnInfiniteDoubleIsRefused` a line carrying NaN or an infinite Double.
- R23 · When a person is asked: The two asking cases of `decisions/cases/01-sync.jsonl` ask, and the other eight merge without a question (`SyncCasesTest`).
- R24 · Answers settle the clash everywhere: `ResolutionTest` checks each answer, and `FolderSyncTest.anAnswerSettlesTheQuestionOnBothDevices` an answer settling the question on both devices.
- R25 · The clock never goes back: `ClockAndIdTest` sets the wall clock back and gets a newer stamp.
- R26 · Old versions do not move the base: Replaying an older version of the other side through the folder leaves the base and any pending question as they were, and the next change on the other side is still asked.
- R27 · A permanent purge registry: The purge case of `decisions/cases/01-sync.jsonl` passes (`SyncCasesTest.tendrilPurgeHolds`), `FolderSyncTest.anImportTouchingOnePurgedIdReadsOneRegistryRow` reads one registry row for an import touching one of 30 purged ids, and `FolderSyncTest.aPurgeAlreadyHeldChangesNothingAndAnEarlierOneLowersIt` imports a purge already held, at its stamp and at a later one, with nothing changed, and an earlier one that lowers the entry.
- R28 · A purge undone by a later edit: After a purge is undone by a peer's later edit, both devices hold the same rows under the revived one.
- R29 · One deletion vocabulary: `VocabularyTest` walks every kind through Delete, its Trash, Restore, Delete again and Delete forever; a kind missing one does not compile or fails.
- R30 · What Delete and Restore take: `VocabularyTest` restores each kind and checks that exactly what its deletion took comes back.
- R31 · Delete forever: `VocabularyTest` checks that Delete forever of a live row of each kind is refused.
- R32 · The device id: `SyncStorageTest.anUnreadableDeviceIdIsSetAsideAndReplaced` sets an unreadable id file aside and makes a new id; the Android manifest's backup rules exclude the file.
- R33 · The composition root: Every two-device test runs through `Factotum` (`World.Device` delegates to it).
- R34 · Recovery re-reads its own files: `SettingsCasesTest.aDeviceWhoseDatabaseWasRecoveredGetsItsSettingsBackFromItsOwnFiles` recovers a device alone and finds its PERSONAL settings again, and `aRecoveredDeviceGetsItsRowsBackFromItsOwnFilesAndItsDeviceSettingsStartAtTheirDefaults` finds its rows again and its DEVICE settings at their defaults.
- R35 · Device logs in the folder: The 4 cases of `decisions/cases/13-folder.jsonl` pass through the real importer and exporter under a Syncthing double (`FolderSyncTest`).
- R36 · Folder requirements: `ExportTimingTest.aBurstOfWritesExportsOnceThirtySecondsAfterTheLast` (debounce), `DirectorySyncFolderTest.aReplaceLandsWholeAndLeavesNoTemporaryFile` (atomic replace), `RecordCodecTest.aRecordIsOneCompactLine` (compact JSON) and `FolderSyncTest.aReminderFiringLeavesTheOutboxEmpty` (a firing writes nothing) pass. In each shell, every export starts through `exportAfterQuiet` (R38), with no other production call to the export. The Android manifest's `dataExtractionRules` and `fullBackupContent` both exclude the device-id file (R32).
- R37 · Conflict copies: `FolderSyncTest.aClonedDeviceIdsClashIsMergedAndTheCopyRemoved` merges and deletes a conflict copy. `FolderSyncTest.aClonedIdIsOwedANewOneUntilTheDeviceRunsUnderAnother`: after one in its own folder the device owes a new id across imports; built again under a new id it owes none, its folder starts with a snapshot, and the clone and a third device hold every row with no further clash. `FolderSyncTest.aClonedIdIsOwedBeforeItsConflictCopyIsDeleted`: an import stopped at the copy's delete leaves the debt held. `SyncStorageTest.anOwedIdOutlivesAReopen` and `SyncStorageTest.aRenewedDeviceIdReplacesTheOldOneForGood` cover the debt and the id file. Each shell asks `newIdOwed` at start and after each import and, while owed, renews and builds again.
- R38 · A local outbox decides what to export: A write through any repository, and an import that changes a row, each leave the row queued for export.
- R39 · Imports in chunks: `FolderSyncTest` imports a snapshot larger than one chunk and stops and resumes it at a chunk boundary.
- R40 · Read positions: `FolderSyncTest.aPeerFileIsReadOnlyWhenItHasGrown`, `aLineStillBeingWrittenWaitsForItsNewline` and `aFileThatShrankIsReadAgainFromTheStart` pass.
- R41 · Lines this version cannot read: `FolderSyncTest` skips an unreadable line, applies it after the table set changes, and drops a line that breaks its table's rules.
- R42 · A row whose parent has not arrived waits: A completion imported before its item waits, then applies once the item arrives; one whose item was purged is dropped.
- R43 · A deleted row takes its merge state: Purging a row with a pending question leaves no base or question behind.
- R44 · Tables reach the importer through RowTable: Every synced table of R18 has its `RowTable`, and a snapshot of a large table is written with bounded memory.
- R45 · Folder implementations: `DirectorySyncFolderTest` passes; the SAF folder passes the same tests on a device.
- R46 · One item table: The 9 cases of `decisions/cases/02-task.jsonl` pass as tests against the real database: eight in `ItemCasesTest`, and `tendril-reminder-fk` in `ReminderCasesTest`.
- R47 · Names in code: No class, table or column in `core/` or `data/` is named Entry.
- R48 · Item field groups: `FolderSyncTest.anAnswerSettlesTheQuestionOnBothDevices` asks for a schedule clash, and `theDetailsAndStatusGroupsChangedOnTwoDevicesMergeWithNoQuestion` merges the details and status groups changed on two devices with no question, the later write standing.
- R49 · Kind rules are triggers: `ItemCasesTest.sharedEventHasNoTaskState_theDatabaseRefusesIt` and `theKindRulesHoldAfterAReopen` (updates), `PlannerCasesTest.plannedAndBlockRulesHold` (inserts), `HabitCasesTest.aTaskWithoutAStatusIsRefused`, `ReminderCasesTest.aStandaloneReminderNeedsATime` and `TimeCasesTest.activitiesKeepTheirOrderAndTheirColumnsStayTheirs` pass.
- R50 · The completion log: `FolderSyncTest.oneOccurrenceResolvedOnTwoDevicesReadsOneResultTheLater` resolves one occurrence on two devices, keeps two log rows and reads one result, the later.
- R51 · Subtasks go with their parent: `ItemCasesTest` and `VocabularyTest` delete, restore and purge a parent with subtasks.
- R52 · The capacity query: The query plan of the capacity query names `item_kind_date` and no table scan.
- R53 · Reminders on any item: The 11 cases of `decisions/cases/03-reminder.jsonl` pass: ten in `ReminderCasesTest`, and `chronicle-standalone-repeats` in `RecurringItemTest`, where `shared-one-recurrence-home` is also checked across every synced table.
- R54 · Reminder field groups: `FolderSyncTest.aSnoozeOnOneDeviceAndAnAlertChangeOnAnotherBothStayWithoutAQuestion` passes.
- R55 · Standalone reminders on the day view: `ReminderCasesTest` reads the day with the setting off and on.
- R56 · Fire time: `ReminderCasesTest` computes fire times across a DST change and after an item is done, skipped and deleted, and a firing writes no synced row.
- R57 · Snooze syncs: `ReminderCasesTest` snoozes on one device, reads the snooze on the other, then reschedules and gets the new time.
- R58 · A reminder needs a start date: `ReminderCasesTest` is refused in each of the three cases and keeps the synced reminder silent.
- R59 · A standalone reminder's last reminder: `ReminderCasesTest` deletes the last reminder and keeps both on a clash.
- R60 · Alarms and missed occurrences: On each platform an alarm set before the app is closed rings (Android) or is shown at the next start (Windows), and a missed NOTIFICATION fires once.
- R61 · A force-stopped app says so: On a device, force-stopping the app and opening it again shows the notice, and the alarms are set again.
- R62 · Recurrence kinds: The 11 cases of `decisions/cases/04-recurrence.jsonl` pass (`RecurrenceCasesTest`): the 9 fixed rules match, occurrence by occurrence, the truth `tools/recurrence_sim.py` computes from the owner apps' rules (written as a fixture by `tools/recurrence_fixtures.py`), Mnemo's three through the cron converter.
- R63 · Random forms: `RandomKindsTest` and `WhenKindsTest` pass.
- R64 · Seeded random draws: `RecurrenceCasesTest` compares the draws with the spike's own SplitMix64 in Python and in its Java, and checks the random kinds' properties.
- R65 · DTSTART and set times: `RecurrenceCasesTest.theNineFixedRulesGiveTheOwnerAppsOccurrences` and `aStartTheRuleDoesNotMatchIsNotAnOccurrence` cover an unaligned start, a cron rule from midnight and a month end, and `CronTest.severalLinesAreOneRuleTheirUnion` a rule set.
- R66 · Times are floating: `RecurrenceCasesTest.anUntilEndingInZIsReadAsLocal_SPEC_R66` reads an `UNTIL` ending in `Z` as the same local time without it, and expands it to that day.
- R67 · The expander: `RecurrenceCasesTest` and the expander's ported tests refuse each row's rule and pass the fixed rules.
- R68 · Cron is input only: `CronTest` passes.
- R69 · One recurrence engine: Tasks, events, reminders and habits all expand through `com.hazia.factotum.core.recurrence`, with no second expander in `core/` or `data/`.
- R70 · Reminders on a repeating item: `RecurringItemTest` passes, including a whole-day item reminded before its anchor after a firing has passed.
- R71 · The occurrence-edit log: The 10 cases of `decisions/cases/11-occurrence-edits.jsonl` pass on the engine (`OccurrenceEditsTest`, with `tools/occurrence_sim.py`'s fixture) and across two syncing devices (`OccurrenceEditSyncTest`).
- R72 · What each scope reaches: `OccurrenceEditsTest` applies each scope over moved and added occurrences, as `tools/occurrence_sim.py` does.
- R73 · A clash on one occurrence asks: `OccurrenceEditSyncTest` makes the clash on two devices and a third that saw only one, and asks exactly once.
- R74 · Answers are edits: `OccurrenceEditSyncTest` answers each way, answers differently on two devices, and is refused an update.
- R75 · Series edits: `OccurrenceEditsTest` renames a series with a moved occurrence.
- R76 · Habit fields in an edit: An edit carrying `sort_order`, `rule_patch` and `pause` round-trips through the folder unchanged.
- R77 · Edits reach reminders: `OccurrenceEditSyncTest.aSkippedOccurrenceDoesNotFireAndAMovedOneFiresAtItsNewTime`, `anAddedOccurrenceOnAWholeDayItemFiresAtTheAnchor`, `aRetimedOccurrenceFiresAtItsNewTimeWithoutBeingMoved` and `anAddedOccurrenceGivenATimeOnAWholeDayItemFiresAtThatTime` pass.
- R79 · Trackers move across as they are: `HabitCasesTest.trackerAndReadingRulesHold` refuses a row breaking each rule: a reading with two values or none, a rating of 0 or 6 on a reading or a default, a unit on a yes/no or rating tracker, and a default of any kind on a CHOICE tracker.
- R203 · A choice tracker's choices: `TrackerChoicesTest` adds, renames, recolours and moves choices and refuses a taken name, a blank one and a choice on a NUMBER tracker, and on a trashed tracker until its restore; refuses a Log of a deleted choice or another tracker's; restores and deletes forever from the Trash, with Logs keeping the id; merges two choices of one name made on two devices into the first on both, refuses to restore or delete forever the merged one, and Logs it as the first; brings back a choice Logged after its delete, directly or through a choice merged into it, but not one Logged before it or Logged and undone; keeps a rename made elsewhere when a move lands; and renumbers when a move falls between two tied places.
- R80 · A habit is an item over a tracker: The 8 cases of `decisions/cases/06-habit.jsonl` pass (`HabitCasesTest`), with the owner's answers.
- R81 · No streaks in Habits: No table or column stores a streak or missed-day count, and presence (R82) returns none.
- R82 · Presence: `HabitPresenceTest` and `HabitCasesTest` pass.
- R83 · Habit types and Logs: `HabitCasesTest` Logs a number habit with and without a value, a rating habit (refused without one) and a yes/no habit without one, and `aYesNoHabitLoggedWithAnExplicitValueKeepsIt` keeps an explicit no and an explicit yes.
- R84 · Deleting a tracker: `HabitCasesTest` and `VocabularyTest` delete, restore and purge a tracker with habits and goals.
- R85 · Habit columns: `HabitCasesTest.habitColumnsChangedOnTwoDevicesAskOnlyForTheSchedule` changes a details column on two devices with no question, then a schedule column on two devices with one.
- R86 · Pause: `PlannerCasesTest.twoHabitsOnOneTrackerPauseOnTheirOwn` passes.
- R87 · Rolling habits: `HabitCasesTest` rolls a habit by days and by a month.
- R88 · Logged occurrences are quiet: `HabitCasesTest.aLogNamingNoOccurrenceQuietsOnlyOneOfTheDays` Logs one dose of three, the other two still fire that day, and the next day's first fires as usual.
- R89 · Time blocks: `PlannerCasesTest` makes a database on two devices and finds the same five blocks.
- R90 · The week planner: `PlannerTest` and `PlannerCasesTest` pass.
- R91 · A confirmed week: `PlannerCasesTest` confirms a week, then applies an earlier skip and a later time, and both reach it.
- R92 · PLANNED habits: `PlannerTest` and `PlannerCasesTest` pass.
- R93 · Placing an occurrence: `PlannerCasesTest` (a set time in a block, an edit's block, a slot's block) and `PlannerTest` (a set time outside every block, the habit's block, `overlappingBlocksAreReportedOncePerOverlappingPair`) pass.
- R94 · Timed and whole-day occurrences: `PlannerCasesTest.aWholeDayOccurrenceIsPausedOnItsOwnDateWhenTheDayStartsLater` and `aTimedOccurrenceBeforeTheDayStartBelongsToTheDayBefore` (a pause and its reminder read an occurrence before the day start as the day before's) pass.
- R95 · An occurrence's block and order: `OccurrenceEditSyncTest.anOccurrencesBlockMovedOnTwoDevicesMergesWithoutAQuestion` moves an occurrence's block on one device while the other retimes it, and moves another's block on both, with no question and one result on both devices; `PlannerTest.habitsInABlockFollowTheirManualOrderThenTheirId` passes.
- R96 · Reminders on an "n a day" habit: `PlannerCasesTest` fires each occurrence at its block's start and an unblocked one at the anchor.
- R97 · Activities: `TimeCasesTest.activitiesKeepTheirOrderAndTheirColumnsStayTheirs` makes and orders activities, `reorderingAnActivityMovesItBetweenItsNewNeighbours` moves one to a fractional key between two others, and `PlannerTest.habitsInABlockFollowTheirManualOrderThenTheirId` orders a block's habits by `sort_order`, then id.
- R98 · One span table, several timers: The 9 cases of `decisions/cases/07-timelog.jsonl` pass (`TimeCasesTest`), two of them as later rulings changed them: `chronicle-activity-delete-refused` as R104, and `chronicle-activity-and-category-totals` without its category half (R117).
- R99 · Span field groups: `TimeCasesTest.aCommentWrittenOnOneDeviceDoesNotReopenATimerStoppedOnAnother`, `aStaleKeepOrStartEditDoesNotReopenOrReviveASpan` and `eachOfASpansFiveGroupsWrittenOnADifferentDeviceSurvives` (five devices, one group each) pass.
- R100 · A span's end is checked where it is written: `TimeCasesTest.tendrilExactlyOneOwner_aSpanHasOneOwnerOfAKindThatIsTimed` refuses an end before the start locally, and `aMergedSpanEndingBeforeItStartsCountsAsNothing` counts a span merged to end before its start as nothing.
- R101 · Day totals: `TimeTotalsTest` and `TimeCasesTest` pass. Not checked: amounts in the total wait for the amount table.
- R102 · Time is an activity's: spans and amounts: An amount added on a picked day syncs to a peer and counts in that day's total, and no tracker accepts a time unit.
- R103 · Goals on tracked time: `TimeTotalsTest.goalWindowsAreTheDayTheWeekFromMondayTheMonthFromThe1stAndAMilestones400Days` checks each window's bounds, and `TimeCasesTest.aGoalIsReachedInEachWindowThroughTheRepository` reaches a day, week, month and milestone goal through `ActivityRepository`, each counting only its window.
- R104 · Deleting an activity: `VocabularyTest` and `TimeCasesTest` delete, restore and purge an activity with a running timer.
- R105 · What ends a running timer: `TimeCasesTest` and `RowTasksTest` run each event with a timer running, locally and through an import.
- R106 · A timer past its limit asks: A span past 3x its activity's usual length is listed by `runningLong`, and each answer ends or keeps it as its words say (`TimeCasesTest`).
- R109 · One label vocabulary: The 10 cases of `decisions/cases/08-tagging.jsonl` pass: six in `LabelCasesTest`, `chronicle-applies-to-scope` as R110 changed it (`anyLabelGoesOnAnyElementAndEveryLiveLabelIsOffered`), and the page cases (`tendril-page-many-labels`, `tendril-page-delete-no-orphans`, the members half of `tendril-database-doorway`) in `PageCasesTest`.
- R110 · Labels are global: `LabelCasesTest.anyLabelGoesOnAnyElementAndEveryLiveLabelIsOffered` passes.
- R111 · How many labels each element carries: `LabelCasesTest` (one label on a habit, activity, task, event, standalone reminder, tracker and checklist, a second replacing the first; `aStandaloneReminderCarriesOneLabelAndASecondReplacesTheFirst_SPEC_R111`), `PageCasesTest` (many on a page) and `DatabaseCasesTest` (the doorway) pass.
- R112 · Label names are unique: `LabelCasesTest` refuses a second label differing only in case or form.
- R113 · Same-name labels merge: `LabelCasesTest` makes one name on two devices, syncs, and reads one label everywhere.
- R114 · Label field groups: `LabelCasesTest` renames and recolours on two devices and both stand.
- R115 · No foreign key on a label: `PageCasesTest` deletes a label carried by a trashed page, and the page stays trashed.
- R116 · A label in the Trash: `LabelCasesTest.aRestoredLabelIsBackOnWhatItsDeletionTookItOffAndOneDeletedForeverReadsAsNone`, `deletingASurvivorClearsWhatCarriedTheLabelsMergedIntoItAndADeadLabelIsNotEdited` and `VocabularyTest` pass.
- R117 · What a label counts: `VocabularyTest.aLabelCountsTheLiveElementsCarryingItEachOnce` counts each kind once, `LabelCasesTest` reads a merged label's elements, and `VocabularyTest.aTemplateCarryingALabelIsNotCounted_SPEC_R117` leaves a template out.
- R118 · Settings by scope: The 9 cases of `decisions/cases/09-settings.jsonl` pass (`SettingsCasesTest`): A and B share a folder, and C is a phone restored from A's backup.
- R119 · A typed registry: `SettingsCasesTest` reads an unreadable value as the default and clears a value set to its default.
- R120 · Setting keys: `SettingsCasesTest.eachSettingKeyHasItsScopeAndDefaultAndThePersonalOnesSync` reads each key's scope and default in the table and syncs the PERSONAL ones to a second device.
- R121 · Where each scope lives: `SettingsCasesTest.aPersonalSettingChangedOnTwoDevicesKeepsTheLaterAndTheDefaultClearsIt` sets one key on two devices and reads one row, and `aDevicePreferenceNeverReachesTheFolder` finds no DEVICE_PREF value in the folder or the `setting` table.
- R122 · Repositories read settings on every call: `SettingsCasesTest.theDayStartSetOnOneDeviceDecidesTheDayOnAnotherAtOnce` passes, and every repository that reads the day boundary takes it through a required parameter.
- R123 · The settings part of a backup: `SettingsCasesTest` restores an old backup on a phone and keeps the newer values; a backup with app lock on leaves it off.
- R124 · One search index: The 7 cases of `decisions/cases/10-search.jsonl` pass: the item, tracker and Log cases in `SearchCasesTest`, the page and block halves in `PageCasesTest`.
- R125 · What search indexes: `SearchCasesTest`, `PageCasesTest` and `ChecklistChartTest` find each source.
- R126 · Kept current by triggers: `SearchCasesTest` finds a row written by an import, and an index emptied by hand is rebuilt at the next open.
- R127 · What a search shows: `SearchCasesTest` and `PageCasesTest` search under each deleted parent and find nothing, and find a done task marked.
- R128 · Queries: `SearchCasesTest` orders names before text, ignores one letter, and finds a word with its accent typed apart mid-word.
- R129 · One check-in table, mood on its own axis: The 7 cases of `decisions/cases/05-checkin.jsonl` pass (`CheckInCasesTest`).
- R130 · No numbers on the check-in screen: The check-in screen's mockup and build show no number, average, count or curve.
- R131 · A check-in about a past day: `CheckInCasesTest` makes a check-in about yesterday and finds it on yesterday, and refuses one about tomorrow.
- R132 · Check-in field groups: `CheckInCasesTest` edits a note on one device while the other undoes the check-in, and it stays undone.
- R133 · Check-in scales: `CheckInScalesTest` passes.
- R134 · Check-in engines: `LowMomentTest`, `StabilityTrendTest` and `CheckInCasesTest.aCheckInMayBeAboutAPastDayButNotAFutureOneAndTheEnginesReadTheMoment` pass.
- R135 · The direction engine: `DirectionEngineSpikeTest`, `OnboardingTest`, `MixedModeTest` and `RegulationLedgerTest` pass.
- R136 · Outcome at the next open: `OutcomeAtNextOpenTest` passes.
- R137 · The masking ledger: `RegulationLedgerTest` makes one day on two devices, clears it on one, and taps it back.
- R138 · Sensory logs: `RegulationLedgerTest` writes and undoes a sensory log.
- R139 · The burnout index: `BurnoutIndexSpikeTest`, `MaskingLoadSpikeTest` and `RegulationLedgerTest` pass.
- R140 · Page parts are rows: The 8 cases of `decisions/cases/12-page-merge.jsonl` pass: five in `PageCasesTest`, the two cell cases in `DatabaseCasesTest`, and `shared-canvas-nodes` in `CanvasCasesTest`.
- R141 · Page and block field groups: `PageCasesTest.twoGroupsOfOneBlockEditedOnTwoDevicesBothStand_SPEC_R141` changes a block's type and text on one device and its attributes and place on another, and all four stand.
- R142 · Block order: `PageCasesTest.blocksNestAndKeepTheirOrderAfterTheKeysRunOutOfRoom`, `placingBlocksNeverWritesOverAMoveOrADeletionMadeElsewhere` and `OutlineTest` pass.
- R143 · Later text wins, earlier is kept: `PageCasesTest.theLaterTextWinsAndTheEarlierIsKeptInHistoryWithOneNoticeDismissedEverywhere` (two devices), `KeepLoserMergeTest.withThreeDevicesEveryReplacedTextIsLostSomewhereWhateverTheOrder` (three, in memory) and `PageCasesTest.withThreeDevicesEveryReplacedTextIsKeptInAHistoryAndNoticedEverywhere_SPEC_R143` (three, on the real database, read from History) pass.
- R144 · The replaced-by-a-sync notice: `PageCasesTest` makes a clash on two devices, dismisses the notice on one, and it stays dismissed on both.
- R145 · Revive: `PageCasesTest.aLaterEditBringsATrashedPageBackAndAnEarlierOneDoesNot`, `aLaterEditToASubPageBringsBackItsTrashedParents` and `aLaterEditBringsADeletedBlockBack` pass, and `aMoveALabelOrASubPageMadeUnderItAfterTheTrashBringsAPageBackStampedJustAboveTheTrash_SPEC_R145` brings pages back by a place, a label and a sub-page and reads each revival's stamp as the trash's time and device followed by `~`.
- R146 · The app's own writes are marked: `CanvasCasesTest` deletes a card and its parent on two devices and neither comes back.
- R147 · Trash, restore and delete forever for pages: `PageCasesTest` and `VocabularyTest` trash, restore and purge a page tree.
- R148 · What a merge can leave: `PageCasesTest` makes a cycle on two devices and reads both pages at the top.
- R149 · Page History: `PageCasesTest` writes, merges and restores versions and keeps fifty.
- R150 · Database tables: `DatabaseCasesTest` (`shared-cell-and-body`, `shared-cell-loser-recoverable`) passes.
- R151 · Cell values and type changes: `DatabaseCasesTest` changes a column's type both ways and reads the same stored values.
- R152 · A cell is kept when replaced: `DatabaseCasesTest` (`shared-cell-loser-recoverable`) passes, and two picks made apart both stand.
- R153 · A property in the Trash: `VocabularyTest` and `DatabaseCasesTest` delete, restore and purge a column and a relation pair.
- R154 · Select options: `DatabaseCasesTest` deletes, picks again, merges and restores options.
- R155 · Renames take the later name: `DatabaseCasesTest.aPropertyOptionAndViewRenamedOnTwoDevicesTakeTheLaterNameSilentlyAndShownColumnsSync_SPEC_R155` (the later names, with no notice or question, and the shown columns synced) and `aSortAndAFilterChangedApartBothStand` pass.
- R156 · A database's rows: `DatabaseCasesTest` and `PageCasesTest` read the members, trash and revive a database.
- R157 · Views: `DatabaseCasesTest.aViewSortsByTypeWithEmptyLastAndFiltersByType`, `aSelectSortsByItsOptionsOrderTextIgnoresCaseAndADateFilterReadsDates_SPEC_R157` and `aDatabaseKeepsOneViewAndATrashedOnesSchemaIsNotEdited` pass; the second sorts text in mixed case and filters it with "is" and "contains" typed in capitals.
- R158 · Databases in pages: The cases of `decisions/cases/16-databases.jsonl` pass against the real database.
- R159 · Formulas and rollups: `FormulaLexerTest`, `FormulaParserTest`, `FormulaTypeCheckerTest`, `FormulaDependencyGraphTest`, `FormulaEvaluatorTest`, `FormulaKeysTest` and `FormulaColumnsTest` pass.
- R160 · A formula is checked when written: `FormulaColumnsTest` is refused in each case.
- R161 · Where formulas differ from Tendril: `FormulaColumnsTest` covers each row.
- R162 · Database rows as tasks: `RowTasksTest` passes.
- R163 · A row task's life is its page's: `RowTasksTest` trashes, restores and purges from each side.
- R164 · Row-task clashes: `RowTasksTest` makes each clash on two devices.
- R165 · Bound columns read the task: `RowTasksTest.bindingOnADeviceThatHadNotSeenATrashDoesNotBringTheRowBack` and `unbindingOrTurningTasksOffOnADeviceThatHadNotSeenATrashDoesNotBringTheRowBack_SPEC_R165` pass.
- R166 · Repeating rows and intervals: `IntervalTest` and `RowTasksTest` pass.
- R167 · Rows changed: A write that adds a page to a database through the screens is followed by `rowsChanged()`, and the new row has its task.
- R168 · Pictures in pages: `ImagesTest` passes.
- R169 · Inserting a picture: `ImagesTest.aPictureIsScaledToAt2048TurnedUprightAndStrippedOfItsMetadata` and `aGifABmpAndAnAnimationAreReadWebpHeicAndCmykRefusedAndAJpegIsWrittenAtQuality85_SPEC_R169`, which also reads a TIFF and a WBMP, pass on the desktop; the device check passes on Android.
- R170 · Pictures through the folder: `ImagesTest` syncs a picture to a peer, damages a copy, and reads a waiting placeholder.
- R171 · Collecting pictures: `ImagesTest` collects the folder copy after 30 days unnamed and keeps the device copy History names.
- R172 · Canvas tables: `CanvasCasesTest` (`shared-canvas-nodes`) passes.
- R173 · Moving cards: `CanvasCasesTest.aCardMovedOnTwoDevicesTakesTheLaterPosition` and `aFrameAndACardInItMovedApartEachKeepTheirOwnLaterPosition_SPEC_R173` pass. Dragging a frame on the canvas screen moves the cards inside its box through one `moveNodes` call.
- R174 · Deleting a card: `CanvasCasesTest` and `VocabularyTest` delete, revive, restore and purge a card with lines and children.
- R175 · Page cards: `CanvasCasesTest` reads a page card in each of the four states.
- R176 · Canvas History: `CanvasCasesTest` replaces a card's text on two devices and restores it from History.
- R177 · The journal: `JournalLinksTemplatesTest` opens one day on two devices and finds one page.
- R178 · Road Map links: `JournalLinksTemplatesTest` removes and remakes a link and links a trashed page.
- R179 · Database relations: `JournalLinksTemplatesTest` and `DatabaseCasesTest` link rows from either side, remove and remake a link, and delete one column.
- R180 · Blocked-by: `JournalLinksTemplatesTest` blocks a row and unblocks it by trashing the blocker.
- R181 · Templates: `JournalLinksTemplatesTest.aTemplateIsNotFoundNorAParentAndATrashedOneIsInTheTrash` makes a template and finds it only in `templates()` and the Trash, and `aTemplateIsNoDatabaseRowAndNoBoardOffersIt_SPEC_R181` keeps it out of a database's rows and a board's page picker.
- R182 · Copying a template: `JournalLinksTemplatesTest` copies each kind and edits the copy without touching the template.
- R183 · Checklists: `ChecklistChartTest` passes.
- R184 · Deleting a checklist: `ChecklistChartTest` and `VocabularyTest` delete a list with an item deleted by hand, restore it, and find that item still deleted.
- R185 · Checklist order and text: `ChecklistChartTest` adds lists, charts and items and refuses a blank name.
- R186 · Saved charts: `ChecklistChartTest` and `ChartsTest` pass.
- R187 · Screens are settled tier by tier: Every screen built in `:ui` has its approval recorded in `decisions/` and a mockup under `docs/screens/`, and a screenshot of the running app matches it.
- R188 · Dark mode: The settings offer the four choices on the phone and three on Windows.
- R189 · Settings in two sections: Every PERSONAL setting appears under "On every device" and every DEVICE_PREF setting under "On this device".
- R190 · Fixed words: The screens' wording uses each word only in its meaning.
- R193 · Build order: No `:ui` screen code exists before step 4 begins, and every slice of step 2 has its cases passing (R194).
- R194 · Schema slices: Every case of every `decisions/cases/*.jsonl` file has a passing test, counted fresh from the JUnit XML (`tools/test_summary.py`).
- R198 · Importing data from the source apps: No code in `core/`, `data/`, `android/` or `windows/` reads a source app's database or sync files.
- R199 · A sync server, accounts or cloud storage: No code opens a network connection for sync.
- R200 · Source mechanisms not carried over: No table or column of those names exists in `data/schemas/`.
- R202 · Tendril's Claude text verbs: No code calls the Claude API.

## Out of scope

### D-R198 · Importing data from the source apps

**Rule:** No data is migrated from the four source apps, and nothing is built to read their databases or sync files. Migration cost is never a reason for a design.

**Why:** Factotum is a fresh start (owner, 2026-09-30).

**Acceptance:** No code in `core/`, `data/`, `android/` or `windows/` reads a source app's database or sync files.

**Since:** 2026-09-30 · owner · migrated

### D-R199 · A sync server, accounts or cloud storage

**Rule:** Factotum has no sync server, accounts or cloud storage.

**Why:** Folder sync for one person needs none (R20).

**Acceptance:** No code opens a network connection for sync.

**Since:** 2026-09-30 · owner · migrated

### D-R200 · Source mechanisms not carried over

**Rule:** The source-app mechanisms below are not carried over; their behaviour is kept where the row says.

**Why:** One home per concept (R02).

**Values:**

| Mechanism | Kept by |
|---|---|
| Tendril's `.tendril-lost` folder files | the notice and History (R144, R149) |
| Tendril's Entry exception columns and `HabitScheduleEdit` | the occurrence-edit log (R71) |
| Tendril's stored streak columns and `show_habit_streaks` | nothing (R81) |
| the four settings stores | the scoped registry (R118) |
| Tendril's and Chronicle's separate FTS tables | the one index (R124) |
| Equipoise's parked `greyDay` column | nothing (ADR 09) |

**Acceptance:** No table or column of those names exists in `data/schemas/`.

**Since:** 2026-10-01 · owner · migrated

### D-R201 · Waking a powered-off phone

**Rule:** Factotum does not wake a powered-off phone to ring an alarm.

**Why:** No third-party app can do it.

**Acceptance:** none: a platform limit, with nothing to build.

**Since:** 2026-10-01 · unrecorded · migrated

### D-R202 · Tendril's Claude text verbs

**Rule:** Tendril's opt-in Claude text verbs do not move across.

**Why:** The owner accepted this exception to R06 (decision 15, `docs/screens/t0/jobs.md`).

**Acceptance:** No code calls the Claude API.

**Since:** 2026-10-05 · owner · migrated
