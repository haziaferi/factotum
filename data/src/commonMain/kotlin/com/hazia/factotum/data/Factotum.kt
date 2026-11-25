package com.hazia.factotum.data

import com.hazia.factotum.core.sync.HybridClock
import com.hazia.factotum.data.chart.ChartRepository
import com.hazia.factotum.data.checkin.CheckInRepository
import com.hazia.factotum.data.checkin.LedgerRepository
import com.hazia.factotum.data.checkin.RegulationRepository
import com.hazia.factotum.data.checklist.ChecklistRepository
import com.hazia.factotum.data.image.BlobStore
import com.hazia.factotum.data.image.BlobSync
import com.hazia.factotum.data.image.ImageRepository
import com.hazia.factotum.data.image.ImageScaler
import com.hazia.factotum.data.item.HabitRepository
import com.hazia.factotum.data.item.ItemRepository
import com.hazia.factotum.data.item.OccurrenceRepository
import com.hazia.factotum.data.label.LabelRepository
import com.hazia.factotum.data.page.CanvasRepository
import com.hazia.factotum.data.page.DatabaseRepository
import com.hazia.factotum.data.page.JournalRepository
import com.hazia.factotum.data.page.PageRepository
import com.hazia.factotum.data.page.RelationRepository
import com.hazia.factotum.data.page.RowTaskRepository
import com.hazia.factotum.data.page.TemplateRepository
import com.hazia.factotum.data.reminder.ReminderRepository
import com.hazia.factotum.data.settings.SecretStore
import com.hazia.factotum.data.settings.SettingsRepository
import com.hazia.factotum.data.sync.FolderSync
import com.hazia.factotum.data.sync.ImportReport
import com.hazia.factotum.data.sync.RowTable
import com.hazia.factotum.data.sync.SyncFolder
import com.hazia.factotum.data.time.ActivityRepository
import com.hazia.factotum.data.time.TimeRepository
import com.hazia.factotum.data.tracker.TrackerRepository
import kotlinx.datetime.LocalDateTime

/**
 * The data layer as one device runs it (SPEC:R33): every repository over one database, and sync over
 * one folder, wired in the one order the rules need. Each shell builds this once, from its own
 * database, folder, secret store, picture store and scaler; tests build it the same way. What
 * the shells see of it waits for the screens (SPEC:R187).
 *
 * - [export] publishes the pictures the logs will name, then writes the logs (SPEC:R170).
 * - [import] reads the logs and settles what peers wrote, then fetches and collects pictures.
 * - [rowsChanged] runs after a local write that changes which pages are rows of a database (a page
 *   made, moved, trashed or restored, a label put on or taken off, a doorway set), so their tasks
 *   follow at once (rows as tasks).
 */
internal class Factotum(
    val db: FactotumDatabase,
    folder: SyncFolder,
    device: String,
    clock: HybridClock,
    secrets: SecretStore,
    blobs: BlobStore,
    scaler: ImageScaler,
    newId: () -> String,
    /** The wall clock, in milliseconds: History's times and how long a picture has gone unused. */
    wallMillis: () -> Long,
    /** The wall clock as a local date-time, for the rules that read the day (time, rows as tasks). */
    private val now: () -> LocalDateTime,
    /** The database was made anew after a corrupt one was set aside (`DatabaseOpen.recovered`). */
    recovered: Boolean = false,
    tables: Map<String, RowTable> = db.syncedTables(),
    segmentBytes: Int = 16 * 1024,
    snapshotEvery: Int = 64,
) {
    val writes = LocalWrites(db, clock)
    val settings = SettingsRepository(db, writes, secrets)
    val items = ItemRepository(db, writes, newId, now)
    val reminders = ReminderRepository(db, writes, newId, settings)
    val occurrences = OccurrenceRepository(db, writes, newId, settings)
    val habits = HabitRepository(db, writes, newId, settings)
    val trackers = TrackerRepository(db, writes, newId)
    val time = TimeRepository(db, writes, newId, settings)
    val activities = ActivityRepository(db, writes, newId, settings, now)
    val labels = LabelRepository(db, writes, newId)
    val checkIns = CheckInRepository(db, writes, newId, settings)
    val pages = PageRepository(db, writes, newId, wallMillis, now)
    val databases = DatabaseRepository(db, writes, newId, pages)
    val canvases = CanvasRepository(db, writes, newId, pages)
    val journal = JournalRepository(db, writes, settings)
    val relations = RelationRepository(db, writes)
    val templates = TemplateRepository(db, writes, newId)
    val checklists = ChecklistRepository(db, writes, newId)
    val charts = ChartRepository(db, writes, newId, settings)
    val regulation = RegulationRepository(db, writes, newId, settings)
    val ledger = LedgerRepository(db, writes, newId, settings)
    val rowTasks = RowTaskRepository(db, writes, items, occurrences, databases, settings, now)
    val images = ImageRepository(pages, blobs, scaler)
    private val blobSync = BlobSync(db, folder, blobs, wallMillis)

    /**
     * The rules that follow from what peers wrote, after every import, in this order: duplicate
     * labels merge (ADR 08); finished timers end (ADR 07); a row task's clash with its page's trash
     * is settled before revive reads it; pages keep what a sync replaced and revive; options and
     * cards settle; rows' tasks follow their rows.
     */
    val sync = FolderSync(db, folder, device, clock, tables, segmentBytes, snapshotEvery, recovered = recovered, afterImport = {
        labels.mergeDuplicates()
        time.endFinished(now())
        rowTasks.settleClashes()
        pages.settle()
        databases.settle()
        canvases.settle()
        rowTasks.settle()
    })

    suspend fun export() {
        blobSync.exchange()
        sync.export()
    }

    suspend fun import(): ImportReport = sync.import().also { blobSync.exchange() }

    /**
     * Whether this device must take a new id (SPEC:R37). The shell asks at start and after each
     * import; when it must, it writes a new id with `renewDeviceId` and builds this again over the
     * same database and folder, with a clock loaded for the new id.
     */
    suspend fun newIdOwed(): Boolean = sync.newIdOwed()

    suspend fun rowsChanged() = rowTasks.settle()
}
