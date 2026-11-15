package org.speclang.jetbrains.debug

import com.intellij.execution.ExecutionException
import com.intellij.execution.configurations.GeneralCommandLine
import com.intellij.execution.configurations.RunConfiguration
import com.intellij.execution.configurations.RunConfigurationOptions
import com.intellij.execution.process.ProcessHandler
import com.intellij.execution.process.ProcessOutput
import com.intellij.execution.runners.ExecutionEnvironment
import com.intellij.execution.util.ExecUtil
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.fileTypes.FileType
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.VirtualFile
import java.util.concurrent.Callable
import com.redhat.devtools.lsp4ij.dap.DebugMode
import com.redhat.devtools.lsp4ij.dap.LaunchConfiguration
import com.redhat.devtools.lsp4ij.dap.configurations.DAPRunConfiguration
import com.redhat.devtools.lsp4ij.dap.configurations.DAPRunConfigurationOptions
import com.redhat.devtools.lsp4ij.dap.descriptors.DebugAdapterDescriptor
import com.redhat.devtools.lsp4ij.dap.descriptors.DebugAdapterDescriptorFactory
import com.redhat.devtools.lsp4ij.dap.descriptors.ServerReadyConfig
import org.speclang.jetbrains.SpecFileType
import org.speclang.jetbrains.SpecToolchain
import java.nio.file.Files
import java.nio.file.Path

class SpecDebugAdapterFactory : DebugAdapterDescriptorFactory() {

    override fun createDebugAdapterDescriptor(
        options: RunConfigurationOptions,
        environment: ExecutionEnvironment
    ): DebugAdapterDescriptor = SpecDebugAdapterDescriptor(options, environment, this)

    override fun isDebuggableFile(file: VirtualFile, project: Project): Boolean =
        file.extension.equals("spec", ignoreCase = true)

    override fun prepareConfiguration(
        configuration: RunConfiguration,
        file: VirtualFile,
        project: Project
    ): Boolean {
        if (configuration is DAPRunConfiguration) {
            configuration.name = "Debug ${file.nameWithoutExtension}"
            configuration.file = file.path
            val manifest = SpecToolchain.findManifestFor(file.path, project.basePath)
            configuration.workingDirectory = manifest?.parent?.toString()
                ?: project.basePath
                ?: file.parent?.path
                ?: ""
            return true
        }
        return false
    }

    override fun getLaunchConfigurations(): List<LaunchConfiguration> = listOf(
        LaunchConfiguration(
            "spec-gdb-launch",
            "Launch Spec (GDB DAP)",
            """{"request":"launch","program":"${'$'}{file}","cwd":"${'$'}{workspaceFolder}"}""",
            DebugMode.LAUNCH
        )
    )
}

class SpecDebugAdapterDescriptor(
    options: RunConfigurationOptions,
    environment: ExecutionEnvironment,
    factory: SpecDebugAdapterFactory
) : DebugAdapterDescriptor(options, environment, factory.serverDefinition) {

    private var compiledBinary: Path? = null

    override fun startServer(): ProcessHandler {
        val dapOpts = options as? DAPRunConfigurationOptions
        val sourceOrBin = dapOpts?.file?.takeIf { it.isNotBlank() }
            ?: throw ExecutionException("No .spec file or executable specified for Spec debugger.")

        val targetPath = Path.of(sourceOrBin)
        val project = environment.project
        val workDir = dapOpts.workingDirectory?.takeIf { it.isNotBlank() } ?: project.basePath

        compiledBinary = if (sourceOrBin.endsWith(".spec", ignoreCase = true)) {
            compileWithDebug(targetPath, workDir, project.basePath)
        } else {
            targetPath
        }

        val gdbPy = SpecToolchain.pluginRoot()?.resolve("utilities")?.resolve("spec-gdb.py")
        val dapPy = SpecToolchain.pluginRoot()?.resolve("utilities")?.resolve("spec-dap.py")
        val cmd = if (dapPy != null && Files.isRegularFile(dapPy)) {
            GeneralCommandLine("python3", dapPy.toString())
        } else {
            GeneralCommandLine("gdb", "-i", "dap")
        }
        if (gdbPy != null && Files.isRegularFile(gdbPy)) {
            cmd.addParameters("-x", gdbPy.toString())
        }
        workDir?.let { cmd.withWorkDirectory(it) }
        return startServer(cmd)
    }

    private fun compileWithDebug(specFile: Path, workDir: String?, projectBasePath: String?): Path {
        val specBin = SpecToolchain.findExecutable("spec", projectBasePath)?.toString()
            ?: "spec"
        val outBin = Files.createTempFile("spec-dbg-", "")
        outBin.toFile().deleteOnExit()

        val cmd = GeneralCommandLine(specBin, "--debug", "--quiet", "-i", specFile.toString(), "-o", outBin.toString())
        val manifest = SpecToolchain.findManifestFor(specFile.toString(), projectBasePath)
        if (manifest != null) {
            for (srcDir in SpecToolchain.readManifestSourceDirs(manifest)) {
                if (Files.isDirectory(srcDir)) {
                    cmd.addParameters("-s", srcDir.toString())
                }
            }
        }
        SpecToolchain.pluginRoot()?.let { root ->
            val bundledUnit = root.resolve("utilities").resolve("specunit")
            if (Files.isDirectory(bundledUnit)) {
                cmd.addParameters("-s", bundledUnit.toString())
            }
            val bundledSpec = root.resolve("spec")
            if (Files.isDirectory(bundledSpec)) {
                cmd.addParameters("-s", bundledSpec.toString())
            }
        }
        workDir?.let { cmd.withWorkDirectory(it) }

        val output: ProcessOutput = ApplicationManager.getApplication()
            .executeOnPooledThread(Callable { ExecUtil.execAndGetOutput(cmd, 60_000) })
            .get()
        if (output.exitCode != 0) {
            val details = (output.stderr + "\n" + output.stdout).trim()
            throw ExecutionException("Spec --debug compilation failed (exit ${output.exitCode}):\n$details")
        }
        outBin.toFile().setExecutable(true)
        return outBin
    }

    override fun getDapParameters(): Map<String, Any> {
        val dapOpts = options as? DAPRunConfigurationOptions
        val workDir = dapOpts?.workingDirectory?.takeIf { it.isNotBlank() }
            ?: environment.project.basePath
            ?: "."
        val prog = compiledBinary?.toString() ?: dapOpts?.file.orEmpty()
        return mapOf(
            "request" to "launch",
            "program" to prog,
            "cwd" to workDir
        )
    }

    override fun getServerReadyConfig(debugMode: DebugMode): ServerReadyConfig =
        ServerReadyConfig(0)

    override fun getFileType(): FileType = SpecFileType

    override fun isDebuggableFile(file: VirtualFile, project: Project): Boolean =
        file.extension.equals("spec", ignoreCase = true)
}
