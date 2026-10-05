plugins {
    alias(libs.plugins.android.application)
}

android {
    namespace = "com.hazia.factotum"
    compileSdk = libs.versions.compileSdk.get().toInt()

    defaultConfig {
        applicationId = "com.hazia.factotum"
        minSdk = libs.versions.minSdk.get().toInt()
        targetSdk = libs.versions.targetSdk.get().toInt()
        versionCode = 1
        versionName = "0.0.1"
    }

    // Personal use only, sideloaded, never distributed (owner, 2026-10-05): every build is signed with
    // Tendril's shared debug key, committed on purpose so any checkout can update the installed app.
    // Its password is public, so anyone could sign an update to this package; that is accepted here.
    // The key can never change without an uninstall, which loses the app's data.
    signingConfigs {
        getByName("debug") {
            storeFile = rootProject.file("keystores/my-shared-debug.keystore")
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
        }
    }

    buildTypes {
        // No applicationIdSuffix: only debug builds are installed, and the installed id is com.hazia.factotum.
        release {
            signingConfig = signingConfigs.getByName("debug")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_21
        targetCompatibility = JavaVersion.VERSION_21
    }
}

dependencies {
    implementation(project(":data"))
}
