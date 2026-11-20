#! Bottom action bar with Save, Save As, Open, and Quit buttons.

Class of Frame is BottomActionBar{
	replace Array of Array of String is using: [
		['base', 'theo', Frame],
		['base', 'theo', Widget],
		['base', 'theo', FocusTarget],
		['base', 'theo', KeyEvent],
		['base', 'theo', TheoTheme],
		['base', 'theo', Panel],
		['base', 'theo', Row],
		['base', 'theo', Spacer],
		['base', 'theo', Button],
		['base', 'sys', as Conditional()]
	];

	TheoTheme is theme: TheoTheme();
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
		Function is onReturnToEditor,
		TheoTheme is theme: TheoTheme()
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
		:theme: theme;
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ !saveFocus:focused && !saveAsFocus:focused && !openFocus:focused && !exitFocus:focused }, {
			return false;
		});
		if({ event:isUp() }, {
			local Function is fn: onReturnToEditor;
			fn();
			return true;
		});
		if({ event:isLeft() }, {
			if({ openFocus:focused }, { saveAsFocus:requestFocus(); return true; });
			if({ saveAsFocus:focused }, { saveFocus:requestFocus(); return true; });
			if({ saveFocus:focused }, { exitFocus:requestFocus(); return true; });
			return true;
		});
		if({ event:isRight() }, {
			if({ exitFocus:focused }, { saveFocus:requestFocus(); return true; });
			if({ saveFocus:focused }, { saveAsFocus:requestFocus(); return true; });
			if({ saveAsFocus:focused }, { openFocus:requestFocus(); return true; });
			return true;
		});
		return false;
	}

	replace Function of Widget is ui(){
		Panel(
			border: true,
			borderColor: theme:borderColor,
			rounded: theme:roundedBorders,
			padX: 1,
			padY: 0,
			child: Row(
				gap: 2,
				children: [
					Button(
						label: ' Quit ',
						shortcutKey: 'q',
						focusTarget: exitFocus,
						fg: theme:buttonFg,
						bg: theme:buttonBg,
						focusFg: theme:buttonFocusFg,
						focusBg: theme:buttonFocusBg,
						onClick: onQuit
					),
					Spacer(weight: 1.0),
					Button(
						label: ' Save ',
						shortcutKey: 's',
						focusTarget: saveFocus,
						fg: theme:buttonFg,
						bg: theme:buttonBg,
						focusFg: theme:buttonFocusFg,
						focusBg: theme:buttonFocusBg,
						onClick: onSave
					),
					Button(
						label: ' Save As ',
						shortcutKey: 'a',
						focusTarget: saveAsFocus,
						fg: theme:buttonFg,
						bg: theme:buttonBg,
						focusFg: theme:buttonFocusFg,
						focusBg: theme:buttonFocusBg,
						onClick: onSaveAs
					),
					Button(
						label: ' Open ',
						shortcutKey: 'o',
						focusTarget: openFocus,
						fg: theme:buttonFg,
						bg: theme:buttonBg,
						focusFg: theme:buttonFocusFg,
						focusBg: theme:buttonFocusBg,
						onClick: onOpen
					)
				]
			)
		);
	}
}
