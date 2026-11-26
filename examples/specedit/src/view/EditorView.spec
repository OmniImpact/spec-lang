#! Package specedit:view
#! Absolutely pure composable MVVM View for SpecEdit (Theo-style declarative composition).

Class is EditorView{
	replace [String] is namespace: ['specedit', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'fabric', Theme],
		['base', 'scrap', ToolkitContainer],
		['base', 'scrap', ToolbarContainer],
		['base', 'scrap', Toolbar],
		['base', 'scrap', ScrollView],
		['base', 'scrap', TextView],
		['base', 'wardrobe', FileDialog],
		['specedit', 'viewmodel', EditorViewModel]
	];

	Function of ToolkitContainer is build(EditorViewModel is vm){
		ToolkitContainer(
			title: vm:title,
			running: vm:running,
			theme: Theme(preset: 'light_grayscale'),
			widthPt: vm:windowWidthPt,
			heightPt: vm:windowHeightPt,
			toolbar: ToolbarContainer(
				toolbar: Toolbar(config: vm:toolbarConfig)
			),
			body: ScrollView(
				child: TextView(text: vm:documentText)
			),
			fileDialog: FileDialog(
				title: 'Open File',
				open: vm:fileDialogOpen,
				allowMultiple: false,
				onSelect: local Function(Array of String is paths){ vm:openFiles(paths: paths); },
				onCancel: local Function(){ vm:cancelOpen(); }
			),
			hasFileDialog: true
		)
	}
}
