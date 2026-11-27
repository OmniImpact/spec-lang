#! Package specedit:view
#! Pure declarative MVVM View for SpecEdit (ViewModel wired in `init`; `build` is a single View expression).

Class is EditorView{
	replace [String] is namespace: ['specedit', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'sew', HAlign],
		['base', 'sew', Center],
		['base', 'sew', Column],
		['base', 'sew', Row],
		['base', 'sew', ZStack],
		['base', 'sew', 'nav', NavStack],
		['base', 'sew', 'nav', NavRoute],
		['base', 'sew', 'grid', GridFlexH],
		['base', 'sew', 'grid', GridFlexPanel],
		['base', 'fabric', Theme],
		['base', 'scrap', ToolkitContainer],
		['base', 'scrap', 'toolbar', ToolbarContainer],
		['base', 'scrap', 'toolbar', Toolbar],
		['base', 'scrap', 'menu', MenuConfig],
		['base', 'scrap', 'tab', TabBar],
		['base', 'scrap', ScrollView],
		['base', 'scrap', 'text', CodeEditorView],
		['base', 'scrap', 'text', TextScrap],
		['base', 'scrap', ScrapPanel],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', Bar],
		['base', 'scrap', Dialog],
		['base', 'scrap', 'icon', ImageSvg],
		['base', 'wardrobe', 'file', FileDialog],
		['base', 'wardrobe', 'file', FileTree],
		['specedit', 'view', 'settings', SettingsDialogView],
		['specedit', 'viewmodel', EditorViewModel],
		['specedit', 'util', SpecEditStrings],
		['specedit', 'util', EditorSignalSlot]
	];

	EditorViewModel is vm: EditorViewModel();
	ToolkitContainer is container: ToolkitContainer();
	CodeEditorView is editorBody: CodeEditorView(text: TextEmitter(initial: ''));
	ScrollView is editorScroll: ScrollView(child: CodeEditorView(text: TextEmitter(initial: '')));
	TabBar is tabBar: TabBar();
	FileTree is fileTree: FileTree();
	GridFlexH is splitGrid: GridFlexH();

	replace Function is init(EditorViewModel is vm){
		:vm: vm;
		editorBody: CodeEditorView(
			text: vm:documentText,
			filePath: vm:activeFilePath,
			language: vm:activeLanguage,
			wrap: vm:wrapEnabled,
			lineNumbers: vm:lineNumbersEnabled,
			monospace: vm:monospaceEnabled,
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
			onRightClickTab: local Function(Int is idx, Int is x, Int is y){ vm:showTabContextMenu(index: idx, x: x, y: y); },
			onReorderTab: local Function(Int is fromIdx, Int is toIdx){ vm:reorderTab(fromIdx: fromIdx, toIdx: toIdx); }
		);
		vm:bindTabBar(tabBar: tabBar);
		vm:bindCodeEditor(editor: editorBody);
		fileTree: FileTree(
			contextMenu: vm:contextMenu,
			dropdownIconSvg: vm:icons:chevronDown,
			plusIconSvg: vm:icons:treePlus,
			minusIconSvg: vm:icons:treeMinus,
			onOpenFile: local Function(String is path){ vm:openFiles(paths: Array([path])); }
		);
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
			onTick: local Function(Int is nowMs){ vm:stepAboutStats(nowMs: nowMs); },
			content: Center(
				child: Column(
					gapPt: 8.0,
					padPt: 20.0,
					children: Array([
						Center(
							child: ImageSvg(
								svg: vm:icons:appIcon,
								widthPt: 48.0,
								heightPt: 48.0
							) as SewNode
						) as SewNode,
						TextScrap(content: SpecEditStrings:VERSION_TEXT, align: HAlign:CENTER) as SewNode,
						TextScrap(content: SpecEditStrings:DESCRIPTION_TEXT, align: HAlign:CENTER, wrap: true, muted: true) as SewNode,
						TextScrap(text: vm:processStatsText, align: HAlign:CENTER, muted: true) as SewNode
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
			directoryMode: vm:fileDialogDirMode,
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

	local Function of SewNode is buildSplitBody(){
		local NavStack is nav: NavStack(
			route: vm:activeRoute,
			routes: Array([
				NavRoute(name: SpecEditStrings:ROUTE_WELCOME, child: :welcomeContainer()),
				NavRoute(name: SpecEditStrings:ROUTE_FILES, child: :filesContainer())
			])
		);
		:splitGrid: GridFlexH(
			panels: Array([
				GridFlexPanel(
					child: fileTree as SewNode,
					sizePt: 220.0,
					minSizePt: 140.0,
					maxSizePt: 480.0,
					flex: false,
					visible: vm:fileTreeEnabled:current()
				),
				GridFlexPanel(
					child: nav as SewNode,
					minSizePt: 200.0,
					flex: true
				)
			]),
			spacingPt: 6.0,
			movable: true
		);
		splitGrid:signalBag:track(
			slot: EditorSignalSlot:FILE_TREE_VISIBLE as String,
			emitter: vm:fileTreeEnabled,
			collector: vm:fileTreeEnabled:collect(onEmit: local Function(){
				splitGrid:setPanelVisible(index: 0, visible: vm:fileTreeEnabled:current());
			})
		);
		return splitGrid;
	}

	Function of ToolkitContainer is build(){
		:container: ToolkitContainer(
			title: vm:title,
			iconSvg: vm:icons:appIcon,
			running: vm:running,
			theme: vm:settingsVm:currentTheme(),
			widthPt: vm:windowWidthPt,
			heightPt: vm:windowHeightPt,
			toolbar: ToolbarContainer(
				toolbar: Toolbar(
					config: vm:toolbarConfig,
					onMenuOpen: local Function(MenuConfig is _m){ vm:refreshMenuStates(); }
				)
			),
			body: :buildSplitBody(),
			bottomBar: Bar(
				leftText: vm:cursorStatus,
				rightText: vm:syntaxStatus,
				rightInteractive: true,
				rightIconSvg: vm:icons:chevronDown,
				onRightClick: local Function(Int is x, Int is y){ vm:showSyntaxMenu(x: x, y: y); }
			),
			hasBottomBar: true,
			dialog: :aboutDialog(),
			hasDialog: true,
			fileDialog: :openFileDialog(),
			hasFileDialog: true,
			contextMenu: vm:contextMenu,
			onKey: local Function of Boolean(Int is key, Int is mods){ vm:handleShortcut(key: key, mods: mods) }
		);
		container:addDialog(d: SettingsDialogView(vm: vm:settingsVm));
		container:setZoom(zoomFactor: vm:settingsVm:model:zoomFactor());
		editorBody:setDocTextDeltaPt(deltaPt: vm:settingsVm:model:docTextDeltaPt);
		vm:settingsVm:bindHandlers(
			onThemeChange: local Function(Theme is t){ container:setTheme(nextTheme: t); },
			onZoomChange: local Function(Float is z){ container:setZoom(zoomFactor: z); },
			onDocTextDeltaChange: local Function(Float is d){
				editorBody:setDocTextDeltaPt(deltaPt: d);
				container:isDirty: true;
			},
			onPinnedChange: local Function(){ fileTree:invalidate(); },
			onDefaultsChange: local Function(Boolean is mono, Boolean is wrap, Boolean is showTree){
				vm:applyInterfaceDefaults(mono: mono, wrap: wrap, showTree: showTree);
			},
			onAddLocation: local Function(){ vm:requestPinLocation(); },
			getActiveDir: local Function of String(){ fileTree:rootPath }
		);
		container
	}
}
