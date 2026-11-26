#! Package specedit:view:settings
#! Theme- and scale-aware selectable chip/button primitive for the Settings dialog.

Class of SewNode is SettingsChip{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', DrawContext]
	];

	String is label: '';
	Boolean is selected: false;
	Boolean is hovered: false;
	Float is minWidthPt: 56.0;
	Float is heightPt: 28.0;
	Function is onClick: local Function(){};

	replace Function is init(
		String is label: '',
		Boolean is selected: false,
		Float is minWidthPt: 56.0,
		Float is heightPt: 28.0,
		Function is onClick: local Function(){}
	){
		:label: label;
		:selected: selected;
		:minWidthPt: minWidthPt;
		:heightPt: heightPt;
		:onClick: onClick;
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

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Boolean is contains(Int is x, Int is y){
		local Rect is b: bounds();
		return x >= b:x && x < b:x + b:width && y >= b:y && y < b:y + b:height;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is fpx: :fontPx();
		local Int is padX: activeScale:px(pt: activeTheme:paddingPt * 2.0);
		local Int is tw: DrawContext:measureWidth(text: label, pixelHeight: fpx) + padX;
		local Int is minW: activeScale:px(pt: minWidthPt);
		local Int is w: if({ tw > minW }, { tw }, { minW });
		local Int is h: activeScale:px(pt: heightPt);
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is bg: if({ selected }, { activeTheme:activeBg }, {
			if({ hovered }, { activeTheme:hoverBg }, { activeTheme:panelBg })
		});
		local Int is border: if({ selected }, { activeTheme:textAccent }, { activeTheme:panelBorder });
		local Int is bw: activeScale:px(pt: activeTheme:borderThicknessPt);
		if({ bw < 1 }, { bw: 1; });
		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: bg);
		ctx:strokeRect(x: b:x, y: b:y, w: b:width, h: b:height, color: border, thickness: bw);
		local Int is fpx: :fontPx();
		local Int is tw: DrawContext:measureWidth(text: label, pixelHeight: fpx);
		local Int is th: DrawContext:measureHeight(pixelHeight: fpx);
		local Int is fg: if({ selected }, { activeTheme:textAccent }, { activeTheme:textPrimary });
		ctx:drawText(x: b:x + (b:width - tw) / 2, y: b:y + (b:height - th) / 2, text: label, color: fg, pixelHeight: fpx);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is h: :contains(x: x, y: y);
		if({ h != hovered }, {
			:hovered: h;
			invalidate();
			return true;
		});
		return false;
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods){
		if({ :contains(x: x, y: y) }, {
			local Function is cb: onClick;
			cb();
			return true;
		});
		return false;
	}
}