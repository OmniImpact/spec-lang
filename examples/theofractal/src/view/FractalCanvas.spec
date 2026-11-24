#! Package theofractal:view
#! Half-block fractal canvas widget with overlayed L/R/U/D and zoom +/- navigation buttons.

Class of Widget is FractalCanvas{
	replace [String] is namespace: ['theofractal', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theofractal', 'util', FractalStrings],
		['theofractal', 'vm', ExplorerViewModel]
	];

	ExplorerViewModel is vm: ExplorerViewModel();
	Array of Button is navButtons: Array();

	replace Function is init(ExplorerViewModel is vm){
		:vm: vm;
		:navButtons: Array([
			Button(label: FractalStrings:NAV_ZOOM_OUT, width: 3, onClick: { :vm:zoomOut(); }),
			Button(label: FractalStrings:NAV_UP, width: 3, onClick: { :vm:panUp(); }),
			Button(label: FractalStrings:NAV_ZOOM_IN, width: 3, onClick: { :vm:zoomIn(); }),
			Button(label: FractalStrings:NAV_LEFT, width: 3, onClick: { :vm:panLeft(); }),
			Button(label: FractalStrings:NAV_DOWN, width: 3, onClick: { :vm:panDown(); }),
			Button(label: FractalStrings:NAV_RIGHT, width: 3, onClick: { :vm:panRight(); })
		]);
	}

	replace Function of Float is flexWeight(){ 1.0 }

	replace Function of Int is measureWidth(Int is maxW){ maxW }

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){ maxH }

	replace Function is applyTheme(TheoTheme is theme){
		:activeTheme: theme;
		local Int is i: 0;
		while({ i < navButtons:length() }, {
			navButtons:get(index: i):applyTheme(theme: theme);
			i: i + 1;
		});
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		local Int is i: 0;
		while({ i < navButtons:length() }, {
			navButtons:get(index: i):bindDirty(cb: cb);
			i: i + 1;
		});
	}

	replace Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
		if({ w >= 13 && h >= 3 && navButtons:length() >= 6 }, {
			local Int is rx: x + w - 12;
			local Int is topY: y + h - 3;
			local Int is botY: y + h - 2;
			navButtons:get(index: 0):layout(x: rx, y: topY, w: 3, h: 1);
			navButtons:get(index: 1):layout(x: rx + 4, y: topY, w: 3, h: 1);
			navButtons:get(index: 2):layout(x: rx + 8, y: topY, w: 3, h: 1);
			navButtons:get(index: 3):layout(x: rx, y: botY, w: 3, h: 1);
			navButtons:get(index: 4):layout(x: rx + 4, y: botY, w: 3, h: 1);
			navButtons:get(index: 5):layout(x: rx + 8, y: botY, w: 3, h: 1);
		});
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		if({ !vm:hasFractal() }, {
			buf:fillRect(x: boxX, y: boxY, w: boxW, h: boxH, fg: activeTheme:foreground, bg: activeTheme:background);
			return;
		});

		local Int is pixH: boxH * 2;
		local Array of TheoColor is pixels: vm:ensurePixels(w: boxW, h: pixH);
		if({ pixels:length() >= boxW * pixH }, {
			local Int is cy: 0;
			while({ cy < boxH }, {
				local Int is topOff: (cy * 2) * boxW;
				local Int is botOff: (cy * 2 + 1) * boxW;
				local Int is cx: 0;
				while({ cx < boxW }, {
					buf:setCell(
						x: boxX + cx,
						y: boxY + cy,
						ch: '▀',
						fg: pixels:get(index: topOff + cx),
						bg: pixels:get(index: botOff + cx)
					);
					cx: cx + 1;
				});
				cy: cy + 1;
			});
		});

		if({ boxW >= 13 && boxH >= 3 }, {
			local Int is i: 0;
			while({ i < navButtons:length() }, {
				navButtons:get(index: i):paint(buf: buf, renderer: renderer);
				i: i + 1;
			});
		});
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		if({ !vm:hasFractal() || boxW < 13 || boxH < 3 }, { return false; });
		local Int is i: 0;
		while({ i < navButtons:length() }, {
			if({ navButtons:get(index: i):handleMouse(event: event) }, {
				return true;
			});
			i: i + 1;
		});
		return false;
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ !vm:hasFractal() || boxW < 13 || boxH < 3 }, { return false; });
		local Int is i: 0;
		while({ i < navButtons:length() }, {
			if({ navButtons:get(index: i):handleKey(event: event) }, {
				return true;
			});
			i: i + 1;
		});
		return false;
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		if({ !vm:hasFractal() || boxW < 13 || boxH < 3 }, { return; });
		local Int is i: 0;
		while({ i < navButtons:length() }, {
			navButtons:get(index: i):collectFocus(targets: targets, owners: owners);
			i: i + 1;
		});
	}
}
