#! Package base:scrap
#! Draggable wrapper (`SewNode`) that initiates a [DragDropState] mouse-follow drag with optional 6-dot grip indicator.

Class of SewNode is Draggable{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'sew', CursorShape],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', DragDropState]
	];

	SewNode is child: SewNode();
	String is payload: '';
	String is dragLabel: '';
	Boolean is showGrip: true;
	Function is onDragStart: local Function(String is _payload){};
	Function is onDragEnd: local Function(String is _payload){};

	Boolean is dragging: false;
	Int is startX: 0;
	Int is startY: 0;
	Boolean is startedThreshold: false;

	replace Function is init(
		SewNode is child: SewNode(),
		String is payload: '',
		String is dragLabel: '',
		Boolean is showGrip: true,
		Function is onDragStart: local Function(String is _payload){},
		Function is onDragEnd: local Function(String is _payload){},
		String is tooltip: ''
	){
		:child: child;
		:payload: payload;
		:dragLabel: dragLabel;
		:showGrip: showGrip;
		:onDragStart: onDragStart;
		:onDragEnd: onDragEnd;
		:tooltip: tooltip;
	}

	local Function of Int is gripWidthPx(){
		if({ !showGrip }, { return 0; });
		local Int is linePx: activeTheme:linePx(scaleFactor: activeScale:factor);
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is dotSz: linePx + 1;
		local Int is dotGap: dotSz + activeScale:px(pt: 2.0);
		return dotGap * 2 + pad;
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		child:applyTheme(theme: theme);
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		child:setScale(scale: scale);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		child:bindDirty(cb: cb);
	}

	replace Function of Size is measure(Constraints is c){
		local Int is gw: :gripWidthPx();
		local Int is availW: if({ c:maxW > gw }, { c:maxW - gw }, { 0 });
		local Size is cs: child:measure(c: Constraints(minW: 0, maxW: availW, minH: c:minH, maxH: c:maxH));
		desiredSize: Size(width: c:clampW(w: cs:width + gw), height: c:clampH(h: cs:height));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is gw: :gripWidthPx();
		local Int is cw: if({ bounds:width > gw }, { bounds:width - gw }, { 0 });
		child:arrange(bounds: Rect(x: bounds:x + gw, y: bounds:y, width: cw, height: bounds:height));
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		if({ showGrip }, {
			local Int is linePx: activeTheme:linePx(scaleFactor: activeScale:factor);
			local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
			local Int is dotSz: linePx + 1;
			local Int is dotGap: dotSz + activeScale:px(pt: 2.0);
			local Int is gx: b:x + pad / 2;
			local Int is gy: b:y + (b:height - dotGap * 2 - dotSz) / 2;
			local Int is gCol: if({ dragging }, { activeTheme:textAccent }, { activeTheme:textMuted });
			local Int is r: 0;
			while({ r < 3 }, {
				local Int is cIdx: 0;
				while({ cIdx < 2 }, {
					ctx:fillRect(x: gx + cIdx * dotGap, y: gy + r * dotGap, w: dotSz, h: dotSz, color: gCol);
					cIdx: cIdx + 1;
				});
				r: r + 1;
			});
		});
		child:paint(ctx: ctx);
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ :containsPoint(x: x, y: y) }, { return CursorShape:POINTER; });
		return child:cursorAt(x: x, y: y);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		return child:onPointerMove(x: x, y: y);
	}

	replace Function is clearHover(){
		child:clearHover();
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ !dragging }, {
			if({ !:containsPoint(x: x, y: y) }, { return false; });
			:dragging: true;
			:startX: x;
			:startY: y;
			:startedThreshold: false;
			return true;
		});
		if({ !startedThreshold }, {
			local Int is dx: if({ x >= startX }, { x - startX }, { startX - x });
			local Int is dy: if({ y >= startY }, { y - startY }, { startY - y });
			local Int is thresh: activeScale:px(pt: 4.0);
			if({ thresh < 3 }, { thresh: 3; });
			if({ dx + dy >= thresh }, {
				:startedThreshold: true;
				local String is lbl: if({ dragLabel != '' }, { dragLabel }, { payload });
				DragDropState:shared:beginDrag(payload: payload, label: lbl, x: x, y: y);
				local Function is scb: onDragStart;
				scb(payload);
			});
		}, {
			DragDropState:shared:updatePointer(x: x, y: y);
		});
		invalidate();
		return true;
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		if({ dragging }, {
			local Boolean is wasActive: startedThreshold;
			:dragging: false;
			:startedThreshold: false;
			if({ wasActive }, {
				local Function is ecb: onDragEnd;
				ecb(payload);
			});
			invalidate();
			return true;
		});
		return false;
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
