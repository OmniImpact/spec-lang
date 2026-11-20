#! Dynamic message/prompt panel shown between the editor and bottom action bar.

Class of Frame is MessagePanel{
	replace Array of Array of String is using: [
		['base', 'theo', Frame],
		['base', 'theo', Widget],
		['base', 'theo', FocusTarget],
		['base', 'theo', KeyEvent],
		['base', 'theo', TheoTheme],
		['base', 'theo', Panel],
		['base', 'theo', Row],
		['base', 'theo', Spacer],
		['base', 'theo', TextLine],
		['base', 'theo', Button],
		['base', 'sys', as Conditional()],
		[EditorViewModel]
	];

	EditorViewModel is vm;
	TheoTheme is theme: TheoTheme();
	FocusTarget is saveFocus;
	FocusTarget is discardFocus;
	FocusTarget is cancelFocus;
	Function is onSave;
	Function is onDiscard;
	Function is onCancel;

	replace Function is init(
		EditorViewModel is vm,
		FocusTarget is saveFocus,
		FocusTarget is discardFocus,
		FocusTarget is cancelFocus,
		Function is onSave,
		Function is onDiscard,
		Function is onCancel,
		TheoTheme is theme: TheoTheme()
	){
		:vm: vm;
		:saveFocus: saveFocus;
		:discardFocus: discardFocus;
		:cancelFocus: cancelFocus;
		:onSave: onSave;
		:onDiscard: onDiscard;
		:onCancel: onCancel;
		:theme: theme;
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ !saveFocus:focused && !discardFocus:focused && !cancelFocus:focused }, {
			return false;
		});
		if({ event:isEsc() }, {
			local Function is fn: onCancel;
			fn();
			return true;
		});
		if({ event:isLeft() }, {
			if({ cancelFocus:focused }, { discardFocus:requestFocus(); return true; });
			if({ discardFocus:focused }, { saveFocus:requestFocus(); return true; });
			return true;
		});
		if({ event:isRight() }, {
			if({ saveFocus:focused }, { discardFocus:requestFocus(); return true; });
			if({ discardFocus:focused }, { cancelFocus:requestFocus(); return true; });
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
				gap: 1,
				children: [
					TextLine(
						value: vm:messageText,
						color: theme:titleColor,
						bold: true
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
						label: ' Discard ',
						shortcutKey: 'd',
						focusTarget: discardFocus,
						fg: theme:buttonFg,
						bg: theme:buttonBg,
						focusFg: theme:buttonFocusFg,
						focusBg: theme:buttonFocusBg,
						onClick: onDiscard
					),
					Button(
						label: ' Cancel ',
						shortcutKey: 'c',
						focusTarget: cancelFocus,
						fg: theme:buttonFg,
						bg: theme:buttonBg,
						focusFg: theme:buttonFocusFg,
						focusBg: theme:buttonFocusBg,
						onClick: onCancel
					)
				]
			)
		);
	}
}
