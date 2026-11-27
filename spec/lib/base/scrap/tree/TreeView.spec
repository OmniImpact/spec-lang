#! Package base:scrap
#! Generic scrollable tree widget supporting expandable/collapsible nodes, lazy loading, selection, and activation.

Class of SewNode is TreeView{
	replace [String] is namespace: ['base', 'scrap', 'tree'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', Time],
		['base', 'struct', Array],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'fabric', 'svg', SvgRenderer],
		['base', 'scrap', 'tree', TreeNode]
	];

	Array of TreeNode is roots: Array();
	Array of TreeNode is flatNodes: Array();
	Array of Int is flatDepths: Array();
	Array of Boolean is flatIsLast: Array();
	Array of Array of Boolean is flatAncestors: Array();
	String is selectedId: '';
	Int is hoverIdx: -1;
	String is lastClickId: '';
	Int is lastClickMs: 0;
	Time is clock: Time();
	String is plusIconSvg: '';
	String is minusIconSvg: '';
	Function is onSelect: local Function(TreeNode is _node){};
	Function is onActivate: local Function(TreeNode is _node){};
	Function is onToggle: local Function(TreeNode is _node){};

	replace Function is init(
		Array of TreeNode is roots: Array(),
		String is plusIconSvg: '',
		String is minusIconSvg: '',
		Function is onSelect: local Function(TreeNode is _node){},
		Function is onActivate: local Function(TreeNode is _node){},
		Function is onToggle: local Function(TreeNode is _node){}
	){
		:roots: roots;
		:plusIconSvg: plusIconSvg;
		:minusIconSvg: minusIconSvg;
		:onSelect: onSelect;
		:onActivate: onActivate;
		:onToggle: onToggle;
		:rebuildFlat();
	}

	Function is setRoots(Array of TreeNode is roots){
		:roots: roots;
		:hoverIdx: -1;
		:rebuildFlat();
		invalidate();
	}

	local Function is appendFlat(TreeNode is node, Int is depth, Boolean is isLast, Array of Boolean is ancestors){
		flatNodes:add(item: node);
		flatDepths:add(item: depth);
		flatIsLast:add(item: isLast);
		local Array of Boolean is ancCopy: Array();
		local Int is ai: 0;
		while({ ai < ancestors:length() }, {
			ancCopy:add(item: ancestors:get(index: ai));
			ai: ai + 1;
		});
		flatAncestors:add(item: ancCopy);
		if({ node:expandable && node:expanded }, {
			local Array of Boolean is nextAnc: Array();
			ai: 0;
			while({ ai < ancCopy:length() }, {
				nextAnc:add(item: ancCopy:get(index: ai));
				ai: ai + 1;
			});
			nextAnc:add(item: !isLast);
			local Int is chLen: node:children:length();
			local Int is i: 0;
			while({ i < chLen }, {
				:appendFlat(
					node: node:children:get(index: i),
					depth: depth + 1,
					isLast: (i == chLen - 1),
					ancestors: nextAnc
				);
				i: i + 1;
			});
		});
	}

	Function is rebuildFlat(){
		:flatNodes: Array();
		:flatDepths: Array();
		:flatIsLast: Array();
		:flatAncestors: Array();
		local Int is rLen: roots:length();
		local Int is i: 0;
		while({ i < rLen }, {
			:appendFlat(
				node: roots:get(index: i),
				depth: 0,
				isLast: (i == rLen - 1),
				ancestors: Array()
			);
			i: i + 1;
		});
	}

	local Function of Int is rowHeightPx(){
		local Int is h: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 15.0) + activeTheme:paddingPt);
		return if({ h < 14 }, { 14 }, { h });
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 15.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Int is indentPx(){
		local Int is ind: activeScale:px(pt: 12.0);
		return if({ ind < 10 }, { 10 }, { ind });
	}

	replace Function of Size is measure(Constraints is c){
		local Int is rowH: :rowHeightPx();
		local Int is fpx: :fontPx();
		local Int is ind: :indentPx();
		local Int is padX: activeScale:px(pt: activeTheme:paddingSmallPt);
		if({ padX < 2 }, { padX: 2; });
		local Int is maxW: c:minW;
		local Int is i: 0;
		while({ i < flatNodes:length() }, {
			local TreeNode is node: flatNodes:get(index: i);
			local Int is depth: flatDepths:get(index: i);
			local Int is labelX: padX + (depth + 1) * ind + 2;
			local Int is rw: labelX + DrawContext:measureWidth(text: node:label, pixelHeight: fpx) + padX * 2;
			if({ rw > maxW }, { maxW: rw; });
			i: i + 1;
		});
		local Int is totalH: flatNodes:length() * rowH;
		local Int is finalH: if({ totalH > c:minH }, { totalH }, { c:minH });
		desiredSize: Size(width: maxW, height: finalH);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: activeTheme:panelBg);

		local Int is rowH: :rowHeightPx();
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is indentPx: :indentPx();
		local Int is padX: activeScale:px(pt: activeTheme:paddingSmallPt);
		if({ padX < 2 }, { padX: 2; });
		local Int is boxSz: activeScale:px(pt: 9.0);
		if({ boxSz < 9 }, { boxSz: 9; });
		if({ (boxSz & 1) == 0 }, { boxSz: boxSz + 1; });
		local Int is halfBox: boxSz / 2;
		local Int is lineCol: activeTheme:textMuted;

		local Int is i: 0;
		while({ i < flatNodes:length() }, {
			local Int is ry: b:y + (i * rowH);
				local TreeNode is node: flatNodes:get(index: i);
				local Int is depth: flatDepths:get(index: i);
				local Boolean is isLast: flatIsLast:get(index: i);
				local Array of Boolean is anc: flatAncestors:get(index: i);
				local Boolean is isSel: (selectedId != '' && node:id == selectedId);
				local Int is rowBg: activeTheme:panelBg;
				if({ isSel }, {
					rowBg: activeTheme:activeBg;
					ctx:fillRect(x: b:x, y: ry, w: b:width, h: rowH, color: rowBg);
				}, {
					if({ hoverIdx == i }, {
						rowBg: activeTheme:hoverBg;
						ctx:fillRect(x: b:x, y: ry, w: b:width, h: rowH, color: rowBg);
					});
				});

				local Int is linePx: activeTheme:linePx(scaleFactor: activeScale:factor);
				local Int is dotStep: activeScale:px(pt: 3.0);
				if({ dotStep < 2 }, { dotStep: 2; });
				local Int is cy: ry + rowH / 2;
				# Solid vertical guide lines for ancestor depths with remaining siblings
				local Int is d: 0;
				while({ d < depth && d < anc:length() }, {
					if({ anc:get(index: d) }, {
						local Int is ax: b:x + padX + d * indentPx + indentPx / 2;
						ctx:fillRect(x: ax, y: ry, w: linePx, h: rowH, color: lineCol);
					});
					d: d + 1;
				});

				# Vertical connector at this node's own depth
				local Int is cx: b:x + padX + depth * indentPx + indentPx / 2;
				if({ depth > 0 || i > 0 }, {
					ctx:fillRect(x: cx, y: ry, w: linePx, h: cy - ry + linePx, color: lineCol);
				});
				if({ !isLast }, {
					ctx:fillRect(x: cx, y: cy, w: linePx, h: ry + rowH - cy, color: lineCol);
				});

				local Int is labelX: b:x + padX + (depth + 1) * indentPx + 2;
				local Int is hEnd: labelX - 4;
				if({ node:expandable }, {
					# Solid horizontal line to folder label
					if({ hEnd > cx }, {
						ctx:fillRect(x: cx, y: cy, w: hEnd - cx, h: linePx, color: lineCol);
					});
					local Int is bx: cx - halfBox;
					local Int is by: cy - halfBox;
					ctx:fillRect(x: bx, y: by, w: boxSz, h: boxSz, color: rowBg);
					local String is boxSvg: if({ node:expanded }, { minusIconSvg }, { plusIconSvg });
					if({ boxSvg != '' }, {
						SvgRenderer:shared:draw(ctx: ctx, svgSrc: boxSvg, x: bx, y: by, widthPx: boxSz, heightPx: boxSz, tintColor: activeTheme:textPrimary, useTint: true);
					}, {
						ctx:strokeRect(x: bx, y: by, w: boxSz, h: boxSz, color: lineCol, thickness: linePx);
						local Int is arm: boxSz - 4;
						if({ arm < 3 }, { arm: 3; });
						local Int is armOff: (boxSz - arm) / 2;
						ctx:fillRect(x: bx + armOff, y: cy - linePx / 2, w: arm, h: linePx, color: activeTheme:textPrimary);
						if({ !node:expanded }, {
							ctx:fillRect(x: cx - linePx / 2, y: by + armOff, w: linePx, h: arm, color: activeTheme:textPrimary);
						});
					});
				}, {
					# Dotted horizontal line connecting vertical line to file label
					local Int is dx: cx + dotStep;
					while({ dx < hEnd }, {
						ctx:fillRect(x: dx, y: cy, w: linePx, h: linePx, color: lineCol);
						dx: dx + dotStep;
					});
				});

				local Int is ty: ry + (rowH - th) / 2;
				ctx:drawText(x: labelX, y: ty, text: node:label, color: activeTheme:textPrimary, pixelHeight: fpx, bold: node:expandable);
				i: i + 1;
		});
	}

	local Function of Int is rowAt(Int is x, Int is y){
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return -1; });
		local Int is rowH: :rowHeightPx();
		if({ rowH <= 0 }, { return -1; });
		local Int is idx: (y - b:y) / rowH;
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

	replace Function is clearHover(){
		if({ hoverIdx >= 0 }, {
			hoverIdx: -1;
			invalidate();
		});
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Int is idx: :rowAt(x: x, y: y);
		if({ idx < 0 || idx >= flatNodes:length() }, { return false; });
		local TreeNode is node: flatNodes:get(index: idx);
		selectedId: node:id;
		local Function is selCb: onSelect;
		selCb(node);
		if({ node:expandable }, {
			:lastClickId: '';
			:lastClickMs: 0;
			node:expanded: !node:expanded;
			local Function is togCb: onToggle;
			togCb(node);
			:rebuildFlat();
		}, {
			local Int is nowMs: clock:monotonicMs();
			local Boolean is isDouble: (node:id == lastClickId) && ((nowMs - lastClickMs) <= 450);
			if({ isDouble }, {
				:lastClickId: '';
				:lastClickMs: 0;
				local Function is actCb: onActivate;
				actCb(node);
			}, {
				:lastClickId: node:id;
				:lastClickMs: nowMs;
			});
		});
		invalidate();
		return true;
	}
}
