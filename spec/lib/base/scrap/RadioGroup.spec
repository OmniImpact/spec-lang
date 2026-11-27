#! Package base:scrap
#! Mutually-exclusive group of [RadioButton] controls arranged vertically or horizontally.

Class of SewNode is RadioGroup{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'sew', Row],
		['base', 'sew', Column],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', RadioButton]
	];

	Array of String is options: Array();
	Int is selectedIndex: 0;
	Boolean is horizontal: false;
	Float is gapPt: 0.0;
	Function is onSelect: local Function(Int is _idx){};
	Array of RadioButton is items: Array();
	Row is row: Row();
	Column is col: Column();

	replace Function is init(
		Array of String is options: Array(),
		Int is selectedIndex: 0,
		Boolean is horizontal: false,
		Float is gapPt: 0.0,
		Function is onSelect: local Function(Int is _idx){}
	){
		:options: options;
		:selectedIndex: selectedIndex;
		:horizontal: horizontal;
		:gapPt: gapPt;
		:onSelect: onSelect;
		:items: Array();
		local Array of SewNode is nodes: Array();
		local Int is i: 0;
		while({ i < options:length() }, {
			local Int is idx: i;
			local RadioButton is rb: RadioButton(
				label: options:get(index: idx),
				selected: idx == selectedIndex,
				onSelect: local Function(){
					:setSelectedIndex(index: idx);
					local Function is cb: :onSelect;
					cb(idx);
				}
			);
			items:add(item: rb);
			nodes:add(item: rb);
			i: i + 1;
		});
		if({ horizontal }, {
			:row: Row(children: nodes, gapPt: gapPt);
		}, {
			:col: Column(children: nodes, gapPt: gapPt);
		});
	}

	local Function of SewNode is rootNode(){
		return if({ horizontal }, { row as SewNode }, { col as SewNode });
	}

	Function is setSelectedIndex(Int is index){
		:selectedIndex: index;
		local Int is i: 0;
		while({ i < items:length() }, {
			items:get(index: i):setSelected(next: i == index);
			i: i + 1;
		});
		invalidate();
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		local Float is g: if({ gapPt > 0.0 }, { gapPt }, { if({ horizontal }, { theme:paddingLargePt }, { theme:paddingSmallPt }) });
		if({ horizontal }, { row:gapPt: g; }, { col:gapPt: g; });
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

	replace Function of String is tooltipAt(Int is x, Int is y){
		return :rootNode():tooltipAt(x: x, y: y);
	}

	replace Function is collectFocusables(Array of SewNode is out){
		:rootNode():collectFocusables(out: out);
	}
}
