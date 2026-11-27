#! Package base:scrap
#! Horizontal sectional container with optional title and theme-derived spacing.

Class of SewNode is SectionH{
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
	Row is row: Row();
	Column is wrapper: Column();
	Boolean is hasTitle: false;

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
		:hasTitle: title != '';
		local Array of SewNode is rowChildren: children;
		if({ options:length() > 0 }, {
			rowChildren: Array();
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
				rowChildren:add(item: item);
				oi: oi + 1;
			});
		});
		:row: Row(children: rowChildren, flexFlags: flexFlags, gapPt: if({ segmented }, { 0.0 }, { gapPt }));
		if({ hasTitle }, {
			:wrapper: Column(
				children: Array([Label(text: title, muted: true), row]),
				flexFlags: Array([false, true]),
				gapPt: gapPt
			);
		});
	}

	Function is setSelectedIndex(Int is index){
		:selectedIndex: index;
		local Int is i: 0;
		while({ i < segmentItems:length() }, {
			segmentItems:get(index: i):setSelected(next: i == index);
			i: i + 1;
		});
	}

	local Function of SewNode is rootNode(){
		if({ hasTitle }, { return wrapper; });
		return row;
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		if({ segmented }, {
			row:gapPt: 0.0;
		}, {
		if({ gapPt <= 0.0 }, {
			row:gapPt: theme:paddingPt;
		}); });
		if({ hasTitle && gapPt <= 0.0 }, {
			wrapper:gapPt: theme:paddingSmallPt;
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
		local Size is s: :rootNode():measure(c: c);
		if({ segmented }, {
			local Int is linePx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
			local Int is count: row:children:length();
			if({ count > 1 && linePx > 0 }, {
				local Int is overlap: (count - 1) * linePx;
				local Int is nw: if({ s:width > overlap }, { s:width - overlap }, { s:width });
				s: Size(width: nw, height: s:height);
			});
		});
		desiredSize: s;
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		:rootNode():arrange(bounds: bounds);
		if({ segmented }, {
			local Int is linePx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
			local Int is count: row:children:length();
			if({ count > 1 && linePx > 0 }, {
				local Int is i: 1;
				while({ i < count }, {
					local SewNode is ch: row:children:get(index: i);
					local Rect is cb: ch:bounds();
					local Int is shift: i * linePx;
					ch:arrange(bounds: Rect(x: cb:x - shift, y: cb:y, width: cb:width, height: cb:height));
					i: i + 1;
				});
			});
		});
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		:rootNode():paint(ctx: ctx);
		if({ segmented }, {
			local Int is btnPx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
			local Int is divPx: activeTheme:dividerPx(scaleFactor: activeScale:factor);
			local Int is radPx: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
			local Int is count: row:children:length();
			if({ count > 0 }, {
				local Rect is firstB: row:children:get(index: 0):bounds();
				local Rect is lastB: row:children:get(index: count - 1):bounds();
				local Int is gx: firstB:x;
				local Int is gy: firstB:y;
				local Int is gw: (lastB:x + lastB:width) - firstB:x;
				local Int is gh: firstB:height;
				if({ gw > 0 && gh > 0 && btnPx > 0 }, {
					ctx:drawStyledBox(
						x: gx, y: gy, w: gw, h: gh,
						bgColor: 0, borderColor: activeTheme:buttonBorderColorArgb(),
						thickness: btnPx, radius: radPx, style: activeTheme:buttonBorderStyle
					);
				});
				if({ divPx > 0 }, {
					local Int is di: 1;
					while({ di < count }, {
						local Rect is cb: row:children:get(index: di):bounds();
						if({ cb:height > btnPx * 2 }, {
							ctx:drawDivider(
								x: cb:x, y: cb:y + btnPx, w: divPx, h: cb:height - btnPx * 2,
								color: activeTheme:dividerColorArgb(), thickness: divPx, style: activeTheme:dividerStyle
							);
						});
						di: di + 1;
					});
				});
				if({ btnPx > 0 }, {
					local Int is si: 0;
					while({ si < count }, {
						local SewNode is ch: row:children:get(index: si);
						if({ ch:isSelected() || ch:isFocused() }, {
							local Rect is cb: ch:bounds();
							if({ cb:width > 0 && cb:height > 0 }, {
								local Int is segRad: if({ count == 1 }, { radPx }, { 0 });
								ctx:drawStyledBox(
									x: cb:x, y: cb:y, w: cb:width, h: cb:height,
									bgColor: 0, borderColor: activeTheme:textAccent,
									thickness: btnPx, radius: segRad, style: activeTheme:buttonBorderStyle
								);
							});
						});
						si: si + 1;
					});
				});
			});
		});
	}

	replace Function is paintOverlay(DrawContext is ctx){
		:rootNode():paintOverlay(ctx: ctx);
	}

	replace Function of Boolean is closePopupsOutside(Int is x, Int is y){
		return :rootNode():closePopupsOutside(x: x, y: y);
	}

	replace Function of Boolean is onOverlayPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return :rootNode():onOverlayPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onOverlayPointerMove(Int is x, Int is y){
		return :rootNode():onOverlayPointerMove(x: x, y: y);
	}

	replace Function of Boolean is onOverlayPointerDrag(Int is x, Int is y, Int is mods: 0){
		return :rootNode():onOverlayPointerDrag(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onOverlayPointerUp(Int is x, Int is y){
		return :rootNode():onOverlayPointerUp(x: x, y: y);
	}

	replace Function of Boolean is blocksPointerAt(Int is x, Int is y){
		if({ pointerTransparent }, { return false; });
		return :containsPoint(x: x, y: y) || :rootNode():blocksPointerAt(x: x, y: y);
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

	replace Function is collectFocusables(Array of SewNode is out){
		:rootNode():collectFocusables(out: out);
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		return :rootNode():tooltipAt(x: x, y: y);
	}
}