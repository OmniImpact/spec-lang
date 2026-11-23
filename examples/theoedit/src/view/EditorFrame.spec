#! Package theoedit:view
#! Root Frame for the Theo simple text editor.

Class of Frame is EditorFrame{
	namespace: ['theoedit', 'view'];

	merge Array of Array of String is using: [
		['base', 'theo', [Frame, TheoScreen, Widget, Grid, GridPane, FocusTarget, KeyEvent]],
		['base', 'sys', as Loops()],
		['theoedit', 'vm', [EditorFocus, EditorViewModel, FileManagerViewModel]],
		['theoedit', 'view', [TopBar, EditorBody, MessagePanel, BottomActionBar, FileManagerFrame]]
	];

	EditorViewModel is vm;

	FocusTarget is editorFocus: FocusTarget(initial: true);
	FocusTarget is saveFocus: FocusTarget();
	FocusTarget is saveAsFocus: FocusTarget();
	FocusTarget is openFocus: FocusTarget();
	FocusTarget is exitFocus: FocusTarget();

	FocusTarget is msgSaveFocus: FocusTarget();
	FocusTarget is msgDiscardFocus: FocusTarget();
	FocusTarget is msgCancelFocus: FocusTarget();

	replace Function is init(EditorViewModel is vm, Function is onQuit: local Function(){}){
		:vm: vm;
		vm:onQuit: onQuit;
		vm:onRebuild: { rebuild(); };

		local [FocusTarget] is targets: [editorFocus, saveFocus, saveAsFocus, openFocus, exitFocus, msgSaveFocus, msgDiscardFocus, msgCancelFocus];
		local [EditorFocus] is focusIds: [EditorFocus:EDITOR, EditorFocus:SAVE, EditorFocus:SAVE_AS, EditorFocus:OPEN, EditorFocus:QUIT, EditorFocus:PROMPT_SAVE, EditorFocus:PROMPT_DISCARD, EditorFocus:PROMPT_CANCEL];

		times(count: targets:length(), worker: local Function(Int is i){
			local FocusTarget is ft: targets:get(index: i);
			local EditorFocus is fid: focusIds:get(index: i);
			ft:onFocus(handler: {
				vm:setFocus(target: fid);
			});
			ft:onHover(handler: {
				vm:setHover(target: fid, isHovered: ft:hovered);
			});
		});

		vm:focus:collect(onEmit: {
			local EditorFocus is cur: vm:focus:current();
			times(count: targets:length(), worker: local Function(Int is i){
				local FocusTarget is ft: targets:get(index: i);
				if({ focusIds:get(index: i) == cur }, {
					if({ !ft:focused }, {
						ft:requestFocus();
					});
				}, {
					ft:focused: false;
				});
			});
		});
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
			vm:toggleMenuOrCancelPrompt();
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
