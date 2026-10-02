package com.factotum.data.label

import java.text.Normalizer

internal actual fun nfc(text: String): String = Normalizer.normalize(text, Normalizer.Form.NFC)
