#! Package base:scrap
#! Drop zone wrapper (`SewNode`) that highlights when a [Draggable] hovers during a drag and fires [onDrop] on release.

Class of SingleChildNode is DropTarget{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', SingleChildNode],
		['base', 'sew', Rect],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext],
		['base', 'scrap', DragDropState]
	];

	Function is onDrop: local Function(String is _payload){};
	Boolean is dragHover: false;

	replace Function is init(
		SewNode is child: SewNode(),
		Function is onDrop: local Function(String is _payload){},
		String is tooltip: ''
	){
		:child: child;
		:onDrop: onDrop;
		:dragHover: false;
		:tooltip: tooltip;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		child:paint(ctx: ctx);
		if({ dragHover && DragDropState:shared:active }, {
			local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
			if({ bw < 2 }, { bw: 2; });
			local Int is radPx: activeScale:px(pt: activeTheme:panelCornerRadiusPt);
			ctx:drawStyledBox(
				x: b:x, y: b:y, w: b:width, h: b:height,
				bgColor: 0, borderColor: activeTheme:textAccent,
				thickness: bw, radius: radPx, style: activeTheme:panelBorderStyle
			);
		});
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is over: :containsPoint(x: x, y: y);
		if({ DragDropState:shared:active }, {
			if({ over }, {
				DragDropState:shared:setDropTarget(accepted: true, handler: onDrop);
			});
			if({ over != dragHover }, {
				:dragHover: over;
				invalidate();
				return true;
			});
		}, {
			if({ dragHover }, {
				:dragHover: false;
				invalidate();
			});
		});
		return child:onPointerMove(x: x, y: y);
	}

	replace Function is clearHover(){
		if({ dragHover }, {
			:dragHover: false;
			invalidate();
		});
		child:clearHover();
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		if({ DragDropState:shared:active && :containsPoint(x: x, y: y) }, {
			:dragHover: false;
			DragDropState:shared:setDropTarget(accepted: true, handler: onDrop);
			DragDropState:shared:finishDrag();
			invalidate();
			return true;
		});
		if({ dragHover }, {
			:dragHover: false;
			invalidate();
		});
		return child:onPointerUp(x: x, y: y);
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return child:onPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		local String is ct: child:tooltipAt(x: x, y: y);
		if({ ct != '' }, { return ct; });
		if({ tooltip != '' && :containsPoint(x: x, y: y) }, { return tooltip; });
		return '';
	}
}
