#! Package base:theo
#! Focusable, scrollable list widget with Up/Down selection and Enter activation.

Class of Widget is ListView{
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

	Array of String is items: [];
	Int is selectedIdx: 0;
	Int is scrollY: 0;
	FocusTarget is focusTarget: FocusTarget();
	TheoColor is fg: TheoColor:ansi(code: 252);
	TheoColor is selectedFg: TheoColor:ansi(code: 16);
	TheoColor is selectedBg: TheoColor:ansi(code: 255);
	Array of TheoCallback is activateHooks: [];
	Array of TheoCallback is changeHooks: [];

	replace Function is init(
		Array of String is items: [],
		FocusTarget is focusTarget: FocusTarget(),
		TheoColor is fg: TheoColor:ansi(code: 252),
		TheoColor is selectedFg: TheoColor:ansi(code: 16),
		TheoColor is selectedBg: TheoColor:ansi(code: 255)
	){
		:items: items;
		:selectedIdx: 0;
		:scrollY: 0;
		:focusTarget: focusTarget;
		:fg: fg;
		:selectedFg: selectedFg;
		:selectedBg: selectedBg;
		:activateHooks: [];
		:changeHooks: [];
	}

	Function is bindOnActivate(Function is cb){
		:activateHooks: [TheoCallback(fn: cb)];
	}

	Function is bindOnSelectChange(Function is cb){
		:changeHooks: [TheoCallback(fn: cb)];
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

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		if({ selectedIdx < scrollY }, { :scrollY: selectedIdx; });
		if({ selectedIdx >= scrollY + boxH }, { :scrollY: selectedIdx - boxH + 1; });
		if({ scrollY < 0 }, { :scrollY: 0; });

		local Int is r: 0;
		while({ r < boxH && scrollY + r < items:length() }, {
			local Int is idx: scrollY + r;
			local String is item: items:get(index: idx);
			if({ idx == selectedIdx && focusTarget:focused }, {
				buf:fillRect(x: boxX, y: boxY + r, w: boxW, h: 1, fg: selectedFg, bg: selectedBg);
				buf:drawText(x: boxX, y: boxY + r, text: "  {{item}}", fg: selectedFg, bg: selectedBg, bold: true);
			}, {
				if({ idx == selectedIdx }, {
					buf:drawText(x: boxX, y: boxY + r, text: "> {{item}}", fg: fg, bold: true);
				}, {
					buf:drawText(x: boxX, y: boxY + r, text: "  {{item}}", fg: fg);
				});
			});
			r: r + 1;
		});
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ !focusTarget:focused }, { return false; });
		if({ items:length() == 0 }, { return false; });
		if({ event:isUp() }, {
			if({ selectedIdx > 0 }, {
				:selectedIdx: selectedIdx - 1;
				if({ changeHooks:length() > 0 }, {
					changeHooks:get(index: 0):callStr(s: selectedItem());
				});
				invalidate();
			});
			return true;
		});
		if({ event:isDown() }, {
			if({ selectedIdx + 1 < items:length() }, {
				:selectedIdx: selectedIdx + 1;
				if({ changeHooks:length() > 0 }, {
					changeHooks:get(index: 0):callStr(s: selectedItem());
				});
				invalidate();
			});
			return true;
		});
		if({ event:isEnter() }, {
			if({ activateHooks:length() > 0 }, {
				activateHooks:get(index: 0):callStr(s: selectedItem());
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
