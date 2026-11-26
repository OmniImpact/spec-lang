#! Package base:scrap
#! Vertical sectional container with optional title and theme-derived spacing.

Class of SewNode is SectionV{
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
		['base', 'sew', Column],
		['base', 'scrap', Label]
	];

	String is title: '';
	Float is gapPt: 0.0;
	Boolean is segmented: false;
	Column is col: Column();

	replace Function is init(
		String is title: '',
		Array of SewNode is children: Array(),
		Array of Boolean is flexFlags: Array(),
		Float is gapPt: 0.0,
		Boolean is segmented: false
	){
		:title: title;
		:gapPt: gapPt;
		:segmented: segmented;
		local Array of SewNode is allChildren: Array();
		local Array of Boolean is allFlex: Array();
		if({ title != '' }, {
			allChildren:add(item: Label(text: title, muted: true));
			allFlex:add(item: false);
		});
		local Int is i: 0;
		while({ i < children:length() }, {
			local SewNode is ch: children:get(index: i);
			allChildren:add(item: ch);
			local Boolean is fx: if({ i < flexFlags:length() }, { flexFlags:get(index: i) }, { false });
			allFlex:add(item: fx);
			i: i + 1;
		});
		:col: Column(children: allChildren, flexFlags: allFlex, gapPt: if({ segmented }, { 0.0 }, { gapPt }));
		if({ segmented }, { :joinSegmentedEdges(); });
	}

	Function is joinSegmentedEdges(){
		local Int is startIdx: if({ title != '' }, { 1 }, { 0 });
		local Int is count: col:children:length();
		local Int is i: startIdx;
		while({ i < count }, {
			local SewNode is ch: col:children:get(index: i);
			ch:setBorderEdges(top: true, right: true, bottom: (i + 1 >= count), left: true);
			i: i + 1;
		});
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		if({ segmented }, {
			col:gapPt: 0.0;
			:joinSegmentedEdges();
		}, {
		if({ gapPt <= 0.0 }, {
			col:gapPt: theme:paddingPt;
		}); });
		col:applyTheme(theme: theme);
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		col:setScale(scale: scale);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		col:bindDirty(cb: cb);
	}

	replace Function of Size is measure(Constraints is c){
		desiredSize: col:measure(c: c);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		col:arrange(bounds: bounds);
	}

	replace Function is paint(DrawContext is ctx){
		col:paint(ctx: ctx);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		return col:onPointerMove(x: x, y: y);
	}

	replace Function is clearHover(){
		col:clearHover();
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return col:onPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		return col:onRightClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		return col:onPointerDrag(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		return col:onPointerUp(x: x, y: y);
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		return col:onScroll(deltaY: deltaY);
	}

	replace Function of Boolean is onScrollX(Int is deltaX){
		return col:onScrollX(deltaX: deltaX);
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		return col:onKey(key: key, mods: mods);
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		return col:onText(ch: ch, mods: mods);
	}

	replace Function of Boolean is tick(Int is nowMs){
		return col:tick(nowMs: nowMs);
	}
}