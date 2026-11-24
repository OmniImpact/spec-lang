#! Package theoedit:view
#! Main scrollable text-editing pane for the Theo simple text editor.

Class of Frame is EditorBody{
	replace [String] is namespace: ['theoedit', 'view'];

	merge [[String]] is using: [
		['base', 'theo', [Frame, Widget, FocusTarget, Panel, CodeTextArea]],
		['theoedit', 'vm', EditorViewModel]
	];

	EditorViewModel is vm: EditorViewModel(filePath: '');
	FocusTarget is focusTarget: FocusTarget();

	replace Function of Widget is ui(){
		Panel(
			border: true,
			padding: 0,
			scrollable: true,
			child: CodeTextArea:fromEmitters(
				value: vm:content,
				filePath: vm:currentPath,
				focusTarget: focusTarget,
				onChange: local Function(String is nextText){
					vm:onTextChanged(nextText: nextText);
				}
			)
		);
	}
}
