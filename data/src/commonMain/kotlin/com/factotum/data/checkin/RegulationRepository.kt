package com.factotum.data.checkin

import com.factotum.core.checkin.CheckIn
import com.factotum.core.checkin.DirectionEngine
import com.factotum.core.checkin.Direction
import com.factotum.core.checkin.Logged
import com.factotum.core.checkin.Outcome
import com.factotum.core.checkin.OutcomeAtNextOpen
import com.factotum.core.checkin.PendingOutcome
import com.factotum.core.checkin.Recommendation
import com.factotum.core.checkin.RegulationEvent
import com.factotum.core.checkin.Stability
import com.factotum.core.checkin.Step
import com.factotum.core.habit.dayOf
import com.factotum.core.settings.Settings
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.settings.SettingsRepository
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime

/** An outcome owed: asked at the next open (Equipoise's outcome at next open). */
data class OwedOutcome(val checkInId: String, val direction: Direction, val toolKey: String?)

/**
 * Equipoise's direction engine and outcome taps (decision 14). Which way to regulate is worked out
 * from the outcomes recorded so far, on demand, with the onboarding answer and Mixed mode that every
 * device shares; an outcome whose check-in was undone stops teaching (owner, 2026-10-03). Outcomes are
 * taken only for a check-in with both axes, the only kind the engine can learn from. A tool done away
 * from the phone is asked about once, at the next open, and lapses as "not now" (Equipoise's rule,
 * which it designed and never wired); what is owed is this device's alone, and is dropped without a
 * word when its check-in is undone.
 */
internal class RegulationRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
    private val settings: SettingsRepository,
) {
    private val dao = db.regulationDao()
    private val checkIns = db.checkInDao()
    private val clock = writes.clock

    /** What to suggest for the check-in [checkInId]: up, down, hold, or ask (Equipoise's engine). */
    suspend fun recommend(checkInId: String): Recommendation {
        val c = judgeable(checkInId)
        val history = dao.teaching().map { t ->
            RegulationEvent(CheckIn(t.energy, t.pleasantness, stability(t.stability)), Direction.valueOf(t.direction), Outcome.valueOf(t.outcome))
        }
        val dayStart = settings.dayStart()
        return DirectionEngine.recommend(
            requireNotNull(c.state()), history, settings.get(Settings.ONBOARDING_ANSWER), settings.get(Settings.MIXED_MODE),
            dayOf(LocalDateTime.parse(c.at), dayStart).toEpochDays().toInt(), checkIns.bothAxes(c.at).map { it.logged(dayStart) },
        )
    }

    /** An outcome tapped at [at] for a tool done in the app. */
    suspend fun record(checkInId: String, direction: Direction, toolKey: String?, outcome: Outcome, at: LocalDateTime): String {
        val id = newId()
        writes.write({ judgeable(checkInId); mapOf(REGULATION_EVENT to listOf(id)) }) { store, _ -> writes.merger.created(store, event(id, checkInId, direction, toolKey, outcome, at)) }
        return id
    }

    /** A tool chosen to do away from the phone: owed until the next open. One still owed lapses as "not now". */
    suspend fun startTool(checkInId: String, direction: Direction, toolKey: String?, at: LocalDateTime) {
        apply(at) { owed -> judgeable(checkInId); OutcomeAtNextOpen.start(owed?.pending(), direction, toolKey.orEmpty()) to checkInId }
    }

    /** The app came to the front: the outcome owed, to ask once now, if any; one asked before lapses as "not now". */
    suspend fun onOpen(at: LocalDateTime): OwedOutcome? = apply(at) { owed -> OutcomeAtNextOpen.open(owed?.pending()) to owed?.checkInId }

    /** The answer to the outcome asked. */
    suspend fun answer(outcome: Outcome, at: LocalDateTime) {
        apply(at) { owed -> OutcomeAtNextOpen.answer(owed?.pending(), outcome) to owed?.checkInId }
    }

    /** Undoes an outcome tapped by mistake. */
    suspend fun undo(eventId: String) = writes.edit(REGULATION_EVENT, eventId, GONE, {
        requireNotNull(dao.events(listOf(eventId)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no outcome $eventId" }
    }) { s -> mapOf("deleted_at" to s.hlc) }

    /** The live outcomes of [checkInId]. */
    suspend fun outcomes(checkInId: String): List<Pair<Direction, Outcome>> =
        dao.eventsOf(checkInId).map { Direction.valueOf(it.direction) to Outcome.valueOf(it.outcome) }

    /**
     * Carries out one step in one transaction: [next] gets what is owed (none when its check-in was
     * undone) and gives the step and the check-in it is for; the outcome it resolves is written and
     * what stays owed is kept on this device, together or not at all.
     */
    private suspend fun apply(at: LocalDateTime, next: suspend (PendingOutcomeEntity?) -> Pair<Step, String?>): OwedOutcome? {
        var resolved: Row? = null
        var asked: OwedOutcome? = null
        writes.write({
            val owed = dao.pending()?.takeIf { live(it.checkInId) != null }
            val (step, checkInId) = next(owed)
            resolved = step.resolved?.let { r -> event(newId(), requireNotNull(owed).checkInId, r.pending.direction, r.pending.tool.ifEmpty { null }, r.outcome, at) }
            val pending = step.pending
            if (pending == null) dao.clearPending()
            else dao.putPending(PendingOutcomeEntity(checkInId = requireNotNull(checkInId), direction = pending.direction.name, toolKey = pending.tool.ifEmpty { null }, asked = pending.asked))
            asked = step.ask?.let { OwedOutcome(requireNotNull(checkInId), it.direction, it.tool.ifEmpty { null }) }
            mapOf(REGULATION_EVENT to listOfNotNull(resolved?.id))
        }) { store, _ -> resolved?.let { writes.merger.created(store, it) } }
        return asked
    }

    private fun event(id: String, checkInId: String, direction: Direction, toolKey: String?, outcome: Outcome, at: LocalDateTime) = clock.tick().let { s ->
        Row(REGULATION_EVENT, id, mapOf(
            SAID to Group(s, mapOf("at" to at.toString(), "check_in_id" to checkInId, "direction" to direction.name, "tool_key" to toolKey, "outcome" to outcome.name)),
            GONE to Group(s, mapOf("deleted_at" to null)),
        ))
    }

    private suspend fun live(id: String) = checkIns.checkIns(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }

    private suspend fun judgeable(id: String) = requireNotNull(live(id)?.takeIf { it.state() != null }) { "check-in $id has no two axes to judge" }
}

private fun PendingOutcomeEntity.pending() = PendingOutcome(Direction.valueOf(direction), toolKey.orEmpty(), asked)

private fun stability(name: String?) = name?.let(Stability::valueOf) ?: Stability.UNSET

/** A check-in's state on Equipoise's two axes, or null for a one-axis tap. */
internal fun CheckInEntity.state(): CheckIn? =
    if (energy == null || pleasantness == null) null else CheckIn(energy, pleasantness, stability(stability))

/** A check-in with both axes as Equipoise's engines read it: on the personal day it was made. */
internal fun CheckInEntity.logged(dayStart: LocalTime) = Logged(dayOf(LocalDateTime.parse(at), dayStart).toEpochDays().toInt(), requireNotNull(state()))
