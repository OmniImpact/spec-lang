#! Package theoedit:view
#! Main scrollable text-editing pane for the Theo simple text editor.

Class of Frame is EditorBody{
	namespace: ['theoedit', 'view'];

	merge Array of Array of String is using: [
		['base', 'theo', [Frame, Widget, FocusTarget, Panel, TextArea]],
		['theoedit', 'vm', EditorViewModel]
	];

	EditorViewModel is vm;
	FocusTarget is focusTarget;

	replace Function is init(EditorViewModel is vm, FocusTarget is focusTarget){
		:vm: vm;
		:focusTarget: focusTarget;
	}

	replace Function of Widget is ui(){
		Panel(
			border: true,
			padding: 0,
			scrollable: true,
			child: TextArea(
				value: vm:content,
				focusTarget: focusTarget,
				onChange: local Function(String is nextText){
					vm:onTextChanged(nextText: nextText);
				}
			)
		);
	}
}
