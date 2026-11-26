#! Package base:scrap:icon
#! Point-sized SVG image widget backed by [SvgRenderer].

Class of SewNode is ImageSvg{
	replace [String] is namespace: ['base', 'scrap', 'icon'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'fabric', DrawContext],
		['base', 'fabric', 'svg', SvgRenderer],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints]
	];

	String is svg: '';
	Float is widthPt: 16.0;
	Float is heightPt: 16.0;

	replace Function is init(String is svg: '', Float is widthPt: 16.0, Float is heightPt: 16.0){
		:svg: svg;
		:widthPt: widthPt;
		:heightPt: heightPt;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is w: activeScale:px(pt: widthPt);
		local Int is h: activeScale:px(pt: heightPt);
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ svg == '' || b:width <= 0 || b:height <= 0 }, { return; });
		SvgRenderer:shared:draw(
			ctx: ctx,
			svgSrc: svg,
			x: b:x,
			y: b:y,
			widthPx: b:width,
			heightPx: b:height,
			useTint: false
		);
	}
}
