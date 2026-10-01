plugins {
    alias(libs.plugins.kotlin.multiplatform)
    alias(libs.plugins.android.kotlin.multiplatform.library)
}

kotlin {
    jvmToolchain(21)

    android {
        namespace = "com.factotum.data"
        compileSdk = libs.versions.compileSdk.get().toInt()
        minSdk = libs.versions.minSdk.get().toInt()
        withHostTest {}
    }

    jvm("desktop")

    applyDefaultHierarchyTemplate()

    sourceSets {
        val jvmCommon = create("jvmCommon") { dependsOn(commonMain.get()) }
        androidMain { dependsOn(jvmCommon) }
        getByName("desktopMain") { dependsOn(jvmCommon) }

        commonMain.dependencies {
            api(project(":core"))
            api(libs.androidx.sqlite)
        }
        androidMain.dependencies {
            implementation(libs.androidx.sqlite.framework)
        }
        getByName("desktopMain").dependencies {
            implementation(libs.androidx.sqlite.bundled)
        }
        commonTest.dependencies {
            implementation(kotlin("test"))
        }
        getByName("androidHostTest").dependencies {
            implementation(libs.junit)
            implementation(libs.robolectric)
        }
    }
}
