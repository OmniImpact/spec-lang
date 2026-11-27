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
		['base', 'sew', CursorShape],
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
	Boolean is reorderable: false;
	Int is selectedIndex: -1;
	Float is itemMinWidthPt: 0.0;
	Float is itemHeightPt: 0.0;
	Function is onSelect: local Function(Int is _idx){};
	Function is onReorder: local Function(Int is _from, Int is _to){};
	Array of Clickable is segmentItems: Array();
	Row is row: Row();
	Column is wrapper: Column();
	Boolean is hasTitle: false;
	Int is dragIdx: -1;
	Int is dragTargetIdx: -1;
	Int is dragStartX: 0;
	Boolean is dragMoved: false;

	replace Function is init(
		String is title: '',
		Array of SewNode is children: Array(),
		Array of Boolean is flexFlags: Array(),
		Float is gapPt: 0.0,
		Boolean is segmented: false,
		Boolean is reorderable: false,
		Array of String is options: Array(),
		Int is selectedIndex: -1,
		Float is itemMinWidthPt: 0.0,
		Float is itemHeightPt: 0.0,
		Function is onSelect: local Function(Int is _idx){},
		Function is onReorder: local Function(Int is _from, Int is _to){}
	){
		:title: title;
		:gapPt: gapPt;
		:segmented: segmented;
		:reorderable: reorderable;
		:selectedIndex: selectedIndex;
		:itemMinWidthPt: itemMinWidthPt;
		:itemHeightPt: itemHeightPt;
		:onSelect: onSelect;
		:onReorder: onReorder;
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
				if({ segmented }, {
					local Int is nOpt: options:length();
					item:roundLeft: idx == 0;
					item:roundRight: idx == nOpt - 1;
					item:roundTop: idx == 0 || idx == nOpt - 1;
					item:roundBottom: idx == 0 || idx == nOpt - 1;
					item:insetLeft: idx == 0;
					item:insetRight: idx == nOpt - 1;
					item:insetTop: true;
					item:insetBottom: true;
				});
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
		if({ !segmented }, {
			:rootNode():paint(ctx: ctx);
		}, {
			local Int is btnPx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
			local Int is divPx: activeTheme:dividerPx(scaleFactor: activeScale:factor);
			local Int is radPx: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
			local Int is count: row:children:length();
			if({ hasTitle && wrapper:children:length() > 0 }, {
				wrapper:children:get(index: 0):paint(ctx: ctx);
			});
			if({ count > 0 }, {
				local Rect is firstB: row:children:get(index: 0):bounds();
				local Rect is lastB: row:children:get(index: count - 1):bounds();
				local Int is gx: firstB:x;
				local Int is gy: firstB:y;
				local Int is gw: (lastB:x + lastB:width) - firstB:x;
				local Int is gh: firstB:height;
				if({ btnPx > 0 && gw > btnPx * 2 && gh > btnPx * 2 }, {
					ctx:setClip(x: gx + btnPx, y: gy + btnPx, w: gw - btnPx * 2, h: gh - btnPx * 2);
					row:paint(ctx: ctx);
					ctx:clearClip();
				}, {
					row:paint(ctx: ctx);
				});
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
								if({ count == 1 || (si > 0 && si < count - 1) || radPx <= 0 }, {
									local Int is segRad: if({ count == 1 }, { radPx }, { 0 });
									ctx:drawStyledBox(
										x: cb:x, y: cb:y, w: cb:width, h: cb:height,
										bgColor: 0, borderColor: activeTheme:textAccent,
										thickness: btnPx, radius: segRad, style: activeTheme:buttonBorderStyle
									);
								}, {
									ctx:setClip(x: cb:x, y: cb:y, w: cb:width, h: cb:height);
									if({ si == 0 }, {
										ctx:drawStyledBox(
											x: cb:x, y: cb:y, w: cb:width + radPx, h: cb:height,
											bgColor: 0, borderColor: activeTheme:textAccent,
											thickness: btnPx, radius: radPx, style: activeTheme:buttonBorderStyle
										);
										ctx:fillRect(x: cb:x + cb:width - btnPx, y: cb:y, w: btnPx, h: cb:height, color: activeTheme:textAccent);
									}, {
										ctx:drawStyledBox(
											x: cb:x - radPx, y: cb:y, w: cb:width + radPx, h: cb:height,
											bgColor: 0, borderColor: activeTheme:textAccent,
											thickness: btnPx, radius: radPx, style: activeTheme:buttonBorderStyle
										);
										ctx:fillRect(x: cb:x, y: cb:y, w: btnPx, h: cb:height, color: activeTheme:textAccent);
									});
									ctx:clearClip();
								});
							});
						});
						si: si + 1;
					});
				});
			});
		});
		if({ reorderable && dragIdx >= 0 && dragMoved && dragTargetIdx >= 0 && dragTargetIdx < segmentItems:length() }, {
			local Rect is tb: segmentItems:get(index: dragTargetIdx):bounds();
			local Int is lineW: activeScale:px(pt: 2.0);
			if({ lineW < 2 }, { lineW: 2; });
			local Int is ix: if({ dragTargetIdx > dragIdx }, { tb:x + tb:width - lineW }, { tb:x });
			ctx:fillRect(x: ix, y: tb:y, w: lineW, h: tb:height, color: activeTheme:textAccent);
		});
	}

	local Function is reorderSegment(Int is fromIdx, Int is toIdx){
		local Int is n: segmentItems:length();
		if({ fromIdx < 0 || fromIdx >= n || toIdx < 0 || toIdx >= n || fromIdx == toIdx }, { return; });
		local Clickable is moved: segmentItems:get(index: fromIdx);
		local Array of Clickable is nextSegs: Array();
		local Int is i: 0;
		while({ i < n }, {
			if({ i != fromIdx }, { nextSegs:add(item: segmentItems:get(index: i)); });
			i: i + 1;
		});
		local Array of Clickable is finalSegs: Array();
		local Int is j: 0;
		local Boolean is inserted: false;
		while({ j < nextSegs:length() }, {
			if({ j == toIdx }, {
				finalSegs:add(item: moved);
				inserted: true;
			});
			finalSegs:add(item: nextSegs:get(index: j));
			j: j + 1;
		});
		if({ !inserted }, { finalSegs:add(item: moved); });
		:segmentItems: finalSegs;

		if({ selectedIndex == fromIdx }, {
			:selectedIndex: toIdx;
		}, {
			if({ fromIdx < selectedIndex && toIdx >= selectedIndex }, {
				:selectedIndex: selectedIndex - 1;
			}, {
				if({ fromIdx > selectedIndex && toIdx <= selectedIndex }, {
					:selectedIndex: selectedIndex + 1;
				});
			});
		});

		local Array of SewNode is newChildren: Array();
		local Int is k: 0;
		while({ k < finalSegs:length() }, {
			local Int is idx: k;
			local Clickable is item: finalSegs:get(index: idx);
			item:onClick: local Function(){
				:setSelectedIndex(index: idx);
				local Function is cb: :onSelect;
				cb(idx);
			};
			item:setSelected(next: idx == selectedIndex);
			if({ segmented }, {
				item:roundLeft: idx == 0;
				item:roundRight: idx == n - 1;
				item:roundTop: idx == 0 || idx == n - 1;
				item:roundBottom: idx == 0 || idx == n - 1;
				item:insetLeft: idx == 0;
				item:insetRight: idx == n - 1;
				item:insetTop: true;
				item:insetBottom: true;
			});
			newChildren:add(item: item);
			k: k + 1;
		});
		row:children: newChildren;
		:invalidate();
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
		if({ reorderable && segmentItems:length() > 1 }, {
			local Int is i: 0;
			while({ i < segmentItems:length() }, {
				if({ segmentItems:get(index: i):containsPoint(x: x, y: y) }, {
					:dragIdx: i;
					:dragTargetIdx: i;
					:dragStartX: x;
					:dragMoved: false;
					i: segmentItems:length();
				});
				i: i + 1;
			});
		});
		return :rootNode():onPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		return :rootNode():onRightClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ reorderable && dragIdx >= 0 && segmentItems:length() > 1 }, {
			local Int is dx: x - dragStartX;
			if({ dx < 0 }, { dx: 0 - dx; });
			if({ dx > 4 }, { :dragMoved: true; });
			if({ dragMoved }, {
				local Int is n: segmentItems:length();
				local Int is newTarget: n - 1;
				local Int is i: 0;
				while({ i < n }, {
					local Rect is ib: segmentItems:get(index: i):bounds();
					if({ x < ib:x + ib:width / 2 }, {
						newTarget: i;
						i: n;
					});
					i: i + 1;
				});
				if({ newTarget != dragTargetIdx }, {
					:dragTargetIdx: newTarget;
					:invalidate();
				});
				return true;
			});
		});
		return :rootNode():onPointerDrag(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		if({ dragIdx >= 0 }, {
			local Int is fromI: dragIdx;
			local Int is toI: dragTargetIdx;
			local Boolean is moved: dragMoved;
			:dragIdx: -1;
			:dragTargetIdx: -1;
			:dragMoved: false;
			if({ moved && fromI != toI && toI >= 0 && toI < segmentItems:length() }, {
				:reorderSegment(fromIdx: fromI, toIdx: toI);
				local Function is rcb: :onReorder;
				rcb(fromI, toI);
				:rootNode():onPointerUp(x: x, y: y);
				return true;
			});
			:invalidate();
		});
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

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		return :rootNode():cursorAt(x: x, y: y);
	}
}