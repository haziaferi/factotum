package com.factotum.core.label

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotEquals

class LabelsTest {

    @Test
    fun namesCompareIgnoringCaseAndOuterSpaces() {
        assertEquals(nameKey("Health"), nameKey("  HEALTH "))
        assertEquals(nameKey("Ärger"), nameKey("ärger"))
        assertNotEquals(nameKey("Health"), nameKey("Healthy"))
    }

    @Test
    fun aNewLabelsColourIsTendrilsForTheSameName() {
        // Java's hash: "a" is 97, 97 mod 8 = 1; "Health" is -2137395588, floorMod 8 = 4.
        assertEquals(LABEL_PALETTE[1], colorForName("a"))
        assertEquals(LABEL_PALETTE[4], colorForName("Health"))
        assertEquals(0xFFB68E51, colorForName("Health"))
    }
}
