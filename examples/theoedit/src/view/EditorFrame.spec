#! Package theoedit:view
#! Root Frame for the Theo simple text editor.

Class of Frame is EditorFrame{
	namespace: ['theoedit', 'view'];

	merge Array of Array of String is using: [
		['base', 'theo', [Frame, TheoScreen, Widget, Grid, GridPane, FocusTarget, KeyEvent]],
		['theoedit', 'vm', EditorViewModel],
		['theoedit', 'view', [TopBar, EditorBody, MessagePanel, BottomActionBar, FileManagerFrame]]
	];

	EditorViewModel is vm: EditorViewModel(filePath: '');
	Function is onQuit: local Function(){};
	Array of TheoScreen is screenRefs: Array();

	FocusTarget is editorFocus: FocusTarget(initial: true);
	FocusTarget is saveFocus: FocusTarget();
	FocusTarget is saveAsFocus: FocusTarget();
	FocusTarget is openFocus: FocusTarget();
	FocusTarget is exitFocus: FocusTarget();

	FocusTarget is msgSaveFocus: FocusTarget();
	FocusTarget is msgDiscardFocus: FocusTarget();
	FocusTarget is msgCancelFocus: FocusTarget();

	Function is bindScreen(TheoScreen is screen){
		screenRefs: Array([screen]);
	}

	local Function is openFileManager(String is mode){
		if({ screenRefs:length() == 0 }, { return; });
		local TheoScreen is scr: screenRefs:get(index: 0);
		local String is initName: if({ mode == 'saveAs' }, { vm:filePath }, { '' });
		local FileManagerFrame is fm: FileManagerFrame(
			mode: mode,
			initialDir: '.',
			initialName: initName,
			onConfirm: local Function(String is chosenPath){
				local Boolean is finished: false;
				vm:completeFileDialog(
					mode: mode,
					path: chosenPath,
					onReadyToQuit: {
						finished: true;
						scr:pop();
						onQuit();
					}
				);
				if({ !finished }, {
					scr:pop();
					editorFocus:requestFocus();
				});
			},
			onCancel: {
				vm:clearMessage();
				scr:pop();
				editorFocus:requestFocus();
			}
		);
		scr:push(frame: fm);
	}

	local Function is clearAllFocus(){
		editorFocus:focused: false;
		saveFocus:focused: false;
		saveAsFocus:focused: false;
		openFocus:focused: false;
		exitFocus:focused: false;
		msgDiscardFocus:focused: false;
		msgCancelFocus:focused: false;
	}

	local Function is triggerSave(){
		local Boolean is openedDialog: false;
		vm:requestSave(onNeedSaveAs: {
			openedDialog: true;
			openFileManager(mode: 'saveAs');
		});
		if({ !openedDialog }, {
			editorFocus:requestFocus();
		});
	}

	local Function is triggerQuit(){
		vm:requestQuit(
			onNeedPrompt: {
				clearAllFocus();
				rebuild();
				msgSaveFocus:requestFocus();
			},
			onReadyToQuit: onQuit
		);
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ ((event:ctrl || event:alt) && event:key == 'm') || event:isEsc() }, {
			if({ vm:hasMessage() }, {
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
		local Array of GridPane is panes: Array([
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
		]);
		if({ vm:hasMessage() }, {
			panes:add(item: Grid:fixed(
				size: 3,
				child: MessagePanel(
					vm: vm,
					saveFocus: msgSaveFocus,
					discardFocus: msgDiscardFocus,
					cancelFocus: msgCancelFocus,
					onSave: {
						local Boolean is handled: false;
						vm:confirmPromptSave(
							onNeedSaveAs: {
								handled: true;
								rebuild();
								openFileManager(mode: 'saveAs');
							},
							onReadyToQuit: {
								handled: true;
								rebuild();
								onQuit();
							}
						);
						if({ !handled }, {
							rebuild();
						});
					},
					onDiscard: onQuit,
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
				onSaveAs: { openFileManager(mode: 'saveAs'); },
				onOpen: { openFileManager(mode: 'open'); },
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
