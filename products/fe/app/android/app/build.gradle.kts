import java.util.Base64

plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

val allowInsecureLan = (project.findProperty("dart-defines") as? String)
    ?.split(",")
    ?.map { String(Base64.getDecoder().decode(it), Charsets.UTF_8) }
    ?.contains("ALLOW_INSECURE_LAN=true") == true

android {
    namespace = "com.example.app"
    compileSdk = 37
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.example.app"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
        manifestPlaceholders["networkSecurityConfig"] = if (allowInsecureLan)
            "@xml/network_security_config_lan" else "@xml/network_security_config"
        manifestPlaceholders["appLabel"] = "Cứu hộ khẩn cấp"
    }

    buildTypes {
        release {
            // TODO: Add your own signing config for the release build.
            // Signing with the debug keys for now, so `flutter run --release` works.
            signingConfig = signingConfigs.getByName("debug")
        }
    }

    flavorDimensions += "audience"
    productFlavors {
        create("user") { dimension = "audience" }
        create("admin") {
            dimension = "audience"
            applicationIdSuffix = ".admin"
            manifestPlaceholders["appLabel"] = "Cứu hộ · Admin"
        }
    }
}

androidComponents {
    onVariants(selector().withFlavor("audience" to "user")) { variant ->
        variant.packaging.jniLibs.excludes.add("**/libonnxruntime.so")
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}

dependencies {
    implementation(files("libs/executorch-1.4.1-xnnpack.aar"))
    implementation("com.facebook.fbjni:fbjni:0.7.0")
    implementation("com.facebook.soloader:nativeloader:0.10.5")
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("org.jetbrains.kotlin:kotlin-stdlib:1.9.23")
}
