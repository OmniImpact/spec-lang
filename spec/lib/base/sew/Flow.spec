#! Package base:sew
#! Wrapping flow layout container arranging children into rows or columns that wrap when exceeding main-axis constraints.

Class of MultiChildNode is Flow{
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

	Boolean is horizontal: true;
	Float is gapPt: 6.0;
	Float is lineGapPt: 6.0;
	Float is minItemPt: 0.0;
	Float is maxItemPt: 0.0;
	Float is maxLinePt: 0.0;
	Boolean is fill: false;
	Boolean is stretchCross: false;

	replace Function is init(
		Array of SewNode is children: Array(),
		Boolean is horizontal: true,
		Float is gapPt: 6.0,
		Float is lineGapPt: 6.0,
		Float is minItemPt: 0.0,
		Float is maxItemPt: 0.0,
		Float is maxLinePt: 0.0,
		Boolean is fill: false,
		Boolean is stretchCross: false
	){
		:children: children;
		:horizontal: horizontal;
		:gapPt: gapPt;
		:lineGapPt: lineGapPt;
		:minItemPt: minItemPt;
		:maxItemPt: maxItemPt;
		:maxLinePt: maxLinePt;
		:fill: fill;
		:stretchCross: stretchCross;
	}

	## Appends a child node to the flow layout.
	Function is addChild(SewNode is child){
		children:add(item: child);
		invalidate();
	}

	local Function of Constraints is makeItemConstraints(Int is minMain, Int is maxMain, Constraints is baseC){
		if({ horizontal }, {
			return Constraints(minW: minMain, maxW: maxMain, minH: 0, maxH: baseC:maxH);
		});
		return Constraints(minW: 0, maxW: baseC:maxW, minH: minMain, maxH: maxMain);
	}

	local Function of Int is distributeFill(
		Int is lineStart,
		Int is lineEnd,
		Int is extra,
		Int is maxItemPx,
		Array of Int is itemMains
	){
		local Int is lineCount: lineEnd - lineStart + 1;
		if({ lineCount <= 0 || extra <= 0 }, { return 0; });

		if({ maxItemPx <= 0 }, {
			local Int is each: extra / lineCount;
			local Int is rem: extra - (each * lineCount);
			local Int is k: lineStart;
			while({ k <= lineEnd }, {
				local Int is add: each;
				if({ k - lineStart < rem }, { add: add + 1; });
				itemMains:set(index: k, item: itemMains:get(index: k) + add);
				k: k + 1;
			});
			return extra;
		});

		local Int is remExtra: extra;
		local Int is distributed: 0;
		local Boolean is progressing: true;
		while({ remExtra > 0 && progressing }, {
			local Int is eligCount: 0;
			local Int is k: lineStart;
			while({ k <= lineEnd }, {
				if({ itemMains:get(index: k) < maxItemPx }, { eligCount: eligCount + 1; });
				k: k + 1;
			});
			if({ eligCount == 0 }, {
				progressing: false;
			}, {
				local Int is share: remExtra / eligCount;
				if({ share < 1 }, { share: 1; });
				local Int is passUsed: 0;
				k: lineStart;
				while({ k <= lineEnd && remExtra > 0 }, {
					local Int is curM: itemMains:get(index: k);
					local Int is cap: maxItemPx - curM;
					if({ cap > 0 }, {
						local Int is add: if({ cap < share }, { cap }, { share });
						if({ add > remExtra }, { add: remExtra; });
						itemMains:set(index: k, item: curM + add);
						remExtra: remExtra - add;
						passUsed: passUsed + add;
						distributed: distributed + add;
					});
					k: k + 1;
				});
				if({ passUsed == 0 }, { progressing: false; });
			});
		});
		return distributed;
	}

	local Function of Size is runFlow(
		Int is availMain,
		Boolean is mainBounded,
		Constraints is baseC,
		Boolean is applyBounds,
		Int is originX,
		Int is originY
	){
		local Int is count: children:length();
		if({ count == 0 }, { return Size(width: 0, height: 0); });

		local Int is gapPx: activeScale:px(pt: gapPt);
		local Int is lineGapPx: activeScale:px(pt: lineGapPt);
		local Int is minItemPx: if({ minItemPt > 0.0 }, { activeScale:px(pt: minItemPt) }, { 0 });
		local Int is maxItemPx: if({ maxItemPt > 0.0 }, { activeScale:px(pt: maxItemPt) }, { 0 });
		local Int is maxLinePx: if({ maxLinePt > 0.0 }, { activeScale:px(pt: maxLinePt) }, { 0 });

		local Boolean is effBounded: mainBounded;
		local Int is effAvailMain: availMain;
		if({ maxLinePx > 0 }, {
			effBounded: true;
			if({ !mainBounded || maxLinePx < availMain }, { effAvailMain: maxLinePx; });
		});

		local Int is itemMaxMain: if({ horizontal }, { baseC:maxW }, { baseC:maxH });
		if({ maxItemPx > 0 }, {
			itemMaxMain: if({ effBounded && effAvailMain < maxItemPx }, { effAvailMain }, { maxItemPx });
		}, {
			if({ effBounded }, { itemMaxMain: effAvailMain; });
		});
		local Int is itemMinMain: minItemPx;
		if({ itemMaxMain > 0 && itemMinMain > itemMaxMain }, { itemMinMain: itemMaxMain; });
		local Constraints is itemC: :makeItemConstraints(minMain: itemMinMain, maxMain: itemMaxMain, baseC: baseC);

		local Array of Int is itemMains: Array();
		local Array of Int is itemCrosses: Array();
		local Int is idx: 0;
		while({ idx < count }, {
			local Size is sz: children:get(index: idx):measure(c: itemC);
			local Int is m: if({ horizontal }, { sz:width }, { sz:height });
			local Int is cr: if({ horizontal }, { sz:height }, { sz:width });
			if({ effBounded && effAvailMain > 0 && m > effAvailMain }, { m: effAvailMain; });
			itemMains:add(item: m);
			itemCrosses:add(item: cr);
			idx: idx + 1;
		});

		local Int is curCross: if({ horizontal }, { originY }, { originX });
		local Int is maxLineMain: 0;
		local Int is totalCross: 0;
		local Int is lineIdx: 0;
		local Int is i: 0;

		while({ i < count }, {
			local Int is lineStart: i;
			local Int is lineEnd: i;
			local Int is lineMainUsed: itemMains:get(index: i);
			local Int is j: i + 1;
			local Boolean is fits: true;
			while({ j < count && fits }, {
				local Int is nextM: itemMains:get(index: j);
				if({ effBounded && lineMainUsed + gapPx + nextM > effAvailMain }, {
					fits: false;
				}, {
					lineMainUsed: lineMainUsed + gapPx + nextM;
					lineEnd: j;
					j: j + 1;
				});
			});

			if({ fill && effBounded && effAvailMain > lineMainUsed }, {
				local Array of Int is oldMains: Array();
				local Int is k0: lineStart;
				while({ k0 <= lineEnd }, {
					oldMains:add(item: itemMains:get(index: k0));
					k0: k0 + 1;
				});
				local Int is added: :distributeFill(
					lineStart: lineStart, lineEnd: lineEnd,
					extra: effAvailMain - lineMainUsed, maxItemPx: maxItemPx, itemMains: itemMains
				);
				lineMainUsed: lineMainUsed + added;
				local Int is k1: lineStart;
				while({ k1 <= lineEnd }, {
					local Int is newM: itemMains:get(index: k1);
					if({ newM != oldMains:get(index: k1 - lineStart) }, {
						local Constraints is tightC: :makeItemConstraints(minMain: newM, maxMain: newM, baseC: baseC);
						local Size is rsz: children:get(index: k1):measure(c: tightC);
						itemCrosses:set(index: k1, item: if({ horizontal }, { rsz:height }, { rsz:width }));
					});
					k1: k1 + 1;
				});
			});

			local Int is lineMaxCross: 0;
			local Int is kc: lineStart;
			while({ kc <= lineEnd }, {
				local Int is cr: itemCrosses:get(index: kc);
				if({ cr > lineMaxCross }, { lineMaxCross: cr; });
				kc: kc + 1;
			});

			if({ lineMainUsed > maxLineMain }, { maxLineMain: lineMainUsed; });

			if({ applyBounds }, {
				local Int is curMain: if({ horizontal }, { originX }, { originY });
				local Int is ka: lineStart;
				while({ ka <= lineEnd }, {
					local SewNode is ch: children:get(index: ka);
					local Int is m: itemMains:get(index: ka);
					local Int is cr: itemCrosses:get(index: ka);
					local Int is effCr: if({ stretchCross }, { lineMaxCross }, { cr });
					if({ effCr > lineMaxCross }, { effCr: lineMaxCross; });
					local Int is crossPos: curCross + (lineMaxCross - effCr) / 2;
					if({ horizontal }, {
						ch:arrange(bounds: Rect(x: curMain, y: crossPos, width: m, height: effCr));
					}, {
						ch:arrange(bounds: Rect(x: crossPos, y: curMain, width: effCr, height: m));
					});
					curMain: curMain + m + gapPx;
					ka: ka + 1;
				});
			});

			if({ lineIdx > 0 }, { totalCross: totalCross + lineGapPx; });
			totalCross: totalCross + lineMaxCross;
			curCross: curCross + lineMaxCross + lineGapPx;
			lineIdx: lineIdx + 1;
			i: lineEnd + 1;
		});

		if({ horizontal }, {
			return Size(width: maxLineMain, height: totalCross);
		});
		return Size(width: totalCross, height: maxLineMain);
	}

	replace Function of Size is measure(Constraints is c){
		local Boolean is bounded: if({ horizontal }, { c:isBoundedW() }, { c:isBoundedH() });
		local Int is avail: if({ bounded }, { if({ horizontal }, { c:maxW }, { c:maxH }) }, { 0 });
		local Size is sz: :runFlow(
			availMain: avail, mainBounded: bounded, baseC: c,
			applyBounds: false, originX: 0, originY: 0
		);
		desiredSize: Size(width: c:clampW(w: sz:width), height: c:clampH(h: sz:height));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is avail: if({ horizontal }, { bounds:width }, { bounds:height });
		local Constraints is c: Constraints(minW: 0, maxW: bounds:width, minH: 0, maxH: bounds:height);
		:runFlow(
			availMain: avail, mainBounded: true, baseC: c,
			applyBounds: true, originX: bounds:x, originY: bounds:y
		);
	}
}
