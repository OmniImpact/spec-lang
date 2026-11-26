#! Package base:scrap
#! Simple filled rectangular surface widget participating in Sew layout.

Class of SewNode is ScrapPanel{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', DrawContext]
	];

	Int is bgColor: -1;

	replace Function is init(Int is bgColor: -1){
		:bgColor: bgColor;
	}

	replace Function of Size is measure(Constraints is c){
		desiredSize: Size(width: c:maxW, height: c:maxH);
		return desiredSize;
	}

	Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: bgColor);
	}
}
