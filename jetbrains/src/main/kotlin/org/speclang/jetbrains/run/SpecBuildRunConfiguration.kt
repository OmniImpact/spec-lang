package org.speclang.jetbrains.run

import com.intellij.execution.Executor
import com.intellij.execution.RunManager
import com.intellij.execution.actions.ConfigurationContext
import com.intellij.execution.actions.ConfigurationFromContext
import com.intellij.execution.actions.LazyRunConfigurationProducer
import com.intellij.execution.configurations.*
import com.intellij.execution.executors.DefaultDebugExecutor
import com.intellij.execution.process.ProcessHandler
import com.intellij.execution.process.ProcessHandlerFactory
import com.intellij.execution.process.ProcessTerminatedListener
import com.intellij.execution.runners.ExecutionEnvironment
import com.intellij.execution.runners.ExecutionEnvironmentBuilder
import com.intellij.execution.runners.ProgramRunner
import com.intellij.icons.AllIcons
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.components.BaseState
import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.options.SettingsEditor
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.ComboBox
import com.intellij.openapi.util.Ref
import com.intellij.openapi.vfs.VirtualFile
import com.intellij.psi.PsiElement
import com.intellij.ui.components.JBTextField
import com.intellij.util.ui.FormBuilder
import com.redhat.devtools.lsp4ij.dap.DebugMode
import com.redhat.devtools.lsp4ij.dap.configurations.DAPRunConfiguration
import org.speclang.jetbrains.SpecToolchain
import java.nio.file.Files
import java.nio.file.Path
import javax.swing.JComponent

class SpecBuildRunOptions : RunConfigurationOptions() {
    var manifestPath by string("specbuild.json")
    var subcommand by string("run")
    var extraArgs by string("")
}

class SpecBuildConfigurationType : ConfigurationTypeBase(
    "SpecBuildConfiguration",
    "SpecBuild",
    "Run, build, or test a Spec project using specbuild.json",
    AllIcons.RunConfigurations.Application
) {
    init {
        addFactory(SpecBuildConfigurationFactory(this))
    }
}

class SpecBuildConfigurationFactory(type: ConfigurationType) : ConfigurationFactory(type) {
    override fun getId(): String = "SpecBuildFactory"
    override fun createTemplateConfiguration(project: Project): RunConfiguration =
        SpecBuildRunConfiguration(project, this, "SpecBuild")
    override fun getOptionsClass(): Class<out BaseState> = SpecBuildRunOptions::class.java
}

class SpecBuildRunConfiguration(
    project: Project,
    factory: ConfigurationFactory,
    name: String
) : RunConfigurationBase<SpecBuildRunOptions>(project, factory, name) {

    public override fun getOptions(): SpecBuildRunOptions =
        super.getOptions() as SpecBuildRunOptions

    override fun getConfigurationEditor(): SettingsEditor<out RunConfiguration> =
        SpecBuildSettingsEditor()

    override fun getState(executor: Executor, environment: ExecutionEnvironment): RunProfileState {
        return object : CommandLineState(environment) {
            override fun startProcess(): ProcessHandler {
                val sub = options.subcommand?.takeIf { it.isNotBlank() }
                val target = options.manifestPath?.takeIf { it.isNotBlank() } ?: "specbuild.json"
                val cmd = if (sub == "specunit") {
                    val unitExe = SpecToolchain.findExecutable("specunit", project.basePath)?.toString()
                        ?: "specunit"
                    val specExe = SpecToolchain.findExecutable("spec", project.basePath)?.toString()
                        ?: "spec"
                    GeneralCommandLine(unitExe, "-s", specExe, "-t", target)
                } else {
                    val exe = SpecToolchain.findExecutable("specbuild", project.basePath)?.toString()
                        ?: "specbuild"
                    GeneralCommandLine(exe, target).apply {
                        if (sub != null) addParameter(sub)
                    }
                }
                val extra = options.extraArgs?.trim().orEmpty()
                if (extra.isNotEmpty()) {
                    extra.split(Regex("\\s+")).forEach { cmd.addParameter(it) }
                }
                project.basePath?.let { cmd.withWorkDirectory(it) }
                val handler = ProcessHandlerFactory.getInstance().createColoredProcessHandler(cmd)
                ProcessTerminatedListener.attach(handler)
                return handler
            }
        }
    }
}

class SpecBuildSettingsEditor : SettingsEditor<SpecBuildRunConfiguration>() {
    private val manifestField = JBTextField()
    private val subcommandBox = ComboBox(arrayOf("run", "build", "test", "lint", "clean", "specunit"))
    private val extraArgsField = JBTextField()

    override fun resetEditorFrom(s: SpecBuildRunConfiguration) {
        manifestField.text = s.options.manifestPath ?: "specbuild.json"
        subcommandBox.selectedItem = s.options.subcommand ?: "run"
        extraArgsField.text = s.options.extraArgs ?: ""
    }

    override fun applyEditorTo(s: SpecBuildRunConfiguration) {
        s.options.manifestPath = manifestField.text.trim()
        s.options.subcommand = subcommandBox.selectedItem?.toString() ?: "run"
        s.options.extraArgs = extraArgsField.text.trim()
    }

    override fun createEditor(): JComponent =
        FormBuilder.createFormBuilder()
            .addLabeledComponent("Manifest:", manifestField)
            .addLabeledComponent("Command:", subcommandBox)
            .addLabeledComponent("Extra args:", extraArgsField)
            .panel
}

