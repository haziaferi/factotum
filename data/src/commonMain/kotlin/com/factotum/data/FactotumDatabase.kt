package com.factotum.data

import androidx.room.AutoMigration
import androidx.room.ConstructedBy
import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.RoomDatabaseConstructor
import androidx.room.migration.AutoMigrationSpec
import androidx.sqlite.SQLiteConnection
import com.factotum.data.item.COMPLETION
import com.factotum.data.item.HABIT_BLOCK
import com.factotum.data.item.HabitBlockEntity
import com.factotum.data.item.habitBlockTable
import com.factotum.data.item.seedBlocks
import com.factotum.data.item.CompletionEntity
import com.factotum.data.item.completionTable
import com.factotum.data.item.ITEM
import com.factotum.data.item.ItemDao
import com.factotum.data.item.ItemEntity
import com.factotum.data.item.OCCURRENCE_EDIT
import com.factotum.data.item.OccurrenceEditEntity
import com.factotum.data.item.occurrenceEditTable
import com.factotum.data.item.itemTable
import com.factotum.data.reminder.REMINDER
import com.factotum.data.reminder.ReminderDao
import com.factotum.data.reminder.ReminderEntity
import com.factotum.data.reminder.reminderTable
import com.factotum.data.sync.AskEntity
import com.factotum.data.tracker.GOAL
import com.factotum.data.tracker.GoalEntity
import com.factotum.data.tracker.TRACKER
import com.factotum.data.tracker.TRACKER_CHOICE
import com.factotum.data.tracker.TRACKER_READING
import com.factotum.data.tracker.TrackerChoiceEntity
import com.factotum.data.tracker.TrackerDao
import com.factotum.data.tracker.TrackerEntity
import com.factotum.data.tracker.TrackerReadingEntity
import com.factotum.data.tracker.choiceTable
import com.factotum.data.tracker.goalTable
import com.factotum.data.tracker.readingTable
import com.factotum.data.tracker.trackerTable
import com.factotum.data.sync.BaseEntity
import com.factotum.data.sync.ClockEntity
import com.factotum.data.sync.KnownTablesEntity
import com.factotum.data.sync.OutboxEntity
import com.factotum.data.sync.PurgeEntity
import com.factotum.data.sync.ReadEntity
import com.factotum.data.sync.RowTable
import com.factotum.data.sync.SyncDao
import com.factotum.data.sync.WaitingEntity
import com.factotum.data.label.LABEL
import com.factotum.data.label.LabelDao
import com.factotum.data.label.LabelEntity
import com.factotum.data.label.labelTable
import com.factotum.data.settings.DeviceSettingEntity
import com.factotum.data.settings.SETTING
import com.factotum.data.settings.SettingDao
import com.factotum.data.settings.SettingEntity
import com.factotum.data.settings.settingTable
import com.factotum.data.search.SearchDao
import com.factotum.data.checkin.CHECK_IN
import com.factotum.data.checkin.CheckInDao
import com.factotum.data.checkin.CheckInEntity
import com.factotum.data.checkin.MASKING_ENTRY
import com.factotum.data.checkin.MaskingEntryEntity
import com.factotum.data.checkin.PendingOutcomeEntity
import com.factotum.data.checkin.REGULATION_EVENT
import com.factotum.data.checkin.RegulationDao
import com.factotum.data.checkin.RegulationEventEntity
import com.factotum.data.checkin.SENSORY_LOG
import com.factotum.data.checkin.SensoryLogEntity
import com.factotum.data.checkin.maskingTable
import com.factotum.data.checkin.regulationEventTable
import com.factotum.data.checkin.sensoryTable
import com.factotum.data.checkin.checkInTable
import com.factotum.data.search.SearchKeyEntity
import com.factotum.data.search.SearchTextEntity
import com.factotum.data.time.TIME_SPAN
import com.factotum.data.time.TimeDao
import com.factotum.data.time.TimeSpanEntity
import com.factotum.data.time.timeSpanTable
import com.factotum.data.page.BLOCK
import com.factotum.data.chart.CHART_SOURCE
import com.factotum.data.chart.ChartDao
import com.factotum.data.chart.ChartSourceEntity
import com.factotum.data.chart.SAVED_CHART
import com.factotum.data.chart.SavedChartEntity
import com.factotum.data.chart.chartSourceTable
import com.factotum.data.chart.chartTable
import com.factotum.data.checklist.CHECKLIST
import com.factotum.data.checklist.CHECKLIST_ITEM
import com.factotum.data.checklist.ChecklistDao
import com.factotum.data.checklist.ChecklistEntity
import com.factotum.data.checklist.ChecklistItemEntity
import com.factotum.data.checklist.checklistItemTable
import com.factotum.data.checklist.checklistTable
import com.factotum.data.page.LinkDao
import com.factotum.data.page.PAGE_RELATION
import com.factotum.data.page.PageRelationEntity
import com.factotum.data.page.RELATION_LINK
import com.factotum.data.page.RelationLinkEntity
import com.factotum.data.page.linkTable
import com.factotum.data.page.relationTable
import com.factotum.data.page.CANVAS_EDGE
import com.factotum.data.page.CANVAS_NODE
import com.factotum.data.page.CanvasDao
import com.factotum.data.page.CanvasEdgeEntity
import com.factotum.data.page.CanvasNodeEntity
import com.factotum.data.page.PAGE_CANVAS
import com.factotum.data.page.PageCanvasEntity
import com.factotum.data.page.canvasTable
import com.factotum.data.page.edgeTable
import com.factotum.data.page.nodeTable
import com.factotum.data.page.DatabaseDao
import com.factotum.data.page.OptionEntity
import com.factotum.data.page.PAGE_DATABASE
import com.factotum.data.page.PAGE_VIEW
import com.factotum.data.page.PROPERTY
import com.factotum.data.page.PROPERTY_OPTION
import com.factotum.data.page.PROPERTY_VALUE
import com.factotum.data.page.PageDatabaseEntity
import com.factotum.data.page.PropertyEntity
import com.factotum.data.page.PropertyValueEntity
import com.factotum.data.page.VALUE_PICK
import com.factotum.data.page.ValuePickEntity
import com.factotum.data.page.ViewEntity
import com.factotum.data.page.databaseTable
import com.factotum.data.page.optionTable
import com.factotum.data.page.pickTable
import com.factotum.data.page.propertyTable
import com.factotum.data.page.valueTable
import com.factotum.data.page.viewTable
import com.factotum.data.page.BlockEntity
import com.factotum.data.page.PAGE
import com.factotum.data.page.PAGE_LABEL
import com.factotum.data.page.PAGE_NOTICE
import com.factotum.data.page.PageDao
import com.factotum.data.page.PageEntity
import com.factotum.data.page.PageLabelEntity
import com.factotum.data.page.PageNoticeEntity
import com.factotum.data.page.PageRevisionEntity
import com.factotum.data.page.blockTable
import com.factotum.data.page.noticeTable
import com.factotum.data.page.pageLabelTable
import com.factotum.data.page.pageTable
import com.factotum.data.sync.LostEntity

