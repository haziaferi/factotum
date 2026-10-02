package com.factotum.core.recurrence

import com.factotum.core.sync.Stamp
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

/**
 * ADR 11's cases (`decisions/cases/11-occurrence-edits.jsonl`) on the edit engine, with the
 * fixture of `tools/occurrence_sim.py`: a weekly Tuesday task, a Mon/Wed/Fri 08:00 series, and a
 * planned item with no days of its own, over three weeks from Monday 5 October 2026.
 */
class OccurrenceEditsTest {

    private val monday = LocalDate(2026, 10, 5)
    private val from = LocalDateTime(monday, LocalTime(0, 0))
    private val to = LocalDateTime(LocalDate(2026, 10, 26), LocalTime(0, 0))
    private var hlc = 0L

    private fun weekly(vararg days: String) = Recurrence.Rule(requireNotNull(RRule.parse("FREQ=WEEKLY;BYDAY=" + days.joinToString(","))))

    private fun day(d: Int) = LocalDate(2026, 10, d)

    private fun edit(scope: EditScope, changes: EditChanges, at: LocalDateTime? = null, date: LocalDate? = null, device: String = "A", seen: Set<String> = emptySet()) =
        OccurrenceEdit("e${++hlc}", scope, at, date, changes = changes, created = Stamp(hlc, device), seen = seen)

    private fun report(edits: List<OccurrenceEdit>, title: String = "Report") =
        weekly("TU").occurrencesWithEdits("T", LocalDateTime(monday, LocalTime(9, 0)), title, null, edits, from, to)

    private fun stretch(edits: List<OccurrenceEdit>) =
        weekly("MO", "WE", "FR").occurrencesWithEdits("H", LocalDateTime(monday, LocalTime(8, 0)), "Stretch", 15, edits, from, to)

    private fun dates(o: List<Occurrence>) = o.map { it.at.date.day }

    @Test
    fun tendrilTaskMoveOne_movingOneTuesdayMovesThatOneOnly() {
        val move = edit(EditScope.OCCURRENCE, EditChanges(movedTo = day(14)), at = LocalDateTime(day(13), LocalTime(9, 0)))

        assertEquals(listOf(6, 14, 20), dates(report(listOf(move))))
    }

    @Test
    fun tendrilHabitSkipOne_skippingOneLeavesTheRest() {
        val skip = edit(EditScope.OCCURRENCE, EditChanges(skip = true), at = LocalDateTime(day(7), LocalTime(8, 0)))

        assertEquals(listOf(5, 9), dates(stretch(listOf(skip))).take(2))
    }

    @Test
    fun tendrilHabitMoveThisWeek_movingWednesdayToThursdayLeavesLaterWeeks() {
        val move = edit(EditScope.OCCURRENCE, EditChanges(movedTo = day(8)), at = LocalDateTime(day(7), LocalTime(8, 0)))

        assertEquals(listOf(5, 8, 9, 12), dates(stretch(listOf(move))).take(4))
    }

    @Test
    fun tendrilPlannerWeekConfirm_aConfirmedWeekHoldsForThatWeekOnly() {
        val confirm = edit(EditScope.WEEK, EditChanges(weekDays = setOf(DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.SATURDAY)), date = monday)

        val swim = null.occurrencesWithEdits("P", LocalDateTime(monday, LocalTime(18, 0)), "Swim", null, listOf(confirm), from, to)

        assertEquals(listOf(5, 7, 10), dates(swim))
    }

    @Test
    fun tendrilHabitFromNowOn_sevenFromTheTwelfthAndEightBefore() {
        val fromNow = edit(EditScope.FROM, EditChanges(time = LocalTime(7, 0)), date = day(12))

        assertEquals(List(3) { LocalTime(8, 0) } + List(6) { LocalTime(7, 0) }, stretch(listOf(fromNow)).map { it.at.time })
    }

    @Test
    fun tendrilConcurrentFieldEdits_aRetimeAndARenameOfOneOccurrenceBothHold() {
        val friday = LocalDateTime(day(9), LocalTime(8, 0))
        val retime = edit(EditScope.OCCURRENCE, EditChanges(time = LocalTime(7, 30)), at = friday, device = "A")
        val rename = edit(EditScope.OCCURRENCE, EditChanges(title = "Stretch, slowly"), at = friday, device = "B")

        val got = stretch(listOf(rename, retime)).single { it.original == friday }

        assertEquals(LocalDateTime(day(9), LocalTime(7, 30)), got.at)
        assertEquals("Stretch, slowly", got.title)
    }

