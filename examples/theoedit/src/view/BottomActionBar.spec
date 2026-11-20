#! Package theoedit:view
#! Bottom action bar with Quit (left) and Save, Save As, Open (right) buttons.

Class of Frame is BottomActionBar{
	namespace: ['theoedit', 'view'];

	merge Array of Array of String is using: [
		['base', 'theo', [Frame, Widget, FocusTarget, KeyEvent, Panel, Row, Spacer, Button]]
	];

	FocusTarget is saveFocus;
	FocusTarget is saveAsFocus;
	FocusTarget is openFocus;
	FocusTarget is exitFocus;
	Function is onSave;
	Function is onSaveAs;
	Function is onOpen;
	Function is onQuit;
	Function is onReturnToEditor;

	replace Function is init(
		FocusTarget is saveFocus,
		FocusTarget is saveAsFocus,
		FocusTarget is openFocus,
		FocusTarget is exitFocus,
		Function is onSave,
		Function is onSaveAs,
		Function is onOpen,
		Function is onQuit,
		Function is onReturnToEditor
	){
		:saveFocus: saveFocus;
		:saveAsFocus: saveAsFocus;
		:openFocus: openFocus;
		:exitFocus: exitFocus;
		:onSave: onSave;
		:onSaveAs: onSaveAs;
		:onOpen: onOpen;
		:onQuit: onQuit;
		:onReturnToEditor: onReturnToEditor;
	}

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
				children: [
					Button(
						label: ' Quit ',
						shortcutKey: 'q',
						focusTarget: exitFocus,
						onClick: onQuit
					),
					Spacer(weight: 1.0),
					Button(
						label: ' Save ',
						shortcutKey: 's',
						focusTarget: saveFocus,
						onClick: onSave
					),
					Button(
						label: ' Save As ',
						shortcutKey: 'a',
						focusTarget: saveAsFocus,
						onClick: onSaveAs
					),
					Button(
						label: ' Open ',
						shortcutKey: 'o',
						focusTarget: openFocus,
						onClick: onOpen
					)
				]
			)
		);
	}
}
