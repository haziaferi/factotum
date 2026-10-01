# Contest 13 evidence: how comparable apps lay out a synced folder

Web research, 2026-10-01, by a Sonnet 5.5 agent. Quotes are short and taken from fetched pages. "Paraphrase" means the fetch tool summarised the page instead of quoting it. UNVERIFIED marks a claim that was not confirmed.

## Syncthing behaviour (the transport)

- **Conflict copies.** A copy is named `<filename>.sync-conflict-<date>-<time>-<modifiedBy>.<ext>`. "The file with the older modification time will be marked as the conflicting file." When the times are equal, the device with "the larger value of the first 63 bits" of its device ID loses. Conflict copies "are treated as normal files... so they are propagated". Source: https://docs.syncthing.net/users/syncing.html
- **Atomic replace.** Syncthing writes a temp file, then renames it, "as the rename... has to be atomic". Source: https://forum.syncthing.net/t/how-to-set-temporary-files-location/13360
- **No ordering.** There is "no ordering of operations between folders", and the BEP spec has "no required order or synchronization among BEP messages". Sources: https://forum.syncthing.net/t/sync-operations-order/10789 and https://docs.syncthing.net/specs/bep-v1.html
- **Blocks.** Blocks run "from 128 KiB... to 16 MiB". Only changed blocks are transferred. Source: BEP spec.
- **Scanning.** Syncthing rescans "every hour when watching for changes or every minute if that's disabled". Source: https://docs.syncthing.net/users/faq.html
- **Android.** "Storage access is very slow in Android 11 and newer", especially with many files in one folder (https://forum.syncthing.net/t/syncthing-fork-slow-due-to-android-filesystem-abstraction-layer/24040/2). With 55,000 files on Android 11, scanning slows after 10,000 to 16,000 files to "one file every few seconds" (https://github.com/syncthing/syncthing-android/issues/1630).

## Apps

| Layout | Apps | Documented failures | Sources |
|---|---|---|---|
| One file per entity | Obsidian, Logseq (file graph), Joplin | Config and UI-state files conflict. Small edits rewrite the whole file. One device's edit replaces the other's. File-count limits: a 150,000-item OneDrive cap, and Android scan slowdowns. With Syncthing, Joplin's lock files cancel its own sync. | forum.obsidian.md/t/44853; discuss.logseq.com/t/26744; joplinapp.org/news/20200906-172325; github.com/laurent22/joplin/issues/9759 |
| One monolithic file (snapshot or op-log) | Super Productivity v2, KeePassXC | Writes are last-writer or produce a conflict copy. "approximately 2% of seq-0 hydrations dropped operations". A merge tool is needed for conflict copies. | github.com/super-productivity/super-productivity/issues/10256; github.com/keepassxreboot/keepassxc/issues/4192, /10225 |
| Ops file plus snapshot | Super Productivity v3 (opt-in) | A mixed-version overwrite. An interrupted Android write was misread as an empty folder. Atomic writes are unresolved. | github.com/super-productivity/super-productivity/issues/10395 (paraphrase) |
| Live database in the folder | Trilium, Zotero, Calibre, SiYuan | Corruption ("database disk image is malformed"). The vendors say not to do it. | docs.triliumnotes.org/user-guide/faq; forums.zotero.org/discussion/66342; mobileread t=265174 |
| Per-device append-only logs | outl, Tonsky's design | "each device only writes its own file", so "Dropbox will not report any conflicts". The costs are read positions, log growth and batching. | outl.app/docs/sync; tonsky.me/blog/crdt-filesync |
| Content-addressed immutable chunks plus compaction | Automerge repo | Chunks are incremental or snapshot. Compaction deletes only the chunks it has already loaded. | automerge.org/docs/reference/under-the-hood/storage; patternist.xyz/posts/concurrent-compaction-in-automerge-repo (paraphrase) |
| Protocol sync, no shared folder | Anytype, Trilium's server, SiYuan's S3 and WebDAV | Not comparable. | tech.anytype.io/any-sync/overview |

UNVERIFIED: any measured end-to-end Syncthing latency; a files-per-folder limit on Windows desktop; Kleppmann's file-sync paper.