    @Test
    fun sharedConcurrentMovesOnce_twoMovesOfOneOccurrenceLeaveItOnce() {
        val tuesday = LocalDateTime(day(13), LocalTime(9, 0))
        val toWednesday = edit(EditScope.OCCURRENCE, EditChanges(movedTo = day(14)), at = tuesday, device = "A")
        val toThursday = edit(EditScope.OCCURRENCE, EditChanges(movedTo = day(15)), at = tuesday, device = "B")

        // Applied in stamp order, the later move wins; either order leaves one occurrence.
        assertEquals(listOf(6, 15, 20), dates(report(listOf(toThursday, toWednesday))))
    }

    @Test
    fun sharedRenameReachesMoved_renamingTheSeriesRenamesAMovedOccurrence() {
        val move = edit(EditScope.OCCURRENCE, EditChanges(movedTo = day(14)), at = LocalDateTime(day(13), LocalTime(9, 0)))

        assertEquals(setOf("Weekly report"), report(listOf(move), title = "Weekly report").map { it.title }.toSet())
    }

    @Test
    fun ownerOccurrenceClashAsks_twoRetimesAskAndARetimeAgainstARenameDoesNot() {
        val friday = LocalDateTime(day(9), LocalTime(8, 0))
        val a = edit(EditScope.OCCURRENCE, EditChanges(time = LocalTime(7, 30)), at = friday, device = "A")
        val b = edit(EditScope.OCCURRENCE, EditChanges(time = LocalTime(6, 45)), at = friday, device = "B")
        val rename = edit(EditScope.OCCURRENCE, EditChanges(title = "Evening stretch"), at = friday, device = "B")

        assertEquals(listOf(a to b), clashes(listOf(a, b)))
        assertEquals(emptyList(), clashes(listOf(a, rename)))
    }

    @Test
    fun aCorrectionMadeAfterSeeingTheOtherEditIsNoClash() {
        val friday = LocalDateTime(day(9), LocalTime(8, 0))
        val a = edit(EditScope.OCCURRENCE, EditChanges(time = LocalTime(7, 30)), at = friday, device = "A")
        val b = edit(EditScope.OCCURRENCE, EditChanges(time = LocalTime(6, 45)), at = friday, device = "B", seen = setOf(a.id))

        assertEquals(emptyList(), clashes(listOf(a, b)))
    }

    @Test
    fun twoEditsSettingTheSameValueAreNoClash() {
        val friday = LocalDateTime(day(9), LocalTime(8, 0))
        val a = edit(EditScope.OCCURRENCE, EditChanges(time = LocalTime(7, 30)), at = friday, device = "A")
        val b = edit(EditScope.OCCURRENCE, EditChanges(time = LocalTime(7, 30)), at = friday, device = "B")

        assertEquals(emptyList(), clashes(listOf(a, b)))
    }

    @Test
    fun aLaterEditThatHasSeenBothSettlesTheClash() {
        val friday = LocalDateTime(day(9), LocalTime(8, 0))
        val a = edit(EditScope.OCCURRENCE, EditChanges(time = LocalTime(7, 30)), at = friday, device = "A")
        val b = edit(EditScope.OCCURRENCE, EditChanges(time = LocalTime(6, 45)), at = friday, device = "B")
        val answer = edit(EditScope.OCCURRENCE, EditChanges(time = LocalTime(6, 45)), at = friday, device = "A", seen = setOf(a.id, b.id))

        assertEquals(emptyList(), clashes(listOf(a, b, answer)))
    }

    @Test
    fun anEditMadeWithoutSeeingAnotherClashesWithItThoughItSawALaterOne() {
        // A and E edit apart; D, which has seen only E's, edits after both: D never saw A's.
        val friday = LocalDateTime(day(9), LocalTime(8, 0))
        val a = edit(EditScope.OCCURRENCE, EditChanges(time = LocalTime(7, 30)), at = friday, device = "A")
        val e = edit(EditScope.OCCURRENCE, EditChanges(title = "Stretch, slowly"), at = friday, device = "E")
        val d = edit(EditScope.OCCURRENCE, EditChanges(time = LocalTime(6, 45)), at = friday, device = "D", seen = setOf(e.id))

        assertEquals(listOf(a to d), clashes(listOf(a, e, d)))
    }

