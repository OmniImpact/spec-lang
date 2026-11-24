#! Package base:theo
#! Container widget that centers a single [child] horizontally and vertically.

Class of Widget is Center{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [Widget, TheoTheme, TheoBuffer, TheoRenderer, KeyEvent, MouseEvent, FocusTarget]],
		['base', 'sys', as Conditional()]
	];

	Widget is child;

	replace Function is init(Widget is child: Widget()){
		:child: child;
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
		return child:measureWidth(maxW: maxW);
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){
		return child:measureHeight(maxW: maxW, maxH: maxH);
	}

	replace Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
		local Int is cw: child:measureWidth(maxW: w);
		if({ cw > w }, { cw: w; });
		if({ cw < 0 }, { cw: 0; });
		local Int is ch: child:measureHeight(maxW: cw, maxH: h);
		if({ ch > h }, { ch: h; });
		if({ ch < 0 }, { ch: 0; });
		local Int is cx: x + (w - cw) / 2;
		local Int is cy: y + (h - ch) / 2;
		child:layout(x: cx, y: cy, w: cw, h: ch);
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		child:paint(buf: buf, renderer: renderer);
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		return child:handleKey(event: event);
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		return child:handleMouse(event: event);
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		child:collectFocus(targets: targets, owners: owners);
	}

	replace Function is dispose(){
		disposeBindings();
		child:dispose();
	}
}
