#! Package base:scrap
#! Scrollable list widget with selection, keyboard navigation, and optional 6-dot grip reordering.

Class of SewNode is ListView{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'fabric', Theme],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'scrap', DragDropState]
	];

	Array of String is items: Array();
	Int is selectedIndex: -1;
	Boolean is reorderable: false;
	Float is rowHeightPt: 0.0;
	Float is minWidthPt: 160.0;
	Float is heightPt: 180.0;
	Boolean is showBorder: true;
	Function is onSelect: local Function(Int is _idx){};
	Function is onReorder: local Function(Int is _from, Int is _to){};

	Int is hoverIdx: -1;
	Boolean is hovered: false;
	Boolean is focused: false;
	Int is scrollY: 0;
	Int is maxScrollY: 0;
	Int is dragIdx: -1;
	Int is dragTargetIdx: -1;
	Int is dragStartY: 0;
	Boolean is dragMoved: false;

	replace Function is init(
		Array of String is items: Array(),
		Int is selectedIndex: -1,
		Boolean is reorderable: false,
		Float is rowHeightPt: 0.0,
		Float is minWidthPt: 160.0,
		Float is heightPt: 180.0,
		Boolean is showBorder: true,
		Function is onSelect: local Function(Int is _idx){},
		Function is onReorder: local Function(Int is _from, Int is _to){}
	){
		:items: items;
		:selectedIndex: selectedIndex;
		:reorderable: reorderable;
		:rowHeightPt: rowHeightPt;
		:minWidthPt: minWidthPt;
		:heightPt: heightPt;
		:showBorder: showBorder;
		:onSelect: onSelect;
		:onReorder: onReorder;
	}

	Function is setItems(Array of String is next){
		:items: next;
		if({ selectedIndex >= items:length() }, {
			:selectedIndex: items:length() - 1;
		});
		:hoverIdx: -1;
		:dragIdx: -1;
		:dragTargetIdx: -1;
		:dragMoved: false;
		:invalidate();
	}

	Function is setSelectedIndex(Int is index){
		if({ index < -1 || index >= items:length() }, { return; });
		:selectedIndex: index;
		:invalidate();
	}

	local Function of Int is rowHeightPx(){
		if({ rowHeightPt > 0.0 }, {
			local Int is h: activeScale:px(pt: rowHeightPt);
			return if({ h < 16 }, { 16 }, { h });
		});
		local Int is fontPx: activeScale:px(pt: activeTheme:baseTextPt);
		local Int is padPx: activeScale:px(pt: activeTheme:paddingPt);
		local Int is h: fontPx + padPx;
		local Int is minH: activeScale:px(pt: activeTheme:buttonHeightPt * 0.85);
		return if({ h > minH }, { h }, { minH });
	}

	local Function of Int is insetPx(){
		local Int is bw: if({ showBorder }, { activeTheme:panelBorderPx(scaleFactor: activeScale:factor) }, { 0 });
		return bw;
	}

	local Function of Int is rowAtY(Int is y){
		local Rect is b: bounds();
		local Int is ins: :insetPx();
		local Int is rh: :rowHeightPx();
		local Int is relY: y - (b:y + ins) + scrollY;
		if({ relY < 0 || rh <= 0 }, { return -1; });
		local Int is idx: relY / rh;
		if({ idx < 0 || idx >= items:length() }, { return -1; });
		return idx;
	}

	local Function is moveItem(Int is fromIdx, Int is toIdx){
		local Int is n: items:length();
		if({ fromIdx < 0 || fromIdx >= n || toIdx < 0 || toIdx >= n || fromIdx == toIdx }, { return; });
		local String is moved: items:get(index: fromIdx);
		local Array of String is without: Array();
		local Int is i: 0;
		while({ i < n }, {
			if({ i != fromIdx }, { without:add(item: items:get(index: i)); });
			i: i + 1;
		});
		local Array of String is finalItems: Array();
		local Int is j: 0;
		local Boolean is inserted: false;
		while({ j < without:length() }, {
			if({ j == toIdx }, {
				finalItems:add(item: moved);
				inserted: true;
			});
			finalItems:add(item: without:get(index: j));
			j: j + 1;
		});
		if({ !inserted }, { finalItems:add(item: moved); });
		:items: finalItems;

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
	}

	replace Function of Size is measure(Constraints is c){
		local Int is rh: :rowHeightPx();
		local Int is ins: :insetPx();
		local Int is padX: activeScale:px(pt: activeTheme:paddingPt) * 2;
		local Int is gripSpace: if({ reorderable }, { activeScale:px(pt: 18.0) }, { 0 });
		local Int is maxTextW: activeScale:px(pt: minWidthPt);
		local Int is fontPx: activeScale:px(pt: activeTheme:baseTextPt);
		local Int is i: 0;
		while({ i < items:length() }, {
			local Int is tw: (items:get(index: i):length() * fontPx * 6) / 10 + padX + gripSpace + ins * 2;
			if({ tw > maxTextW }, { maxTextW: tw; });
			i: i + 1;
		});
		local Int is prefW: c:clampW(w: maxTextW);
		local Int is contentH: items:length() * rh + ins * 2;
		local Int is prefH: if({ heightPt > 0.0 }, {
			activeScale:px(pt: heightPt)
		}, {
			contentH
		});
		desiredSize: Size(width: prefW, height: c:clampH(h: prefH));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is ins: :insetPx();
		local Int is rh: :rowHeightPx();
		local Int is viewH: bounds:height - ins * 2;
		local Int is contentH: items:length() * rh;
		local Int is ms: contentH - viewH;
		:maxScrollY: if({ ms > 0 }, { ms }, { 0 });
		if({ scrollY > maxScrollY }, { :scrollY: maxScrollY; });
		if({ scrollY < 0 }, { :scrollY: 0; });
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is bw: if({ showBorder }, { activeTheme:panelBorderPx(scaleFactor: activeScale:factor) }, { 0 });
		local Int is rad: if({ showBorder }, { activeScale:px(pt: activeTheme:panelCornerRadiusPt) }, { 0 });
		local Int is bgCol: activeTheme:surfaceBg;
		if({ showBorder }, {
			ctx:drawStyledBox(
				x: b:x, y: b:y, w: b:width, h: b:height,
				bgColor: bgCol, borderColor: activeTheme:panelBorderColorArgb(),
				thickness: bw, radius: rad, style: activeTheme:panelBorderStyle
			);
		}, {
			ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: bgCol);
		});

		local Int is ins: bw;
		local Int is clipX: b:x + ins;
		local Int is clipY: b:y + ins;
		local Int is clipW: b:width - ins * 2;
		local Int is clipH: b:height - ins * 2;
		if({ clipW <= 0 || clipH <= 0 }, { return; });
		ctx:setClip(x: clipX, y: clipY, w: clipW, h: clipH);

		local Int is rh: :rowHeightPx();
		local Int is fontPx: activeScale:px(pt: activeTheme:baseTextPt);
		local Int is padX: activeScale:px(pt: activeTheme:paddingPt);
		local Int is gripW: if({ reorderable }, { activeScale:px(pt: 16.0) }, { 0 });
		local Int is divPx: activeTheme:dividerPx(scaleFactor: activeScale:factor);
		local Int is dotSz: activeScale:px(pt: 2.0);
		if({ dotSz < 2 }, { dotSz: 2; });
		local Int is dotGap: dotSz + 2;

		local Int is n: items:length();
		local Int is i: 0;
		while({ i < n }, {
			local Int is ry: clipY + i * rh - scrollY;
			if({ ry + rh > clipY && ry < clipY + clipH }, {
				local Boolean is isSel: i == selectedIndex;
				local Boolean is isHov: i == hoverIdx;
				local Boolean is isDragSrc: dragIdx == i && dragMoved;
				if({ isSel || isHov || isDragSrc }, {
					local FillStyle is rowFill: activeTheme:resolveButtonFill(
						enabled: true,
						selected: isSel,
						hovered: isHov || isDragSrc,
						focused: false
					);
					ctx:drawStyledBoxFill(
						x: clipX, y: ry, w: clipW, h: rh,
						fill: rowFill, borderColor: 0, thickness: 0, radius: 0,
						style: activeTheme:buttonBorderStyle
					);
				});
				if({ reorderable }, {
					local Int is gx: clipX + padX / 2;
					local Int is gy: ry + (rh - (dotSz * 3 + 4)) / 2;
					local Int is gripCol: if({ isSel || isHov }, { activeTheme:textPrimary }, { activeTheme:textMuted });
					local Int is gr: 0;
					while({ gr < 3 }, {
						local Int is gc: 0;
						while({ gc < 2 }, {
							ctx:fillRect(x: gx + gc * dotGap, y: gy + gr * dotGap, w: dotSz, h: dotSz, color: gripCol);
							gc: gc + 1;
						});
						gr: gr + 1;
					});
				});
				local Int is textX: clipX + padX + gripW;
				local Int is textY: ry + (rh - fontPx) / 2;
				local Int is textCol: if({ isSel }, { activeTheme:textPrimary }, { activeTheme:textMuted });
				ctx:drawText(
					x: textX, y: textY,
					text: items:get(index: i),
					color: textCol,
					pixelHeight: fontPx,
					bold: isSel,
					italic: false,
					mono: false
				);
				if({ divPx > 0 && i + 1 < n }, {
					ctx:drawDivider(
						x: clipX, y: ry + rh - divPx, w: clipW, h: divPx,
						color: activeTheme:dividerColorArgb(), thickness: divPx, style: activeTheme:dividerStyle
					);
				});
			});
			i: i + 1;
		});

		if({ reorderable && dragIdx >= 0 && dragMoved && dragTargetIdx >= 0 && dragTargetIdx <= n }, {
			local Int is lineH: activeScale:px(pt: 3.0);
			if({ lineH < 3 }, { lineH: 3; });
			local Int is divY: clipY + dragTargetIdx * rh - scrollY - lineH / 2;
			if({ divY < clipY }, { divY: clipY; });
			if({ divY + lineH > clipY + clipH }, { divY: clipY + clipH - lineH; });
			ctx:fillRect(x: clipX, y: divY, w: clipW, h: lineH, color: activeTheme:textAccent);
		});

		if({ maxScrollY > 0 }, {
			local Int is barW: activeScale:px(pt: 4.0);
			if({ barW < 3 }, { barW: 3; });
			local Int is contentH: n * rh;
			local Int is thumbH: (clipH * clipH) / contentH;
			if({ thumbH < 16 }, { thumbH: 16; });
			if({ thumbH > clipH }, { thumbH: clipH; });
			local Int is trackH: clipH - thumbH;
			local Int is thumbY: clipY + if({ maxScrollY > 0 }, { (scrollY * trackH) / maxScrollY }, { 0 });
			ctx:fillRect(x: clipX + clipW - barW - 1, y: thumbY, w: barW, h: thumbH, color: activeTheme:textMuted);
		});

		ctx:clearClip();
		if({ focused && bw > 0 }, {
			ctx:drawStyledBox(
				x: b:x, y: b:y, w: b:width, h: b:height,
				bgColor: 0, borderColor: activeTheme:textAccent,
				thickness: bw, radius: rad, style: activeTheme:panelBorderStyle
			);
		});
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		if({ !:containsPoint(x: x, y: y) }, {
			if({ hoverIdx != -1 || hovered }, {
				:hoverIdx: -1;
				:hovered: false;
				:invalidate();
			});
			return false;
		});
		:hovered: true;
		local Int is idx: :rowAtY(y: y);
		if({ idx != hoverIdx }, {
			:hoverIdx: idx;
			:invalidate();
		});
		return true;
	}

	replace Function is clearHover(){
		if({ hoverIdx != -1 || hovered }, {
			:hoverIdx: -1;
			:hovered: false;
			:invalidate();
		});
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ !:containsPoint(x: x, y: y) }, { return false; });
		local Int is idx: :rowAtY(y: y);
		if({ idx >= 0 }, {
			:selectedIndex: idx;
			if({ reorderable && items:length() > 1 }, {
				:dragIdx: idx;
				:dragTargetIdx: idx;
				:dragStartY: y;
				:dragMoved: false;
			});
			local Function is cb: :onSelect;
			cb(idx);
			:invalidate();
		});
		return true;
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ !reorderable || dragIdx < 0 || items:length() <= 1 }, { return false; });
		local Int is dy: y - dragStartY;
		if({ dy < 0 }, { dy: 0 - dy; });
		if({ dy > 4 && !dragMoved }, {
			:dragMoved: true;
			DragDropState:shared:beginDrag(payload: '', label: items:get(index: dragIdx), x: x, y: y);
		});
		if({ dragMoved }, {
			DragDropState:shared:updatePointer(x: x, y: y);
			local Rect is b: bounds();
			local Int is ins: :insetPx();
			local Int is rh: :rowHeightPx();
			local Int is relY: y - (b:y + ins) + scrollY;
			local Int is slot: if({ rh > 0 }, { (relY + rh / 2) / rh }, { 0 });
			if({ slot < 0 }, { slot: 0; });
			if({ slot > items:length() }, { slot: items:length(); });
			if({ slot != dragTargetIdx }, {
				:dragTargetIdx: slot;
				:invalidate();
			});
			return true;
		});
		return false;
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		if({ dragIdx >= 0 }, {
			local Int is fromI: dragIdx;
			local Int is slot: dragTargetIdx;
			local Boolean is moved: dragMoved;
			:dragIdx: -1;
			:dragTargetIdx: -1;
			:dragMoved: false;
			DragDropState:shared:finishDrag();
			if({ moved && slot >= 0 && slot <= items:length() }, {
				local Int is toI: if({ slot > fromI }, { slot - 1 }, { slot });
				if({ toI != fromI && toI >= 0 && toI < items:length() }, {
					:moveItem(fromIdx: fromI, toIdx: toI);
					local Function is rcb: :onReorder;
					rcb(fromI, toI);
				});
			});
			:invalidate();
			return true;
		});
		return false;
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		if({ !hovered || maxScrollY <= 0 }, { return false; });
		local Int is step: activeScale:px(pt: 28.0);
		local Int is next: scrollY - deltaY * step;
		if({ next < 0 }, { next: 0; });
		if({ next > maxScrollY }, { next: maxScrollY; });
		if({ next != scrollY }, {
			:scrollY: next;
			:invalidate();
		});
		return true;
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		if({ !focused || items:length() == 0 }, { return false; });
		local Int is n: items:length();
		local Int is next: selectedIndex;
		if({ key == 1001 }, {
			next: if({ selectedIndex > 0 }, { selectedIndex - 1 }, { 0 });
		}, {
		if({ key == 1002 }, {
			next: if({ selectedIndex + 1 < n }, { selectedIndex + 1 }, { n - 1 });
		}, {
		if({ key == 1005 }, {
			next: 0;
		}, {
		if({ key == 1006 }, {
			next: n - 1;
		}, {
			return false;
		}); }); }); });
		if({ next != selectedIndex }, {
			:selectedIndex: next;
			local Int is rh: :rowHeightPx();
			local Int is ins: :insetPx();
			local Int is viewH: bounds():height - ins * 2;
			local Int is rowTop: next * rh;
			local Int is rowBot: rowTop + rh;
			if({ rowTop < scrollY }, { :scrollY: rowTop; });
			if({ rowBot > scrollY + viewH && viewH > 0 }, { :scrollY: rowBot - viewH; });
			local Function is cb: :onSelect;
			cb(next);
			:invalidate();
		});
		return true;
	}

	replace Function of Boolean is canFocus(){
		return true;
	}

	replace Function of Boolean is isFocused(){
		return focused;
	}

	replace Function is setFocused(Boolean is next){
		:focused: next;
		:invalidate();
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ !:containsPoint(x: x, y: y) }, { return CursorShape:DEFAULT; });
		if({ dragIdx >= 0 && dragMoved }, { return CursorShape:POINTER; });
		if({ :rowAtY(y: y) >= 0 }, { return CursorShape:POINTER; });
		return CursorShape:DEFAULT;
	}
}
