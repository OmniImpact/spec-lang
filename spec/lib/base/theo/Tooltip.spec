#! Package base:theo
#! Hover tooltip wrapper that displays a bordered box on a specified side of [child] via a non-blocking [Overlay].

Class of Widget is Tooltip{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [Widget, Frame, Overlay, Surface, Panel, TextLine, FocusTarget, KeyEvent, MouseEvent, TheoColor, TheoBuffer, TheoRenderer, TheoTheme]],
		['base', 'sys', as Conditional()]
	];

	Widget is child;
	String is text: '';
	String is side: 'top';
	[Frame] is hostFrames: [];
	[Overlay] is tipOverlays: [];

	replace Function is init(
		Frame is host,
		Widget is child: Widget(),
		String is text: '',
		String is side: 'top'
	){
		:child: child;
		:text: text;
		:side: side;
		:hostFrames: [host];

		local Widget is box: Surface(
			child: Panel(
				border: true,
				padX: 1,
				padY: 0,
				child: TextLine(value: text)
			)
		);
		local Overlay is ov: Overlay(
			blocking: false,
			closeOnEsc: false,
			closeOnBackdrop: false,
			content: box
		);
		:tipOverlays: [ov];
		host:addOverlay(overlay: ov);
	}

	Function is show(){
		if({ hostFrames:length() == 0 || tipOverlays:length() == 0 }, { return; });
		local Overlay is ov: tipOverlays:get(index: 0);
		if({ !ov:open }, {
			hostFrames:get(index: 0):showOverlay(overlay: ov, anchor: child);
		});
	}

	Function is hide(){
		if({ hostFrames:length() == 0 || tipOverlays:length() == 0 }, { return; });
		local Overlay is ov: tipOverlays:get(index: 0);
		if({ ov:open }, {
			hostFrames:get(index: 0):closeOverlay(overlay: ov);
		});
	}

	Function of Boolean is isShowing(){
		if({ tipOverlays:length() == 0 }, { return false; });
		return tipOverlays:get(index: 0):open;
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
		child:layout(x: x, y: y, w: w, h: h);

		if({ tipOverlays:length() > 0 }, {
			local Overlay is ov: tipOverlays:get(index: 0);
			local Int is tipW: text:runeCount() + 4;
			local Int is tipH: 3;
			local Int is hostW: if({ hostFrames:length() > 0 && hostFrames:get(index: 0):boxW > 0 }, { hostFrames:get(index: 0):boxW }, { 80 });
			local Int is hostH: if({ hostFrames:length() > 0 && hostFrames:get(index: 0):boxH > 0 }, { hostFrames:get(index: 0):boxH }, { 24 });
			local Int is tx: x + (w - tipW) / 2;
			local Int is ty: y - tipH;
			if({ side == 'bottom' }, {
				ty: y + h;
			});
			if({ side == 'left' }, {
				tx: x - tipW - 1;
				ty: y + (h - tipH) / 2;
			});
			if({ side == 'right' }, {
				tx: x + w + 1;
				ty: y + (h - tipH) / 2;
			});
			if({ tx + tipW > hostW }, { tx: hostW - tipW; });
			if({ tx < 0 }, { tx: 0; });
			if({ ty + tipH > hostH }, { ty: hostH - tipH; });
			if({ ty < 0 }, { ty: 0; });
			ov:content:layout(x: tx, y: ty, w: tipW, h: tipH);
		});
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		child:paint(buf: buf, renderer: renderer);
	}

	replace Function of Boolean is handleKey(KeyEvent is event){
		return child:handleKey(event: event);
	}

	replace Function of Boolean is handleMouse(MouseEvent is event){
		if({ event:isMove() }, {
			local Boolean is inside: containsPoint(x: event:x, y: event:y);
			local Boolean is handled: child:handleMouse(event: event);
			if({ inside }, {
				if({ !isShowing() }, {
					show();
					return true;
				});
			}, {
				if({ isShowing() }, {
					hide();
					return true;
				});
			});
			return handled;
		});
		return child:handleMouse(event: event);
	}

	replace Function is collectFocus(Array of FocusTarget is targets, Array of Widget is owners){
		child:collectFocus(targets: targets, owners: owners);
	}

	replace Function is dispose(){
		disposeBindings();
		if({ hostFrames:length() > 0 && tipOverlays:length() > 0 }, {
			local Overlay is ov: tipOverlays:get(index: 0);
			ov:close();
			hostFrames:get(index: 0):removeOverlay(overlay: ov);
			ov:dispose();
		});
		child:dispose();
	}
}
