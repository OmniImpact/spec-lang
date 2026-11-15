package org.speclang.jetbrains

import org.jetbrains.plugins.textmate.api.TextMateBundleProvider
import java.nio.file.Files

class SpecTextMateBundleProvider : TextMateBundleProvider {
    override fun getBundles(): List<TextMateBundleProvider.PluginBundle> {
        val bundlePath = SpecToolchain.pluginRoot()?.resolve("textmate")?.resolve("spec")
        if (bundlePath != null && Files.isDirectory(bundlePath)) {
            return listOf(TextMateBundleProvider.PluginBundle("Spec", bundlePath))
        }
        return emptyList()
    }
}
