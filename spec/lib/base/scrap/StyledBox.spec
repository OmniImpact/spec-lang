#! Package base:scrap
#! Styled container box supporting border styles (single/double/bevel/groove/inset/outset), corner radius, and drop shadow.

Class of SewNode is StyledBox{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', Color],
		['base', 'fabric', DrawContext]
	];

	String is label: '';
	String is borderStyle: 'single';
	Color is lineColor: Color(r: 100, g: 180, b: 255);
	Boolean is useThemeBorder: true;
	Float is thicknessPt: 2.0;
	Float is radiusPt: 6.0;
	Float is shadowOffsetXPt: 0.0;
	Float is shadowOffsetYPt: 3.0;
	Float is shadowBlurPt: 6.0;
	Int is shadowAlpha: 96;
	Float is innerShadowOffsetXPt: 0.0;
	Float is innerShadowOffsetYPt: 0.0;
	Float is innerShadowBlurPt: 0.0;
	Int is innerShadowAlpha: 96;
	Float is minWidthPt: 96.0;
	Float is minHeightPt: 52.0;

	replace Function is init(
		String is label: '',
		String is borderStyle: 'single',
		Color is lineColor: Color(r: 100, g: 180, b: 255),
		Boolean is useThemeBorder: true,
		Float is thicknessPt: 2.0,
		Float is radiusPt: 6.0,
		Float is shadowOffsetXPt: 0.0,
		Float is shadowOffsetYPt: 3.0,
		Float is shadowBlurPt: 6.0,
		Int is shadowAlpha: 96,
		Float is innerShadowOffsetXPt: 0.0,
		Float is innerShadowOffsetYPt: 0.0,
		Float is innerShadowBlurPt: 0.0,
		Int is innerShadowAlpha: 96,
		Float is minWidthPt: 96.0,
		Float is minHeightPt: 52.0
	){
		:label: label;
		:borderStyle: borderStyle;
		:lineColor: lineColor;
		:useThemeBorder: useThemeBorder;
		:thicknessPt: thicknessPt;
		:radiusPt: radiusPt;
		:shadowOffsetXPt: shadowOffsetXPt;
		:shadowOffsetYPt: shadowOffsetYPt;
		:shadowBlurPt: shadowBlurPt;
		:shadowAlpha: shadowAlpha;
		:innerShadowOffsetXPt: innerShadowOffsetXPt;
		:innerShadowOffsetYPt: innerShadowOffsetYPt;
		:innerShadowBlurPt: innerShadowBlurPt;
		:innerShadowAlpha: innerShadowAlpha;
		:minWidthPt: minWidthPt;
		:minHeightPt: minHeightPt;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is w: activeScale:px(pt: minWidthPt);
		local Int is h: activeScale:px(pt: minHeightPt);
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is inset: activeScale:px(pt: 12.0);
		local Int is bx: b:x + inset;
		local Int is by: b:y + inset;
		local Int is bw: b:width - inset * 2;
		local Int is bh: b:height - inset * 2;
		if({ bw <= 4 || bh <= 4 }, {
			bx: b:x;
			by: b:y;
			bw: b:width;
			bh: b:height;
		});
		local Int is bCol: if({ useThemeBorder }, { activeTheme:textAccent }, { lineColor:toArgb() });
		local Int is sCol: if({ shadowAlpha > 0 }, { Color(r: 0, g: 0, b: 0, a: shadowAlpha):toArgb() }, { 0 });
		local Int is tPx: if({ thicknessPt > 0.0 }, { activeScale:px(pt: thicknessPt) }, { 0 });
		if({ thicknessPt > 0.0 && tPx < 1 }, { tPx: 1; });
		local Int is rPx: if({ radiusPt > 0.0 }, { activeScale:px(pt: radiusPt) }, { 0 });
		local Int is sxPx: activeScale:px(pt: shadowOffsetXPt);
		local Int is syPx: activeScale:px(pt: shadowOffsetYPt);
		local Int is sbPx: if({ shadowBlurPt > 0.0 }, { activeScale:px(pt: shadowBlurPt) }, { 0 });
		local Int is inSCol: if({ innerShadowAlpha > 0 }, { Color(r: 0, g: 0, b: 0, a: innerShadowAlpha):toArgb() }, { 0 });
		local Int is isxPx: activeScale:px(pt: innerShadowOffsetXPt);
		local Int is isyPx: activeScale:px(pt: innerShadowOffsetYPt);
		local Int is isbPx: if({ innerShadowBlurPt > 0.0 }, { activeScale:px(pt: innerShadowBlurPt) }, { 0 });
		ctx:drawStyledBox(
			x: bx,
			y: by,
			w: bw,
			h: bh,
			bgColor: activeTheme:panelBg,
			borderColor: bCol,
			thickness: tPx,
			radius: rPx,
			style: borderStyle,
			shadowOffsetX: sxPx,
			shadowOffsetY: syPx,
			shadowBlur: sbPx,
			shadowColor: sCol,
			innerShadowOffsetX: isxPx,
			innerShadowOffsetY: isyPx,
			innerShadowBlur: isbPx,
			innerShadowColor: inSCol
		);
		if({ label != '' }, {
			local Int is fpx: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 13.0));
			if({ fpx < 10 }, { fpx: 10; });
			local Int is tw: ctx:measureTextWidth(text: label, pixelHeight: fpx);
			local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
			ctx:drawText(
				x: bx + (bw - tw) / 2,
				y: by + (bh - th) / 2,
				text: label,
				color: activeTheme:textPrimary,
				pixelHeight: fpx
			);
		});
	}
}
