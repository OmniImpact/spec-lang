#! Package specedit:view
#! Absolutely pure composable MVVM View for SpecEdit (Theo-style declarative composition).

Class is EditorView{
	replace [String] is namespace: ['specedit', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
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
		['specedit', 'viewmodel', EditorViewModel]
	];

	Function of ToolkitContainer is build(EditorViewModel is vm){
		local TextView is tv: TextView(
			text: vm:documentText,
			wrap: vm:wrapEnabled,
			lineNumbers: vm:lineNumbersEnabled,
			cursorStatus: vm:cursorStatus,
			onTextChange: local Function(String is next){ vm:onDocumentEdited(text: next); }
		);
		vm:copyHandler: local Function(){ tv:copySelection(); };
		vm:cutHandler: local Function(){ tv:cutSelection(); };
		vm:pasteHandler: local Function(){ tv:pasteText(); };
		vm:selectAllHandler: local Function(){ tv:selectAll(); };

		return ToolkitContainer(
			title: vm:title,
			running: vm:running,
			theme: Theme(preset: 'light_grayscale'),
			widthPt: vm:windowWidthPt,
			heightPt: vm:windowHeightPt,
			toolbar: ToolbarContainer(
				toolbar: Toolbar(config: vm:toolbarConfig)
			),
			body: ScrollView(
				child: tv
			),
			bottomBar: Bar(
				leftText: vm:cursorStatus,
				rightText: vm:title
			),
			hasBottomBar: true,
			dialog: Dialog(
				title: 'About SpecEdit',
				open: vm:aboutOpen,
				widthPt: 420.0,
				heightPt: 170.0,
				content: Center(
					child: Column(
						gapPt: 8.0,
						padPt: 20.0,
						children: Array([
							TextScrap(text: vm:versionText, align: 'center') as SewNode,
							TextScrap(text: vm:descriptionText, align: 'center', wrap: true, muted: true) as SewNode
						])
					)
				)
			),
			hasDialog: true,
			fileDialog: FileDialog(
				title: 'Open File',
				open: vm:fileDialogOpen,
				allowMultiple: false,
				onSelect: local Function(Array of String is paths){ vm:openFiles(paths: paths); },
				onCancel: local Function(){ vm:cancelOpen(); }
			),
			hasFileDialog: true
		);
	}
}
