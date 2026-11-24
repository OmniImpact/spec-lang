#! Package theofractal:view
#! Floating 3x2 overlay button cluster for panning (L/R/U/D) and zooming (+/-).

Class of Widget is NavOverlay{
	replace [String] is namespace: ['theofractal', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theofractal', 'util', FractalStrings],
		['theofractal', 'vm', ExplorerViewModel]
	];

	Array of Button is buttons: Array();

	replace Function is init(ExplorerViewModel is vm: ExplorerViewModel()){
		:buttons: Array([
			Button(label: FractalStrings:NAV_ZOOM_OUT, width: 3, onClick: { vm:zoomOut(); }),
			Button(label: FractalStrings:NAV_UP, width: 3, onClick: { vm:panUp(); }),
			Button(label: FractalStrings:NAV_ZOOM_IN, width: 3, onClick: { vm:zoomIn(); }),
			Button(label: FractalStrings:NAV_LEFT, width: 3, onClick: { vm:panLeft(); }),
			Button(label: FractalStrings:NAV_DOWN, width: 3, onClick: { vm:panDown(); }),
			Button(label: FractalStrings:NAV_RIGHT, width: 3, onClick: { vm:panRight(); })
		]);
	}

	Function of Boolean is fitsIn(Int is w, Int is h){ w >= 13 && h >= 3 }

	replace Function is applyTheme(TheoTheme is theme){
		:activeTheme: theme;
		local Int is i: 0;
		while({ i < buttons:length() }, {
			buttons:get(index: i):applyTheme(theme: theme);
			i: i + 1;
		});
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		local Int is i: 0;
		while({ i < buttons:length() }, {
			buttons:get(index: i):bindDirty(cb: cb);
			i: i + 1;
		});
	}

	replace Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
		if({ !fitsIn(w: w, h: h) || buttons:length() < 6 }, { return; });
		local Int is rx: x + w - 12;
		local Int is topY: y + h - 3;
		local Int is botY: y + h - 2;
		buttons:get(index: 0):layout(x: rx, y: topY, w: 3, h: 1);
		buttons:get(index: 1):layout(x: rx + 4, y: topY, w: 3, h: 1);
		buttons:get(index: 2):layout(x: rx + 8, y: topY, w: 3, h: 1);
		buttons:get(index: 3):layout(x: rx, y: botY, w: 3, h: 1);
		buttons:get(index: 4):layout(x: rx + 4, y: botY, w: 3, h: 1);
		buttons:get(index: 5):layout(x: rx + 8, y: botY, w: 3, h: 1);
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ !fitsIn(w: boxW, h: boxH) }, { return; });
		local Int is i: 0;
		while({ i < buttons:length() }, {
			buttons:get(index: i):paint(buf: buf, renderer: renderer);
			i: i + 1;
		});
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		if({ !fitsIn(w: boxW, h: boxH) }, { return false; });
		local Int is i: 0;
		while({ i < buttons:length() }, {
			if({ buttons:get(index: i):handleMouse(event: event) }, { return true; });
			i: i + 1;
		});
		return false;
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ !fitsIn(w: boxW, h: boxH) }, { return false; });
		local Int is i: 0;
		while({ i < buttons:length() }, {
			if({ buttons:get(index: i):handleKey(event: event) }, { return true; });
			i: i + 1;
		});
		return false;
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		if({ !fitsIn(w: boxW, h: boxH) }, { return; });
		local Int is i: 0;
		while({ i < buttons:length() }, {
			buttons:get(index: i):collectFocus(targets: targets, owners: owners);
			i: i + 1;
		});
	}
}
