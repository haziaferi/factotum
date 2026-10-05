# Reference apps: how navigation is measured

This is the input to the navigation scoring (decision 15, Q2). Every reference app is measured the same way, on the same jobs (`jobs.md`). This lets their numbers be compared with each other, and later with Factotum's candidates and the built app.

## Privacy

- **The owner's real installs and accounts** (Notion, Google Calendar, Fossify Calendar, Todoist and so on) are measured for **geometry only**. The UI tree is read to count taps and destinations; **no screenshot is kept and no content is written down**. Only numbers and control labels are recorded, never item text.
- **Apps installed fresh for this**, with no account or an empty one, may be screenshotted into `_screens-sources/reference/<app>/` (gitignored).
- **Logins:** where an app needs one, the owner signs in on the phone or the PC when it is handed over. Claude never creates an account and never types a password.
- **Installs come from:**
  - the phone: Aurora or Droid-ify, never Google Play;
  - this PC: the app's own installer or winget.

  Anything installed for the survey is uninstalled when the survey phase ends, unless the owner already used it.

## What is measured, per app and per form factor (phone; Windows or web at 840dp and up)

| Measure | How |
|---|---|
| **Pattern** | The persistent navigation: bottom bar, rail, sidebar, drawer, hub, tabs or none. |
| **Destinations** | The number of items in the persistent navigation, with their labels as shown. |
| **Taps per job** | For each job the app supports, from a cold launch (the app's own start screen) to the screen or control where the job is done. A tap, a swipe or a key chord is one. Typing a search query is one step. For J1, count to a focused input; for J4, to the control that logs. |
| **From anywhere** | Whether the job has an affordance that works from any screen: a FAB on every screen, a global hotkey, a widget, the share sheet, a notification action. |
| **Search reach** | Whether search or a switcher reaches the job's target, and in how many steps. |
| **Phone ↔ desktop** | Whether the same destinations appear in the same order on both, and what changes. |

A job the app does not support is recorded as **n/a**, not as a cost.

## Jobs measured

These are the J-numbers from `jobs.md`:
- **J1** catch (to a focused input);
- **J2** see what's next (to today's list or agenda);
- **J4** do and log (to the tick or log control of a daily item);
- **J5** check in (to the mood input);
- **J6** plan (to the week view, and to a new item's recurrence field);
- **J7** write (to today's journal page, and to a new page's body);
- **J8** find (to search with focus);
- **J9** look back (to a stats or chart screen);
- **J10** settings (to the settings root).

J3 (prompts) arrives and is not measured.

## Output

`reference.json` holds one record per app and form factor, with the measures above. `reference.md` is the comparison table, and lists every app that was left out and why.