@Database(
    entities = [
        PurgeEntity::class, ClockEntity::class,
        BaseEntity::class, AskEntity::class, ReadEntity::class, OutboxEntity::class, KnownTablesEntity::class,
        WaitingEntity::class, ItemEntity::class, CompletionEntity::class, ReminderEntity::class, OccurrenceEditEntity::class,
        TrackerEntity::class, TrackerChoiceEntity::class, TrackerReadingEntity::class, GoalEntity::class, HabitBlockEntity::class,
        TimeSpanEntity::class, LabelEntity::class, SettingEntity::class, DeviceSettingEntity::class,
        SearchTextEntity::class, SearchKeyEntity::class, CheckInEntity::class,
        PageEntity::class, BlockEntity::class, PageLabelEntity::class, PageNoticeEntity::class, PageRevisionEntity::class, LostEntity::class,
        PageDatabaseEntity::class, PropertyEntity::class, OptionEntity::class, PropertyValueEntity::class, ValuePickEntity::class, ViewEntity::class,
        PageCanvasEntity::class, CanvasNodeEntity::class, CanvasEdgeEntity::class, PageRelationEntity::class, RelationLinkEntity::class,
        ChecklistEntity::class, ChecklistItemEntity::class, SavedChartEntity::class, ChartSourceEntity::class,
        SensoryLogEntity::class, MaskingEntryEntity::class, RegulationEventEntity::class, PendingOutcomeEntity::class,
    ],
    version = SCHEMA_VERSION,
    exportSchema = true,
    autoMigrations = [
        AutoMigration(from = 1, to = 2), AutoMigration(from = 2, to = 3), AutoMigration(from = 3, to = 4), AutoMigration(from = 4, to = 5),
        AutoMigration(from = 5, to = 6), AutoMigration(from = 6, to = 7), AutoMigration(from = 7, to = 8, spec = SeedBlocks::class),
        AutoMigration(from = 8, to = 9), AutoMigration(from = 9, to = 10), AutoMigration(from = 10, to = 11), AutoMigration(from = 11, to = 12), AutoMigration(from = 12, to = 13),
        AutoMigration(from = 13, to = 14), AutoMigration(from = 14, to = 15), AutoMigration(from = 15, to = 16), AutoMigration(from = 16, to = 17), AutoMigration(from = 17, to = 18), AutoMigration(from = 18, to = 19), AutoMigration(from = 19, to = 20),
    ],
)
@ConstructedBy(FactotumDatabaseConstructor::class)
abstract class FactotumDatabase : RoomDatabase() {
    internal abstract fun syncDao(): SyncDao
    internal abstract fun itemDao(): ItemDao
    internal abstract fun reminderDao(): ReminderDao
    internal abstract fun trackerDao(): TrackerDao
    internal abstract fun timeDao(): TimeDao
    internal abstract fun labelDao(): LabelDao
    internal abstract fun settingDao(): SettingDao
    internal abstract fun searchDao(): SearchDao
    internal abstract fun checkInDao(): CheckInDao
    internal abstract fun pageDao(): PageDao
    internal abstract fun databaseDao(): DatabaseDao
    internal abstract fun canvasDao(): CanvasDao
    internal abstract fun linkDao(): LinkDao
    internal abstract fun checklistDao(): ChecklistDao
    internal abstract fun chartDao(): ChartDao
    internal abstract fun regulationDao(): RegulationDao
}

