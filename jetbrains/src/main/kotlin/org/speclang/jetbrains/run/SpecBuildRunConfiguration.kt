package org.speclang.jetbrains.run

import com.intellij.execution.Executor
import com.intellij.execution.actions.ConfigurationContext
import com.intellij.execution.actions.LazyRunConfigurationProducer
import com.intellij.execution.configurations.*
import com.intellij.execution.process.ProcessHandler
import com.intellij.execution.process.ProcessHandlerFactory
import com.intellij.execution.process.ProcessTerminatedListener
import com.intellij.execution.runners.ExecutionEnvironment
import com.intellij.icons.AllIcons
import com.intellij.openapi.components.BaseState
import com.intellij.openapi.options.SettingsEditor
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.ComboBox
import com.intellij.openapi.util.Ref
import com.intellij.psi.PsiElement
import com.intellij.ui.components.JBTextField
import com.intellij.util.ui.FormBuilder
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
                val exe = SpecToolchain.findExecutable("specbuild", project.basePath)?.toString()
                    ?: "specbuild"
                val cmd = GeneralCommandLine(exe)
                val manifest = options.manifestPath?.takeIf { it.isNotBlank() } ?: "specbuild.json"
                cmd.addParameter(manifest)
                val sub = options.subcommand?.takeIf { it.isNotBlank() }
                if (sub != null) {
                    cmd.addParameter(sub)
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
    private val subcommandBox = ComboBox(arrayOf("run", "build", "test", "lint", "clean"))
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

    override fun setupConfigurationFromContext(
        configuration: SpecBuildRunConfiguration,
        context: ConfigurationContext,
        sourceElement: Ref<PsiElement>
    ): Boolean {
        val vf = context.location?.virtualFile ?: return false
        val basePath = context.project.basePath ?: return false
        val manifestPath = findManifestFor(vf.path, basePath) ?: return false
        val rel = Path.of(basePath).relativize(manifestPath).toString()
        val isTestContext = vf.path.contains("/tests/") || vf.path.endsWith("/tests")
        val sub = if (isTestContext) "test" else "run"
        configuration.options.manifestPath = rel
        configuration.options.subcommand = sub
        configuration.name = if (isTestContext) "SpecBuild Test ($rel)" else "SpecBuild ($rel)"
        return true
    }

    override fun isConfigurationFromContext(
        configuration: SpecBuildRunConfiguration,
        context: ConfigurationContext
    ): Boolean {
        val vf = context.location?.virtualFile ?: return false
        val basePath = context.project.basePath ?: return false
        val manifestPath = findManifestFor(vf.path, basePath) ?: return false
        val rel = Path.of(basePath).relativize(manifestPath).toString()
        return configuration.options.manifestPath == rel
    }

    private fun findManifestFor(filePath: String, basePath: String): Path? {
        val p = Path.of(filePath)
        if (p.fileName?.toString() == "specbuild.json" && Files.isRegularFile(p)) {
            return p
        }
        var dir = if (Files.isDirectory(p)) p else p.parent
        val root = Path.of(basePath)
        while (dir != null && dir.startsWith(root)) {
            val cand = dir.resolve("specbuild.json")
            if (Files.isRegularFile(cand)) return cand
            if (dir == root) break
            dir = dir.parent
        }
        return null
    }
}
