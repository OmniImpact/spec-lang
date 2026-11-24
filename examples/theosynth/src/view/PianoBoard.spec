#! Package theosynth:view
#! Main 3-row octave piano keyboard widget with mouse click and active-key highlight.

Class of Widget is PianoBoard{
	replace [String] is namespace: ['theosynth', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['base', 'sys', [as Conditional(), as Loops()]],
		['theosynth', 'model', PianoKey],
		['theosynth', 'vm', SynthViewModel]
	];

	SynthViewModel is vm: SynthViewModel();

	replace Function is init(SynthViewModel is vm){
		:vm: vm;
	}

	replace Function of Float is flexWeight(){ 1.0 }

	replace Function of Int is measureWidth(Int is maxW){ maxW }

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){ maxH }

	local Function of Int is keyWidth(){
		local Int is avail: boxW - 10;
		local Int is kw: avail / 12;
		if({ kw < 4 }, { return 4; });
		if({ kw > 9 }, { return 9; });
		return kw;
	}

	local Function of Int is keyHeight(){
		local Int is avail: boxH - 4;
		local Int is kh: avail / 3;
		if({ kh < 3 }, { return 3; });
		if({ kh > 6 }, { return 6; });
		return kh;
	}

	local Function of Int is boardOriginX(){
		local Int is totalW: 8 + keyWidth() * 12;
		local Int is ox: boxX + (boxW - totalW) / 2;
		if({ ox < boxX }, { return boxX; });
		return ox;
	}

	local Function of Int is boardOriginY(){
		local Int is totalH: keyHeight() * 3 + 2;
		local Int is oy: boxY + (boxH - totalH) / 2;
		if({ oy < boxY }, { return boxY; });
		return oy;
	}

	local Function is paintKeyTile(TheoBuffer is buf, PianoKey is pk, Int is kx, Int is ky, Int is kw, Int is kh, Boolean is active){
		local TheoColor is fg: TheoColor:rgb(r: 22, g: 24, b: 30);
		local TheoColor is bg: TheoColor:rgb(r: 235, g: 237, b: 242);
		if({ pk:isSharp }, {
			fg: TheoColor:rgb(r: 225, g: 230, b: 240);
			bg: TheoColor:rgb(r: 42, g: 46, b: 58);
		});
		if({ active }, {
			fg: TheoColor:rgb(r: 15, g: 20, b: 28);
			bg: TheoColor:rgb(r: 95, g: 210, b: 255);
		});
		local TheoColor is borderCol: if({ active }, { TheoColor:rgb(r: 255, g: 255, b: 255) }, { TheoColor:rgb(r: 110, g: 116, b: 132) });

		buf:fillRect(x: kx, y: ky, w: kw, h: kh, fg: fg, bg: bg);
		if({ kw >= 3 && kh >= 3 }, {
			buf:drawBox(x: kx, y: ky, w: kw, h: kh, borderColor: borderCol, bg: bg, rounded: false);
		});
		local String is noteShown: if({ pk:noteName:runeCount() > kw - 2 }, { pk:noteName:sliceRunes(start: 0, end: kw - 2) }, { pk:noteName });
		local Int is noteRow: ky + 1;
		if({ kh < 3 }, { noteRow: ky; });
		local Int is keyRow: if({ kh >= 4 }, { ky + kh - 2 }, { noteRow + 1 });
		if({ noteRow < ky + kh }, {
			buf:drawText(x: kx + 1, y: noteRow, text: noteShown, fg: fg, bg: bg, bold: true);
		});
		if({ keyRow < ky + kh && keyRow != noteRow }, {
			buf:drawText(x: kx + 1, y: keyRow, text: pk:keyChar, fg: fg, bg: bg, bold: active);
		});
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		buf:fillRect(x: boxX, y: boxY, w: boxW, h: boxH, fg: activeTheme:foreground, bg: activeTheme:background);

		local String is header: "TheoSynth  ·  {{vm:lastNoteLabel()}}";
		buf:drawText(x: boxX + 2, y: boxY, text: header, fg: activeTheme:foreground, bg: activeTheme:background, bold: true);

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
			while({ c < 12 }, {
				local Int is idx: r * 12 + c;
				if({ idx < vm:keys:length() }, {
					local PianoKey is pk: vm:keys:get(index: idx);
					local Int is kx: ox + 7 + c * kw;
					local Int is sharpOffset: if({ pk:isSharp && kh >= 4 }, { 0 }, { 0 });
					local Boolean is active: vm:activeTicks:get(index: idx) > 0;
					paintKeyTile(buf: buf, pk: pk, kx: kx, ky: ry + sharpOffset, kw: kw - 1, kh: kh, active: active);
				});
				c: c + 1;
			});
			r: r + 1;
		});
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		if({ !event:isLeftPress() || !containsPoint(x: event:x, y: event:y) }, { return false; });
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
					if({ col >= 0 && col < 12 }, {
						vm:triggerKeyIndex(idx: r * 12 + col);
						return true;
					});
				});
			});
			r: r + 1;
		});
		return false;
	}
}
