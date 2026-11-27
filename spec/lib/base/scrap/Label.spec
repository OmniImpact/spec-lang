#! Package base:scrap
#! Theme- and scale-aware text label widget participating in Sew layout and painting via Fabric.

Class of SewNode is Label{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', Color],
		['base', 'fabric', TextStyle],
		['base', 'fabric', DrawContext]
	];

	String is text: '';
	TextStyle is style: TextStyle:BODY;
	Boolean is heading: false;
	Boolean is muted: false;
	Boolean is boxed: false;
	Float is minWidthPt: 0.0;
	Float is outlinePt: 0.0;
	Color is outlineColor: Color(r: 0, g: 0, b: 0, a: 220);
	Boolean is useCustomOutlineColor: false;
	Float is shadowOffsetXPt: 0.0;
	Float is shadowOffsetYPt: 0.0;
	Float is shadowBlurPt: 0.0;
	Int is shadowAlpha: 120;

	replace Function is init(
		String is text: '',
		TextStyle is style: TextStyle:BODY,
		Boolean is heading: false,
		Boolean is muted: false,
		Boolean is boxed: false,
		Float is minWidthPt: 0.0,
		Float is outlinePt: 0.0,
		Color is outlineColor: Color(r: 0, g: 0, b: 0, a: 220),
		Boolean is useCustomOutlineColor: false,
		Float is shadowOffsetXPt: 0.0,
		Float is shadowOffsetYPt: 0.0,
		Float is shadowBlurPt: 0.0,
		Int is shadowAlpha: 120
	){
		:text: text;
		:style: style;
		:heading: heading;
		:muted: muted;
		:boxed: boxed;
		:minWidthPt: minWidthPt;
		:outlinePt: outlinePt;
		:outlineColor: outlineColor;
		:useCustomOutlineColor: useCustomOutlineColor;
		:shadowOffsetXPt: shadowOffsetXPt;
		:shadowOffsetYPt: shadowOffsetYPt;
		:shadowBlurPt: shadowBlurPt;
		:shadowAlpha: shadowAlpha;
	}

	Function is setText(String is text){
		if({ :text != text }, {
			:text: text;
			invalidate();
		});
	}

	local Function of TextStyle is effectiveStyle(){
		if({ heading && style == TextStyle:BODY }, { return TextStyle:H1; });
		return style;
	}

	local Function of Boolean is isBold(){
		local TextStyle is s: :effectiveStyle();
		return s == TextStyle:DISPLAY || s == TextStyle:H1 || s == TextStyle:H2 || s == TextStyle:H3 || s == TextStyle:OVERLINE;
	}

	local Function of Boolean is isMono(){
		return :effectiveStyle() == TextStyle:CODE;
	}

	local Function of Boolean is isMutedStyle(){
		local TextStyle is s: :effectiveStyle();
		return muted || s == TextStyle:SUBTITLE || s == TextStyle:CAPTION || s == TextStyle:OVERLINE;
	}

	local Function of Int is fontPx(){
		local TextStyle is s: :effectiveStyle();
		local Float is pt: 15.0;
		if({ s == TextStyle:DISPLAY }, { pt: 26.0; });
		if({ s == TextStyle:H1 }, { pt: 22.0; });
		if({ s == TextStyle:H2 }, { pt: 18.5; });
		if({ s == TextStyle:H3 }, { pt: 16.0; });
		if({ s == TextStyle:SUBTITLE }, { pt: 15.5; });
		if({ s == TextStyle:CAPTION }, { pt: 12.5; });
		if({ s == TextStyle:OVERLINE }, { pt: 11.5; });
		if({ s == TextStyle:CODE }, { pt: 14.0; });
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: pt));
		return if({ px < 10 }, { 10 }, { px });
	}

	replace Function of Size is measure(Constraints is c){
		local Int is fpx: :fontPx();
		local Int is outPx: if({ outlinePt > 0.0 }, { activeScale:px(pt: outlinePt) }, { 0 });
		local Int is tw: DrawContext:measureWidth(text: text, pixelHeight: fpx) + (if({ :isBold() }, { fpx / 3 }, { 0 })) + outPx * 2;
		local Int is padX: if({ boxed }, { activeScale:px(pt: activeTheme:paddingPt) }, { 0 });
		local Int is padY: if({ boxed }, { activeScale:px(pt: activeTheme:paddingPt * 0.75) }, { activeScale:px(pt: 4.0) });
		local Int is minW: activeScale:px(pt: minWidthPt);
		local Int is w: if({ tw + padX * 2 > minW }, { tw + padX * 2 }, { minW });
		local Int is h: DrawContext:measureHeight(pixelHeight: fpx) + padY * 2 + outPx * 2;
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is padX: if({ boxed }, { activeScale:px(pt: activeTheme:paddingPt) }, { 0 });
		if({ boxed }, {
			ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: activeTheme:panelBg);
			local Int is bw: activeTheme:borderPx(scaleFactor: activeScale:factor);
			if({ bw > 0 }, {
				ctx:strokeRect(x: b:x, y: b:y, w: b:width, h: b:height, color: activeTheme:panelBorder, thickness: bw);
			});
		});
		local Int is fpx: :fontPx();
		local Int is th: DrawContext:measureHeight(pixelHeight: fpx);
		local Int is fg: if({ :isMutedStyle() }, { activeTheme:textMuted }, { activeTheme:textPrimary });
		local Int is outPx: if({ outlinePt > 0.0 }, { activeScale:px(pt: outlinePt) }, { 0 });
		local Int is shOffX: activeScale:px(pt: shadowOffsetXPt);
		local Int is shOffY: activeScale:px(pt: shadowOffsetYPt);
		local Int is shBlur: activeScale:px(pt: shadowBlurPt);
		if({ outPx > 0 || shOffX != 0 || shOffY != 0 || shBlur > 0 }, {
			local Int is outCol: if({ useCustomOutlineColor }, { outlineColor:toArgb() }, { activeTheme:background:toArgb() });
			local Int is shCol: (shadowAlpha & 255) << 24;
			ctx:drawTextStyled(
				x: b:x + padX + outPx, y: b:y + (b:height - th) / 2, text: text, color: fg,
				pixelHeight: fpx, bold: :isBold(), mono: :isMono(),
				outlinePx: outPx, outlineColor: outCol,
				shadowOffsetX: shOffX, shadowOffsetY: shOffY, shadowBlur: shBlur, shadowColor: shCol
			);
		}, {
			ctx:drawText(x: b:x + padX, y: b:y + (b:height - th) / 2, text: text, color: fg, pixelHeight: fpx, bold: :isBold(), mono: :isMono());
		});
	}
}