/** The synced tables, by the name their folder records carry; [SchemaTriggers] queues writes to each for export. */
internal val SYNCED_TABLES = listOf(SETTING, LABEL, TRACKER, TRACKER_CHOICE, HABIT_BLOCK, ITEM, TIME_SPAN, COMPLETION, REMINDER, OCCURRENCE_EDIT, TRACKER_READING, GOAL, CHECK_IN, PAGE, PAGE_DATABASE, PROPERTY, PROPERTY_OPTION, PAGE_VIEW, PAGE_CANVAS, CANVAS_NODE, CANVAS_EDGE, BLOCK, PAGE_LABEL, PAGE_NOTICE, PROPERTY_VALUE, VALUE_PICK, PAGE_RELATION, RELATION_LINK, CHECKLIST, CHECKLIST_ITEM, SAVED_CHART, CHART_SOURCE, SENSORY_LOG, MASKING_ENTRY, REGULATION_EVENT)

/** In [SYNCED_TABLES]' order, parents before children, which is the order a snapshot is written in. */
internal fun FactotumDatabase.syncedTables(): Map<String, RowTable> {
    val items = itemDao()
    val trackers = trackerDao()
    val pages = pageDao()
    val databases = databaseDao()
    val canvases = canvasDao()
    val links = linkDao()
    return mapOf(
        SETTING to settingTable(settingDao()), LABEL to labelTable(labelDao()), TRACKER to trackerTable(trackers), TRACKER_CHOICE to choiceTable(trackers), HABIT_BLOCK to habitBlockTable(items), ITEM to itemTable(items),
        TIME_SPAN to timeSpanTable(timeDao()),
        COMPLETION to completionTable(items), REMINDER to reminderTable(reminderDao()), OCCURRENCE_EDIT to occurrenceEditTable(items),
        TRACKER_READING to readingTable(trackers), GOAL to goalTable(trackers), CHECK_IN to checkInTable(checkInDao()),
        PAGE to pageTable(pages), PAGE_DATABASE to databaseTable(databases), PROPERTY to propertyTable(databases), PROPERTY_OPTION to optionTable(databases),
        PAGE_VIEW to viewTable(databases), PAGE_CANVAS to canvasTable(canvases), CANVAS_NODE to nodeTable(canvases), CANVAS_EDGE to edgeTable(canvases),
        BLOCK to blockTable(pages), PAGE_LABEL to pageLabelTable(pages), PAGE_NOTICE to noticeTable(pages),
        PROPERTY_VALUE to valueTable(databases), VALUE_PICK to pickTable(databases), PAGE_RELATION to relationTable(links), RELATION_LINK to linkTable(links),
        CHECKLIST to checklistTable(checklistDao()), CHECKLIST_ITEM to checklistItemTable(checklistDao()), SAVED_CHART to chartTable(chartDao()), CHART_SOURCE to chartSourceTable(chartDao()),
        SENSORY_LOG to sensoryTable(regulationDao()), MASKING_ENTRY to maskingTable(regulationDao()), REGULATION_EVENT to regulationEventTable(regulationDao()),
    ).also { check(it.keys.toList() == SYNCED_TABLES) { "every synced table needs its export triggers" } }
}

/** Version 8 brings the time blocks, and a database that had none gets the defaults a new one starts with. */
internal class SeedBlocks : AutoMigrationSpec {
    override fun onPostMigrate(connection: SQLiteConnection) = seedBlocks(connection)
}

// Room's KSP processor generates the actual for each target.
@Suppress("KotlinNoActualForExpect")
expect object FactotumDatabaseConstructor : RoomDatabaseConstructor<FactotumDatabase>

const val DATABASE_NAME = "factotum.db"

/** The schema's version; a file below it is upgraded by Room's migrations on open. */
internal const val SCHEMA_VERSION = 20
