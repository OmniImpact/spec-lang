#! Package base:theo
#! Focusable push button widget with background highlight and optional Ctrl+letter shortcut.

Class of Widget is Button{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', Widget],
		['base', 'theo', FocusTarget],
		['base', 'theo', KeyEvent],
		['base', 'theo', TheoColor],
		['base', 'theo', TheoBuffer],
		['base', 'theo', TheoRenderer],
		['base', 'theo', TheoCallback],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	String is label: '';
	String is shortcutKey: '';
	FocusTarget is focusTarget: FocusTarget();
	TheoColor is fg: TheoColor:ansi(code: 252);
	TheoColor is bg: TheoColor:ansi(code: 237);
	TheoColor is focusFg: TheoColor:ansi(code: 16);
	TheoColor is focusBg: TheoColor:ansi(code: 255);
	Array of TheoCallback is clickHooks: [];

	replace Function is init(
		String is label,
		Function is onClick,
		FocusTarget is focusTarget: FocusTarget(),
		String is shortcutKey: '',
		TheoColor is fg: TheoColor:ansi(code: 252),
		TheoColor is bg: TheoColor:ansi(code: 237),
		TheoColor is focusFg: TheoColor:ansi(code: 16),
		TheoColor is focusBg: TheoColor:ansi(code: 255)
	){
		:label: label;
		:shortcutKey: shortcutKey:toLower();
		:clickHooks: [TheoCallback(fn: onClick)];
		:focusTarget: focusTarget;
		:fg: fg;
		:bg: bg;
		:focusFg: focusFg;
		:focusBg: focusBg;
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
		local TheoColor is useFg: if({ foc }, { focusFg }, { fg });
		local TheoColor is useBg: if({ foc }, { focusBg }, { bg });
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
			buf:setCell(x: boxX + i, y: boxY, ch: ch, fg: useFg, bg: useBg, bold: foc, underline: under);
			i: i + 1;
		});
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ shortcutKey != '' && event:ctrl && event:key:toLower() == shortcutKey }, {
			if({ clickHooks:length() > 0 }, {
				clickHooks:get(index: 0):call();
			});
			return true;
		});
		if({ !focusTarget:focused }, { return false; });
		if({ event:isEnter() || (event:isChar() && event:key == ' ') }, {
			if({ clickHooks:length() > 0 }, {
				clickHooks:get(index: 0):call();
			});
			return true;
		});
		return false;
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		targets:add(item: focusTarget);
		owners:add(item: :);
	}
}
