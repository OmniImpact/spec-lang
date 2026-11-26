#! Package base:scrap
#! Generic scrollable tree widget supporting expandable/collapsible nodes, lazy loading, selection, and activation.

Class of SewNode is TreeView{
	replace [String] is namespace: ['base', 'scrap'];

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
		['base', 'sew', Scale],
		['base', 'scrap', TreeNode]
	];

	Array of TreeNode is roots: Array();
	Array of TreeNode is flatNodes: Array();
	Array of Int is flatDepths: Array();
	String is selectedId: '';
	Int is hoverIdx: -1;
	Int is scrollY: 0;
	Function is onSelect: local Function(TreeNode is _node){};
	Function is onActivate: local Function(TreeNode is _node){};
	Function is onToggle: local Function(TreeNode is _node){};

	replace Function is init(
		Array of TreeNode is roots: Array(),
		Function is onSelect: local Function(TreeNode is _node){},
		Function is onActivate: local Function(TreeNode is _node){},
		Function is onToggle: local Function(TreeNode is _node){}
	){
		:roots: roots;
		:onSelect: onSelect;
		:onActivate: onActivate;
		:onToggle: onToggle;
		:rebuildFlat();
	}

	Function is setRoots(Array of TreeNode is roots){
		:roots: roots;
		:scrollY: 0;
		:hoverIdx: -1;
		:rebuildFlat();
		invalidate();
	}

	local Function is appendFlat(TreeNode is node, Int is depth){
		flatNodes:add(item: node);
		flatDepths:add(item: depth);
		if({ node:expandable && node:expanded }, {
			local Int is i: 0;
			while({ i < node:children:length() }, {
				:appendFlat(node: node:children:get(index: i), depth: depth + 1);
				i: i + 1;
			});
		});
	}

	Function is rebuildFlat(){
		:flatNodes: Array();
		:flatDepths: Array();
		local Int is i: 0;
		while({ i < roots:length() }, {
			:appendFlat(node: roots:get(index: i), depth: 0);
			i: i + 1;
		});
		:clampScroll();
	}

	local Function of Int is rowHeightPx(){
		local Int is h: activeScale:px(pt: 24.0);
		return if({ h < 18 }, { 18 }, { h });
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: 15.0);
		return if({ px < 11 }, { 11 }, { px });
	}

	local Function is clampScroll(){
		local Rect is b: bounds();
		local Int is totalH: flatNodes:length() * :rowHeightPx();
		local Int is maxScroll: if({ totalH > b:height && b:height > 0 }, { totalH - b:height }, { 0 });
		if({ scrollY < 0 }, { scrollY: 0; });
		if({ scrollY > maxScroll }, { scrollY: maxScroll; });
	}

	replace Function of Size is measure(Constraints is c){
		desiredSize: Size(width: c:clampW(w: c:maxW), height: c:clampH(h: c:maxH));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		:clampScroll();
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: activeTheme:panelBg);
		ctx:setClip(x: b:x, y: b:y, w: b:width, h: b:height);

		local Int is rowH: :rowHeightPx();
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is indentPx: activeScale:px(pt: 14.0);
		local Int is padX: activeScale:px(pt: 8.0);
		local Int is chevronW: activeScale:px(pt: 14.0);

		local Int is firstIdx: if({ rowH > 0 }, { scrollY / rowH }, { 0 });
		local Int is i: firstIdx;
		while({ i < flatNodes:length() }, {
			local Int is ry: b:y + (i * rowH) - scrollY;
			if({ ry >= b:y + b:height }, { i: flatNodes:length(); }, {
				local TreeNode is node: flatNodes:get(index: i);
				local Int is depth: flatDepths:get(index: i);
				local Boolean is isSel: (selectedId != '' && node:id == selectedId);
				if({ isSel }, {
					ctx:fillRect(x: b:x, y: ry, w: b:width, h: rowH, color: activeTheme:activeBg);
				}, {
					if({ hoverIdx == i }, {
						ctx:fillRect(x: b:x, y: ry, w: b:width, h: rowH, color: activeTheme:hoverBg);
					});
				});
				local Int is ix: b:x + padX + depth * indentPx;
				local Int is ty: ry + (rowH - th) / 2;
				if({ node:expandable }, {
					local String is chev: if({ node:expanded }, { 'v' }, { '>' });
					ctx:drawText(x: ix, y: ty, text: chev, color: activeTheme:textMuted, pixelHeight: fpx);
				});
				local Int is textCol: if({ isSel }, { activeTheme:textPrimary }, { if({ node:expandable }, { activeTheme:textPrimary }, { activeTheme:textPrimary }) });
				ctx:drawText(x: ix + chevronW, y: ty, text: node:label, color: textCol, pixelHeight: fpx, bold: node:expandable);
				i: i + 1;
			});
		});

		# Thin vertical scrollbar thumb when content overflows
		local Int is totalH: flatNodes:length() * rowH;
		if({ totalH > b:height && totalH > 0 }, {
			local Int is sbW: activeScale:px(pt: 4.0);
			if({ sbW < 3 }, { sbW: 3; });
			local Int is thumbH: (b:height * b:height) / totalH;
			if({ thumbH < 20 }, { thumbH: 20; });
			local Int is maxScroll: totalH - b:height;
			local Int is thumbY: b:y + ((scrollY * (b:height - thumbH)) / maxScroll);
			ctx:fillRect(x: b:x + b:width - sbW - 2, y: thumbY, w: sbW, h: thumbH, color: activeTheme:toolbarBorder);
		});

		ctx:clearClip();
	}

	local Function of Int is rowAt(Int is x, Int is y){
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return -1; });
		local Int is rowH: :rowHeightPx();
		if({ rowH <= 0 }, { return -1; });
		local Int is idx: (y - b:y + scrollY) / rowH;
		if({ idx >= 0 && idx < flatNodes:length() }, { return idx; });
		return -1;
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Int is nextHover: :rowAt(x: x, y: y);
		if({ nextHover != hoverIdx }, {
			hoverIdx: nextHover;
			invalidate();
			return true;
		});
		return false;
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Int is idx: :rowAt(x: x, y: y);
		if({ idx < 0 || idx >= flatNodes:length() }, { return false; });
		local TreeNode is node: flatNodes:get(index: idx);
		selectedId: node:id;
		local Function is selCb: onSelect;
		selCb(node);
		if({ node:expandable }, {
			node:expanded: !node:expanded;
			local Function is togCb: onToggle;
			togCb(node);
			:rebuildFlat();
		}, {
			local Function is actCb: onActivate;
			actCb(node);
		});
		invalidate();
		return true;
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		local Int is oldScroll: scrollY;
		scrollY: scrollY - (deltaY * :rowHeightPx() / 15);
		if({ deltaY > 0 && scrollY == oldScroll }, { scrollY: oldScroll - :rowHeightPx(); });
		if({ deltaY < 0 && scrollY == oldScroll }, { scrollY: oldScroll + :rowHeightPx(); });
		:clampScroll();
		if({ scrollY != oldScroll }, {
			invalidate();
			return true;
		});
		return false;
	}
}
