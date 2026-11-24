#! Package base:theo
#! Dropdown selector widget that opens a [ListView] menu inside a [Frame]-hosted [Overlay] anchored below itself.

Class of Widget is Dropdown{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [Widget, Frame, Overlay, Surface, Panel, ListView, FocusTarget, KeyEvent, MouseEvent, TheoColor, TheoBuffer, TheoRenderer, TheoTheme]],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	[String] is options: [];
	Int is selectedIdx: 0;
	Int is width: 0;
	FocusTarget is focusTarget: FocusTarget();
	Function is onSelect: local Function(String is _val){};
	Boolean is hovered: false;
	[Frame] is hostFrames: [];
	[Overlay] is menuOverlays: [];
	[ListView] is menuLists: [];

	local Function of Int is computeMenuWidth(Int is maxW){
		local Int is best: 10;
		local Int is i: 0;
		while({ i < options:length() }, {
			# Panel border (2) + ListView "  " prefix (2) + trailing space (1) = 5
			local Int is w: options:get(index: i):runeCount() + 5;
			if({ w > best }, { best: w; });
			i: i + 1;
		});
		if({ width > best }, { best: width; });
		if({ best > maxW }, { return maxW; });
		return best;
	}

	local Function of Int is computeWidth(Int is maxW){
		local Int is best: width;
		if({ best <= 0 }, {
			best: computeMenuWidth(maxW: maxW);
		});
		if({ best > maxW }, { return maxW; });
		return best;
	}

	replace Function is init(
		Frame is host,
		[String] is options: [],
		Int is selectedIdx: 0,
		String is selected: '',
		Int is width: 0,
		FocusTarget is focusTarget: FocusTarget(),
		Function is onSelect: local Function(String is _val){}
	){
		:options: options;
		:selectedIdx: selectedIdx;
		:width: width;
		:focusTarget: focusTarget;
		:onSelect: onSelect;
		:hovered: false;
		:hostFrames: [host];

		if({ selected != '' }, {
			local Int is si: 0;
			while({ si < options:length() }, {
				if({ options:get(index: si) == selected }, {
					:selectedIdx: si;
				});
				si: si + 1;
			});
		});

		local FocusTarget is listFocus: FocusTarget(initial: true);
		local ListView is lv: ListView(
			items: options,
			focusTarget: listFocus,
			onActivate: local Function(String is chosen){
				:selectByName(name: chosen);
				:closeMenu();
			}
		);
		if({ :selectedIdx >= 0 && :selectedIdx < options:length() }, {
			lv:selectedIdx: :selectedIdx;
		});
		:menuLists: [lv];

		local Widget is box: Panel(
			border: true,
			padX: 0,
			padY: 0,
			child: lv
		);
		local Surface is surf: Surface(
			child: box
		);
		local Overlay is ov: Overlay(
			closeOnEsc: true,
			closeOnBackdrop: true,
			content: surf
		);
		:menuOverlays: [ov];
		host:addOverlay(overlay: ov);
	}

	Function of String is selectedValue(){
		if({ selectedIdx >= 0 && selectedIdx < options:length() }, {
			return options:get(index: selectedIdx);
		});
		return '';
	}

	Function is selectByName(String is name){
		local Int is i: 0;
		while({ i < options:length() }, {
			if({ options:get(index: i) == name }, {
				:selectedIdx: i;
				onSelect(name);
				invalidate();
				return;
			});
			i: i + 1;
		});
	}

	Function is openMenu(){
		if({ hostFrames:length() == 0 || menuOverlays:length() == 0 }, { return; });
		local Overlay is ov: menuOverlays:get(index: 0);
		if({ menuLists:length() > 0 }, {
			menuLists:get(index: 0):selectedIdx: selectedIdx;
		});
		hostFrames:get(index: 0):showOverlay(overlay: ov, anchor: :);
	}

	Function is closeMenu(){
		if({ hostFrames:length() == 0 || menuOverlays:length() == 0 }, { return; });
		hostFrames:get(index: 0):closeOverlay(overlay: menuOverlays:get(index: 0));
	}

	Function of Boolean is isOpen(){
		if({ menuOverlays:length() == 0 }, { return false; });
		return menuOverlays:get(index: 0):open;
	}

	replace Function of Int is measureWidth(Int is maxW){ computeWidth(maxW: maxW) }

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){ 1 }

	replace Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
		if({ menuOverlays:length() > 0 }, {
			local Overlay is ov: menuOverlays:get(index: 0);
			local Int is menuW: computeMenuWidth(maxW: 80);
			if({ w > menuW }, { menuW: w; });
			local Int is menuH: options:length() + 2;
			if({ menuH < 3 }, { menuH: 3; });
			local Int is mx: x;
			local Int is my: y + h;
			local Int is hostW: if({ hostFrames:length() > 0 && hostFrames:get(index: 0):boxW > 0 }, { hostFrames:get(index: 0):boxW }, { 80 });
			local Int is hostH: if({ hostFrames:length() > 0 && hostFrames:get(index: 0):boxH > 0 }, { hostFrames:get(index: 0):boxH }, { 24 });
			if({ mx + menuW > hostW }, { mx: hostW - menuW; });
			if({ mx < 0 }, { mx: 0; });
			if({ my + menuH > hostH }, {
				if({ y - menuH >= 0 }, { my: y - menuH; }, { my: hostH - menuH; });
			});
			if({ my < 0 }, { my: 0; });
			ov:content:layout(x: mx, y: my, w: menuW, h: menuH);
		});
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		local Boolean is foc: focusTarget:focused;
		local TheoColor is useFg: if({ foc }, { activeTheme:buttonFocusFg }, { if({ hovered }, { activeTheme:buttonHoverFg }, { activeTheme:buttonFg }) });
		local TheoColor is useBg: if({ foc }, { activeTheme:buttonFocusBg }, { if({ hovered }, { activeTheme:buttonHoverBg }, { activeTheme:buttonBg }) });
		local String is val: selectedValue();
		local String is arrow: if({ isOpen() }, { '▲' }, { '▾' });
		local Int is innerW: boxW - 2;
		if({ innerW < 1 }, { innerW: 1; });
		local String is shown: if({ val:runeCount() > innerW - 2 }, { val:sliceRunes(start: 0, end: innerW - 2) }, { val });
		buf:fillRect(x: boxX, y: boxY, w: boxW, h: 1, fg: useFg, bg: useBg);
		buf:drawText(x: boxX + 1, y: boxY, text: shown, fg: useFg, bg: useBg, bold: foc || hovered);
		buf:drawText(x: boxX + boxW - 2, y: boxY, text: arrow, fg: useFg, bg: useBg, bold: foc || hovered);
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
			openMenu();
			return true;
		});
		return false;
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ !focusTarget:focused }, { return false; });
		if({ event:isEnter() || event:key == ' ' || event:isDown() || event:isUp() }, {
			openMenu();
			return true;
		});
		return false;
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		targets:add(item: focusTarget);
		owners:add(item: :);
	}
}
