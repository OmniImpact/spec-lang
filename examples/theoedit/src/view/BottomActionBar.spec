#! Package theoedit:view
#! Bottom action bar with Quit (left) and Save, Save As, Open (right) buttons.

Class of Frame is BottomActionBar{
	replace [String] is namespace: ['theoedit', 'view'];

	merge [[String]] is using: [
		['base', 'theo', [Frame, Widget, FocusTarget, KeyEvent, Panel, Row, Spacer, Button]],
		['theoedit', 'util', EditorStrings]
	];

	FocusTarget is saveFocus: FocusTarget();
	FocusTarget is saveAsFocus: FocusTarget();
	FocusTarget is openFocus: FocusTarget();
	FocusTarget is exitFocus: FocusTarget();
	Function is onSave: local Function(){};
	Function is onSaveAs: local Function(){};
	Function is onOpen: local Function(){};
	Function is onQuit: local Function(){};
	Function is onReturnToEditor: local Function(){};

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ (saveFocus:focused || saveAsFocus:focused || openFocus:focused || exitFocus:focused) && event:isUp() }, {
			onReturnToEditor();
			return true;
		});
		false;
	}

	replace Function of Widget is ui(){
		Panel(
			border: true,
			padX: 1,
			padY: 0,
			child: Row(
				gap: 2,
				arrowFocus: true,
				children: Array([
					Button(
						label: EditorStrings:LABEL_QUIT,
						shortcutKey: EditorStrings:KEY_QUIT,
						focusTarget: exitFocus,
						onClick: onQuit
					),
					Spacer(weight: 1.0),
					Button(
						label: EditorStrings:LABEL_SAVE,
						shortcutKey: EditorStrings:KEY_SAVE,
						focusTarget: saveFocus,
						onClick: onSave
					),
					Button(
						label: EditorStrings:LABEL_SAVE_AS,
						shortcutKey: EditorStrings:KEY_SAVE_AS,
						focusTarget: saveAsFocus,
						onClick: onSaveAs
					),
					Button(
						label: EditorStrings:LABEL_OPEN,
						shortcutKey: EditorStrings:KEY_OPEN,
						focusTarget: openFocus,
						onClick: onOpen
					)
				])
			)
		);
	}
}
