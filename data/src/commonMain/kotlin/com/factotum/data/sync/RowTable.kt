package com.factotum.data.sync

import com.factotum.core.sync.Row

/**
 * One synced table as the importer and exporter see it: rows in [Row] form, grouped as ADR 01
 * stamps them. Each schema slice implements it for its tables, inside the repository's transaction.
 */
internal interface RowTable {
    /** The rows among [ids] this table holds. */
    suspend fun load(ids: Collection<String>): List<Row>

    suspend fun all(): List<Row>

    suspend fun save(rows: Collection<Row>)

    suspend fun delete(ids: Collection<String>)
}
