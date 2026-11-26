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
		['base', 'sew', Row],
		['base', 'sew', ZStack],
		['base', 'sew', NavStack],
		['base', 'sew', NavRoute],
		['base', 'fabric', Theme],
		['base', 'scrap', ToolkitContainer],
		['base', 'scrap', ToolbarContainer],
		['base', 'scrap', Toolbar],
		['base', 'scrap', MenuConfig],
		['base', 'scrap', TabBar],
		['base', 'scrap', ScrollView],
		['base', 'scrap', TextView],
		['base', 'scrap', TextScrap],
		['base', 'scrap', ScrapPanel],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', Bar],
		['base', 'scrap', Dialog],
		['base', 'wardrobe', FileDialog],
		['specedit', 'viewmodel', EditorViewModel],
		['specedit', 'util', SpecEditStrings]
	];

	EditorViewModel is vm: EditorViewModel();
	ToolkitContainer is container: ToolkitContainer();
	TextView is editorBody: TextView(text: TextEmitter(initial: ''));
	ScrollView is editorScroll: ScrollView(child: TextView(text: TextEmitter(initial: '')));
	TabBar is tabBar: TabBar();

	replace Function is init(EditorViewModel is vm){
		:vm: vm;
		editorBody: TextView(
			text: vm:documentText,
			wrap: vm:wrapEnabled,
			lineNumbers: vm:lineNumbersEnabled,
			cursorStatus: vm:cursorStatus,
			onTextChange: local Function(String is next){ vm:onDocumentEdited(text: next); },
			onRightClickMenu: local Function(Int is x, Int is y){ vm:showEditorContextMenu(x: x, y: y); },
			onClipboardWrite: local Function(String is txt){ container:setClipboard(text: txt); },
			onClipboardRead: local Function of String(){ container:getClipboard() }
		);
		editorScroll: ScrollView(child: editorBody);
		tabBar: TabBar(
			onSelectTab: local Function(Int is idx){ vm:selectTab(index: idx); },
			onCloseTab: local Function(Int is idx){ vm:closeTab(index: idx); },
			onRightClickTab: local Function(Int is idx, Int is x, Int is y){ vm:showTabContextMenu(index: idx, x: x, y: y); }
		);
		vm:bindTabBar(tabBar: tabBar);
		vm:bindEditorActions(
			onCopy: local Function(){ editorBody:copySelection(); },
			onCut: local Function(){ editorBody:cutSelection(); },
			onPaste: local Function(){ editorBody:pasteText(); },
			onSelectAll: local Function(){ editorBody:selectAll(); },
			canCopy: local Function of Boolean(){ editorBody:hasSelectedText() },
			canPaste: local Function of Boolean(){ editorBody:hasClipboardText() }
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
			title: vm:fileDialogTitle:current(),
			open: vm:fileDialogOpen,
			saveMode: vm:fileDialogSaveMode,
			dialogTitle: vm:fileDialogTitle,
			suggestedName: vm:fileDialogSuggestedName,
			allowMultiple: vm:allowMultipleFiles,
			onSelect: local Function(Array of String is paths){ vm:onFileDialogSelected(paths: paths); },
			onCancel: local Function(){ vm:cancelOpen(); }
		)
	}

	local Function of SewNode is welcomeContainer(){
		ZStack(
			children: Array([
				ScrapPanel() as SewNode,
				Center(
					child: Row(
						gapPt: 14.0,
						children: Array([
							ScrapButton(
								label: SpecEditStrings:ITEM_OPEN_LABEL,
								onClick: local Function(){ vm:requestOpen(); }
							) as SewNode,
							ScrapButton(
								label: SpecEditStrings:ITEM_NEW_LABEL,
								onClick: local Function(){ vm:newDocument(); }
							) as SewNode
						])
					)
				) as SewNode
			])
		)
	}

	local Function of SewNode is filesContainer(){
		Column(
			children: Array([
				tabBar as SewNode,
				editorScroll as SewNode
			]),
			flexFlags: Array([false, true])
		)
	}

	Function of ToolkitContainer is build(){
		:container: ToolkitContainer(
			title: vm:title,
			running: vm:running,
			theme: Theme(preset: vm:themePreset),
			widthPt: vm:windowWidthPt,
			heightPt: vm:windowHeightPt,
			toolbar: ToolbarContainer(
				toolbar: Toolbar(
					config: vm:toolbarConfig,
					onMenuOpen: local Function(MenuConfig is _m){ vm:refreshMenuStates(); }
				)
			),
			body: NavStack(
				route: vm:activeRoute,
				routes: Array([
					NavRoute(name: SpecEditStrings:ROUTE_WELCOME, child: :welcomeContainer()),
					NavRoute(name: SpecEditStrings:ROUTE_FILES, child: :filesContainer())
				])
			),
			bottomBar: Bar(
				leftText: vm:cursorStatus,
				rightText: vm:title
			),
			hasBottomBar: true,
			dialog: :aboutDialog(),
			hasDialog: true,
			fileDialog: :openFileDialog(),
			hasFileDialog: true,
			contextMenu: vm:contextMenu,
			onKey: local Function of Boolean(Int is key, Int is mods){ vm:handleShortcut(key: key, mods: mods) }
		);
		container
	}
}
