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
		['base', 'scrap', Label],
		['base', 'scrap', Clickable]
	];

	String is title: '';
	Float is gapPt: 0.0;
	Boolean is segmented: false;
	Int is selectedIndex: -1;
	Float is itemMinWidthPt: 0.0;
	Float is itemHeightPt: 0.0;
	Function is onSelect: local Function(Int is _idx){};
	Array of Clickable is segmentItems: Array();
	Column is col: Column();

	replace Function is init(
		String is title: '',
		Array of SewNode is children: Array(),
		Array of Boolean is flexFlags: Array(),
		Float is gapPt: 0.0,
		Boolean is segmented: false,
		Array of String is options: Array(),
		Int is selectedIndex: -1,
		Float is itemMinWidthPt: 0.0,
		Float is itemHeightPt: 0.0,
		Function is onSelect: local Function(Int is _idx){}
	){
		:title: title;
		:gapPt: gapPt;
		:segmented: segmented;
		:selectedIndex: selectedIndex;
		:itemMinWidthPt: itemMinWidthPt;
		:itemHeightPt: itemHeightPt;
		:onSelect: onSelect;
		:segmentItems: Array();
		local Array of SewNode is allChildren: Array();
		local Array of Boolean is allFlex: Array();
		if({ title != '' }, {
			allChildren:add(item: Label(text: title, muted: true));
			allFlex:add(item: false);
		});
		if({ options:length() > 0 }, {
			local Int is oi: 0;
			while({ oi < options:length() }, {
				local Int is idx: oi;
				local Clickable is item: Clickable(
					label: options:get(index: idx),
					selected: (idx == selectedIndex),
					minWidthPt: itemMinWidthPt,
					heightPt: itemHeightPt,
					onClick: local Function(){
						:setSelectedIndex(index: idx);
						local Function is cb: :onSelect;
						cb(idx);
					}
				);
				segmentItems:add(item: item);
				allChildren:add(item: item);
				local Boolean is fx: if({ idx < flexFlags:length() }, { flexFlags:get(index: idx) }, { false });
				allFlex:add(item: fx);
				oi: oi + 1;
			});
		}, {
			local Int is i: 0;
			while({ i < children:length() }, {
				local SewNode is ch: children:get(index: i);
				allChildren:add(item: ch);
				local Boolean is fx: if({ i < flexFlags:length() }, { flexFlags:get(index: i) }, { false });
				allFlex:add(item: fx);
				i: i + 1;
			});
		});
		:col: Column(children: allChildren, flexFlags: allFlex, gapPt: if({ segmented }, { 0.0 }, { gapPt }));
	}

	Function is setSelectedIndex(Int is index){
		:selectedIndex: index;
		local Int is i: 0;
		while({ i < segmentItems:length() }, {
			segmentItems:get(index: i):setSelected(next: i == index);
			i: i + 1;
		});
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		if({ segmented }, {
			col:gapPt: 0.0;
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
		local Size is s: col:measure(c: c);
		if({ segmented }, {
			local Int is linePx: activeTheme:borderPx(scaleFactor: activeScale:factor);
			local Int is startIdx: if({ title != '' }, { 1 }, { 0 });
			local Int is segCount: col:children:length() - startIdx;
			if({ segCount > 1 && linePx > 0 }, {
				local Int is overlap: (segCount - 1) * linePx;
				local Int is nh: if({ s:height > overlap }, { s:height - overlap }, { s:height });
				s: Size(width: s:width, height: nh);
			});
		});
		desiredSize: s;
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		col:arrange(bounds: bounds);
		if({ segmented }, {
			local Int is linePx: activeTheme:borderPx(scaleFactor: activeScale:factor);
			local Int is startIdx: if({ title != '' }, { 1 }, { 0 });
			local Int is count: col:children:length();
			if({ count - startIdx > 1 && linePx > 0 }, {
				local Int is i: startIdx + 1;
				while({ i < count }, {
					local SewNode is ch: col:children:get(index: i);
					local Rect is cb: ch:bounds();
					local Int is shift: (i - startIdx) * linePx;
					ch:arrange(bounds: Rect(x: cb:x, y: cb:y - shift, width: cb:width, height: cb:height));
					i: i + 1;
				});
			});
		});
	}

	replace Function is paint(DrawContext is ctx){
		col:paint(ctx: ctx);
		if({ segmented }, {
			local Int is linePx: activeTheme:borderPx(scaleFactor: activeScale:factor);
			if({ linePx > 0 }, {
				local Int is startIdx: if({ title != '' }, { 1 }, { 0 });
				local Int is count: col:children:length();
				local Int is i: startIdx;
				while({ i < count }, {
					local SewNode is ch: col:children:get(index: i);
					if({ !ch:isSelected() && !ch:isFocused() }, {
						local Rect is cb: ch:bounds();
						if({ cb:width > 0 && cb:height > 0 }, {
							ctx:strokeRect(x: cb:x, y: cb:y, w: cb:width, h: cb:height, color: activeTheme:buttonBorder, thickness: linePx);
						});
					});
					i: i + 1;
				});
				i: startIdx;
				while({ i < count }, {
					local SewNode is ch: col:children:get(index: i);
					if({ ch:isSelected() || ch:isFocused() }, {
						local Rect is cb: ch:bounds();
						if({ cb:width > 0 && cb:height > 0 }, {
							ctx:strokeRect(x: cb:x, y: cb:y, w: cb:width, h: cb:height, color: activeTheme:textAccent, thickness: linePx);
						});
					});
					i: i + 1;
				});
			});
		});
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

	replace Function is collectFocusables(Array of SewNode is out){
		col:collectFocusables(out: out);
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		return col:tooltipAt(x: x, y: y);
	}
}