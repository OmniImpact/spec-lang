#! Main scrollable text-editing pane for the Theo simple text editor.

Class of Frame is EditorBody{
	replace Array of Array of String is using: [
		['base', 'theo', Frame],
		['base', 'theo', Widget],
		['base', 'theo', FocusTarget],
		['base', 'theo', TheoTheme],
		['base', 'theo', Panel],
		['base', 'theo', TextArea],
		[EditorViewModel]
	];

	EditorViewModel is vm;
	FocusTarget is focusTarget;
	TheoTheme is theme: TheoTheme();

	replace Function is init(EditorViewModel is vm, FocusTarget is focusTarget, TheoTheme is theme: TheoTheme()){
		:vm: vm;
		:focusTarget: focusTarget;
		:theme: theme;
	}

	replace Function of Widget is ui(){
		Panel(
			border: true,
			borderColor: theme:borderColor,
			rounded: theme:roundedBorders,
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
