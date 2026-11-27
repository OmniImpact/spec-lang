#! Package base:scrap
#! Data grid / table widget with sticky sortable header, row selection, and vertical/horizontal scrolling.

Class of SewNode is TableView{
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
		['base', 'sew', Scale]
	];

	Array of String is columns: Array();
	Array of Float is colWidthsPt: Array();
	Array of Array of String is rows: Array();
	Int is selectedIndex: -1;
	Int is sortColumn: -1;
	Boolean is sortAscending: true;
	Boolean is sortable: true;
	Float is rowHeightPt: 0.0;
	Float is minWidthPt: 240.0;
	Float is heightPt: 200.0;
	Function is onSelect: local Function(Int is _idx){};
	Function is onSort: local Function(Int is _col, Boolean is _asc){};

	Int is hoverRow: -1;
	Int is hoverCol: -1;
	Int is scrollY: 0;
	Int is maxScrollY: 0;
	Int is scrollX: 0;
	Int is maxScrollX: 0;

	replace Function is init(
		Array of String is columns: Array(),
		Array of Float is colWidthsPt: Array(),
		Array of Array of String is rows: Array(),
		Int is selectedIndex: -1,
		Int is sortColumn: -1,
		Boolean is sortAscending: true,
		Boolean is sortable: true,
		Float is rowHeightPt: 0.0,
		Float is minWidthPt: 240.0,
		Float is heightPt: 200.0,
		Function is onSelect: local Function(Int is _idx){},
		Function is onSort: local Function(Int is _col, Boolean is _asc){}
	){
		:columns: columns;
		:colWidthsPt: colWidthsPt;
		:rows: rows;
		:selectedIndex: selectedIndex;
		:sortColumn: sortColumn;
		:sortAscending: sortAscending;
		:sortable: sortable;
		:rowHeightPt: rowHeightPt;
		:minWidthPt: minWidthPt;
		:heightPt: heightPt;
		:onSelect: onSelect;
		:onSort: onSort;
	}

	Function is setRows(Array of Array of String is next){
		:rows: next;
		if({ selectedIndex >= rows:length() }, {
			:selectedIndex: rows:length() - 1;
		});
		:hoverRow: -1;
		:invalidate();
	}

	Function is setSelectedIndex(Int is index){
		if({ index < -1 || index >= rows:length() }, { return; });
		:selectedIndex: index;
		:invalidate();
	}

	local Function of Int is rowHeightPx(){
		if({ rowHeightPt > 0.0 }, {
			local Int is h: activeScale:px(pt: rowHeightPt);
			return if({ h < 18 }, { 18 }, { h });
		});
		local Int is fontPx: activeScale:px(pt: activeTheme:fontSizePt);
		local Int is padPx: activeScale:px(pt: activeTheme:paddingPt);
		local Int is h: fontPx + padPx;
		local Int is minH: activeScale:px(pt: activeTheme:buttonMinHeightPt * 0.9);
		return if({ h > minH }, { h }, { minH });
	}

	local Function of Int is colWidthPx(Int is colIdx){
		if({ colIdx >= 0 && colIdx < colWidthsPt:length() }, {
			local Float is wPt: colWidthsPt:get(index: colIdx);
			if({ wPt > 0.0 }, {
				local Int is px: activeScale:px(pt: wPt);
				return if({ px < 40 }, { 40 }, { px });
			});
		});
		return activeScale:px(pt: 110.0);
	}

	local Function of Int is totalColsWidthPx(){
		local Int is total: 0;
		local Int is i: 0;
		while({ i < columns:length() }, {
			total: total + :colWidthPx(colIdx: i);
			i: i + 1;
		});
		return total;
	}

	local Function of Int is compareStrings(String is a, String is b){
		local String is la: a:toLower();
		local String is lb: b:toLower();
		local Int is na: la:runeCount();
		local Int is nb: lb:runeCount();
		local Int is minN: if({ na < nb }, { na }, { nb });
		local Int is i: 0;
		while({ i < minN }, {
			local Int is ca: la:codePointAtRune(runeIndex: i);
			local Int is cb: lb:codePointAtRune(runeIndex: i);
			if({ ca < cb }, { return -1; });
			if({ ca > cb }, { return 1; });
			i: i + 1;
		});
		if({ na < nb }, { return -1; });
		if({ na > nb }, { return 1; });
		return 0;
	}

	Function is sortBy(Int is colIdx, Boolean is ascending){
		if({ colIdx < 0 || colIdx >= columns:length() }, { return; });
		:sortColumn: colIdx;
		:sortAscending: ascending;
		local Int is n: rows:length();
		local Array of String is selRow: Array();
		local Boolean is hasSel: selectedIndex >= 0 && selectedIndex < n;
		if({ hasSel }, { selRow: rows:get(index: selectedIndex); });

		local Int is i: 1;
		while({ i < n }, {
			local Array of String is keyRow: rows:get(index: i);
			local String is keyVal: if({ colIdx < keyRow:length() }, { keyRow:get(index: colIdx) }, { '' });
			local Int is j: i - 1;
			local Boolean is shifting: true;
			while({ j >= 0 && shifting }, {
				local Array of String is cmpRow: rows:get(index: j);
				local String is cmpVal: if({ colIdx < cmpRow:length() }, { cmpRow:get(index: colIdx) }, { '' });
				local Int is c: :compareStrings(a: cmpVal, b: keyVal);
				local Boolean is shouldSwap: if({ ascending }, { c > 0 }, { c < 0 });
				if({ shouldSwap }, {
					rows:set(index: j + 1, item: cmpRow);
					j: j - 1;
				}, {
					shifting: false;
				});
			});
			rows:set(index: j + 1, item: keyRow);
			i: i + 1;
		});

		if({ hasSel }, {
			local Int is k: 0;
			while({ k < n }, {
				if({ rows:get(index: k) == selRow }, {
					:selectedIndex: k;
					k: n;
				});
				k: k + 1;
			});
		});
		:invalidate();
	}

	local Function of Int is headerColAtX(Int is x){
		local Rect is b: bounds();
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is relX: x - (b:x + bw) + scrollX;
		if({ relX < 0 }, { return -1; });
		local Int is cx: 0;
		local Int is i: 0;
		while({ i < columns:length() }, {
			local Int is cw: :colWidthPx(colIdx: i);
			if({ relX >= cx && relX < cx + cw }, { return i; });
			cx: cx + cw;
			i: i + 1;
		});
		return -1;
	}

	local Function of Int is bodyRowAtY(Int is y){
		local Rect is b: bounds();
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is rh: :rowHeightPx();
		local Int is bodyTop: b:y + bw + rh;
		local Int is relY: y - bodyTop + scrollY;
		if({ y < bodyTop || relY < 0 || rh <= 0 }, { return -1; });
		local Int is idx: relY / rh;
		if({ idx < 0 || idx >= rows:length() }, { return -1; });
		return idx;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is rh: :rowHeightPx();
		local Int is colsW: :totalColsWidthPx() + bw * 2;
		local Int is minW: activeScale:px(pt: minWidthPt);
		local Int is prefW: if({ colsW > minW }, { colsW }, { minW });
		local Int is contentH: (rows:length() + 1) * rh + bw * 2;
		local Int is prefH: if({ heightPt > 0.0 }, {
			activeScale:px(pt: heightPt)
		}, {
			contentH
		});
		desiredSize: Size(width: c:clampW(w: prefW), height: c:clampH(h: prefH));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is rh: :rowHeightPx();
		local Int is viewW: bounds:width - bw * 2;
		local Int is viewH: bounds:height - bw * 2 - rh;
		local Int is contentW: :totalColsWidthPx();
		local Int is contentH: rows:length() * rh;
		local Int is msX: contentW - viewW;
		local Int is msY: contentH - viewH;
		:maxScrollX: if({ msX > 0 }, { msX }, { 0 });
		:maxScrollY: if({ msY > 0 }, { msY }, { 0 });
		if({ scrollX > maxScrollX }, { :scrollX: maxScrollX; });
		if({ scrollX < 0 }, { :scrollX: 0; });
		if({ scrollY > maxScrollY }, { :scrollY: maxScrollY; });
		if({ scrollY < 0 }, { :scrollY: 0; });
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is divPx: activeTheme:dividerPx(scaleFactor: activeScale:factor);
		local Int is rad: activeScale:px(pt: activeTheme:panelCornerRadiusPt);

		ctx:drawStyledBox(
			x: b:x, y: b:y, w: b:width, h: b:height,
			bgColor: activeTheme:surface, borderColor: activeTheme:panelBorderColorArgb(),
			thickness: bw, radius: rad, style: activeTheme:panelBorderStyle
		);

		local Int is innerX: b:x + bw;
		local Int is innerY: b:y + bw;
		local Int is innerW: b:width - bw * 2;
		local Int is innerH: b:height - bw * 2;
		if({ innerW <= 0 || innerH <= 0 }, { return; });

		local Int is rh: :rowHeightPx();
		local Int is fontPx: activeScale:px(pt: activeTheme:fontSizePt);
		local Int is padX: activeScale:px(pt: activeTheme:paddingPt);

		ctx:setClip(x: innerX, y: innerY, w: innerW, h: innerH);

		# Header row
		local Int is hdrH: if({ rh < innerH }, { rh }, { innerH });
		ctx:fillRect(x: innerX, y: innerY, w: innerW, h: hdrH, color: activeTheme:surfaceHover);
		local Int is cx: innerX - scrollX;
		local Int is ci: 0;
		while({ ci < columns:length() }, {
			local Int is cw: :colWidthPx(colIdx: ci);
			if({ sortable && ci == hoverCol }, {
				ctx:fillRect(x: cx, y: innerY, w: cw, h: hdrH, color: activeTheme:surfacePressed);
			});
			local String is colText: columns:get(index: ci);
			if({ ci == sortColumn }, {
				colText: colText . if({ sortAscending }, { ' ▲' }, { ' ▼' });
			});
			local Int is cellPad: padX / 2;
			ctx:setClip(x: cx, y: innerY, w: cw, h: hdrH);
			ctx:drawText(
				x: cx + cellPad,
				y: innerY + (hdrH - fontPx) / 2,
				text: colText,
				color: activeTheme:textPrimary,
				pixelHeight: fontPx,
				bold: true,
				italic: false,
				mono: false
			);
			ctx:clearClip();
			if({ divPx > 0 && ci + 1 < columns:length() }, {
				ctx:drawDivider(
					x: cx + cw - divPx, y: innerY + 2, w: divPx, h: hdrH - 4,
					color: activeTheme:dividerColorArgb(), thickness: divPx, style: activeTheme:dividerStyle
				);
			});
			cx: cx + cw;
			ci: ci + 1;
		});
		if({ divPx > 0 && hdrH < innerH }, {
			ctx:drawDivider(
				x: innerX, y: innerY + hdrH - divPx, w: innerW, h: divPx,
				color: activeTheme:dividerColorArgb(), thickness: divPx, style: activeTheme:dividerStyle
			);
		});

		# Body rows
		local Int is bodyY: innerY + hdrH;
		local Int is bodyH: innerH - hdrH;
		if({ bodyH > 0 }, {
			ctx:setClip(x: innerX, y: bodyY, w: innerW, h: bodyH);
			local Int is n: rows:length();
			local Int is ri: 0;
			while({ ri < n }, {
				local Int is ry: bodyY + ri * rh - scrollY;
				if({ ry + rh > bodyY && ry < bodyY + bodyH }, {
					local Boolean is isSel: ri == selectedIndex;
					local Boolean is isHov: ri == hoverRow;
					if({ isSel || isHov }, {
						local FillStyle is rowFill: activeTheme:resolveButtonFill(
							enabled: true, selected: isSel, hovered: isHov, focused: false
						);
						ctx:drawStyledBoxFill(
							x: innerX, y: ry, w: innerW, h: rh,
							fill: rowFill, borderColor: 0, thickness: 0, radius: 0,
							style: activeTheme:buttonBorderStyle
						);
					});
					local Array of String is r: rows:get(index: ri);
					local Int is cellX: innerX - scrollX;
					local Int is cj: 0;
					while({ cj < columns:length() }, {
						local Int is cw: :colWidthPx(colIdx: cj);
						local String is cellText: if({ cj < r:length() }, { r:get(index: cj) }, { '' });
						ctx:setClip(x: cellX, y: ry, w: cw, h: rh);
						ctx:drawText(
							x: cellX + padX / 2,
							y: ry + (rh - fontPx) / 2,
							text: cellText,
							color: if({ isSel }, { activeTheme:textPrimary }, { activeTheme:textSecondary }),
							pixelHeight: fontPx,
							bold: isSel,
							italic: false,
							mono: false
						);
						ctx:clearClip();
						cellX: cellX + cw;
						cj: cj + 1;
					});
					if({ divPx > 0 && ri + 1 < n }, {
						ctx:drawDivider(
							x: innerX, y: ry + rh - divPx, w: innerW, h: divPx,
							color: activeTheme:dividerColorArgb(), thickness: divPx, style: activeTheme:dividerStyle
						);
					});
				});
				ri: ri + 1;
			});

			if({ maxScrollY > 0 }, {
				local Int is barW: activeScale:px(pt: 4.0);
				if({ barW < 3 }, { barW: 3; });
				local Int is contentH: n * rh;
				local Int is thumbH: (bodyH * bodyH) / contentH;
				if({ thumbH < 16 }, { thumbH: 16; });
				if({ thumbH > bodyH }, { thumbH: bodyH; });
				local Int is trackH: bodyH - thumbH;
				local Int is thumbY: bodyY + if({ maxScrollY > 0 }, { (scrollY * trackH) / maxScrollY }, { 0 });
				ctx:fillRect(x: innerX + innerW - barW - 1, y: thumbY, w: barW, h: thumbH, color: activeTheme:textMuted);
			});
			ctx:clearClip();
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
			if({ hoverRow != -1 || hoverCol != -1 }, {
				:hoverRow: -1;
				:hoverCol: -1;
				:invalidate();
			});
			return false;
		});
		local Rect is b: bounds();
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is rh: :rowHeightPx();
		local Int is hdrBot: b:y + bw + rh;
		local Int is nextRow: -1;
		local Int is nextCol: -1;
		if({ y >= b:y + bw && y < hdrBot }, {
			nextCol: :headerColAtX(x: x);
		}, {
			nextRow: :bodyRowAtY(y: y);
		});
		if({ nextRow != hoverRow || nextCol != hoverCol }, {
			:hoverRow: nextRow;
			:hoverCol: nextCol;
			:invalidate();
		});
		return true;
	}

	replace Function is clearHover(){
		if({ hoverRow != -1 || hoverCol != -1 }, {
			:hoverRow: -1;
			:hoverCol: -1;
			:invalidate();
		});
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ !:containsPoint(x: x, y: y) }, { return false; });
		local Rect is b: bounds();
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is rh: :rowHeightPx();
		local Int is hdrBot: b:y + bw + rh;
		if({ y >= b:y + bw && y < hdrBot }, {
			if({ sortable }, {
				local Int is colIdx: :headerColAtX(x: x);
				if({ colIdx >= 0 }, {
					local Boolean is nextAsc: if({ sortColumn == colIdx }, { !sortAscending }, { true });
					:sortBy(colIdx: colIdx, ascending: nextAsc);
					local Function is scb: :onSort;
					scb(colIdx, nextAsc);
				});
			});
			return true;
		});
		local Int is rIdx: :bodyRowAtY(y: y);
		if({ rIdx >= 0 }, {
			:selectedIndex: rIdx;
			local Function is cb: :onSelect;
			cb(rIdx);
			:invalidate();
		});
		return true;
	}

	replace Function of Boolean is onScroll(Int is x, Int is y, Int is dy){
		if({ !:containsPoint(x: x, y: y) }, { return false; });
		if({ maxScrollY <= 0 }, { return false; });
		local Int is step: activeScale:px(pt: 28.0);
		local Int is next: scrollY - dy * step;
		if({ next < 0 }, { next: 0; });
		if({ next > maxScrollY }, { next: maxScrollY; });
		if({ next != scrollY }, {
			:scrollY: next;
			:invalidate();
		});
		return true;
	}

	replace Function of Boolean is onScrollX(Int is x, Int is y, Int is dx){
		if({ !:containsPoint(x: x, y: y) }, { return false; });
		if({ maxScrollX <= 0 }, { return false; });
		local Int is step: activeScale:px(pt: 28.0);
		local Int is next: scrollX - dx * step;
		if({ next < 0 }, { next: 0; });
		if({ next > maxScrollX }, { next: maxScrollX; });
		if({ next != scrollX }, {
			:scrollX: next;
			:invalidate();
		});
		return true;
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		if({ !focused || rows:length() == 0 }, { return false; });
		local Int is n: rows:length();
		local Int is next: selectedIndex;
		if({ key == 111 }, {
			next: if({ selectedIndex > 0 }, { selectedIndex - 1 }, { 0 });
		}, {
		if({ key == 116 }, {
			next: if({ selectedIndex + 1 < n }, { selectedIndex + 1 }, { n - 1 });
		}, {
		if({ key == 110 }, {
			next: 0;
		}, {
		if({ key == 115 }, {
			next: n - 1;
		}, {
			return false;
		}); }); }); });
		if({ next != selectedIndex }, {
			:selectedIndex: next;
			local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
			local Int is rh: :rowHeightPx();
			local Int is bodyH: bounds():height - bw * 2 - rh;
			local Int is rowTop: next * rh;
			local Int is rowBot: rowTop + rh;
			if({ rowTop < scrollY }, { :scrollY: rowTop; });
			if({ rowBot > scrollY + bodyH && bodyH > 0 }, { :scrollY: rowBot - bodyH; });
			local Function is cb: :onSelect;
			cb(next);
			:invalidate();
		});
		return true;
	}

	replace Function is collectFocusables(Array of SewNode is out){
		out:add(item: self);
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ !:containsPoint(x: x, y: y) }, { return CursorShape:DEFAULT; });
		if({ (sortable && hoverCol >= 0) || hoverRow >= 0 }, { return CursorShape:POINTER; });
		return CursorShape:DEFAULT;
	}
}
