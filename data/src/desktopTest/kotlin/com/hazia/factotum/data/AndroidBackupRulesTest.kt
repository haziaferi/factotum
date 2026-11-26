package com.hazia.factotum.data

import org.w3c.dom.Element
import java.io.File
import javax.xml.parsers.DocumentBuilderFactory
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/**
 * SPEC:R32: the Android shell's backup rules keep the device-id file out of Auto Backup, cloud
 * backup and device transfer. It runs here, with the gate, because the shell has no tests of its own;
 * it reads the shell's files from the repository, since the test runs in `data/`.
 */
class AndroidBackupRulesTest {

    private val main = File("../android/src/main")

    private fun read(path: String): Element =
        DocumentBuilderFactory.newInstance().apply { isNamespaceAware = true }.newDocumentBuilder().parse(File(main, path)).documentElement

    private fun Element.children(tag: String): List<Element> =
        (0 until childNodes.length).map { childNodes.item(it) }.filterIsInstance<Element>().filter { it.tagName == tag }

    private fun Element.excludesTheDeviceId() =
        children("exclude").any { it.getAttribute("domain") == "file" && it.getAttribute("path") == DEVICE_ID_FILE }

    @Test
    fun theManifestNamesBothRuleFiles() {
        val app = read("AndroidManifest.xml").children("application").single()
        val ns = "http://schemas.android.com/apk/res/android"

        assertEquals("@xml/backup_rules", app.getAttributeNS(ns, "fullBackupContent"))
        assertEquals("@xml/data_extraction_rules", app.getAttributeNS(ns, "dataExtractionRules"))
    }

    @Test
    fun autoBackupLeavesTheDeviceIdOut() {
        assertTrue(read("res/xml/backup_rules.xml").excludesTheDeviceId())
    }

    @Test
    fun cloudBackupAndDeviceTransferLeaveTheDeviceIdOut() {
        val rules = read("res/xml/data_extraction_rules.xml")

        for (section in listOf("cloud-backup", "device-transfer")) {
            assertTrue(rules.children(section).single().excludesTheDeviceId(), section)
        }
    }
}
