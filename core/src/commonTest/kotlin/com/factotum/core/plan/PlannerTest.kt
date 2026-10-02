package com.factotum.core.plan

import com.factotum.core.recurrence.EditChanges
import com.factotum.core.recurrence.EditScope
import com.factotum.core.recurrence.OccurrenceEdit
import com.factotum.core.recurrence.Patch
import com.factotum.core.recurrence.RRule
import com.factotum.core.recurrence.Recurrence
import com.factotum.core.recurrence.inForceOn
import com.factotum.core.recurrence.occurrences
import com.factotum.core.recurrence.occurrencesWithEdits
import com.factotum.core.recurrence.slotTime
import com.factotum.core.sync.Stamp
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.plus
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

/**
 * Tendril's planner tests (`CalendarScheduleTest.kt`) that still apply once expanding and editing
 * moved to `occurrencesWithEdits`, plus the PLANNED kind itself. The week is Monday 5 October 2026;
 * the blocks are Tendril's five defaults.
 */
class PlannerTest {

    private val monday = LocalDate(2026, 10, 5)
    private val from = LocalDateTime(monday, LocalTime(0, 0))
    private val to = LocalDateTime(monday.plus(7, DateTimeUnit.DAY), LocalTime(0, 0))
    private val blocks = listOf(
        TimeBlock("morning", 390, 540, 0), TimeBlock("midday", 540, 780, 1), TimeBlock("afternoon", 780, 1080, 2),
        TimeBlock("evening", 1080, 1290, 3), TimeBlock("night", 1290, 1410, 4),
    )

    private fun day(d: Int) = LocalDate(2026, 10, d)

    private fun daily() = Recurrence.Rule(requireNotNull(RRule.parse("FREQ=DAILY")))

    /** A habit as the data layer hands it over: its week's occurrences from its start on the Monday. */
    private fun habit(
        id: String,
        recurrence: Recurrence?,
        at: LocalTime? = null,
        block: String? = null,
        minutes: Int = 0,
        edits: List<OccurrenceEdit> = emptyList(),
        pool: List<LocalDate> = emptyList(),
    ) = PlanHabit(
        id, (0 until 7).map { monday.plus(it, DateTimeUnit.DAY) }.associateWith { recurrence.inForceOn(it, edits) }, block, minutes, setTime = at != null,
        occurrences = recurrence.occurrencesWithEdits(id, LocalDateTime(monday, at ?: LocalTime(0, 0)), id, null, edits, from, to),
        pool = pool, confirmed = edits.any { it.scope == EditScope.WEEK && it.changes.weekDays != null },
    )

    private fun week(vararg habits: PlanHabit, with: List<TimeBlock> = blocks) = planWeek(monday, with, habits.toList())

    private fun PlanWeek.on(d: Int) = days.single { it.date == day(d) }

    private fun PlanDay.where(id: String): List<String> =
        blocks.flatMap { b -> (b.timed + b.flexible).filter { it.itemId == id }.map { b.block.id } } +
            outside.filter { it.itemId == id }.map { "outside" } + anyTime.filter { it.itemId == id }.map { "any" }

    private var hlc = 0L
    private fun edit(scope: EditScope, changes: EditChanges, at: LocalDateTime? = null, date: LocalDate? = null) =
        OccurrenceEdit("e${++hlc}", scope, at, date, changes = changes, created = Stamp(hlc, "A"))

    @Test
    fun aSetTimeAtABlocksStartBelongsToThatBlockAndAtItsEndToTheNext() {
        val plan = week(habit("nine", daily(), at = LocalTime(9, 0)), habit("half-six", daily(), at = LocalTime(6, 30)))

        assertEquals(listOf("midday"), plan.on(5).where("nine"))
        assertEquals(listOf("morning"), plan.on(5).where("half-six"))
    }

    @Test
    fun aSetTimeAfterTheLastBlockIsKeptAndReportedNotDropped() {
        val plan = week(habit("late", daily(), at = LocalTime(23, 45)))

        assertEquals(listOf("outside"), plan.on(5).where("late"))
    }