    @Test
    fun fromNowOnReachesOccurrencesWhereTheyAreNow() {
        val movedLater = edit(EditScope.OCCURRENCE, EditChanges(movedTo = day(14)), at = LocalDateTime(day(6), LocalTime(9, 0)))
        val movedEarlier = edit(EditScope.OCCURRENCE, EditChanges(movedTo = day(9)), at = LocalDateTime(day(13), LocalTime(9, 0)))
        val eleven = edit(EditScope.FROM, EditChanges(time = LocalTime(11, 0)), date = day(12))

        val got = report(listOf(movedLater, movedEarlier, eleven)).map { it.at }

        assertEquals(listOf(LocalDateTime(day(9), LocalTime(9, 0)), LocalDateTime(day(14), LocalTime(11, 0)), LocalDateTime(day(20), LocalTime(11, 0))), got)
    }

    @Test
    fun aConfirmedWeekReplacesTheSeriesDaysAndKeepsWhatWasMovedOrAddedThere() {
        // As in Tendril, where a move is a skip and an added entry, both applied after the week's days.
        val moveIn = edit(EditScope.OCCURRENCE, EditChanges(movedTo = day(13)), at = LocalDateTime(day(6), LocalTime(9, 0)))
        val extra = edit(EditScope.EXTRA, EditChanges(), at = LocalDateTime(day(15), LocalTime(9, 0)))
        val confirm = edit(EditScope.WEEK, EditChanges(weekDays = setOf(DayOfWeek.FRIDAY)), date = day(12))

        assertEquals(listOf(13, 15, 16, 20), dates(report(listOf(moveIn, extra, confirm))))
    }

    @Test
    fun aNewWeeklyPatternFromADate() {
        val pattern = edit(EditScope.FROM, EditChanges(weekDays = setOf(DayOfWeek.MONDAY, DayOfWeek.THURSDAY)), date = day(12))

        assertEquals(listOf(6, 12, 15, 19, 22), dates(report(listOf(pattern))))
    }

    @Test
    fun onlyOneOccurrenceMoves() {
        assertFailsWith<IllegalArgumentException> { edit(EditScope.FROM, EditChanges(movedTo = day(14)), date = day(12)) }
        assertFailsWith<IllegalArgumentException> { edit(EditScope.DAY, EditChanges(movedTo = day(14)), date = day(13)) }
    }

    @Test
    fun anOccurrenceMovedInFromOutsideTheWindowShows() {
        val move = edit(EditScope.OCCURRENCE, EditChanges(movedTo = day(21)), at = LocalDateTime(day(27), LocalTime(9, 0)))

        assertEquals(listOf(6, 13, 20, 21), dates(report(listOf(move))))
    }

    @Test
    fun anAddedOccurrenceAtASeriesTimeKeepsBoth() {
        val extra = edit(EditScope.EXTRA, EditChanges(), at = LocalDateTime(day(6), LocalTime(9, 0)))

        assertEquals(listOf(6, 6, 13, 20), dates(report(listOf(extra))))
    }

    @Test
    fun aNewRuleFromADateRepeatsDifferentlyFromThen() {
        val daily = edit(EditScope.FROM, EditChanges(rule = Recurrence.Rule(requireNotNull(RRule.parse("FREQ=DAILY")))), date = day(19))

        assertEquals(listOf(6, 13) + (19..25).toList(), dates(report(listOf(daily))))
    }

    @Test
    fun aLaterCreatedRuleWithAnEarlierDateEndsTheEarlierCreatedOne() {
        val daily = edit(EditScope.FROM, EditChanges(rule = Recurrence.Rule(requireNotNull(RRule.parse("FREQ=DAILY")))), date = day(19))
        val weeklyAgain = edit(EditScope.FROM, EditChanges(rule = weekly("TU")), date = day(12))

        assertEquals(listOf(6, 13, 20), dates(report(listOf(daily, weeklyAgain))))
    }
}
