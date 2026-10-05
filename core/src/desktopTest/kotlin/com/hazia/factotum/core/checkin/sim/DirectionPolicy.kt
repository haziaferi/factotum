package com.hazia.factotum.core.checkin.sim

import com.hazia.factotum.core.checkin.CheckIn
import com.hazia.factotum.core.checkin.DirectionModel
import com.hazia.factotum.core.checkin.Recommendation
import com.hazia.factotum.core.checkin.RegulationEvent

/** Anything the simulator can drive: the production model, or a baseline kept for comparison. */
interface DirectionPolicy {
    fun recommend(c: CheckIn): Recommendation
    fun update(e: RegulationEvent): DirectionPolicy
}

class ModelPolicy(val model: DirectionModel = DirectionModel.PRIOR) : DirectionPolicy {
    override fun recommend(c: CheckIn) = model.recommend(c)
    override fun update(e: RegulationEvent) = ModelPolicy(model.update(e))
}