    @Test
    fun aFlexibleHabitWithNoBlockOrABlockThatIsGoneIsAnyTime() {
        val plan = week(habit("none", daily()), habit("gone", daily(), block = "deleted"), habit("kept", daily(), block = "evening"))

        assertEquals(listOf("any"), plan.on(6).where("none"))
        assertEquals(listOf("any"), plan.on(6).where("gone"))
        assertEquals(listOf("evening"), plan.on(6).where("kept"))
    }

    @Test
    fun overlappingBlocksAreReportedOncePerOverlappingPair() {
        val plan = week(with = blocks + TimeBlock("nap", 840, 900, 5) + TimeBlock("walk", 870, 960, 6))

        assertEquals(listOf("afternoon" to "nap", "nap" to "walk"), plan.on(5).overlaps)
    }

    @Test
    fun aWeekdayTimeMovesTheBlockOnThatDayOnlyAndALaterOneWins() {
        val saturdays = TimeBlock(
            "morning", 390, 540, 0,
            listOf(BlockOverride(setOf(DayOfWeek.SATURDAY, DayOfWeek.SUNDAY), 480, 630), BlockOverride(setOf(DayOfWeek.SUNDAY), 600, 700)),
        )
        val plan = week(habit("nine", daily(), at = LocalTime(9, 0)), with = listOf(saturdays) + blocks.drop(1))

        assertEquals(listOf("midday"), plan.on(9).where("nine"))
        assertEquals(listOf("morning"), plan.on(10).where("nine"))
        assertEquals(listOf("midday"), plan.on(11).where("nine"))
    }

    @Test
    fun nADaySpreadsEvenlyOverTheBlocksInTheirOrderOrSitsInTheBlocksItNames() {
        val spread = Recurrence.Planned(3, Recurrence.Planned.Per.DAY)
        val named = Recurrence.Planned(2, Recurrence.Planned.Per.DAY, blocks = listOf("night", "morning"))
        val plan = week(habit("water", spread), habit("pills", named))

        assertEquals(listOf("morning", "afternoon", "night"), plan.on(7).where("water"))
        assertEquals(listOf("morning", "night"), plan.on(7).where("pills"))
        assertEquals(listOf(0, 2, 4), spread(5, 3))
    }

    @Test
    fun aPlannedDaysOccurrencesHaveNoTimeOfTheirOwnAndOnlyItsDays() {
        val r = Recurrence.Planned(2, Recurrence.Planned.Per.DAY, days = setOf(DayOfWeek.MONDAY, DayOfWeek.THURSDAY))

        assertEquals(
            listOf(LocalDateTime(day(5), slotTime(0)), LocalDateTime(day(5), slotTime(1)), LocalDateTime(day(8), slotTime(0)), LocalDateTime(day(8), slotTime(1))),
            r.occurrences("p", from, from, to),
        )
        assertEquals(emptyList(), Recurrence.Planned(3, Recurrence.Planned.Per.WEEK).occurrences("p", from, from, to))
    }

    @Test
    fun anEditsBlockWinsAndNoBlockMeansAnyTime() {
        val first = LocalDateTime(day(6), slotTime(0))
        val second = LocalDateTime(day(6), slotTime(1))
        val edits = listOf(
            edit(EditScope.OCCURRENCE, EditChanges(block = Patch("evening")), at = first),
            edit(EditScope.OCCURRENCE, EditChanges(block = Patch(null)), at = second),
        )
        val plan = week(habit("pills", Recurrence.Planned(2, Recurrence.Planned.Per.DAY), edits = edits))

        assertEquals(listOf("evening", "any"), plan.on(6).where("pills"))
        assertEquals(listOf("midday", "evening"), plan.on(7).where("pills"))
    }

    @Test
    fun anOccurrenceAnEditGaveATimeIsPlacedByThatTime() {
        val edits = listOf(edit(EditScope.OCCURRENCE, EditChanges(time = LocalTime(14, 0)), at = LocalDateTime(day(6), LocalTime(0, 0))))
        val plan = week(habit("walk", daily(), block = "morning", edits = edits))

        assertEquals(listOf("afternoon"), plan.on(6).where("walk"))
        assertEquals(listOf("morning"), plan.on(7).where("walk"))
    }

