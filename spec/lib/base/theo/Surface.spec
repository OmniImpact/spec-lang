#! Package base:theo
#! Solid-background container surface for widgets and overlays.

Class of Widget is Surface{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [Widget, TheoColor, TheoTheme, TheoBuffer, TheoRenderer, KeyEvent, MouseEvent, FocusTarget]],
		['base', 'sys', as Conditional()]
	];

	Widget is child;
	TheoColor is background: TheoColor:none();
	TheoColor is foreground: TheoColor:none();
	Int is width: 0;
	Int is height: 0;
	Int is padX: 0;
	Int is padY: 0;

	replace Function is init(
		Widget is child: Widget(),
		TheoColor is background: TheoColor:none(),
		TheoColor is foreground: TheoColor:none(),
		Int is width: 0,
		Int is height: 0,
		Int is padX: 0,
		Int is padY: 0
	){
		:child: child;
		:background: background;
		:foreground: foreground;
		:width: width;
		:height: height;
		:padX: padX;
		:padY: padY;
	}

	replace Function is applyTheme(TheoTheme is theme){
		:activeTheme: theme;
		child:applyTheme(theme: theme);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		child:bindDirty(cb: cb);
	}

	replace Function of Int is measureWidth(Int is maxW){
		local Int is w: width;
		if({ w <= 0 }, {
			w: child:measureWidth(maxW: maxW - padX * 2) + padX * 2;
		});
		if({ w > maxW }, { return maxW; });
		if({ w < 0 }, { return 0; });
		return w;
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){
		local Int is h: height;
		if({ h <= 0 }, {
			local Int is cw: measureWidth(maxW: maxW) - padX * 2;
			if({ cw < 0 }, { cw: 0; });
			h: child:measureHeight(maxW: cw, maxH: maxH - padY * 2) + padY * 2;
		});
		if({ h > maxH }, { return maxH; });
		if({ h < 0 }, { return 0; });
		return h;
	}

	replace Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
		local Int is innerW: w - padX * 2;
		local Int is innerH: h - padY * 2;
		if({ innerW < 0 }, { innerW: 0; });
		if({ innerH < 0 }, { innerH: 0; });
		child:layout(x: x + padX, y: y + padY, w: innerW, h: innerH);
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		local TheoColor is effBg: if({ background:isSet() }, { background }, { activeTheme:surfaceBg });
		local TheoColor is effFg: if({ foreground:isSet() }, { foreground }, { activeTheme:foreground });
		buf:fillRect(x: boxX, y: boxY, w: boxW, h: boxH, fg: effFg, bg: effBg);
		child:paint(buf: buf, renderer: renderer);
	}

	replace Function of Boolean is handleKey(KeyEvent is event){ child:handleKey(event: event) }

	replace Function of Boolean is handleMouse(MouseEvent is event){ child:handleMouse(event: event) }

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		child:collectFocus(targets: targets, owners: owners);
	}

	replace Function is dispose(){
		disposeBindings();
		child:dispose();
	}
}
