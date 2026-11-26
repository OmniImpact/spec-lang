#! Package base:sew
#! Inset container adding padding around a single child `SewNode`.

Class of SewNode is Padding{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints]
	];

	Int is top: 0;
	Int is right: 0;
	Int is bottom: 0;
	Int is left: 0;
	SewNode is child: SewNode();
	Boolean is shrinkToChild: true;

	replace Function is init(
		SewNode is child,
		Int is top: 0,
		Int is right: 0,
		Int is bottom: 0,
		Int is left: 0,
		Boolean is shrinkToChild: true
	){
		:child: child;
		:top: top;
		:right: right;
		:bottom: bottom;
		:left: left;
		:shrinkToChild: shrinkToChild;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is padW: left + right;
		local Int is padH: top + bottom;
		local Size is cs: child:measure(c: c:deflate(dw: padW, dh: padH));
		desiredSize: Size(
			width: c:clampW(w: cs:width + padW),
			height: c:clampH(h: cs:height + padH)
		);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is availW: if({ bounds:width > left + right }, { bounds:width - left - right }, { 0 });
		local Int is availH: if({ bounds:height > top + bottom }, { bounds:height - top - bottom }, { 0 });
		local Int is cw: if({ shrinkToChild && child:desiredSize:width < availW }, { child:desiredSize:width }, { availW });
		local Int is ch: if({ shrinkToChild && child:desiredSize:height < availH }, { child:desiredSize:height }, { availH });
		child:arrange(bounds: Rect(x: bounds:x + left, y: bounds:y + top, width: cw, height: ch));
	}
}
