#! Package theoedit:view
#! Root Frame for the Theo simple text editor.

Class of Frame is EditorFrame{
	namespace: ['theoedit', 'view'];

	merge Array of Array of String is using: [
		['base', 'theo', [Frame, TheoScreen, Widget, Grid, GridPane, FocusTarget, KeyEvent]],
		['theoedit', 'vm', [EditorViewModel, FileManagerViewModel]],
		['theoedit', 'view', [TopBar, EditorBody, MessagePanel, BottomActionBar, FileManagerFrame]]
	];

	EditorViewModel is vm: EditorViewModel(filePath: '');

	FocusTarget is editorFocus: FocusTarget(initial: true);
	FocusTarget is saveFocus: FocusTarget();
	FocusTarget is saveAsFocus: FocusTarget();
	FocusTarget is openFocus: FocusTarget();
	FocusTarget is exitFocus: FocusTarget();

	FocusTarget is msgSaveFocus: FocusTarget();
	FocusTarget is msgDiscardFocus: FocusTarget();
	FocusTarget is msgCancelFocus: FocusTarget();

	replace Function is init(EditorViewModel is vm: EditorViewModel(filePath: ''), Function is onQuit: local Function(){}){
		:vm: vm;
		vm:onQuit: onQuit;
		vm:onRebuild: { rebuild(); };
		vm:onFocusEditor: { editorFocus:requestFocus(); };
		vm:onFocusMenu: { saveFocus:requestFocus(); };
		vm:onFocusPrompt: {
			editorFocus:focused: false;
			saveFocus:focused: false;
			saveAsFocus:focused: false;
			openFocus:focused: false;
			exitFocus:focused: false;
			msgDiscardFocus:focused: false;
			msgCancelFocus:focused: false;
			msgSaveFocus:requestFocus();
		};
	}

	Function is bindScreen(TheoScreen is screen){
		vm:onPushFileManager: local Function(FileManagerViewModel is fmVm){
			screen:push(frame: FileManagerFrame(vm: fmVm));
		};
		vm:onPopFileManager: {
			screen:pop();
		};
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ ((event:ctrl || event:alt) && event:key == 'm') || event:isEsc() }, {
			vm:toggleMenuOrCancelPrompt(editorIsFocused: editorFocus:focused);
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
					onSave: { vm:triggerPromptSave(); },
					onDiscard: { vm:triggerPromptDiscard(); },
					onCancel: { vm:triggerPromptCancel(); }
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
				onSave: { vm:triggerSave(); },
				onSaveAs: { vm:triggerSaveAs(); },
				onOpen: { vm:triggerOpen(); },
				onQuit: { vm:triggerQuit(); },
				onReturnToEditor: { editorFocus:requestFocus(); }
			)
		));
		Grid(
			orientation: 'vertical',
			panes: panes
		);
	}
}
