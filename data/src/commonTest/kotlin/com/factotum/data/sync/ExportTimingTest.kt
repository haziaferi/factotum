package com.factotum.data.sync

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals

@OptIn(ExperimentalCoroutinesApi::class)
class ExportTimingTest {

    @Test
    fun aBurstOfWritesExportsOnceThirtySecondsAfterTheLast() = runTest {
        val touches = MutableSharedFlow<Unit>(extraBufferCapacity = 1)
        var exports = 0
        backgroundScope.exportAfterQuiet(touches, quietMillis = 30_000) { exports++ }
        runCurrent()

        repeat(3) {
            touches.emit(Unit)
            advanceTimeBy(10_000)
        }
        advanceTimeBy(19_999)
        runCurrent()
        assertEquals(0, exports)

        advanceTimeBy(2)
        runCurrent()
        assertEquals(1, exports)
    }
}
