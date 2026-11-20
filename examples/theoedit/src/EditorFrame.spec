#! Root Frame for the Theo simple text editor.

Class of Frame is EditorFrame{
	replace Array of Array of String is using: [
		['base', 'theo', Frame],
		['base', 'theo', TheoScreen],
		['base', 'theo', Widget],
		['base', 'theo', Grid],
		['base', 'theo', GridPane],
		['base', 'theo', FocusTarget],
		['base', 'theo', KeyEvent],
		['base', 'theo', TheoTheme],
		['base', 'sys', as Conditional()],
		[EditorViewModel],
		[TopBar],
		[EditorBody],
		[MessagePanel],
		[BottomActionBar],
		[FileManagerFrame]
	];

	EditorViewModel is vm;
	TheoTheme is theme: TheoTheme();
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

	replace Function is init(EditorViewModel is vm, Function is onQuit, TheoTheme is theme: TheoTheme()){
		:vm: vm;
		:onQuit: onQuit;
		:theme: theme;
		:screenRefs: [];
	}

	Function is bindScreen(TheoScreen is screen){
		:screenRefs: [screen];
	}

	local Function is openFileManager(String is mode, Boolean is quitAfterSave){
		if({ screenRefs:length() == 0 }, { return; });
		local TheoScreen is scr: screenRefs:get(index: 0);
		local String is initName: if({ mode == 'saveAs' }, { vm:filePath }, { '' });
		local FileManagerFrame is fm: FileManagerFrame(
			mode: mode,
			initialDir: '.',
			initialName: initName,
			theme: theme,
			onConfirm: local Function(String is chosenPath){
				if({ mode == 'saveAs' }, {
					local Boolean is saved: vm:saveTo(path: chosenPath);
					scr:pop();
					if({ saved && quitAfterSave }, {
						local Function is qfn: onQuit;
						qfn();
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
			:editorFocus:focused: false;
			:saveFocus:focused: false;
			:saveAsFocus:focused: false;
			:openFocus:focused: false;
			:exitFocus:focused: false;
			:msgDiscardFocus:focused: false;
			:msgCancelFocus:focused: false;
			vm:showUnsavedPrompt();
			rebuild();
			msgSaveFocus:requestFocus();
			return;
		});
		local Function is fn: onQuit;
		fn();
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
		return false;
	}

	replace Function of Widget is ui(){
		local Array of GridPane is panes: [
			Grid:fixed(
				size: 3,
				child: TopBar(
					title: vm:title,
					status: vm:status,
					theme: theme
				)
			),
			Grid:weight(
				weight: 1.0,
				child: EditorBody(
					vm: vm,
					focusTarget: editorFocus,
					theme: theme
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
					theme: theme,
					onSave: {
						vm:clearMessage();
						rebuild();
						if({ vm:filePath == '' }, {
							openFileManager(mode: 'saveAs', quitAfterSave: true);
						}, {
							if({ vm:save() }, {
								local Function is fn: onQuit;
								fn();
							});
						});
					},
					onDiscard: {
						local Function is fn: onQuit;
						fn();
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
				theme: theme,
				onSave: {
					triggerSave();
				},
				onSaveAs: {
					openFileManager(mode: 'saveAs', quitAfterSave: false);
				},
				onOpen: {
					openFileManager(mode: 'open', quitAfterSave: false);
				},
				onQuit: {
					triggerQuit();
				},
				onReturnToEditor: {
					editorFocus:requestFocus();
				}
			)
		));
		return Grid(
			orientation: 'vertical',
			panes: panes
		);
	}
}
