#! Package theofractal:view
#! Half-block fractal canvas widget delegating overlayed navigation controls to [NavOverlay].

Class of Widget is FractalCanvas{
	replace [String] is namespace: ['theofractal', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theofractal', 'vm', ExplorerViewModel],
		['theofractal', 'view', NavOverlay]
	];

	ExplorerViewModel is vm: ExplorerViewModel();
	NavOverlay is navOverlay: NavOverlay();

	replace Function is init(ExplorerViewModel is vm){
		:vm: vm;
		:navOverlay: NavOverlay(vm: vm);
	}

	replace Function of Float is flexWeight(){ 1.0 }

	replace Function of Int is measureWidth(Int is maxW){ maxW }

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){ maxH }

	replace Function is applyTheme(TheoTheme is theme){
		:activeTheme: theme;
		navOverlay:applyTheme(theme: theme);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		navOverlay:bindDirty(cb: cb);
	}

	replace Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
		navOverlay:layout(x: x, y: y, w: w, h: h);
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

		navOverlay:paint(buf: buf, renderer: renderer);
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		if({ !vm:hasFractal() }, { return false; });
		return navOverlay:handleMouse(event: event);
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ !vm:hasFractal() }, { return false; });
		return navOverlay:handleKey(event: event);
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		if({ !vm:hasFractal() }, { return; });
		navOverlay:collectFocus(targets: targets, owners: owners);
	}
}
