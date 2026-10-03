package com.factotum.data.page

import com.factotum.core.habit.dayOf
import com.factotum.core.sync.Stamp
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.settings.PersonalSettings
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime

internal const val JOURNAL_ROOT = "journal:root"

/** A journal day's page: its id is its date, so every device that opens a day opens one page (owner, 2026-10-03). */
internal fun journalDayId(date: LocalDate) = "journal:$date"

/** The day [pageId] is the journal page of, or null for any other page. */
fun journalDate(pageId: String): LocalDate? =
    pageId.takeIf { it.startsWith("journal:") && it != JOURNAL_ROOT }?.let { runCatching { LocalDate.parse(it.removePrefix("journal:")) }.getOrNull() }

/**
 * Tendril's journal (ADR 12, slice 12d): one page per day under one "Journal" page. A day is the
 * personal day (owner, 2026-10-03, ADR 06), and its page is found by its id, made the first time it
 * is opened, empty and with no title, which reads as its date until the person names it.
 *
 * Both pages are made with one fixed stamp, the app's ([JOURNAL_STAMP]), so two devices that open
 * one day write the same rows, and opening a day never outranks its trash, a move or a rename made
 * on another device: what a person writes in it is newer than any of that. A page this device knows
 * was deleted for good is made again with a fresh stamp and no merge base, so another device's
 * rename still meets it as a clash. A purge this device has not heard of yet holds against a day it
 * opens and writes in meanwhile, as it does against any page's blocks (ADR 12, owner answer 3).
 */
internal class JournalRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val personal: PersonalSettings,
) {
    private val syncDao = db.syncDao()
    private val clock = writes.clock

    /** Today's page at [now], by the personal day boundary. */
    suspend fun today(now: LocalDateTime): String = day(dayOf(now, personal.dayStart()))

    /** [date]'s page, made if this device has none; one in the Trash is opened as it is (typing in it brings it back). */
    suspend fun day(date: LocalDate): String {
        val id = journalDayId(date)
        var purged = emptySet<String>()
        writes.write({
            purged = syncDao.purges(listOf(JOURNAL_ROOT, id)).map { it.id }.toSet()
            mapOf(PAGE to listOf(JOURNAL_ROOT, id))
        }) { store, _ ->
            for ((page, title, parent) in listOf(Triple(JOURNAL_ROOT, "Journal", null), Triple(id, "", JOURNAL_ROOT))) {
                if (store.row(page) != null) continue
                if (page in purged) {
                    store.removePurge(page)
                    store.put(newPageRow(page, clock.tick(), title, null, parent, "PAGE"))
                } else {
                    writes.merger.created(store, newPageRow(page, JOURNAL_STAMP, title, null, parent, "PAGE"))
                }
            }
        }
        return id
    }
}

/** The stamp the journal's pages are made with: the lowest there is, and the app's, so any edit outranks it and revive never reads it. */
private val JOURNAL_STAMP = Stamp(0, "journal~")
