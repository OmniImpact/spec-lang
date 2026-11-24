#! Package theosynth:view
#! Main 3-row octave white-key piano keyboard widget wrapped in a focusable Play-Mode panel.

Class of Widget is PianoBoard{
	replace [String] is namespace: ['theosynth', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['base', 'sys', [as Conditional(), as Loops()]],
		['theosynth', 'model', PianoKey],
		['theosynth', 'vm', SynthViewModel]
	];

	SynthViewModel is vm: SynthViewModel();
	FocusTarget is focusTarget: FocusTarget(initial: true);

	replace Function is init(SynthViewModel is vm, FocusTarget is focusTarget: FocusTarget(initial: true)){
		:vm: vm;
		:focusTarget: focusTarget;
	}

	replace Function of Float is flexWeight(){ 1.0 }

	replace Function of Int is measureWidth(Int is maxW){ maxW }

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){ maxH }

	local Function of Int is keyWidth(){
		local Int is avail: boxW - 12;
		local Int is kw: avail / 7;
		if({ kw < 5 }, { return 5; });
		if({ kw > 11 }, { return 11; });
		return kw;
	}

	local Function of Int is keyHeight(){
		local Int is avail: boxH - 5;
		local Int is kh: avail / 3;
		if({ kh < 3 }, { return 3; });
		if({ kh > 6 }, { return 6; });
		return kh;
	}

	local Function of Int is boardOriginX(){
		local Int is totalW: 7 + keyWidth() * 7;
		local Int is ox: boxX + (boxW - totalW) / 2;
		if({ ox < boxX + 2 }, { return boxX + 2; });
		return ox;
	}

	local Function of Int is boardOriginY(){
		local Int is totalH: keyHeight() * 3 + 2;
		local Int is oy: boxY + 1 + (boxH - 2 - totalH) / 2;
		if({ oy < boxY + 2 }, { return boxY + 2; });
		return oy;
	}

	local Function is paintKeyTile(TheoBuffer is buf, PianoKey is pk, Int is kx, Int is ky, Int is kw, Int is kh, Boolean is active){
		local TheoColor is fg: TheoColor:rgb(r: 22, g: 24, b: 30);
		local TheoColor is bg: TheoColor:rgb(r: 235, g: 237, b: 242);
		if({ active }, {
			fg: TheoColor:rgb(r: 15, g: 20, b: 28);
			bg: TheoColor:rgb(r: 95, g: 210, b: 255);
		});
		local TheoColor is borderCol: TheoColor:rgb(r: 120, g: 128, b: 145);
		if({ active }, {
			borderCol: TheoColor:rgb(r: 255, g: 255, b: 255);
		});

		buf:fillRect(x: kx, y: ky, w: kw, h: kh, fg: fg, bg: bg);
		if({ kw >= 3 && kh >= 3 }, {
			buf:drawBox(x: kx, y: ky, w: kw, h: kh, borderColor: borderCol, bg: bg, rounded: false);
		});
		local Int is noteRow: if({ kh >= 3 }, { ky + 1 }, { ky });
		local Int is keyRow: if({ kh >= 4 }, { ky + kh - 2 }, { noteRow + 1 });
		if({ noteRow < ky + kh }, {
			buf:drawText(x: kx + 1, y: noteRow, text: pk:noteName, fg: fg, bg: bg, bold: true);
		});
		if({ keyRow < ky + kh && keyRow != noteRow }, {
			buf:drawText(x: kx + 1, y: keyRow, text: pk:keyChar, fg: fg, bg: bg, bold: active);
		});
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		local Boolean is focused: focusTarget:focused;
		if({ vm:playMode != focused }, {
			vm:playMode: focused;
		});

		buf:fillRect(x: boxX, y: boxY, w: boxW, h: boxH, fg: activeTheme:foreground, bg: activeTheme:background);
		local TheoColor is panelBorder: activeTheme:borderColor;
		if({ focused }, {
			panelBorder: TheoColor:rgb(r: 95, g: 210, b: 255);
		});
		buf:drawBox(x: boxX, y: boxY, w: boxW, h: boxH, borderColor: panelBorder, bg: activeTheme:background, rounded: true);

		local String is modeLabel: if({ focused }, { 'PLAY MODE' }, { 'CONTROLS' });
		local String is title: " TheoSynth [{{modeLabel}}] (Ctrl+P) · {{vm:lastNoteLabel()}} ";
		if({ boxW > 4 }, {
			local String is shownTitle: if({ title:runeCount() > boxW - 4 }, { title:sliceRunes(start: 0, end: boxW - 4) }, { title });
			buf:drawText(x: boxX + 2, y: boxY, text: shownTitle, fg: panelBorder, bg: activeTheme:background, bold: focused);
		});

		local Int is kw: keyWidth();
		local Int is kh: keyHeight();
		local Int is ox: boardOriginX();
		local Int is oy: boardOriginY();
		local [String] is rowLabels: ['Oct 5', 'Oct 4', 'Oct 3'];

		local Int is r: 0;
		while({ r < 3 }, {
			local Int is ry: oy + r * (kh + 1);
			buf:drawText(x: ox, y: ry + kh / 2, text: rowLabels:get(index: r), fg: activeTheme:foreground, bg: activeTheme:background, bold: true);
			local Int is c: 0;
			while({ c < 7 }, {
				local Int is idx: r * 7 + c;
				if({ idx < vm:keys:length() }, {
					local PianoKey is pk: vm:keys:get(index: idx);
					local Int is kx: ox + 7 + c * kw;
					local Boolean is active: vm:activeTicks:get(index: idx) > 0;
					paintKeyTile(buf: buf, pk: pk, kx: kx, ky: ry, kw: kw - 1, kh: kh, active: active);
				});
				c: c + 1;
			});
			r: r + 1;
		});
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		if({ !event:isLeftPress() || !containsPoint(x: event:x, y: event:y) }, { return false; });
		focusTarget:requestFocus();
		vm:setPlayMode(enabled: true);
		local Int is kw: keyWidth();
		local Int is kh: keyHeight();
		local Int is ox: boardOriginX() + 7;
		local Int is oy: boardOriginY();
		local Int is r: 0;
		while({ r < 3 }, {
			local Int is ry: oy + r * (kh + 1);
			if({ event:y >= ry && event:y < ry + kh }, {
				local Int is relX: event:x - ox;
				if({ relX >= 0 }, {
					local Int is col: relX / kw;
					if({ col >= 0 && col < 7 }, {
						vm:triggerKeyIndex(idx: r * 7 + col, autoRelease: true);
						return true;
					});
				});
			});
			r: r + 1;
		});
		return true;
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		targets:add(item: focusTarget);
		owners:add(item: :);
	}
}
