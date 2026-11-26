#! Package specedit:view
#! Pure declarative MVVM View for SpecEdit (ViewModel wired in `init`; `build` is a single View expression).

Class is EditorView{
	replace [String] is namespace: ['specedit', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'sew', Center],
		['base', 'sew', Column],
		['base', 'fabric', Theme],
		['base', 'scrap', ToolkitContainer],
		['base', 'scrap', ToolbarContainer],
		['base', 'scrap', Toolbar],
		['base', 'scrap', ScrollView],
		['base', 'scrap', TextView],
		['base', 'scrap', TextScrap],
		['base', 'scrap', Bar],
		['base', 'scrap', Dialog],
		['base', 'wardrobe', FileDialog],
		['specedit', 'viewmodel', EditorViewModel],
		['specedit', 'util', SpecEditStrings]
	];

	EditorViewModel is vm: EditorViewModel();
	TextView is editorBody: TextView(text: TextEmitter(initial: ''));

	replace Function is init(EditorViewModel is vm){
		:vm: vm;
		editorBody: TextView(
			text: vm:documentText,
			wrap: vm:wrapEnabled,
			lineNumbers: vm:lineNumbersEnabled,
			cursorStatus: vm:cursorStatus,
			onTextChange: local Function(String is next){ vm:onDocumentEdited(text: next); }
		);
		vm:bindEditorActions(
			onCopy: local Function(){ editorBody:copySelection(); },
			onCut: local Function(){ editorBody:cutSelection(); },
			onPaste: local Function(){ editorBody:pasteText(); },
			onSelectAll: local Function(){ editorBody:selectAll(); }
		);
	}

	local Function of Dialog is aboutDialog(){
		Dialog(
			title: vm:aboutTitle,
			open: vm:aboutOpen,
			widthPt: vm:aboutWidthPt,
			heightPt: vm:aboutHeightPt,
			content: Center(
				child: Column(
					gapPt: 8.0,
					padPt: 20.0,
					children: Array([
						TextScrap(text: vm:versionText, align: SpecEditStrings:TEXT_ALIGN_CENTER) as SewNode,
						TextScrap(text: vm:descriptionText, align: SpecEditStrings:TEXT_ALIGN_CENTER, wrap: true, muted: true) as SewNode
					])
				)
			)
		)
	}

	local Function of FileDialog is openFileDialog(){
		FileDialog(
			title: vm:fileDialogTitle,
			open: vm:fileDialogOpen,
			allowMultiple: vm:allowMultipleFiles,
			onSelect: local Function(Array of String is paths){ vm:openFiles(paths: paths); },
			onCancel: local Function(){ vm:cancelOpen(); }
		)
	}

	Function of ToolkitContainer is build(){
		ToolkitContainer(
			title: vm:title,
			running: vm:running,
			theme: Theme(preset: vm:themePreset),
			widthPt: vm:windowWidthPt,
			heightPt: vm:windowHeightPt,
			toolbar: ToolbarContainer(
				toolbar: Toolbar(config: vm:toolbarConfig)
			),
			body: ScrollView(
				child: editorBody
			),
			bottomBar: Bar(
				leftText: vm:cursorStatus,
				rightText: vm:title
			),
			hasBottomBar: true,
			dialog: :aboutDialog(),
			hasDialog: true,
			fileDialog: :openFileDialog(),
			hasFileDialog: true
		)
	}
}
