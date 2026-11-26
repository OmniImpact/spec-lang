#! Package base:scrap
#! Horizontal sectional container with optional title and theme-derived spacing.

Class of SewNode is HSection{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'sew', Row],
		['base', 'sew', Column],
		['base', 'scrap', Label]
	];

	String is title: '';
	Float is gapPt: 0.0;
	Row is row: Row();
	Column is wrapper: Column();
	Boolean is hasTitle: false;

	replace Function is init(
		String is title: '',
		Array of SewNode is children: Array(),
		Array of Boolean is flexFlags: Array(),
		Float is gapPt: 0.0
	){
		:title: title;
		:gapPt: gapPt;
		:hasTitle: title != '';
		:row: Row(children: children, flexFlags: flexFlags, gapPt: gapPt);
		if({ hasTitle }, {
			:wrapper: Column(
				children: Array([Label(text: title, muted: true), row]),
				flexFlags: Array([false, true]),
				gapPt: gapPt
			);
		});
	}

	local Function of SewNode is rootNode(){
		if({ hasTitle }, { return wrapper; });
		return row;
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		if({ gapPt <= 0.0 }, {
			row:gapPt: theme:paddingPt;
			if({ hasTitle }, {
				wrapper:gapPt: theme:paddingSmallPt;
			});
		});
		:rootNode():applyTheme(theme: theme);
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		:rootNode():setScale(scale: scale);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		:rootNode():bindDirty(cb: cb);
	}

	replace Function of Size is measure(Constraints is c){
		desiredSize: :rootNode():measure(c: c);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		:rootNode():arrange(bounds: bounds);
	}

	replace Function is paint(DrawContext is ctx){
		:rootNode():paint(ctx: ctx);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		return :rootNode():onPointerMove(x: x, y: y);
	}

	replace Function is clearHover(){
		:rootNode():clearHover();
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return :rootNode():onPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		return :rootNode():onRightClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		return :rootNode():onPointerDrag(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		return :rootNode():onPointerUp(x: x, y: y);
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		return :rootNode():onScroll(deltaY: deltaY);
	}

	replace Function of Boolean is onScrollX(Int is deltaX){
		return :rootNode():onScrollX(deltaX: deltaX);
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		return :rootNode():onKey(key: key, mods: mods);
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		return :rootNode():onText(ch: ch, mods: mods);
	}

	replace Function of Boolean is tick(Int is nowMs){
		return :rootNode():tick(nowMs: nowMs);
	}
}