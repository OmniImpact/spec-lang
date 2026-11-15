package org.speclang.jetbrains.lsp

import com.intellij.execution.configurations.GeneralCommandLine
import com.intellij.openapi.project.Project
import com.redhat.devtools.lsp4ij.LanguageServerFactory
import com.redhat.devtools.lsp4ij.server.OSProcessStreamConnectionProvider
import com.redhat.devtools.lsp4ij.server.StreamConnectionProvider
import org.speclang.jetbrains.SpecToolchain

class SpecLspServerFactory : LanguageServerFactory {
    override fun createConnectionProvider(project: Project): StreamConnectionProvider {
        val exe = SpecToolchain.findExecutable("speclsp", project.basePath)?.toString()
            ?: "speclsp"
        val cmd = GeneralCommandLine(exe)
        project.basePath?.let { cmd.withWorkDirectory(it) }
        return OSProcessStreamConnectionProvider(cmd)
    }
}
