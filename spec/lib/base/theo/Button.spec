#! Package base:theo
#! Focusable push button widget with background highlight and optional Ctrl+letter shortcut.

Class of Widget is Button{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [Widget, FocusTarget, KeyEvent, MouseEvent, TheoColor, TheoBuffer, TheoRenderer]],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	String is label: '';
	String is shortcutKey: '';
	FocusTarget is focusTarget: FocusTarget();
	TheoColor is fg: TheoColor:none();
	TheoColor is bg: TheoColor:none();
	TheoColor is focusFg: TheoColor:none();
	TheoColor is focusBg: TheoColor:none();
	TheoColor is hoverFg: TheoColor:none();
	TheoColor is hoverBg: TheoColor:none();
	Boolean is hovered: false;
	Function is onClick: {};

	replace Function is init(
		String is label,
		Function is onClick: {},
		FocusTarget is focusTarget: FocusTarget(),
		String is shortcutKey: '',
		TheoColor is fg: TheoColor:none(),
		TheoColor is bg: TheoColor:none(),
		TheoColor is focusFg: TheoColor:none(),
		TheoColor is focusBg: TheoColor:none(),
		TheoColor is hoverFg: TheoColor:none(),
		TheoColor is hoverBg: TheoColor:none()
	){
		:label: label;
		:shortcutKey: shortcutKey:toLower();
		:onClick: onClick;
		:focusTarget: focusTarget;
		:fg: fg;
		:bg: bg;
		:focusFg: focusFg;
		:focusBg: focusBg;
		:hoverFg: hoverFg;
		:hoverBg: hoverBg;
		:hovered: false;
	}

	replace Function of Int is measureWidth(Int is maxW){
		return label:length();
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){
		return 1;
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		local Boolean is foc: focusTarget:focused;
		local TheoColor is effFg: if({ fg:isSet() }, { fg }, { activeTheme:buttonFg });
		local TheoColor is effBg: if({ bg:isSet() }, { bg }, { activeTheme:buttonBg });
		local TheoColor is effFocusFg: if({ focusFg:isSet() }, { focusFg }, { activeTheme:buttonFocusFg });
		local TheoColor is effFocusBg: if({ focusBg:isSet() }, { focusBg }, { activeTheme:buttonFocusBg });
		local TheoColor is effHoverFg: if({ hoverFg:isSet() }, { hoverFg }, { activeTheme:buttonHoverFg });
		local TheoColor is effHoverBg: if({ hoverBg:isSet() }, { hoverBg }, { activeTheme:buttonHoverBg });
		local TheoColor is useFg: if({ foc }, { effFocusFg }, { if({ hovered }, { effHoverFg }, { effFg }) });
		local TheoColor is useBg: if({ foc }, { effFocusBg }, { if({ hovered }, { effHoverBg }, { effBg }) });
		local Boolean is underlinedShortcut: false;
		local Int is n: label:length();
		local Int is i: 0;
		while({ i < n }, {
			local String is ch: label:charAt(index: i, default: ' ');
			local Boolean is under: false;
			if({ shortcutKey != '' && !underlinedShortcut && ch:toLower() == shortcutKey }, {
				under: true;
				underlinedShortcut: true;
			});
			buf:setCell(x: boxX + i, y: boxY, ch: ch, fg: useFg, bg: useBg, bold: foc || hovered, underline: under);
			i: i + 1;
		});
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		local Boolean is inside: containsPoint(x: event:x, y: event:y);
		if({ event:isMove() }, {
			if({ hovered != inside }, {
				:hovered: inside;
				focusTarget:setHovered(next: inside);
				return true;
			});
			return false;
		});
		if({ event:isLeftPress() && inside }, {
			focusTarget:requestFocus();
			onClick();
			return true;
		});
		return false;
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ shortcutKey != '' && event:ctrl && event:key:toLower() == shortcutKey }, {
			onClick();
			return true;
		});
		if({ !focusTarget:focused }, { return false; });
		if({ event:isEnter() || (event:isChar() && event:key == ' ') }, {
			onClick();
			return true;
		});
		return false;
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		targets:add(item: focusTarget);
		owners:add(item: :);
	}
}
