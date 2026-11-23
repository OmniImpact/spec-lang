#! Package base:theo
#! Navigable UI unit and widget host in Theo.

Class of Widget is Frame{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', [Widget, TheoBuffer, TheoRenderer, TheoTheme, KeyEvent, MouseEvent, FocusTarget]],
		['base', 'sys', as Conditional()]
	];

	Boolean is built: false;
	Widget is rootWidget: Widget();

	## Override to declare this frame's widget tree.
	Function of Widget is ui(){
		return Widget();
	}

	## Override to handle keys at the frame level before child dispatch.
	Function of Boolean is onKey(KeyEvent is event){
		return false;
	}

	Function is onEnter(){ return; }
	Function is onPause(){ return; }
	Function is onResume(){ return; }

	Function is onExit(){
		dispose();
	}

	Function is ensureBuilt(){
		if({ !built }, {
			:rootWidget: ui();
			:built: true;
			rootWidget:applyTheme(theme: activeTheme);
			if({ dirtyListeners:length() > 0 }, {
				rootWidget:bindDirty(cb: dirtyListeners:get(index: 0));
			});
		});
	}

	replace Function is applyTheme(TheoTheme is theme){
		:activeTheme: theme;
		if({ built }, {
			rootWidget:applyTheme(theme: theme);
		});
	}

	Function is rebuild(){
		if({ built }, {
			rootWidget:dispose();
		});
		:built: false;
		ensureBuilt();
		invalidate();
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		if({ built }, {
			rootWidget:bindDirty(cb: cb);
		});
	}

	replace Function of Int is measureWidth(Int is maxW){
		ensureBuilt();
		return rootWidget:measureWidth(maxW: maxW);
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){
		ensureBuilt();
		return rootWidget:measureHeight(maxW: maxW, maxH: maxH);
	}

	replace Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
		ensureBuilt();
		rootWidget:layout(x: x, y: y, w: w, h: h);
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		ensureBuilt();
		rootWidget:paint(buf: buf, renderer: renderer);
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ onKey(event: event) }, {
			return true;
		});
		ensureBuilt();
		return rootWidget:handleKey(event: event);
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		ensureBuilt();
		return rootWidget:handleMouse(event: event);
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		ensureBuilt();
		rootWidget:collectFocus(targets: targets, owners: owners);
	}

	replace Function is dispose(){
		if({ built }, {
			rootWidget:dispose();
			:built: false;
		});
	}
}