    @Test
    fun anUnconfirmedNAWeekHabitIsSuggestedAndPlacedNowhere() {
        val all = (5..11).map(::day)
        val plan = week(habit("gym", Recurrence.Planned(3, Recurrence.Planned.Per.WEEK), block = "evening", minutes = 60, pool = all))

        assertEquals(listOf(WeekSuggestion("gym", listOf(day(6), day(8), day(10)))), plan.suggestions)
        assertTrue(plan.days.all { it.where("gym").isEmpty() })
    }

    @Test
    fun confirmedDaysArePlacedAsConfirmedWhateverTheSuggestionWas() {
        val confirm = edit(EditScope.WEEK, EditChanges(weekDays = setOf(DayOfWeek.TUESDAY, DayOfWeek.SUNDAY)), date = monday)
        val plan = week(habit("gym", Recurrence.Planned(3, Recurrence.Planned.Per.WEEK), block = "evening", edits = listOf(confirm), pool = (5..11).map(::day)))

        assertEquals(emptyList(), plan.suggestions)
        assertEquals(listOf(6, 11), plan.days.filter { it.where("gym") == listOf("evening") }.map { it.date.day })
    }

    @Test
    fun editsMadeBeforeAWeekIsConfirmedReachItsDays() {
        val evening = edit(EditScope.FROM, EditChanges(block = Patch("evening")), date = monday)
        val friday = edit(EditScope.DAY, EditChanges(skip = true), date = day(9))
        val confirm = edit(EditScope.WEEK, EditChanges(weekDays = setOf(DayOfWeek.TUESDAY, DayOfWeek.FRIDAY)), date = monday)
        val plan = week(habit("gym", Recurrence.Planned(2, Recurrence.Planned.Per.WEEK), block = "morning", edits = listOf(evening, friday, confirm)))

        assertEquals(listOf(listOf("evening")), plan.days.map { it.where("gym") }.filter { it.isNotEmpty() })
        assertEquals(listOf("evening"), plan.on(6).where("gym"))
    }

    @Test
    fun aConfirmedDayOutsideTheHabitsDaysOrBeforeItsStartIsNotPlaced() {
        val r = Recurrence.Planned(2, Recurrence.Planned.Per.WEEK, days = setOf(DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY))
        val confirm = edit(EditScope.WEEK, EditChanges(weekDays = setOf(DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.FRIDAY)), date = monday)
        // Monday is before the start, Tuesday is not one of the habit's days.
        val tuesday = LocalDateTime(day(6), LocalTime(0, 0))

        val shown = r.occurrencesWithEdits("gym", tuesday, "gym", null, listOf(confirm), from, to)

        assertEquals(listOf(day(9)), shown.map { it.at.date })
    }

    @Test
    fun aRuleSetFromADateIsTheOnePlacedFromThen() {
        val swap = edit(EditScope.FROM, EditChanges(rule = Recurrence.Planned(2, Recurrence.Planned.Per.DAY, blocks = listOf("night", "midday"))), date = day(8))
        val eight = edit(EditScope.FROM, EditChanges(rule = Recurrence.Rule(requireNotNull(RRule.parse("FREQ=DAILY;BYHOUR=20;BYMINUTE=0")))), date = day(10))
        val plan = week(habit("pills", Recurrence.Planned(2, Recurrence.Planned.Per.DAY, blocks = listOf("morning", "night")), edits = listOf(swap, eight)))

        assertEquals(listOf("morning", "night"), plan.on(7).where("pills"))
        assertEquals(listOf("midday", "night"), plan.on(8).where("pills"))
        assertEquals(listOf("evening"), plan.on(10).where("pills"))
    }

    @Test
    fun aSuggestionKeepsTheBusiestDayLightest() {
        // Tuesday and Saturday, the unrotated pick, already hold an hour each: the next rotation avoids them.
        val busy = habit("busy", Recurrence.Rule(requireNotNull(RRule.parse("FREQ=WEEKLY;BYDAY=TU,SA"))), minutes = 60)
        val plan = week(busy, habit("yoga", Recurrence.Planned(2, Recurrence.Planned.Per.WEEK), minutes = 30, pool = (5..11).map(::day)))

        assertEquals(listOf(WeekSuggestion("yoga", listOf(day(7), day(11)))), plan.suggestions)
    }

