#! Package base:theo
#! Focusable boolean toggle switch widget with optional label and keyboard/mouse activation.

Class of Widget is Switch{
	replace [String] is namespace: ['base', 'theo'];

	merge [[String]] is using: [
		['base', 'theo', [Widget, FocusTarget, KeyEvent, MouseEvent, TheoColor, TheoBuffer, TheoRenderer]]
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
		local Int is w: 5;
		if({ label != '' }, {
			w: label:runeCount() + 6;
		});
		if({ w > maxW }, { return maxW; });
		return w;
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){ 1 }

	local Function is paintTrack(TheoBuffer is buf, Int is tx, Int is ty, String is track, TheoColor is useFg, TheoColor is useBg, Boolean is bold){
		buf:setCell(x: tx, y: ty, ch: '▐', fg: useBg, bg: TheoColor:none());
		buf:drawText(x: tx + 1, y: ty, text: track, fg: useFg, bg: useBg, bold: bold);
		buf:setCell(x: tx + 4, y: ty, ch: '▌', fg: useBg, bg: TheoColor:none());
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		local Boolean is foc: focusTarget:focused;
		local TheoColor is useFg: if({ foc }, { activeTheme:buttonFocusFg }, { if({ hovered }, { activeTheme:buttonHoverFg }, { activeTheme:buttonFg }) });
		local TheoColor is useBg: if({ foc }, { activeTheme:buttonFocusBg }, { if({ hovered }, { activeTheme:buttonHoverBg }, { activeTheme:buttonBg }) });
		local String is track: if({ checked }, { '  ●' }, { '○  ' });
		local Boolean is bold: foc || hovered;

		if({ label == '' }, {
			if({ boxW >= 5 }, {
				paintTrack(buf: buf, tx: boxX, ty: boxY, track: track, useFg: useFg, useBg: useBg, bold: bold);
			}, {
				buf:drawText(x: boxX, y: boxY, text: track, fg: useFg, bg: useBg, bold: bold);
			});
			return;
		});

		local Int is maxLabel: boxW - 6;
		local String is shown: if({ maxLabel > 0 }, {
			if({ label:runeCount() > maxLabel }, { label:sliceRunes(start: 0, end: maxLabel) }, { label })
		}, { '' });
		if({ shown != '' }, {
			buf:drawText(x: boxX, y: boxY, text: shown, fg: activeTheme:foreground, bg: TheoColor:none(), bold: bold);
			local Int is tx: boxX + shown:runeCount() + 1;
			if({ tx + 5 <= boxX + boxW }, {
				paintTrack(buf: buf, tx: tx, ty: boxY, track: track, useFg: useFg, useBg: useBg, bold: bold);
			});
		}, {
			if({ boxW >= 5 }, {
				paintTrack(buf: buf, tx: boxX, ty: boxY, track: track, useFg: useFg, useBg: useBg, bold: bold);
			});
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
