#! Package base:sew
#! Inset container adding padding around a single child `SewNode`.

Class of SewNode is Padding{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'sew', SuitUnit],
		['base', 'sew', Pt]
	];

	Int is top: 0;
	Int is right: 0;
	Int is bottom: 0;
	Int is left: 0;
	Float is padPt: 0.0;
	SuitUnit is pad: Pt(value: 0.0);
	Boolean is hasUnitPad: false;
	Boolean is useThemePad: false;
	Float is padScale: 1.0;
	SewNode is child: SewNode();
	Boolean is shrinkToChild: true;

	replace Function is init(
		SewNode is child,
		Int is top: 0,
		Int is right: 0,
		Int is bottom: 0,
		Int is left: 0,
		Float is padPt: 0.0,
		SuitUnit is pad: Pt(value: 0.0),
		Boolean is hasUnitPad: false,
		Boolean is useThemePad: false,
		Float is padScale: 1.0,
		Boolean is shrinkToChild: true
	){
		:child: child;
		:top: top;
		:right: right;
		:bottom: bottom;
		:left: left;
		:padPt: padPt;
		:pad: pad;
		:hasUnitPad: hasUnitPad;
		:useThemePad: useThemePad;
		:padScale: padScale;
		:shrinkToChild: shrinkToChild;
	}

	local Function of Int is effTop(){
		if({ useThemePad }, { return activeScale:px(pt: activeTheme:padPt(pct: padScale)); });
		if({ hasUnitPad }, { return :unitPx(unit: pad); });
		if({ padPt > 0.0 }, { return activeScale:px(pt: padPt); });
		return top;
	}

	local Function of Int is effRight(){
		if({ useThemePad }, { return activeScale:px(pt: activeTheme:padPt(pct: padScale)); });
		if({ hasUnitPad }, { return :unitPx(unit: pad); });
		if({ padPt > 0.0 }, { return activeScale:px(pt: padPt); });
		return right;
	}

	local Function of Int is effBottom(){
		if({ useThemePad }, { return activeScale:px(pt: activeTheme:padPt(pct: padScale)); });
		if({ hasUnitPad }, { return :unitPx(unit: pad); });
		if({ padPt > 0.0 }, { return activeScale:px(pt: padPt); });
		return bottom;
	}

	local Function of Int is effLeft(){
		if({ useThemePad }, { return activeScale:px(pt: activeTheme:padPt(pct: padScale)); });
		if({ hasUnitPad }, { return :unitPx(unit: pad); });
		if({ padPt > 0.0 }, { return activeScale:px(pt: padPt); });
		return left;
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
		local Int is pl: :effLeft();
		local Int is pr: :effRight();
		local Int is pt: :effTop();
		local Int is pb: :effBottom();
		local Int is padW: pl + pr;
		local Int is padH: pt + pb;
		local Size is cs: child:measure(c: c:deflate(dw: padW, dh: padH));
		desiredSize: Size(
			width: c:clampW(w: cs:width + padW),
			height: c:clampH(h: cs:height + padH)
		);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is pl: :effLeft();
		local Int is pr: :effRight();
		local Int is pt: :effTop();
		local Int is pb: :effBottom();
		local Int is availW: if({ bounds:width > pl + pr }, { bounds:width - pl - pr }, { 0 });
		local Int is availH: if({ bounds:height > pt + pb }, { bounds:height - pt - pb }, { 0 });
		local Int is cw: if({ shrinkToChild && child:desiredSize:width < availW }, { child:desiredSize:width }, { availW });
		local Int is ch: if({ shrinkToChild && child:desiredSize:height < availH }, { child:desiredSize:height }, { availH });
		child:arrange(bounds: Rect(x: bounds:x + pl, y: bounds:y + pt, width: cw, height: ch));
	}

	replace Function is paint(DrawContext is ctx){
		child:paint(ctx: ctx);
	}

	replace Function is paintOverlay(DrawContext is ctx){
		child:paintOverlay(ctx: ctx);
	}

	replace Function of Boolean is closePopupsOutside(Int is x, Int is y){
		return child:closePopupsOutside(x: x, y: y);
	}

	replace Function of Boolean is onOverlayPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return child:onOverlayPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onOverlayPointerMove(Int is x, Int is y){
		return child:onOverlayPointerMove(x: x, y: y);
	}

	replace Function of Boolean is onOverlayPointerDrag(Int is x, Int is y, Int is mods: 0){
		return child:onOverlayPointerDrag(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onOverlayPointerUp(Int is x, Int is y){
		return child:onOverlayPointerUp(x: x, y: y);
	}

	replace Function of Boolean is blocksPointerAt(Int is x, Int is y){
		if({ pointerTransparent }, { return false; });
		return :containsPoint(x: x, y: y) || child:blocksPointerAt(x: x, y: y);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		return child:onPointerMove(x: x, y: y);
	}

	replace Function is clearHover(){
		child:clearHover();
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return child:onPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		return child:onRightClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		return child:onPointerDrag(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		return child:onPointerUp(x: x, y: y);
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		return child:onScroll(deltaY: deltaY);
	}

	replace Function of Boolean is onScrollX(Int is deltaX){
		return child:onScrollX(deltaX: deltaX);
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		return child:onKey(key: key, mods: mods);
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		return child:onText(ch: ch, mods: mods);
	}

	replace Function of Boolean is tick(Int is nowMs){
		return child:tick(nowMs: nowMs);
	}

	replace Function is collectFocusables(Array of SewNode is out){
		if({ child:canFocus() }, { out:add(item: child); }, { child:collectFocusables(out: out); });
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		if({ !:containsPoint(x: x, y: y) }, { return ''; });
		local String is tip: child:tooltipAt(x: x, y: y);
		if({ tip != '' }, { return tip; });
		return tooltip;
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ !:containsPoint(x: x, y: y) }, { return CursorShape:DEFAULT; });
		return child:cursorAt(x: x, y: y);
	}
}