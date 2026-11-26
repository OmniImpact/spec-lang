#! Package specedit:view
#! Absolutely pure composable MVVM View for SpecEdit.
#! Binds ViewModel emitters and menu config into the Scrap toolkit hierarchy.

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
		local Theme is theme: Theme(preset: 'light_grayscale');

		local ToolkitContainer is toolkit: ToolkitContainer(
			title: vm:title,
			running: vm:running,
			theme: theme,
			widthPt: vm:windowWidthPt,
			heightPt: vm:windowHeightPt
		);

		local ToolbarContainer is toolbarContainer: ToolbarContainer();
		toolbarContainer:addToolbar(toolbar: Toolbar(theme: theme));
		toolbarContainer:pushConfig(
			config: vm:toolbarConfig,
			onQuit: local Function(){ vm:requestQuit(); }
		);

		toolkit:addToolbarContainer(container: toolbarContainer);
		toolkit:setBody(body: ScrapPanel(bgColor: theme:windowBg));
		return toolkit;
	}
}
