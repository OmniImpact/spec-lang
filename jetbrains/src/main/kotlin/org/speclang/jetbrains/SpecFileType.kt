package org.speclang.jetbrains

import com.intellij.icons.AllIcons
import com.intellij.openapi.fileTypes.LanguageFileType
import org.jetbrains.plugins.textmate.TextMateBackedFileType
import javax.swing.Icon

object SpecFileType : LanguageFileType(SpecLanguage), TextMateBackedFileType {
    override fun getName(): String = "Spec"
    override fun getDescription(): String = "Spec language source file"
    override fun getDefaultExtension(): String = "spec"
    override fun getIcon(): Icon = AllIcons.FileTypes.Text
}
