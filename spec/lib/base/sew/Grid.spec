#! Package base:sew
#! 2D row-major grid layout container aligning children into uniform column widths and row heights.

Class of SewNode is Grid{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale]
	];

	Int is columns: 2;
	Array of SewNode is children: Array();
	Float is colGapPt: 8.0;
	Float is rowGapPt: 6.0;
	Boolean is equalCols: false;
	Boolean is expandRows: false;
	Array of Boolean is flexCols: Array();
	Array of Int is colWidthsPx: Array();
	Array of Int is rowHeightsPx: Array();
	Int is dragChildIdx: -1;

	replace Function is init(
		Int is columns: 2,
		Array of SewNode is children: Array(),
		Float is colGapPt: 8.0,
		Float is rowGapPt: 6.0,
		Boolean is equalCols: false,
		Boolean is expandRows: false,
		Array of Boolean is flexCols: Array()
	){
		:columns: if({ columns < 1 }, { 1 }, { columns });
		:children: children;
		:colGapPt: colGapPt;
		:rowGapPt: rowGapPt;
		:equalCols: equalCols;
		:expandRows: expandRows;
		:flexCols: flexCols;
	}

	## Appends a child node in row-major order.
	Function is addChild(SewNode is child){
		children:add(item: child);
		invalidate();
	}

	local Function of Int is effectiveCols(){
		return if({ columns < 1 }, { 1 }, { columns });
	}

	local Function of Boolean is isColFlex(Int is col){
		if({ col >= 0 && col < flexCols:length() }, {
			return flexCols:get(index: col);
		});
		return false;
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		local Int is i: 0;
		while({ i < children:length() }, {
			children:get(index: i):applyTheme(theme: theme);
			i: i + 1;
		});
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		local Int is i: 0;
		while({ i < children:length() }, {
			children:get(index: i):setScale(scale: scale);
			i: i + 1;
		});
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		local Int is i: 0;
		while({ i < children:length() }, {
			children:get(index: i):bindDirty(cb: cb);
			i: i + 1;
		});
	}

	replace Function of Size is measure(Constraints is c){
		local Int is cols: :effectiveCols();
		local Int is count: children:length();
		local Int is rows: if({ count == 0 }, { 0 }, { (count + cols - 1) / cols });
		local Int is colGapPx: activeScale:px(pt: colGapPt);
		local Int is rowGapPx: activeScale:px(pt: rowGapPt);

		colWidthsPx: Array();
		rowHeightsPx: Array();
		times(count: cols, worker: local Function(Int is _c){
			colWidthsPx:add(item: 0);
		});
		times(count: rows, worker: local Function(Int is _r){
			rowHeightsPx:add(item: 0);
		});

		local Int is cellMaxW: c:maxW;
		if({ equalCols && c:maxW > 0 }, {
			local Int is totalGapW: if({ cols > 1 }, { (cols - 1) * colGapPx }, { 0 });
			local Int is availW: if({ c:maxW > totalGapW }, { c:maxW - totalGapW }, { 0 });
			cellMaxW: availW / cols;
			if({ cellMaxW < 1 }, { cellMaxW: 1; });
		});
		local Constraints is loose: Constraints(minW: 0, maxW: cellMaxW, minH: 0, maxH: c:maxH);

		local Int is i: 0;
		while({ i < count }, {
			local Int is r: i / cols;
			local Int is col: i - (r * cols);
			local Size is sz: children:get(index: i):measure(c: loose);
			if({ sz:width > colWidthsPx:get(index: col) }, {
				colWidthsPx:set(index: col, item: sz:width);
			});
			if({ sz:height > rowHeightsPx:get(index: r) }, {
				rowHeightsPx:set(index: r, item: sz:height);
			});
			i: i + 1;
		});

		if({ equalCols }, {
			local Int is maxColW: 0;
			local Int is ci: 0;
			while({ ci < cols }, {
				if({ colWidthsPx:get(index: ci) > maxColW }, { maxColW: colWidthsPx:get(index: ci); });
				ci: ci + 1;
			});
			ci: 0;
			while({ ci < cols }, {
				colWidthsPx:set(index: ci, item: maxColW);
				ci: ci + 1;
			});
		});

		local Int is totalW: if({ cols > 1 }, { (cols - 1) * colGapPx }, { 0 });
		local Int is cw: 0;
		while({ cw < cols }, {
			totalW: totalW + colWidthsPx:get(index: cw);
			cw: cw + 1;
		});

		local Int is totalH: if({ rows > 1 }, { (rows - 1) * rowGapPx }, { 0 });
		local Int is rh: 0;
		while({ rh < rows }, {
			totalH: totalH + rowHeightsPx:get(index: rh);
			rh: rh + 1;
		});

		desiredSize: Size(width: c:clampW(w: totalW), height: c:clampH(h: totalH));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is cols: :effectiveCols();
		local Int is count: children:length();
		if({ count == 0 }, { return; });
		local Int is rows: (count + cols - 1) / cols;
		local Int is colGapPx: activeScale:px(pt: colGapPt);
		local Int is rowGapPx: activeScale:px(pt: rowGapPt);
		local Int is totalColGap: if({ cols > 1 }, { (cols - 1) * colGapPx }, { 0 });

		local Array of Int is arrangedColW: Array();
		if({ equalCols }, {
			local Int is availW: if({ bounds:width > totalColGap }, { bounds:width - totalColGap }, { 0 });
			local Int is eachW: availW / cols;
			local Int is remW: availW - (eachW * cols);
			local Int is ci: 0;
			while({ ci < cols }, {
				arrangedColW:add(item: eachW + if({ ci < remW }, { 1 }, { 0 }));
				ci: ci + 1;
			});
		}, {
			local Int is fixedW: totalColGap;
			local Int is flexCount: 0;
			local Int is ci: 0;
			while({ ci < cols }, {
				if({ :isColFlex(col: ci) }, {
					flexCount: flexCount + 1;
				}, {
					local Int is cw: if({ ci < colWidthsPx:length() }, { colWidthsPx:get(index: ci) }, { 0 });
					fixedW: fixedW + cw;
				});
				ci: ci + 1;
			});
			local Int is remW: if({ bounds:width > fixedW }, { bounds:width - fixedW }, { 0 });
			local Int is flexW: if({ flexCount > 0 }, { remW / flexCount }, { 0 });
			ci: 0;
			while({ ci < cols }, {
				if({ :isColFlex(col: ci) }, {
					arrangedColW:add(item: flexW);
				}, {
					local Int is cw: if({ ci < colWidthsPx:length() }, { colWidthsPx:get(index: ci) }, { 0 });
					arrangedColW:add(item: cw);
				});
				ci: ci + 1;
			});
		});

		local Array of Int is colX: Array();
		local Int is curX: bounds:x;
		local Int is cxIdx: 0;
		while({ cxIdx < cols }, {
			colX:add(item: curX);
			curX: curX + arrangedColW:get(index: cxIdx) + colGapPx;
			cxIdx: cxIdx + 1;
		});

		local Array of Int is rowY: Array();
		local Int is curY: bounds:y;
		local Int is ryIdx: 0;
		while({ ryIdx < rows }, {
			rowY:add(item: curY);
			local Int is rh: if({ ryIdx < rowHeightsPx:length() }, { rowHeightsPx:get(index: ryIdx) }, { 0 });
			curY: curY + rh + rowGapPx;
			ryIdx: ryIdx + 1;
		});

		local Int is i: 0;
		while({ i < count }, {
			local Int is r: i / cols;
			local Int is col: i - (r * cols);
			local SewNode is ch: children:get(index: i);
			local Int is cellW: arrangedColW:get(index: col);
			local Int is rowH: if({ r < rowHeightsPx:length() }, { rowHeightsPx:get(index: r) }, { ch:desiredSize:height });
			local Int is childH: if({ expandRows }, { rowH }, { ch:desiredSize:height });
			local Int is childY: if({ expandRows }, { rowY:get(index: r) }, { rowY:get(index: r) + (rowH - childH) / 2 });
			ch:arrange(bounds: Rect(x: colX:get(index: col), y: childY, width: cellW, height: childH));
			i: i + 1;
		});
	}

	replace Function is paint(DrawContext is ctx){
		times(count: children:length(), worker: local Function(Int is i){
			children:get(index: i):paint(ctx: ctx);
		});
	}

	replace Function is paintOverlay(DrawContext is ctx){
		times(count: children:length(), worker: local Function(Int is i){
			children:get(index: i):paintOverlay(ctx: ctx);
		});
	}

	replace Function of Boolean is closePopupsOutside(Int is x, Int is y){
		local Boolean is closed: false;
		local Int is i: 0;
		while({ i < children:length() }, {
			if({ children:get(index: i):closePopupsOutside(x: x, y: y) }, { closed: true; });
			i: i + 1;
		});
		return closed;
	}

	replace Function of Boolean is onOverlayPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onOverlayPointerClickMod(x: x, y: y, mods: mods) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerMove(Int is x, Int is y){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onOverlayPointerMove(x: x, y: y) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerDrag(Int is x, Int is y, Int is mods: 0){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onOverlayPointerDrag(x: x, y: y, mods: mods) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerUp(Int is x, Int is y){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onOverlayPointerUp(x: x, y: y) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onScroll(deltaY: deltaY) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onScrollX(Int is deltaX){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onScrollX(deltaX: deltaX) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is blocksPointerAt(Int is x, Int is y){
		if({ pointerTransparent }, { return false; });
		if({ :containsPoint(x: x, y: y) }, { return true; });
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):blocksPointerAt(x: x, y: y) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	local Function of Int is childIndexAt(Int is x, Int is y){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			local SewNode is ch: children:get(index: i);
			if({ ch:blocksPointerAt(x: x, y: y) }, {
				return i;
			});
			i: i - 1;
		});
		return -1;
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Int is idx: :childIndexAt(x: x, y: y);
		if({ idx >= 0 }, {
			dragChildIdx: idx;
			return children:get(index: idx):onPointerClickMod(x: x, y: y, mods: mods);
		});
		return false;
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return false; });
		local Int is idx: :childIndexAt(x: x, y: y);
		if({ idx >= 0 }, {
			return children:get(index: idx):onRightClickMod(x: x, y: y, mods: mods);
		});
		return false;
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is changed: false;
		local Boolean is blocked: false;
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			local SewNode is ch: children:get(index: i);
			if({ !blocked }, {
				if({ ch:onPointerMove(x: x, y: y) }, { changed: true; });
				if({ ch:blocksPointerAt(x: x, y: y) }, { blocked: true; });
			}, {
				ch:clearHover();
			});
			i: i - 1;
		});
		return changed;
	}

	replace Function is clearHover(){
		times(count: children:length(), worker: local Function(Int is i){
			children:get(index: i):clearHover();
		});
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ dragChildIdx >= 0 && dragChildIdx < children:length() }, {
			return children:get(index: dragChildIdx):onPointerDrag(x: x, y: y, mods: mods);
		});
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return false; });
		local Int is idx: :childIndexAt(x: x, y: y);
		if({ idx >= 0 }, {
			dragChildIdx: idx;
			return children:get(index: idx):onPointerDrag(x: x, y: y, mods: mods);
		});
		return false;
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		if({ dragChildIdx >= 0 && dragChildIdx < children:length() }, {
			local Int is idx: dragChildIdx;
			dragChildIdx: -1;
			return children:get(index: idx):onPointerUp(x: x, y: y);
		});
		local Boolean is changed: false;
		times(count: children:length(), worker: local Function(Int is i){
			if({ children:get(index: i):onPointerUp(x: x, y: y) }, { changed: true; });
		});
		return changed;
	}

	replace Function of Boolean is tick(Int is nowMs){
		local Boolean is changed: false;
		times(count: children:length(), worker: local Function(Int is i){
			if({ children:get(index: i):tick(nowMs: nowMs) }, { changed: true; });
		});
		return changed;
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onKey(key: key, mods: mods) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onText(ch: ch, mods: mods) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function is collectFocusables(Array of SewNode is out){
		local Int is i: 0;
		while({ i < children:length() }, {
			local SewNode is ch: children:get(index: i);
			if({ ch:canFocus() }, { out:add(item: ch); }, { ch:collectFocusables(out: out); });
			i: i + 1;
		});
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		if({ !:containsPoint(x: x, y: y) }, { return ''; });
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			local String is tip: children:get(index: i):tooltipAt(x: x, y: y);
			if({ tip != '' }, { return tip; });
			i: i - 1;
		});
		return tooltip;
	}
}
