#! Package theoedit:view
#! Root Frame for the Theo simple text editor.

Class of Frame is EditorFrame{
	namespace: ['theoedit', 'view'];

	merge Array of Array of String is using: [
		['base', 'theo', [Frame, TheoScreen, Widget, Grid, GridPane, FocusTarget, KeyEvent]],
		['theoedit', 'vm', EditorViewModel],
		['theoedit', 'view', [TopBar, EditorBody, MessagePanel, BottomActionBar, FileManagerFrame]]
	];

	EditorViewModel is vm;
	Function is onQuit;
	Array of TheoScreen is screenRefs: [];

	FocusTarget is editorFocus: FocusTarget(initial: true);
	FocusTarget is saveFocus: FocusTarget();
	FocusTarget is saveAsFocus: FocusTarget();
	FocusTarget is openFocus: FocusTarget();
	FocusTarget is exitFocus: FocusTarget();

	FocusTarget is msgSaveFocus: FocusTarget();
	FocusTarget is msgDiscardFocus: FocusTarget();
	FocusTarget is msgCancelFocus: FocusTarget();

	Function is bindScreen(TheoScreen is screen){
		screenRefs: [screen];
	}

	local Function is openFileManager(String is mode, Boolean is quitAfterSave){
		if({ screenRefs:length() == 0 }, { return; });
		local TheoScreen is scr: screenRefs:get(index: 0);
		local String is initName: if({ mode == 'saveAs' }, { vm:filePath }, { '' });
		local FileManagerFrame is fm: FileManagerFrame(
			mode: mode,
			initialDir: '.',
			initialName: initName,
			onConfirm: local Function(String is chosenPath){
				if({ mode == 'saveAs' }, {
					local Boolean is saved: vm:saveTo(path: chosenPath);
					scr:pop();
					if({ saved && quitAfterSave }, {
						onQuit();
					}, {
						editorFocus:requestFocus();
					});
				}, {
					vm:openFile(path: chosenPath);
					scr:pop();
					editorFocus:requestFocus();
				});
			},
			onCancel: {
				scr:pop();
				editorFocus:requestFocus();
			}
		);
		scr:push(frame: fm);
	}

	local Function is triggerSave(){
		if({ vm:filePath == '' }, {
			openFileManager(mode: 'saveAs', quitAfterSave: false);
			return;
		});
		vm:save();
		editorFocus:requestFocus();
	}

	local Function is triggerQuit(){
		if({ vm:dirty }, {
			editorFocus:focused: false;
			saveFocus:focused: false;
			saveAsFocus:focused: false;
			openFocus:focused: false;
			exitFocus:focused: false;
			msgDiscardFocus:focused: false;
			msgCancelFocus:focused: false;
			vm:showUnsavedPrompt();
			rebuild();
			msgSaveFocus:requestFocus();
			return;
		});
		onQuit();
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ ((event:ctrl || event:alt) && event:key == 'm') || event:isEsc() }, {
			if({ vm:messageMode != 'none' }, {
				vm:clearMessage();
				rebuild();
				editorFocus:requestFocus();
				return true;
			});
			if({ editorFocus:focused }, {
				saveFocus:requestFocus();
			}, {
				editorFocus:requestFocus();
			});
			return true;
		});
		false;
	}

	replace Function of Widget is ui(){
		local Array of GridPane is panes: [
			Grid:fixed(
				size: 3,
				child: TopBar(
					title: vm:title,
					status: vm:status
				)
			),
			Grid:weight(
				weight: 1.0,
				child: EditorBody(
					vm: vm,
					focusTarget: editorFocus
				)
			)
		];
		if({ vm:messageMode != 'none' }, {
			panes:add(item: Grid:fixed(
				size: 3,
				child: MessagePanel(
					vm: vm,
					saveFocus: msgSaveFocus,
					discardFocus: msgDiscardFocus,
					cancelFocus: msgCancelFocus,
					onSave: {
						vm:clearMessage();
						rebuild();
						if({ vm:filePath == '' }, {
							openFileManager(mode: 'saveAs', quitAfterSave: true);
						}, {
							if({ vm:save() }, {
								onQuit();
							});
						});
					},
					onDiscard: {
						onQuit();
					},
					onCancel: {
						vm:clearMessage();
						rebuild();
						editorFocus:requestFocus();
					}
				)
			));
		});
		panes:add(item: Grid:fixed(
			size: 3,
			child: BottomActionBar(
				saveFocus: saveFocus,
				saveAsFocus: saveAsFocus,
				openFocus: openFocus,
				exitFocus: exitFocus,
				onSave: { triggerSave(); },
				onSaveAs: { openFileManager(mode: 'saveAs', quitAfterSave: false); },
				onOpen: { openFileManager(mode: 'open', quitAfterSave: false); },
				onQuit: { triggerQuit(); },
				onReturnToEditor: { editorFocus:requestFocus(); }
			)
		));
		Grid(
			orientation: 'vertical',
			panes: panes
		);
	}
}
