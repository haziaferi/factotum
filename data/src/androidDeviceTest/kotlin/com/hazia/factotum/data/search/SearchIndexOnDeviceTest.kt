package com.hazia.factotum.data.search

import androidx.test.ext.junit.runners.AndroidJUnit4
import com.hazia.factotum.data.DeviceDatabase
import com.hazia.factotum.data.report
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import org.junit.After
import org.junit.runner.RunWith
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/**
 * SPEC:R197: the phone's own SQLite makes ADR 10's FTS4 index with `remove_diacritics=2`, and the
 * index folds case and accents there as it does on the desktop. Whether FTS5 is there too is
 * recorded, not required.
 */
@RunWith(AndroidJUnit4::class)
class SearchIndexOnDeviceTest {

    private val d = DeviceDatabase()
    private val search = SearchRepository(d.db)
    private val now = LocalDateTime(2026, 10, 6, 12, 0)

    @After fun close() = d.close()

    private fun ids(query: String) = runBlocking { search.search(query, now) }.map { it.id }

    @Test
    fun theIndexIsMadeWithRemoveDiacritics() {
        val sql = d.read("SELECT sql FROM sqlite_master WHERE name = 'search_fts'") { it.getText(0) }.single()
        val fts5 = runCatching { d.write("CREATE VIRTUAL TABLE temp.fts5_probe USING fts5(x)") }.exceptionOrNull()
        val options = d.read("PRAGMA compile_options") { it.getText(0) }
        report("R197 sqlite=${d.read("SELECT sqlite_version()") { it.getText(0) }.single()} fts5=${fts5?.message ?: "yes"} options=$options")

        assertTrue("fts4" in sql.lowercase() && "remove_diacritics=2" in sql, sql)
    }

    @Test
    fun accentsAndCaseFoldAndTheIndexFollowsEveryWrite() {
        val pills = runBlocking { d.reminders.createStandalone("Café Müller pills", LocalDate(2026, 10, 5), LocalTime(8, 0)) }

        assertEquals(listOf(pills), ids("cafe"))
        assertEquals(listOf(pills), ids("MULLER"))
        assertEquals(listOf(pills), ids("CAFÉ"))

        runBlocking { d.items.rename(pills, "Tea pills") }
        assertEquals(emptyList(), ids("cafe"))
        assertEquals(listOf(pills), ids("tea"))

        runBlocking { d.items.delete(pills) }
        assertEquals(emptyList(), ids("tea"))
    }
}
