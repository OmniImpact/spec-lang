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
		['base', 'fabric', DrawContext]
	];

	String is text: '';
	Boolean is heading: false;
	Boolean is muted: false;
	Boolean is boxed: false;
	Float is minWidthPt: 0.0;

	replace Function is init(
		String is text: '',
		Boolean is heading: false,
		Boolean is muted: false,
		Boolean is boxed: false,
		Float is minWidthPt: 0.0
	){
		:text: text;
		:heading: heading;
		:muted: muted;
		:boxed: boxed;
		:minWidthPt: minWidthPt;
	}

	Function is setText(String is text){
		if({ :text != text }, {
			:text: text;
			invalidate();
		});
	}

	local Function of Int is fontPx(){
		local Float is pt: if({ heading }, { 17.5 }, { 15.0 });
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: pt));
		return if({ px < 10 }, { 10 }, { px });
	}

	replace Function of Size is measure(Constraints is c){
		local Int is fpx: :fontPx();
		local Int is tw: DrawContext:measureWidth(text: text, pixelHeight: fpx);
		local Int is padX: if({ boxed }, { activeScale:px(pt: activeTheme:paddingPt) }, { 0 });
		local Int is padY: if({ boxed }, { activeScale:px(pt: activeTheme:paddingPt * 0.75) }, { activeScale:px(pt: 4.0) });
		local Int is minW: activeScale:px(pt: minWidthPt);
		local Int is w: if({ tw + padX * 2 > minW }, { tw + padX * 2 }, { minW });
		local Int is h: DrawContext:measureHeight(pixelHeight: fpx) + padY * 2;
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
		local Int is fg: if({ muted }, { activeTheme:textMuted }, { activeTheme:textPrimary });
		ctx:drawText(x: b:x + padX, y: b:y + (b:height - th) / 2, text: text, color: fg, pixelHeight: fpx);
	}
}