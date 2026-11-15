package org.speclang.jetbrains

import com.intellij.ide.plugins.PluginManagerCore
import com.intellij.openapi.extensions.PluginId
import java.nio.file.Files
import java.nio.file.Path

object SpecToolchain {
    private val pluginId = PluginId.getId("org.speclang.jetbrains")

    @Volatile
    private var permissionsEnsured = false

    fun pluginRoot(): Path? =
        PluginManagerCore.getPlugin(pluginId)?.pluginPath

    private fun ensureBinariesExecutable() {
        if (permissionsEnsured) return
        val binDir = pluginRoot()?.resolve("bin") ?: return
        if (Files.isDirectory(binDir)) {
            Files.list(binDir).use { stream ->
                stream.filter { Files.isRegularFile(it) }
                    .forEach { it.toFile().setExecutable(true, false) }
            }
            permissionsEnsured = true
        }
    }

    fun findExecutable(name: String, projectBasePath: String? = null): Path? {
        ensureBinariesExecutable()
        val bundled = pluginRoot()?.resolve("bin")?.resolve(name)
        if (bundled != null && Files.exists(bundled)) {
            bundled.toFile().setExecutable(true, false)
            return bundled
        }
        if (projectBasePath != null) {
            val local = Path.of(projectBasePath, "bin", name)
            if (Files.exists(local)) {
                return local
            }
        }
        return null
    }

    fun findManifestFor(filePath: String, stopRoot: String? = null): Path? {
        val p = Path.of(filePath).normalize()
        if (p.fileName?.toString() == "specbuild.json" && Files.isRegularFile(p)) {
            return p
        }
        var dir = if (Files.isDirectory(p)) p else p.parent
        val root = stopRoot?.let { Path.of(it).normalize() }
        while (dir != null && (root == null || dir.startsWith(root))) {
            val cand = dir.resolve("specbuild.json")
            if (Files.isRegularFile(cand)) return cand
            if (dir == root) break
            dir = dir.parent
        }
        return null
    }

    fun readManifestSource(manifestPath: Path): Path? {
        if (!Files.isRegularFile(manifestPath)) return null
        val text = Files.readString(manifestPath)
        val match = Regex(""""source"\s*:\s*"([^"]+)"""").find(text) ?: return null
        val rel = match.groupValues[1]
        return manifestPath.parent?.resolve(rel)?.normalize()
    }

    fun readManifestSourceDirs(manifestPath: Path): List<Path> {
        if (!Files.isRegularFile(manifestPath)) return emptyList()
        val text = Files.readString(manifestPath)
        val arrMatch = Regex(""""source_dirs"\s*:\s*\[([^\]]*)]""", RegexOption.DOT_MATCHES_ALL).find(text)
            ?: return emptyList()
        val dir = manifestPath.parent ?: return emptyList()
        return Regex(""""([^"]+)"""").findAll(arrMatch.groupValues[1])
            .map { dir.resolve(it.groupValues[1]).normalize() }
            .toList()
    }
}
