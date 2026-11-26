#! Package base:sew
#! Layout container that centers a single child horizontally and vertically.

Class of SewNode is Center{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale]
	];

	SewNode is child: SewNode();
	Float is padXPt: 16.0;

	replace Function is init(SewNode is child, Float is padXPt: 16.0){
		:child: child;
		:padXPt: padXPt;
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		child:applyTheme(theme: theme);
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		child:setScale(scale: scale);
	}

	replace Function of Size is measure(Constraints is c){
		local Int is padPx: activeScale:px(pt: padXPt * 2.0);
		local Constraints is inner: Constraints(
			minW: 0,
			maxW: if({ c:maxW > padPx }, { c:maxW - padPx }, { c:maxW }),
			minH: 0,
			maxH: c:maxH
		);
		local Size is cs: child:measure(c: inner);
		desiredSize: Size(
			width: c:clampW(w: cs:width + padPx),
			height: c:clampH(h: cs:height)
		);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is cw: if({ child:desiredSize:width < bounds:width }, { child:desiredSize:width }, { bounds:width });
		local Int is ch: if({ child:desiredSize:height < bounds:height }, { child:desiredSize:height }, { bounds:height });
		local Int is cx: bounds:x + (bounds:width - cw) / 2;
		local Int is cy: bounds:y + (bounds:height - ch) / 2;
		child:arrange(bounds: Rect(x: cx, y: cy, width: cw, height: ch));
	}

	replace Function is paint(DrawContext is ctx){
		child:paint(ctx: ctx);
	}
}
