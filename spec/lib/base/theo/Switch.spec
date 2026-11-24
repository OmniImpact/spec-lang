#! Package base:theo
#! Focusable boolean toggle switch widget with optional label and keyboard/mouse activation.

Class of Widget is Switch{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [Widget, FocusTarget, KeyEvent, MouseEvent, TheoColor, TheoBuffer, TheoRenderer]],
		['base', 'sys', as Conditional()]
	];

	String is label: '';
	Boolean is checked: false;
	FocusTarget is focusTarget: FocusTarget();
	Function is onChange: local Function(Boolean is _checked){};
	Boolean is hovered: false;

	replace Function is init(
		String is label: '',
		Boolean is checked: false,
		FocusTarget is focusTarget: FocusTarget(),
		Function is onChange: local Function(Boolean is _checked){}
	){
		:label: label;
		:checked: checked;
		:focusTarget: focusTarget;
		:onChange: onChange;
		:hovered: false;
	}

	Function is toggle(){
		:checked: !checked;
		onChange(checked);
		invalidate();
	}

	Function is setChecked(Boolean is next){
		if({ checked == next }, { return; });
		:checked: next;
		onChange(checked);
		invalidate();
	}

	replace Function of Int is measureWidth(Int is maxW){
		local Int is w: 4;
		if({ label != '' }, {
			w: label:runeCount() + 5;
		});
		if({ w > maxW }, { return maxW; });
		return w;
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){ 1 }

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		local Boolean is foc: focusTarget:focused;
		local TheoColor is useFg: if({ foc }, { activeTheme:buttonFocusFg }, { if({ hovered }, { activeTheme:buttonHoverFg }, { activeTheme:buttonFg }) });
		local TheoColor is useBg: if({ foc }, { activeTheme:buttonFocusBg }, { if({ hovered }, { activeTheme:buttonHoverBg }, { activeTheme:buttonBg }) });
		local String is track: if({ checked }, { '[ ●]' }, { '[○ ]' });

		if({ label == '' }, {
			buf:drawText(x: boxX, y: boxY, text: track, fg: useFg, bg: useBg, bold: foc || hovered);
			return;
		});

		local Int is maxLabel: boxW - 5;
		local String is shown: if({ maxLabel > 0 }, {
			if({ label:runeCount() > maxLabel }, { label:sliceRunes(start: 0, end: maxLabel) }, { label })
		}, { '' });
		if({ shown != '' }, {
			buf:drawText(x: boxX, y: boxY, text: shown, fg: activeTheme:foreground, bg: TheoColor:none(), bold: foc || hovered);
			local Int is tx: boxX + shown:runeCount() + 1;
			if({ tx + 4 <= boxX + boxW }, {
				buf:drawText(x: tx, y: boxY, text: track, fg: useFg, bg: useBg, bold: foc || hovered);
			});
		}, {
			buf:drawText(x: boxX, y: boxY, text: track, fg: useFg, bg: useBg, bold: foc || hovered);
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
			toggle();
			return true;
		});
		return false;
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ !focusTarget:focused }, { return false; });
		if({ event:isEnter() || event:key == ' ' }, {
			toggle();
			return true;
		});
		return false;
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		targets:add(item: focusTarget);
		owners:add(item: :);
	}
}
