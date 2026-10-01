package com.factotum.data.sync

import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse

class RecordCodecTest {

    private val row = Row(
        "item", "01ARYZ6S41TSV4RRFFQ69G5FAV",
        mapOf(
            "schedule" to Group(Stamp(7, "B"), mapOf("due" to "2026-10-01", "minutes" to 5L, "hours" to 5.0, "done" to false, "note" to null), settles = Stamp(6, "A")),
            "status" to Group(Stamp(3, "A"), mapOf("big" to Long.MAX_VALUE, "tiny" to 1e-300)),
        ),
    )

    @Test
    fun aRowReadsBackWithEveryValueItsOwnType() {
        val back = RecordCodec.decode(RecordCodec.encode(RowRecord(row)))

        assertEquals(RowRecord(row), back)
        val values = (back as RowRecord).row.groups.getValue("schedule").values
        assertEquals(5L, values["minutes"])
        assertEquals(5.0, values["hours"])
    }

    @Test
    fun aPurgeReadsBack() {
        val purge = PurgeRecord("01ARYZ6S41TSV4RRFFQ69G5FAV", Stamp(9, "A"))

        assertEquals(purge, RecordCodec.decode(RecordCodec.encode(purge)))
    }

    @Test
    fun aRecordIsOneCompactLine() {
        val line = RecordCodec.encode(RowRecord(row))

        assertFalse(line.contains('\n'))
        assertFalse(line.contains(": ") || line.contains(", "), line)
    }

    @Test
    fun aLineThatIsNotARecordIsRefused() {
        for (line in listOf("{not json", "[]", """{"t":"item","id":"x","g":{}}""", """{"t":"item","id":"x","g":{"a":{"h":1,"d":"A","v":{"n":[1]}}}}""", """{"p":"x","h":"soon","d":"A"}""")) {
            assertFailsWith<IllegalArgumentException>(line) { RecordCodec.decode(line) }
        }
    }

    @Test
    fun onlyNewlineTerminatedLinesAreRead() {
        val bytes = "one\ntwo\nthr".encodeToByteArray()

        assertEquals(listOf(Line("one", 4), Line("two", 8)), completeLines(bytes, 0))
        assertEquals(listOf(Line("two", 8)), completeLines(bytes, 4))
        assertEquals(emptyList(), completeLines(bytes, 8))
    }
}
