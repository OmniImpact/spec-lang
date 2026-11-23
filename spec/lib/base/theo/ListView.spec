#! Package base:theo
#! Focusable, scrollable list widget with Up/Down selection and Enter activation.

Class of Widget is ListView{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', [Widget, FocusTarget, KeyEvent, MouseEvent, TheoColor, TheoBuffer, TheoRenderer]],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	Array of String is items: Array();
	Int is selectedIdx: 0;
	Int is scrollY: 0;
	FocusTarget is focusTarget: FocusTarget();
	TheoColor is fg: TheoColor:none();
	TheoColor is selectedFg: TheoColor:none();
	TheoColor is selectedBg: TheoColor:none();
	Function is onActivate: local Function(String is _item){};
	Function is onSelectChange: local Function(String is _item){};

	replace Function is init(
		Array of String is items: Array(),
		FocusTarget is focusTarget: FocusTarget(),
		Function is onActivate: local Function(String is _item){},
		Function is onSelectChange: local Function(String is _item){},
		TheoColor is fg: TheoColor:none(),
		TheoColor is selectedFg: TheoColor:none(),
		TheoColor is selectedBg: TheoColor:none()
	){
		:items: items;
		:selectedIdx: 0;
		:scrollY: 0;
		:focusTarget: focusTarget;
		:onActivate: onActivate;
		:onSelectChange: onSelectChange;
		:fg: fg;
		:selectedFg: selectedFg;
		:selectedBg: selectedBg;
	}

	Function is bindOnActivate(Function is cb){
		:onActivate: cb;
	}

	Function is bindOnSelectChange(Function is cb){
		:onSelectChange: cb;
	}

	Function is setItems(Array of String is nextItems){
		:items: nextItems;
		:selectedIdx: 0;
		:scrollY: 0;
		invalidate();
	}

	Function of String is selectedItem(){
		if({ selectedIdx >= 0 && selectedIdx < items:length() }, {
			return items:get(index: selectedIdx);
		});
		return '';
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){
		return maxH;
	}

	replace Function of Int is scrollOffsetY(){
		return scrollY;
	}

	replace Function of Int is scrollContentH(){
		return items:length();
	}

	replace Function of Int is scrollViewportH(){
		return boxH;
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		if({ selectedIdx < scrollY }, { :scrollY: selectedIdx; });
		if({ selectedIdx >= scrollY + boxH }, { :scrollY: selectedIdx - boxH + 1; });
		if({ scrollY < 0 }, { :scrollY: 0; });

		local TheoColor is effFg: if({ fg:isSet() }, { fg }, { activeTheme:foreground });
		local TheoColor is effSelFg: if({ selectedFg:isSet() }, { selectedFg }, { activeTheme:buttonFocusFg });
		local TheoColor is effSelBg: if({ selectedBg:isSet() }, { selectedBg }, { activeTheme:buttonFocusBg });
		local Int is r: 0;
		while({ r < boxH && scrollY + r < items:length() }, {
			local Int is idx: scrollY + r;
			local String is item: items:get(index: idx);
			if({ idx == selectedIdx && focusTarget:focused }, {
				buf:fillRect(x: boxX, y: boxY + r, w: boxW, h: 1, fg: effSelFg, bg: effSelBg);
				buf:drawText(x: boxX, y: boxY + r, text: "  {{item}}", fg: effSelFg, bg: effSelBg, bold: true);
			}, {
				if({ idx == selectedIdx }, {
					buf:drawText(x: boxX, y: boxY + r, text: "> {{item}}", fg: effFg, bold: true);
				}, {
					buf:drawText(x: boxX, y: boxY + r, text: "  {{item}}", fg: effFg);
				});
			});
			r: r + 1;
		});
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		if({ !containsPoint(x: event:x, y: event:y) }, { return false; });
		if({ items:length() == 0 }, { return false; });
		if({ event:isWheelUp() }, {
			if({ scrollY > 0 }, {
				:scrollY: scrollY - 1;
				invalidate();
				return true;
			});
			return false;
		});
		if({ event:isWheelDown() }, {
			local Int is maxScroll: items:length() - boxH;
			if({ maxScroll < 0 }, { maxScroll: 0; });
			if({ scrollY < maxScroll }, {
				:scrollY: scrollY + 1;
				invalidate();
				return true;
			});
			return false;
		});
		if({ event:isLeftPress() }, {
			focusTarget:requestFocus();
			local Int is idx: scrollY + (event:y - boxY);
			if({ idx >= 0 && idx < items:length() }, {
				if({ idx == selectedIdx }, {
					onActivate(selectedItem());
				}, {
					:selectedIdx: idx;
					onSelectChange(selectedItem());
				});
				invalidate();
			});
			return true;
		});
		return false;
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ !focusTarget:focused }, { return false; });
		if({ items:length() == 0 }, { return false; });
		if({ event:isUp() }, {
			if({ selectedIdx > 0 }, {
				:selectedIdx: selectedIdx - 1;
				onSelectChange(selectedItem());
				invalidate();
			});
			return true;
		});
		if({ event:isDown() }, {
			if({ selectedIdx + 1 < items:length() }, {
				:selectedIdx: selectedIdx + 1;
				onSelectChange(selectedItem());
				invalidate();
			});
			return true;
		});
		if({ event:isEnter() }, {
			onActivate(selectedItem());
			return true;
		});
		return false;
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		targets:add(item: focusTarget);
		owners:add(item: :);
	}
}
