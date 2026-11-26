#! Package base:scrap
#! Resolution-independent push button widget participating in Sew layout and Theme propagation.

Class of SewNode is ScrapButton{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext]
	];

	String is label: '';
	Function is onClick: local Function(){};
	Float is minWidthPt: 60.0;
	Float is heightPt: 22.0;
	Float is padXPt: 0.0;
	Boolean is selected: false;
	Boolean is enabled: true;
	Boolean is hovered: false;

	replace Function is init(
		String is label: '',
		Function is onClick: local Function(){},
		Float is minWidthPt: 60.0,
		Float is heightPt: 22.0,
		Float is padXPt: 0.0,
		Boolean is selected: false,
		Boolean is enabled: true
	){
		:label: label;
		:onClick: onClick;
		:minWidthPt: minWidthPt;
		:heightPt: heightPt;
		:padXPt: padXPt;
		:selected: selected;
		:enabled: enabled;
		:hovered: false;
	}

	Function is setSelected(Boolean is next){
		if({ selected != next }, {
			:selected: next;
			invalidate();
		});
	}

	Function is setLabel(String is next){
		if({ label != next }, {
			:label: next;
			invalidate();
		});
	}

	Function is setEnabled(Boolean is next){
		if({ enabled != next }, {
			:enabled: next;
			invalidate();
		});
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 16.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Boolean is contains(Int is x, Int is y){
		local Rect is b: bounds();
		return x >= b:x && x < b:x + b:width && y >= b:y && y < b:y + b:height;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is fpx: :fontPx();
		local Int is tw: DrawContext:measureWidth(text: label, pixelHeight: fpx);
		local Float is pxPt: if({ padXPt > 0.0 }, { padXPt }, { activeTheme:paddingPt * 1.5 });
		local Int is padPx: activeScale:px(pt: pxPt * 2.0);
		local Int is minW: activeScale:px(pt: minWidthPt);
		local Int is w: if({ tw + padPx > minW }, { tw + padPx }, { minW });
		local Int is h: activeScale:px(pt: heightPt);
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is clearHover(){
		if({ hovered }, {
			:hovered: false;
			invalidate();
		});
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is inside: enabled && :contains(x: x, y: y);
		if({ inside != hovered }, {
			hovered: inside;
			return true;
		});
		return false;
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ enabled && :contains(x: x, y: y) }, {
			local Function is cb: onClick;
			cb();
			return true;
		});
		return false;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is bg: if({ !enabled }, { activeTheme:toolbarBg }, {
			if({ selected }, { activeTheme:activeBg }, {
				if({ hovered }, { activeTheme:hoverBg }, { activeTheme:menuBg })
			})
		});
		local Int is border: if({ selected }, { activeTheme:textAccent }, { activeTheme:buttonBorder });
		local Int is linePx: activeTheme:borderPx(scaleFactor: activeScale:factor);
		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: bg);
		if({ linePx > 0 }, {
			ctx:strokeRect(x: b:x, y: b:y, w: b:width, h: b:height, color: border, thickness: linePx);
		});
		local Int is fpx: :fontPx();
		local Int is tw: ctx:measureTextWidth(text: label, pixelHeight: fpx);
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is tx: b:x + (b:width - tw) / 2;
		local Int is ty: b:y + (b:height - th) / 2;
		local Int is fg: if({ !enabled }, { activeTheme:textMuted }, {
			if({ selected }, { activeTheme:textAccent }, { activeTheme:textPrimary })
		});
		ctx:drawText(x: tx, y: ty, text: label, color: fg, pixelHeight: fpx);
	}
}
