#! Package base:sew
#! Inset container adding padding around a single child `SewNode`.

Class of SingleChildNode is Padding{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', SingleChildNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', SuitUnit],
		['base', 'sew', Pt]
	];

	Int is top: 0;
	Int is right: 0;
	Int is bottom: 0;
	Int is left: 0;
	Float is padPt: 0.0;
	SuitUnit is pad: Pt(value: 0.0);
	Boolean is hasUnitPad: false;
	Boolean is useThemePad: false;
	Float is padScale: 1.0;
	Boolean is shrinkToChild: true;

	replace Function is init(
		SewNode is child,
		Int is top: 0,
		Int is right: 0,
		Int is bottom: 0,
		Int is left: 0,
		Float is padPt: 0.0,
		SuitUnit is pad: Pt(value: 0.0),
		Boolean is hasUnitPad: false,
		Boolean is useThemePad: false,
		Float is padScale: 1.0,
		Boolean is shrinkToChild: true
	){
		:child: child;
		:top: top;
		:right: right;
		:bottom: bottom;
		:left: left;
		:padPt: padPt;
		:pad: pad;
		:hasUnitPad: hasUnitPad;
		:useThemePad: useThemePad;
		:padScale: padScale;
		:shrinkToChild: shrinkToChild;
	}

	local Function of Int is effSide(Int is fallbackPx){
		if({ useThemePad }, { return activeScale:px(pt: activeTheme:padPt(pct: padScale)); });
		if({ hasUnitPad }, { return :unitPx(unit: pad); });
		if({ padPt > 0.0 }, { return activeScale:px(pt: padPt); });
		return fallbackPx;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is pl: :effSide(fallbackPx: left);
		local Int is pr: :effSide(fallbackPx: right);
		local Int is pt: :effSide(fallbackPx: top);
		local Int is pb: :effSide(fallbackPx: bottom);
		local Int is padW: pl + pr;
		local Int is padH: pt + pb;
		local Size is cs: child:measure(c: c:deflate(dw: padW, dh: padH));
		desiredSize: Size(
			width: c:clampW(w: cs:width + padW),
			height: c:clampH(h: cs:height + padH)
		);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is pl: :effSide(fallbackPx: left);
		local Int is pr: :effSide(fallbackPx: right);
		local Int is pt: :effSide(fallbackPx: top);
		local Int is pb: :effSide(fallbackPx: bottom);
		local Int is availW: if({ bounds:width > pl + pr }, { bounds:width - pl - pr }, { 0 });
		local Int is availH: if({ bounds:height > pt + pb }, { bounds:height - pt - pb }, { 0 });
		local Int is cw: if({ shrinkToChild && child:desiredSize:width < availW }, { child:desiredSize:width }, { availW });
		local Int is ch: if({ shrinkToChild && child:desiredSize:height < availH }, { child:desiredSize:height }, { availH });
		child:arrange(bounds: Rect(x: bounds:x + pl, y: bounds:y + pt, width: cw, height: ch));
	}
}
