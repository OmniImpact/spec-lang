#! Package specedit:view:settings
#! Theme- and scale-aware text label primitive for the Settings dialog.

Class of SewNode is SettingsLabel{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

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
	Float is minWidthPt: 0.0;

	replace Function is init(String is text: '', Boolean is heading: false, Boolean is muted: false, Float is minWidthPt: 0.0){
		:text: text;
		:heading: heading;
		:muted: muted;
		:minWidthPt: minWidthPt;
	}

	Function is setText(String is next){
		if({ text != next }, {
			:text: next;
			invalidate();
		});
	}

	local Function of Int is fontPx(){
		local Float is pt: if({ heading }, { 17.0 }, { 14.5 });
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: pt));
		return if({ px < 10 }, { 10 }, { px });
	}

	replace Function of Size is measure(Constraints is c){
		local Int is fpx: :fontPx();
		local Int is tw: DrawContext:measureWidth(text: text, pixelHeight: fpx);
		local Int is minW: activeScale:px(pt: minWidthPt);
		local Int is w: if({ tw > minW }, { tw }, { minW });
		local Int is h: DrawContext:measureHeight(pixelHeight: fpx) + activeScale:px(pt: 6.0);
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is fpx: :fontPx();
		local Int is th: DrawContext:measureHeight(pixelHeight: fpx);
		local Int is color: if({ muted }, { activeTheme:textMuted }, { activeTheme:textPrimary });
		ctx:drawText(x: b:x, y: b:y + (b:height - th) / 2, text: text, color: color, pixelHeight: fpx);
	}
}