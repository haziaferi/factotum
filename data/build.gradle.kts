plugins {
    alias(libs.plugins.kotlin.multiplatform)
    alias(libs.plugins.android.kotlin.multiplatform.library)
    alias(libs.plugins.ksp)
}

kotlin {
    jvmToolchain(21)

    // Room generates an `actual object` for the database constructor.
    compilerOptions {
        freeCompilerArgs.add("-Xexpect-actual-classes")
    }

    android {
        namespace = "com.hazia.factotum.data"
        compileSdk = libs.versions.compileSdk.get().toInt()
        minSdk = libs.versions.minSdk.get().toInt()
        withHostTest {}
        // SPEC:R61, R196, R197: what only a phone can answer, run by hand on one device with
        // `tools/device/run.sh <serial>`, not `connectedAndroidDeviceTest`, which runs on every
        // attached device; CI only builds them.
        withDeviceTest {
            instrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        }
    }

    jvm("desktop")

    applyDefaultHierarchyTemplate()

    sourceSets {
        val jvmCommon = create("jvmCommon") { dependsOn(commonMain.get()) }
        androidMain { dependsOn(jvmCommon) }
        getByName("desktopMain") { dependsOn(jvmCommon) }

        commonMain.dependencies {
            api(project(":core"))
            api(libs.androidx.room.runtime)
            api(libs.androidx.sqlite)
            api(libs.kotlinx.datetime)
            implementation(libs.kotlinx.coroutines.core)
            // The element API only, so no serialization compiler plugin.
            implementation(libs.kotlinx.serialization.json)
        }
        androidMain.dependencies {
            implementation(libs.androidx.sqlite.framework)
        }
        getByName("desktopMain").dependencies {
            implementation(libs.androidx.sqlite.bundled)
        }
        commonTest.dependencies {
            implementation(kotlin("test"))
            implementation(libs.kotlinx.coroutines.test)
        }
        getByName("androidHostTest").dependencies {
            implementation(libs.junit)
            implementation(libs.robolectric)
        }
        getByName("androidDeviceTest").dependencies {
            implementation(kotlin("test"))
            implementation(libs.junit)
            implementation(libs.androidx.test.runner)
            implementation(libs.androidx.test.ext.junit)
        }
    }
}

dependencies {
    add("kspAndroid", libs.androidx.room.compiler)
    add("kspDesktop", libs.androidx.room.compiler)
}

// One database, one schema file per version, committed: a migration needs the previous version's file.
ksp {
    arg("room.schemaLocation", "$projectDir/schemas")
}

// Both targets write the same schema file; running them in parallel races on it.
tasks.matching { it.name == "kspKotlinDesktop" }.configureEach {
    mustRunAfter("kspAndroidMain")
}
