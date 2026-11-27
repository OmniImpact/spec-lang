#! Package base:sew
#! 2D row-major grid layout container aligning children into uniform column widths and row heights.

Class of MultiChildNode is Grid{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', MultiChildNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints]
	];

	Int is columns: 2;
	Float is colGapPt: 8.0;
	Float is rowGapPt: 6.0;
	Boolean is equalCols: false;
	Boolean is expandRows: false;
	Array of Boolean is flexCols: Array();
	Array of Int is colWidthsPx: Array();
	Array of Int is rowHeightsPx: Array();

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
}
