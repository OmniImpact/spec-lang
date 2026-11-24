#! Package theoedit:view
#! Dynamic message/prompt panel shown between the editor and bottom action bar.

Class of Frame is MessagePanel{
	namespace: ['theoedit', 'view'];

	merge Array of Array of String is using: [
		['base', 'theo', [Frame, Widget, FocusTarget, KeyEvent, Panel, Row, Spacer, TextLine, Button]],
		['theoedit', 'util', EditorStrings],
		['theoedit', 'vm', EditorViewModel]
	];

	EditorViewModel is vm: EditorViewModel(filePath: '');
	FocusTarget is saveFocus: FocusTarget();
	FocusTarget is discardFocus: FocusTarget();
	FocusTarget is cancelFocus: FocusTarget();
	Function is onSave: local Function(){};
	Function is onDiscard: local Function(){};
	Function is onCancel: local Function(){};

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ (saveFocus:focused || discardFocus:focused || cancelFocus:focused) && event:isEsc() }, {
			onCancel();
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
				gap: 1,
				arrowFocus: true,
				children: Array([
					TextLine(
						value: vm:messageText,
						color: activeTheme:titleColor,
						bold: true
					),
					Spacer(weight: 1.0),
					Button(
						label: EditorStrings:LABEL_SAVE,
						shortcutKey: EditorStrings:KEY_SAVE,
						focusTarget: saveFocus,
						onClick: onSave
					),
					Button(
						label: EditorStrings:LABEL_DISCARD,
						shortcutKey: EditorStrings:KEY_DISCARD,
						focusTarget: discardFocus,
						onClick: onDiscard
					),
					Button(
						label: EditorStrings:LABEL_CANCEL,
						shortcutKey: EditorStrings:KEY_CANCEL,
						focusTarget: cancelFocus,
						onClick: onCancel
					)
				])
			)
		);
	}
}
