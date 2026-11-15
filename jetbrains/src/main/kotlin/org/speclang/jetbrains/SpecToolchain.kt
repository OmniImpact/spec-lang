package org.speclang.jetbrains

import com.intellij.ide.plugins.PluginManagerCore
import com.intellij.openapi.extensions.PluginId
import java.nio.file.Files
import java.nio.file.Path

object SpecToolchain {
    private val pluginId = PluginId.getId("org.speclang.jetbrains")

    fun pluginRoot(): Path? =
        PluginManagerCore.getPlugin(pluginId)?.pluginPath

    fun findExecutable(name: String, projectBasePath: String? = null): Path? {
        val bundled = pluginRoot()?.resolve("bin")?.resolve(name)
        if (bundled != null && Files.exists(bundled)) {
            bundled.toFile().setExecutable(true)
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
}
