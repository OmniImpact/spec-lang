#! Package base:theo
#! Modal overlay hosted by a [Frame] or container; receives an anchor [Widget] when shown and blocks input beneath while open.

Class of Widget is Overlay{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [Widget, TheoTheme, TheoBuffer, TheoRenderer, KeyEvent, MouseEvent, FocusTarget]],
		['base', 'sys', as Conditional()]
	];

	Widget is content;
	Widget is anchor: Widget();
	Boolean is open: false;
	Boolean is blocking: true;
	Boolean is closeOnEsc: true;
	Boolean is closeOnBackdrop: false;
	Function is onClose: {};

	replace Function is init(
		Widget is content: Widget(),
		Boolean is blocking: true,
		Boolean is closeOnEsc: true,
		Boolean is closeOnBackdrop: false,
		Function is onClose: {}
	){
		:content: content;
		:anchor: Widget();
		:open: false;
		:blocking: blocking;
		:closeOnEsc: closeOnEsc;
		:closeOnBackdrop: closeOnBackdrop;
		:onClose: onClose;
	}

	## Opens this overlay, recording [anchor] (the invoking element) and focusing the overlay's first focus target if blocking.
	Function is show(Widget is anchor: Widget()){
		:anchor: anchor;
		:open: true;
		if({ blocking }, {
			local Array of FocusTarget is fts: Array();
			local Array of Widget is fws: Array();
			content:collectFocus(targets: fts, owners: fws);
			if({ fts:length() > 0 }, {
				fts:get(index: 0):requestFocus();
			});
		});
		invalidate();
	}

	## Closes this overlay and restores focus to [anchor] if blocking and [anchor] has a [FocusTarget].
	Function is close(){
		if({ !open }, { return; });
		:open: false;
		if({ blocking }, {
			local Array of FocusTarget is fts: Array();
			local Array of Widget is fws: Array();
			anchor:collectFocus(targets: fts, owners: fws);
			if({ fts:length() > 0 }, {
				fts:get(index: 0):requestFocus();
			});
		});
		onClose();
		invalidate();
	}

	replace Function is applyTheme(TheoTheme is theme){
		:activeTheme: theme;
		content:applyTheme(theme: theme);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		content:bindDirty(cb: cb);
	}

	replace Function is layout(Int is x, Int is y, Int is w, Int is h){
		:boxX: x;
		:boxY: y;
		:boxW: w;
		:boxH: h;
		content:layout(x: x, y: y, w: w, h: h);
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ !open }, { return; });
		content:paint(buf: buf, renderer: renderer);
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		if({ !open }, { return false; });
		if({ !blocking }, { return false; });
		if({ content:handleKey(event: event) }, {
			return true;
		});
		if({ closeOnEsc && event:isEsc() }, {
			close();
		});
		return true;
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		if({ !open }, { return false; });
		if({ !blocking }, { return false; });
		content:handleMouse(event: event);
		if({ closeOnBackdrop && event:isLeftPress() && !content:containsPoint(x: event:x, y: event:y) }, {
			close();
		});
		return true;
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		if({ !open || !blocking }, { return; });
		content:collectFocus(targets: targets, owners: owners);
	}

	replace Function is dispose(){
		disposeBindings();
		content:dispose();
	}
}
