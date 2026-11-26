plugins {
    alias(libs.plugins.kotlin.jvm)
    application
}

kotlin {
    jvmToolchain(21)
}

// SPEC:R205: until the screens, the app is one sync pass (`gradlew :windows:run --args="<sync folder>"`).
application {
    mainClass = "com.hazia.factotum.windows.MainKt"
    applicationName = "factotum"
}

dependencies {
    implementation(project(":data"))
    testImplementation(kotlin("test"))
    testImplementation(libs.junit)
}
