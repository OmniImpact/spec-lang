import org.gradle.api.tasks.Exec
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    id("java")
    id("org.jetbrains.kotlin.jvm") version "2.1.20"
    id("org.jetbrains.intellij.platform") version "2.20.1"
}

group = "org.speclang"
version = "0.1.0"

repositories {
    mavenCentral()
    intellijPlatform {
        defaultRepositories()
    }
}

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

kotlin {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_21)
    }
}

dependencies {
    intellijPlatform {
        intellijIdeaCommunity("2024.2.5")
        bundledPlugin("org.jetbrains.plugins.textmate")
        plugins("com.redhat.devtools.lsp4ij:0.19.1")
    }
}

val repoRoot = layout.projectDirectory.dir("..").asFile
val binDir = file("$repoRoot/bin")
val specStdlibDir = file("$repoRoot/spec")
val textmateDir = file("$repoRoot/utilities/textmate/spec")
val specGdbPy = file("$repoRoot/utilities/spec-gdb.py")

val ensureSpecToolchain by tasks.registering(Exec::class) {
    group = "spec"
    description = "Ensures bootstrap compiler and Spec utility binaries exist in ../bin"
    workingDir = repoRoot

    val specBin = file("$binDir/spec")
    val utilBins = listOf(
        "speclsp" to "utilities/speclsp/SpecLsp.spec",
        "specbuild" to "utilities/specbuild/SpecBuild.spec",
        "specunit" to "utilities/specunit/SpecUnit.spec",
        "speclint" to "utilities/speclint/SpecLint.spec"
    )

    onlyIf {
        !specBin.exists() || utilBins.any { (name, _) -> !file("$binDir/$name").exists() }
    }

    commandLine("bash", "-c", buildString {
        append("set -e\n")
        append("if [ ! -x bin/spec ]; then ./bootstrap.sh; fi\n")
        for ((name, src) in utilBins) {
            append("if [ ! -x bin/$name ]; then ./bin/spec --quiet -i $src -o bin/$name; fi\n")
        }
    })
}

tasks {
    prepareSandbox {
        dependsOn(ensureSpecToolchain)
        from(binDir) {
            into("${intellijPlatform.projectName.get()}/bin")
            include("spec", "speclsp", "specbuild", "specunit", "speclint")
            filePermissions {
                unix("rwxr-xr-x")
            }
        }
        from(specStdlibDir) {
            into("${intellijPlatform.projectName.get()}/spec")
        }
        from(textmateDir) {
            into("${intellijPlatform.projectName.get()}/textmate/spec")
        }
        from(specGdbPy) {
            into("${intellijPlatform.projectName.get()}/utilities")
        }
    }

    patchPluginXml {
        sinceBuild.set("242")
        untilBuild.set(provider { null })
    }
}
