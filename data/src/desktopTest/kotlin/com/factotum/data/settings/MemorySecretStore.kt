package com.factotum.data.settings

/** A [SecretStore] for tests: a map, held apart from the database and the folder as the real ones are. */
internal class MemorySecretStore : SecretStore {
    private val held = mutableMapOf<String, String>()

    override fun get(key: String): String? = held[key]

    override fun put(key: String, value: String?) {
        if (value == null) held.remove(key) else held[key] = value
    }
}
