#! Package base:sew
#! Horizontal layout container arranging children left-to-right with optional point gap.

Class of MultiChildNode is Row{
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

	Array of Boolean is flexFlags: Array();
	Float is gapPt: 0.0;

	replace Function is init(Array of SewNode is children: Array(), Float is gapPt: 0.0, Array of Boolean is flexFlags: Array()){
		:children: children;
		:gapPt: gapPt;
		if({ flexFlags:length() == children:length() }, {
			:flexFlags: flexFlags;
		}, {
			:flexFlags: Array();
			times(count: children:length(), worker: local Function(Int is _i){
				:flexFlags:add(item: false);
			});
		});
	}

	Function is addChild(SewNode is child, Boolean is expand: false){
		children:add(item: child);
		flexFlags:add(item: expand);
	}

	replace Function of Size is measure(Constraints is c){
		local Int is count: children:length();
		local Int is gapPx: activeScale:px(pt: gapPt);
		local Int is totalGap: if({ count > 1 }, { gapPx * (count - 1) }, { 0 });
		local Int is fixedW: 0;
		local Int is flexCount: 0;
		local Int is maxH: 0;
		local Constraints is loose: Constraints(minW: 0, maxW: c:maxW, minH: 0, maxH: c:maxH);
		times(count: count, worker: local Function(Int is i){
			local Boolean is isFlex: i < flexFlags:length() && flexFlags:get(index: i);
			if({ isFlex }, {
				flexCount: flexCount + 1;
			}, {
				local Size is sz: children:get(index: i):measure(c: loose);
				fixedW: fixedW + sz:width;
				if({ sz:height > maxH }, { maxH: sz:height; });
			});
		});
		local Int is totalW: fixedW + totalGap;
		if({ flexCount > 0 }, {
			local Constraints is flexC: loose;
			if({ c:isBoundedW() }, {
				local Int is remW: c:maxW - fixedW - totalGap;
				if({ remW < 0 }, { remW: 0; });
				local Int is eachW: remW / flexCount;
				flexC: Constraints(minW: eachW, maxW: eachW, minH: 0, maxH: c:maxH);
			});
			times(count: count, worker: local Function(Int is i){
				if({ i < flexFlags:length() && flexFlags:get(index: i) }, {
					local Size is sz: children:get(index: i):measure(c: flexC);
					totalW: totalW + sz:width;
					if({ sz:height > maxH }, { maxH: sz:height; });
				});
			});
		});
		desiredSize: Size(width: c:clampW(w: totalW), height: c:clampH(h: maxH));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is count: children:length();
		local Int is gapPx: activeScale:px(pt: gapPt);
		local Boolean is hasFlex: false;
		times(count: count, worker: local Function(Int is i){
			if({ i < flexFlags:length() && flexFlags:get(index: i) }, { hasFlex: true; });
		});
		local Int is curX: bounds:x;
		times(count: count, worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			local Int is w: ch:desiredSize:width;
			local Boolean is isFlex: i < flexFlags:length() && flexFlags:get(index: i);
			local Int is h: if({ isFlex }, { bounds:height }, { ch:desiredSize:height });
			if({ h > bounds:height }, { h: bounds:height; });
			local Int is cy: if({ hasFlex }, { bounds:y }, { bounds:y + (bounds:height - h) / 2 });
			ch:arrange(bounds: Rect(x: curX, y: cy, width: w, height: h));
			curX: curX + w + gapPx;
		});
	}
}
