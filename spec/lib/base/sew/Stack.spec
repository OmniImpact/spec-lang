#! Package base:sew
#! Z-order overlay layout container stacking children on top of each other.

Class of SewNode is Stack{
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

	replace Function is init(){
		children: Array();
	}

	## Appends a child node in back-to-front z-order.
	Function is addChild(SewNode is child){
		children:add(item: child);
	}

	replace Function of Size is measure(Constraints is c){
		local Int is maxW: 0;
		local Int is maxH: 0;
		local Constraints is childC: Constraints(minW: 0, maxW: c:maxW, minH: 0, maxH: c:maxH);
		times(count: children:length(), worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			local Size is sz: ch:measure(c: childC);
			if({ sz:width > maxW }, { maxW: sz:width; });
			if({ sz:height > maxH }, { maxH: sz:height; });
		});
		desiredSize: Size(width: c:clampW(w: maxW), height: c:clampH(h: maxH));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		times(count: children:length(), worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			ch:arrange(bounds: bounds);
		});
	}
}
