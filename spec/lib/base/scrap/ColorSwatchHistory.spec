#! Package base:scrap
#! Standalone color swatch history strip/grid widget with optional custom palette and click selection.

Class of SewNode is ColorSwatchHistory{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', Color],
		['base', 'fabric', DrawContext]
	];

	Array of Color is colors: Array();
	Int is maxColors: 12;
	Float is swatchSizePt: 18.0;
	Int is hoverIdx: -1;
	Function is onSelect: local Function(Color is _c){};

	replace Function is init(
		Array of Color is colors: Array(),
		Int is maxColors: 12,
		Float is swatchSizePt: 18.0,
		Function is onSelect: local Function(Color is _c){}
	){
		:colors: colors;
		:maxColors: if({ maxColors > 0 }, { maxColors }, { 12 });
		:swatchSizePt: swatchSizePt;
		:hoverIdx: -1;
		:onSelect: onSelect;
	}

	Function is addColor(Color is c){
		local Int is targetArgb: c:toArgb();
		local Array of Color is next: Array([c]);
		local Int is i: 0;
		while({ i < colors:length() && next:length() < maxColors }, {
			local Color is existing: colors:get(index: i);
			if({ existing:toArgb() != targetArgb }, {
				next:add(item: existing);
			});
			i: i + 1;
		});
		:colors: next;
		invalidate();
	}

	local Function of Int is swatchPx(){
		local Int is px: activeScale:px(pt: swatchSizePt);
		return if({ px < 12 }, { 12 }, { px });
	}

	local Function of Int is gapPx(){
		local Int is g: activeScale:px(pt: activeTheme:paddingSmallPt);
		return if({ g < 3 }, { 3 }, { g });
	}

	local Function of Int is colsForWidth(Int is availW, Int is sw, Int is gap){
		if({ availW <= sw }, { return 1; });
		local Int is cols: (availW + gap) / (sw + gap);
		if({ cols < 1 }, { cols: 1; });
		if({ cols > 8 }, { cols: 8; });
		return cols;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is n: colors:length();
		if({ n == 0 }, {
			desiredSize: Size(width: c:clampW(w: 0), height: c:clampH(h: 0));
			return desiredSize;
		});
		local Int is sw: :swatchPx();
		local Int is gap: :gapPx();
		local Int is cols: :colsForWidth(availW: c:maxW, sw: sw, gap: gap);
		if({ cols > n }, { cols: n; });
		local Int is rows: (n + cols - 1) / cols;
		local Int is w: cols * sw + (cols - 1) * gap;
		local Int is h: rows * sw + (rows - 1) * gap;
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	local Function of Int is indexAt(Int is x, Int is y){
		local Rect is b: bounds();
		local Int is n: colors:length();
		if({ n == 0 || x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return -1; });
		local Int is sw: :swatchPx();
		local Int is gap: :gapPx();
		local Int is cols: :colsForWidth(availW: b:width, sw: sw, gap: gap);
		local Int is cell: sw + gap;
		local Int is col: (x - b:x) / cell;
		local Int is row: (y - b:y) / cell;
		if({ col < 0 || col >= cols || row < 0 }, { return -1; });
		if({ (x - b:x) - col * cell >= sw || (y - b:y) - row * cell >= sw }, { return -1; });
		local Int is idx: row * cols + col;
		if({ idx >= 0 && idx < n }, { return idx; });
		return -1;
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Int is nextHover: :indexAt(x: x, y: y);
		if({ nextHover != hoverIdx }, {
			:hoverIdx: nextHover;
			invalidate();
			return true;
		});
		return false;
	}

	replace Function is clearHover(){
		if({ hoverIdx >= 0 }, {
			:hoverIdx: -1;
			invalidate();
		});
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Int is idx: :indexAt(x: x, y: y);
		if({ idx >= 0 && idx < colors:length() }, {
			local Function is cb: onSelect;
			cb(colors:get(index: idx));
			return true;
		});
		return false;
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		local Int is idx: :indexAt(x: x, y: y);
		if({ idx >= 0 && idx < colors:length() }, {
			return colors:get(index: idx):toHex();
		});
		return '';
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		local Int is n: colors:length();
		if({ n == 0 || b:width <= 0 || b:height <= 0 }, { return; });
		local Int is sw: :swatchPx();
		local Int is gap: :gapPx();
		local Int is cols: :colsForWidth(availW: b:width, sw: sw, gap: gap);
		local Int is cell: sw + gap;
		local Int is bw: activeTheme:borderPx(scaleFactor: activeScale:factor);
		local Int is i: 0;
		while({ i < n }, {
			local Int is col: i % cols;
			local Int is row: i / cols;
			local Int is sx: b:x + col * cell;
			local Int is sy: b:y + row * cell;
			ctx:fillRect(x: sx, y: sy, w: sw, h: sw, color: colors:get(index: i):toArgb());
			if({ bw > 0 }, {
				local Int is borderCol: if({ i == hoverIdx }, { activeTheme:textAccent }, { activeTheme:buttonBorder });
				ctx:strokeRect(x: sx, y: sy, w: sw, h: sw, color: borderCol, thickness: bw);
			});
			i: i + 1;
		});
	}
}