    @Test
    fun onATieForTheBusiestDayTheEvenerWeekWins() {
        // Monday holds an hour and Thursday half of one; Thursday and Friday both leave Monday the busiest, Friday more evenly.
        val mondays = habit("mondays", Recurrence.Rule(requireNotNull(RRule.parse("FREQ=WEEKLY;BYDAY=MO"))), minutes = 60)
        val thursdays = habit("thursdays", Recurrence.Rule(requireNotNull(RRule.parse("FREQ=WEEKLY;BYDAY=TH"))), minutes = 30)
        val plan = week(mondays, thursdays, habit("yoga", Recurrence.Planned(1, Recurrence.Planned.Per.WEEK), minutes = 30, pool = (5..11).map(::day)))

        assertEquals(listOf(WeekSuggestion("yoga", listOf(day(9)))), plan.suggestions)
    }

    @Test
    fun aLaterNAWeekHabitIsSuggestedOnTheLoadTheEarlierOnesLeft() {
        val pool = (5..11).map(::day)
        val plan = week(
            habit("b", Recurrence.Planned(1, Recurrence.Planned.Per.WEEK), minutes = 30, pool = pool),
            habit("a", Recurrence.Planned(1, Recurrence.Planned.Per.WEEK), minutes = 30, pool = pool),
        )

        assertEquals(listOf(WeekSuggestion("a", listOf(day(8))), WeekSuggestion("b", listOf(day(9)))), plan.suggestions)
    }

    @Test
    fun aNAWeekHabitWithNoDayLeftThisWeekIsNotSuggested() {
        val plan = week(habit("gym", Recurrence.Planned(2, Recurrence.Planned.Per.WEEK), pool = emptyList()))

        assertEquals(emptyList(), plan.suggestions)
    }

    @Test
    fun aPoolSmallerThanTheCountSuggestsEveryDayInIt() {
        val plan = week(habit("gym", Recurrence.Planned(3, Recurrence.Planned.Per.WEEK), pool = listOf(day(10), day(11))))

        assertEquals(listOf(WeekSuggestion("gym", listOf(day(10), day(11)))), plan.suggestions)
    }

    @Test
    fun entriesKeepTheirOrderPastNine() {
        val plan = week(habit("sips", Recurrence.Planned(12, Recurrence.Planned.Per.DAY, blocks = List(12) { "midday" })))

        assertEquals((0 until 12).map { slotTime(it) }, plan.on(5).blocks.single { it.block.id == "midday" }.flexible.map { it.occurrence.at.time })
    }

    @Test
    fun weekdayTimesReadAndWriteTendrilsText() {
        val text = "SAT,SUN@480-630;MON@420-540"
        val parsed = Overrides.parse(text)

        assertEquals(listOf(BlockOverride(setOf(DayOfWeek.SATURDAY, DayOfWeek.SUNDAY), 480, 630), BlockOverride(setOf(DayOfWeek.MONDAY), 420, 540)), parsed)
        assertEquals(text, Overrides.format(parsed))
        assertEquals(emptyList(), Overrides.parse(null))
        for (bad in listOf("SAT@630-480", "XYZ@1-2", "SAT@0-1441", "SAT 0-60")) assertFailsWith<IllegalArgumentException>(bad) { Overrides.parse(bad) }
    }

    @Test
    fun aPlannedRuleOutOfRangeIsRefused() {
        assertFailsWith<IllegalArgumentException> { Recurrence.Planned(8, Recurrence.Planned.Per.WEEK) }
        assertFailsWith<IllegalArgumentException> { Recurrence.Planned(49, Recurrence.Planned.Per.DAY) }
        assertFailsWith<IllegalArgumentException> { Recurrence.Planned(2, Recurrence.Planned.Per.DAY, blocks = listOf("morning")) }
        assertFailsWith<IllegalArgumentException> { Recurrence.Planned(2, Recurrence.Planned.Per.WEEK, days = emptySet()) }
    }
}