class SpecBuildRunConfigurationProducer : LazyRunConfigurationProducer<SpecBuildRunConfiguration>() {
    override fun getConfigurationFactory(): ConfigurationFactory =
        ConfigurationTypeUtil.findConfigurationType(SpecBuildConfigurationType::class.java)
            .configurationFactories.first()

    override fun shouldReplace(self: ConfigurationFromContext, other: ConfigurationFromContext): Boolean =
        true

    override fun isPreferredConfiguration(self: ConfigurationFromContext, other: ConfigurationFromContext): Boolean =
        true

    private fun resolveTarget(context: ConfigurationContext): Pair<String, String>? {
        val vf: VirtualFile = context.location?.virtualFile
            ?: CommonDataKeys.VIRTUAL_FILE.getData(context.dataContext)
            ?: return null
        val basePath = context.project.basePath ?: return null
        val root = Path.of(basePath).normalize()
        val isTestContext = vf.path.contains("/tests/") ||
            vf.path.endsWith("/tests") ||
            (vf.name.startsWith("Test") && vf.extension.equals("spec", ignoreCase = true))

        val manifestPath = SpecToolchain.findManifestFor(vf.path, basePath)
        if (manifestPath != null) {
            val rel = root.relativize(manifestPath).toString()
            val sub = if (isTestContext) "test" else "run"
            return rel to sub
        }

        if (isTestContext) {
            val rel = root.relativize(Path.of(vf.path).normalize()).toString()
            return rel to "specunit"
        }
        return null
    }

    override fun setupConfigurationFromContext(
        configuration: SpecBuildRunConfiguration,
        context: ConfigurationContext,
        sourceElement: Ref<PsiElement>
    ): Boolean {
        val (target, sub) = resolveTarget(context) ?: return false
        configuration.options.manifestPath = target
        configuration.options.subcommand = sub
        configuration.name = when (sub) {
            "test" -> "SpecBuild Test ($target)"
            "specunit" -> "SpecUnit ($target)"
            else -> "SpecBuild ($target)"
        }
        return true
    }

    override fun isConfigurationFromContext(
        configuration: SpecBuildRunConfiguration,
        context: ConfigurationContext
    ): Boolean {
        val (target, sub) = resolveTarget(context) ?: return false
        return configuration.options.manifestPath == target &&
            configuration.options.subcommand == sub
    }
}

class SpecBuildDebugRunner : ProgramRunner<RunnerSettings> {
    override fun getRunnerId(): String = "SpecBuildDebugRunner"

    override fun canRun(executorId: String, profile: RunProfile): Boolean {
        if (executorId != DefaultDebugExecutor.EXECUTOR_ID) return false
        if (profile !is SpecBuildRunConfiguration) return false
        val sub = profile.options.subcommand
        return sub != "clean" && sub != "lint"
    }

    override fun execute(environment: ExecutionEnvironment) {
        val profile = environment.runProfile as? SpecBuildRunConfiguration ?: return
        val project = environment.project
        val basePath = project.basePath ?: return
        val targetRel = profile.options.manifestPath?.takeIf { it.isNotBlank() } ?: "specbuild.json"
        val targetPath = Path.of(basePath).resolve(targetRel).normalize()
        val sub = profile.options.subcommand

        val sourcePath: Path? = when (sub) {
            "specunit" -> if (Files.isRegularFile(targetPath)) targetPath else findFirstSpecTest(targetPath)
            "test" -> {
                val active = FileEditorManager.getInstance(project).selectedFiles.firstOrNull()
                if (active != null && active.extension.equals("spec", ignoreCase = true) &&
                    (active.path.contains("/tests/") || active.name.startsWith("Test"))
                ) {
                    Path.of(active.path)
                } else {
                    findFirstSpecTest(targetPath.parent?.resolve("tests") ?: targetPath.parent)
                        ?: SpecToolchain.readManifestSource(targetPath)
                }
            }
            else -> SpecToolchain.readManifestSource(targetPath)
        }
        if (sourcePath == null) return

        val workDir = if (Files.isRegularFile(targetPath) && targetPath.fileName?.toString() == "specbuild.json") {
            targetPath.parent?.toString() ?: basePath
        } else {
            basePath
        }

        val dapType = ConfigurationType.CONFIGURATION_TYPE_EP.extensionList
            .firstOrNull { it.displayName == "DAP" || it.id.contains("DAP", ignoreCase = true) }
            ?: return
        val factory = dapType.configurationFactories.firstOrNull() ?: return
        val settings = RunManager.getInstance(project).createConfiguration("Debug ${sourcePath.fileName}", factory)
        val dapConfig = settings.configuration as? DAPRunConfiguration ?: return
        dapConfig.serverId = "spec-gdb-dap"
        dapConfig.serverName = "Spec Debugger (GDB DAP)"
        dapConfig.file = sourcePath.toString()
        dapConfig.workingDirectory = workDir
        dapConfig.debugMode = DebugMode.LAUNCH
        dapConfig.launchConfigurationId = "spec-gdb-launch"
        ExecutionEnvironmentBuilder.create(DefaultDebugExecutor.getDebugExecutorInstance(), settings)
            .buildAndExecute()
    }

    private fun findFirstSpecTest(dir: Path?): Path? {
        if (dir == null || !Files.isDirectory(dir)) return null
        Files.walk(dir).use { stream ->
            return stream.filter { Files.isRegularFile(it) && it.fileName.toString().endsWith(".spec") }
                .findFirst()
                .orElse(null)
        }
    }
}
