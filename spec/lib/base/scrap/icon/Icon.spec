#! Package base:scrap:icon
#! Tintable monochrome SVG icon widget and inline drawing helper.

Class of SewNode is Icon{
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
	Float is sizePt: 14.0;
	Int is color: 0;
	Boolean is muted: false;

	replace Function is init(String is svg: '', Float is sizePt: 14.0, Int is color: 0, Boolean is muted: false){
		:svg: svg;
		:sizePt: sizePt;
		:color: color;
		:muted: muted;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is s: activeScale:px(pt: sizePt);
		desiredSize: Size(width: c:clampW(w: s), height: c:clampH(h: s));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ svg == '' || b:width <= 0 || b:height <= 0 }, { return; });
		local Int is effColor: if({ color != 0 }, { color }, { if({ muted }, { activeTheme:textMuted }, { activeTheme:textPrimary }) });
		SvgRenderer:shared:draw(
			ctx: ctx,
			svgSrc: svg,
			x: b:x,
			y: b:y,
			widthPx: b:width,
			heightPx: b:height,
			tintColor: effColor,
			useTint: true
		);
	}
}
