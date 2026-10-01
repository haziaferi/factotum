package com.factotum.data.sync

import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.io.File
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertNull

class DirectorySyncFolderTest {

    @get:Rule val tmp = TemporaryFolder()

    @Test
    fun aReplaceLandsWholeAndLeavesNoTemporaryFile() {
        val folder = DirectorySyncFolder(tmp.root)
        val path = FolderLayout.segment("A", 0)

        folder.replace(path, "one\n".encodeToByteArray())
        folder.replace(path, "one\ntwo\n".encodeToByteArray())

        assertContentEquals("one\ntwo\n".encodeToByteArray(), folder.read(path))
        assertEquals(8L, folder.size(path))
        assertEquals(listOf("log-000000.jsonl"), folder.list(FolderLayout.dir("A")))
        assertEquals(listOf("A"), folder.list(FolderLayout.DEVICES))
    }

    @Test
    fun aMissingFileOrDirectoryReadsAsAbsent() {
        val folder = DirectorySyncFolder(tmp.root)

        assertNull(folder.read("devices/A/log-000000.jsonl"))
        assertNull(folder.size("devices/A/log-000000.jsonl"))
        assertEquals(emptyList(), folder.list("devices/A"))
        folder.delete("devices/A/log-000000.jsonl")
    }

    @Test
    fun aDeletedFileIsGone() {
        val folder = DirectorySyncFolder(tmp.root)
        folder.replace("devices/A/snapshot-000063.jsonl", byteArrayOf(1))

        folder.delete("devices/A/snapshot-000063.jsonl")

        assertEquals(false, File(tmp.root, "devices/A/snapshot-000063.jsonl").exists())
    }
}
