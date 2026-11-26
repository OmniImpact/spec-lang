#! Package specedit:view
#! Absolutely pure composable MVVM View for SpecEdit (Theo-style declarative composition).

Class is EditorView{
	replace [String] is namespace: ['specedit', 'view'];

	replace [[String]] is using: [
		['base', 'fabric', Theme],
		['base', 'scrap', ToolkitContainer],
		['base', 'scrap', ToolbarContainer],
		['base', 'scrap', Toolbar],
		['base', 'scrap', ScrapPanel],
		['specedit', 'viewmodel', EditorViewModel]
	];

	Function of ToolkitContainer is build(EditorViewModel is vm){
		return ToolkitContainer(
			title: vm:title,
			running: vm:running,
			theme: Theme(preset: 'light_grayscale'),
			widthPt: vm:windowWidthPt,
			heightPt: vm:windowHeightPt,
			toolbar: ToolbarContainer(
				toolbar: Toolbar(config: vm:toolbarConfig)
			),
			body: ScrapPanel()
		);
	}
}
