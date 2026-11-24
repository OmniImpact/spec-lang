#! Package base:theo
#! Navigable UI unit and widget host in Theo.

Class of Widget is Frame{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [Widget, Overlay, TheoBuffer, TheoRenderer, TheoTheme, KeyEvent, MouseEvent, FocusTarget]],
		['base', 'sys', as Conditional()]
	];

	Boolean is built: false;
	Widget is rootWidget: Widget();
	Array of Overlay is overlays: Array();

	## Registers [overlay] with this frame (forwarding theme and dirty hooks).
	Function is addOverlay(Overlay is overlay){
		local Int is i: 0;
		while({ i < overlays:length() }, {
			if({ overlays:get(index: i) == overlay }, { return; });
			i: i + 1;
		});
		overlay:applyTheme(theme: activeTheme);
		if({ dirtyListeners:length() > 0 }, {
			overlay:bindDirty(cb: dirtyListeners:get(index: 0));
		});
		overlays:add(item: overlay);
	}

	## Opens [overlay] on top of this frame, passing [anchor] (the invoking element).
	Function is showOverlay(Overlay is overlay, Widget is anchor: Widget()){
		addOverlay(overlay: overlay);
		overlay:show(anchor: anchor);
	}

	## Closes [overlay] on this frame.
	Function is closeOverlay(Overlay is overlay){
		overlay:close();
	}

	## Unregisters [overlay] from this frame.
	Function is removeOverlay(Overlay is overlay){
		local Int is i: 0;
		while({ i < overlays:length() }, {
			if({ overlays:get(index: i) == overlay }, {
				overlays:removeAt(index: i);
				return;
			});
			i: i + 1;
		});
	}

	## True when at least one overlay on this frame is currently open.
	Function of Boolean is hasOpenOverlay(){
		local Int is i: 0;
		while({ i < overlays:length() }, {
			if({ overlays:get(index: i):open }, { return true; });
			i: i + 1;
		});
		return false;
	}

	## True when at least one blocking overlay on this frame is currently open.
	Function of Boolean is hasBlockingOverlay(){
		local Int is i: 0;
		while({ i < overlays:length() }, {
			local Overlay is ov: overlays:get(index: i);
			if({ ov:open && ov:blocking }, { return true; });
			i: i + 1;
		});
		return false;
	}

	## Override to declare this frame's widget tree.
	Function of Widget is ui(){ Widget() }

	## Override to handle keys at the frame level before child dispatch.
	Function of Boolean is onKey(KeyEvent is event){ false }

	Function is onEnter(){ return; }
	Function is onPause(){ return; }
	Function is onResume(){ return; }

	## Override to run periodic updates on the UI loop; return true to redraw.
	Function of Boolean is onTick(){ false }

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
		local Int is i: 0;
		while({ i < overlays:length() }, {
			overlays:get(index: i):applyTheme(theme: theme);
			i: i + 1;
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
		local Int is i: 0;
		while({ i < overlays:length() }, {
			overlays:get(index: i):bindDirty(cb: cb);
			i: i + 1;
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
		local Int is i: 0;
		while({ i < overlays:length() }, {
			overlays:get(index: i):layout(x: x, y: y, w: w, h: h);
			i: i + 1;
		});
		rootWidget:layout(x: x, y: y, w: w, h: h);
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		ensureBuilt();
		rootWidget:paint(buf: buf, renderer: renderer);
		local Int is i: 0;
		while({ i < overlays:length() }, {
			local Overlay is ov: overlays:get(index: i);
			if({ ov:open }, {
				ov:paint(buf: buf, renderer: renderer);
			});
			i: i + 1;
		});
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		local Int is i: overlays:length() - 1;
		while({ i >= 0 }, {
			local Overlay is ov: overlays:get(index: i);
			if({ ov:open && ov:blocking }, {
				return ov:handleKey(event: event);
			});
			i: i - 1;
		});
		if({ onKey(event: event) }, {
			return true;
		});
		ensureBuilt();
		return rootWidget:handleKey(event: event);
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		local Int is i: overlays:length() - 1;
		while({ i >= 0 }, {
			local Overlay is ov: overlays:get(index: i);
			if({ ov:open && ov:blocking }, {
				return ov:handleMouse(event: event);
			});
			i: i - 1;
		});
		ensureBuilt();
		return rootWidget:handleMouse(event: event);
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		local Int is i: overlays:length() - 1;
		while({ i >= 0 }, {
			local Overlay is ov: overlays:get(index: i);
			if({ ov:open && ov:blocking }, {
				ov:collectFocus(targets: targets, owners: owners);
				return;
			});
			i: i - 1;
		});
		ensureBuilt();
		rootWidget:collectFocus(targets: targets, owners: owners);
	}

	replace Function is dispose(){
		disposeBindings();
		local Int is i: 0;
		while({ i < overlays:length() }, {
			overlays:get(index: i):dispose();
			i: i + 1;
		});
		if({ built }, {
			rootWidget:dispose();
			:built: false;
		});
	}
}
