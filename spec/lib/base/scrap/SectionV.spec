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
		['base', 'sew', CursorShape],
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
	Boolean is reorderable: false;
	Int is selectedIndex: -1;
	Float is itemMinWidthPt: 0.0;
	Float is itemHeightPt: 0.0;
	Function is onSelect: local Function(Int is _idx){};
	Function is onReorder: local Function(Int is _from, Int is _to){};
	Array of Clickable is segmentItems: Array();
	Column is col: Column();
	Int is dragIdx: -1;
	Int is dragTargetIdx: -1;
	Int is dragStartY: 0;
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
				if({ segmented }, {
					local Int is nOpt: options:length();
					item:roundTop: idx == 0;
					item:roundBottom: idx == nOpt - 1;
					item:roundLeft: idx == 0 || idx == nOpt - 1;
					item:roundRight: idx == 0 || idx == nOpt - 1;
					item:insetTop: idx == 0;
					item:insetBottom: idx == nOpt - 1;
					item:insetLeft: true;
					item:insetRight: true;
				});
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
			local Int is linePx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
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
			local Int is linePx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
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
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		if({ !segmented }, {
			col:paint(ctx: ctx);
		}, {
			local Int is btnPx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
			local Int is divPx: activeTheme:dividerPx(scaleFactor: activeScale:factor);
			local Int is radPx: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
			local Int is startIdx: if({ title != '' }, { 1 }, { 0 });
			local Int is count: col:children:length();
			if({ startIdx > 0 && count > 0 }, {
				col:children:get(index: 0):paint(ctx: ctx);
			});
			if({ count > startIdx }, {
				local Rect is firstB: col:children:get(index: startIdx):bounds();
				local Rect is lastB: col:children:get(index: count - 1):bounds();
				local Int is gx: firstB:x;
				local Int is gy: firstB:y;
				local Int is gw: firstB:width;
				local Int is gh: (lastB:y + lastB:height) - firstB:y;
				local Boolean is clippedInner: btnPx > 0 && gw > btnPx * 2 && gh > btnPx * 2;
				if({ clippedInner }, {
					ctx:setClip(x: gx + btnPx, y: gy + btnPx, w: gw - btnPx * 2, h: gh - btnPx * 2);
				});
				local Int is pi: startIdx;
				while({ pi < count }, {
					col:children:get(index: pi):paint(ctx: ctx);
					pi: pi + 1;
				});
				if({ clippedInner }, {
					ctx:clearClip();
				});
				if({ gw > 0 && gh > 0 && btnPx > 0 }, {
					ctx:drawStyledBox(
						x: gx, y: gy, w: gw, h: gh,
						bgColor: 0, borderColor: activeTheme:buttonBorderColorArgb(),
						thickness: btnPx, radius: radPx, style: activeTheme:buttonBorderStyle
					);
				});
				if({ divPx > 0 }, {
					local Int is di: startIdx + 1;
					while({ di < count }, {
						local Rect is cb: col:children:get(index: di):bounds();
						if({ cb:width > btnPx * 2 }, {
							ctx:drawDivider(
								x: cb:x + btnPx, y: cb:y, w: cb:width - btnPx * 2, h: divPx,
								color: activeTheme:dividerColorArgb(), thickness: divPx, style: activeTheme:dividerStyle
							);
						});
						di: di + 1;
					});
				});
				if({ btnPx > 0 }, {
					local Int is segCount: count - startIdx;
					local Int is si: startIdx;
					while({ si < count }, {
						local SewNode is ch: col:children:get(index: si);
						if({ ch:isSelected() || ch:isFocused() }, {
							local Rect is cb: ch:bounds();
							if({ cb:width > 0 && cb:height > 0 }, {
								if({ segCount == 1 || (si > startIdx && si < count - 1) || radPx <= 0 }, {
									local Int is segRad: if({ segCount == 1 }, { radPx }, { 0 });
									ctx:drawStyledBox(
										x: cb:x, y: cb:y, w: cb:width, h: cb:height,
										bgColor: 0, borderColor: activeTheme:textAccent,
										thickness: btnPx, radius: segRad, style: activeTheme:buttonBorderStyle
									);
								}, {
									ctx:setClip(x: cb:x, y: cb:y, w: cb:width, h: cb:height);
									if({ si == startIdx }, {
										ctx:drawStyledBox(
											x: cb:x, y: cb:y, w: cb:width, h: cb:height + radPx,
											bgColor: 0, borderColor: activeTheme:textAccent,
											thickness: btnPx, radius: radPx, style: activeTheme:buttonBorderStyle
										);
										ctx:fillRect(x: cb:x, y: cb:y + cb:height - btnPx, w: cb:width, h: btnPx, color: activeTheme:textAccent);
									}, {
										ctx:drawStyledBox(
											x: cb:x, y: cb:y - radPx, w: cb:width, h: cb:height + radPx,
											bgColor: 0, borderColor: activeTheme:textAccent,
											thickness: btnPx, radius: radPx, style: activeTheme:buttonBorderStyle
										);
										ctx:fillRect(x: cb:x, y: cb:y, w: cb:width, h: btnPx, color: activeTheme:textAccent);
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
			local Int is lineH: activeScale:px(pt: 2.0);
			if({ lineH < 2 }, { lineH: 2; });
			local Int is iy: if({ dragTargetIdx > dragIdx }, { tb:y + tb:height - lineH }, { tb:y });
			ctx:fillRect(x: tb:x, y: iy, w: tb:width, h: lineH, color: activeTheme:textAccent);
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
		if({ title != '' && col:children:length() > 0 }, {
			newChildren:add(item: col:children:get(index: 0));
		});
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
				item:roundTop: idx == 0;
				item:roundBottom: idx == n - 1;
				item:roundLeft: idx == 0 || idx == n - 1;
				item:roundRight: idx == 0 || idx == n - 1;
				item:insetTop: idx == 0;
				item:insetBottom: idx == n - 1;
				item:insetLeft: true;
				item:insetRight: true;
			});
			newChildren:add(item: item);
			k: k + 1;
		});
		col:children: newChildren;
		:invalidate();
	}

	replace Function is paintOverlay(DrawContext is ctx){
		col:paintOverlay(ctx: ctx);
	}

	replace Function of Boolean is closePopupsOutside(Int is x, Int is y){
		return col:closePopupsOutside(x: x, y: y);
	}

	replace Function of Boolean is onOverlayPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return col:onOverlayPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onOverlayPointerMove(Int is x, Int is y){
		return col:onOverlayPointerMove(x: x, y: y);
	}

	replace Function of Boolean is onOverlayPointerDrag(Int is x, Int is y, Int is mods: 0){
		return col:onOverlayPointerDrag(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onOverlayPointerUp(Int is x, Int is y){
		return col:onOverlayPointerUp(x: x, y: y);
	}

	replace Function of Boolean is blocksPointerAt(Int is x, Int is y){
		if({ pointerTransparent }, { return false; });
		return :containsPoint(x: x, y: y) || col:blocksPointerAt(x: x, y: y);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		return col:onPointerMove(x: x, y: y);
	}

	replace Function is clearHover(){
		col:clearHover();
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ reorderable && segmentItems:length() > 1 }, {
			local Int is i: 0;
			while({ i < segmentItems:length() }, {
				if({ segmentItems:get(index: i):containsPoint(x: x, y: y) }, {
					:dragIdx: i;
					:dragTargetIdx: i;
					:dragStartY: y;
					:dragMoved: false;
					i: segmentItems:length();
				});
				i: i + 1;
			});
		});
		return col:onPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		return col:onRightClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ reorderable && dragIdx >= 0 && segmentItems:length() > 1 }, {
			local Int is dy: y - dragStartY;
			if({ dy < 0 }, { dy: 0 - dy; });
			if({ dy > 4 }, { :dragMoved: true; });
			if({ dragMoved }, {
				local Int is n: segmentItems:length();
				local Int is newTarget: n - 1;
				local Int is i: 0;
				while({ i < n }, {
					local Rect is ib: segmentItems:get(index: i):bounds();
					if({ y < ib:y + ib:height / 2 }, {
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
		return col:onPointerDrag(x: x, y: y, mods: mods);
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
				col:onPointerUp(x: x, y: y);
				return true;
			});
			:invalidate();
		});
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

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		return col:cursorAt(x: x, y: y);
	}
}