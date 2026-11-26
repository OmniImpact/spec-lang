#! Package base:sew
#! Vertical layout container stacking children top-to-bottom.

Class of SewNode is Column{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints]
	];

	Array of SewNode is children: Array();
	Array of Boolean is flexFlags: Array();

	replace Function is init(){
		children: Array();
		flexFlags: Array();
	}

	## Appends a child node; if [expand] is true, it fills remaining vertical space.
	Function is addChild(SewNode is child, Boolean is expand: false){
		children:add(item: child);
		flexFlags:add(item: expand);
	}

	replace Function of Size is measure(Constraints is c){
		local Int is totalH: 0;
		local Int is maxW: 0;
		local Int is count: children:length();
		local Constraints is loose: Constraints(minW: 0, maxW: c:maxW, minH: 0, maxH: c:maxH);
		times(count: count, worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			local Size is sz: ch:measure(c: loose);
			if({ sz:width > maxW }, { maxW: sz:width; });
			totalH: totalH + sz:height;
		});
		desiredSize: Size(width: c:clampW(w: maxW), height: c:clampH(h: totalH));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is count: children:length();
		local Int is fixedH: 0;
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
			curY: curY + h;
		});
	}
}
