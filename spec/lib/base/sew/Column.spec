#! Package base:sew
#! Vertical layout container stacking children top-to-bottom with optional point gap.

Class of SewNode is Column{
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

	Array of SewNode is children: Array();
	Array of Boolean is flexFlags: Array();
	Float is gapPt: 0.0;

	replace Function is init(Array of SewNode is children: Array(), Float is gapPt: 0.0){
		:children: children;
		:gapPt: gapPt;
		:flexFlags: Array();
		times(count: children:length(), worker: local Function(Int is _i){
			flexFlags:add(item: false);
		});
	}

	## Appends a child node; if [expand] is true, it fills remaining vertical space.
	Function is addChild(SewNode is child, Boolean is expand: false){
		children:add(item: child);
		flexFlags:add(item: expand);
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		times(count: children:length(), worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			ch:applyTheme(theme: theme);
		});
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		times(count: children:length(), worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			ch:setScale(scale: scale);
		});
	}

	replace Function of Size is measure(Constraints is c){
		local Int is totalH: 0;
		local Int is maxW: 0;
		local Int is count: children:length();
		local Int is gapPx: activeScale:px(pt: gapPt);
		local Constraints is loose: Constraints(minW: 0, maxW: c:maxW, minH: 0, maxH: c:maxH);
		times(count: count, worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			local Size is sz: ch:measure(c: loose);
			if({ sz:width > maxW }, { maxW: sz:width; });
			totalH: totalH + sz:height;
			if({ i > 0 }, { totalH: totalH + gapPx; });
		});
		desiredSize: Size(width: c:clampW(w: maxW), height: c:clampH(h: totalH));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is count: children:length();
		local Int is gapPx: activeScale:px(pt: gapPt);
		local Int is totalGap: if({ count > 1 }, { (count - 1) * gapPx }, { 0 });
		local Int is fixedH: totalGap;
		local Int is flexCount: 0;
		times(count: count, worker: local Function(Int is i){
			if({ flexFlags:get(index: i) }, {
				flexCount: flexCount + 1;
			}, {
				local SewNode is ch: children:get(index: i);
				fixedH: fixedH + ch:desiredSize:height;
			});
		});

		local Int is remH: if({ bounds:height > fixedH }, { bounds:height - fixedH }, { 0 });
		local Int is flexH: if({ flexCount > 0 }, { remH / flexCount }, { 0 });
		local Int is curY: bounds:y;

		times(count: count, worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			local Int is h: if({ flexFlags:get(index: i) }, { flexH }, { ch:desiredSize:height });
			ch:arrange(bounds: Rect(x: bounds:x, y: curY, width: bounds:width, height: h));
			curY: curY + h + gapPx;
		});
	}

	replace Function is paint(DrawContext is ctx){
		times(count: children:length(), worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			ch:paint(ctx: ctx);
		});
	}
}
