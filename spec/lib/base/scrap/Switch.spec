#! Package base:scrap
#! Theme- and scale-aware toggle switch showing a left empty square when off and a right filled square when on.

Class of SewNode is Switch{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', DrawContext]
	];

	Boolean is checked: false;
	Boolean is hovered: false;
	Boolean is focused: false;
	Function is onToggle: local Function(Boolean is _next){};

	replace Function is init(Boolean is checked: false, Function is onToggle: local Function(Boolean is _next){}, String is tooltip: ''){
		:checked: checked;
		:onToggle: onToggle;
		:hovered: false;
		:focused: false;
		:tooltip: tooltip;
	}

	replace Function of Boolean is canFocus(){
		return true;
	}

	replace Function of Boolean is isFocused(){
		return focused;
	}

	replace Function is setFocused(Boolean is next){
		if({ focused != next }, {
			:focused: next;
			invalidate();
		});
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		if({ focused && (key == 10 || key == 13 || key == 32) }, {
			:checked: !checked;
			local Function is cb: onToggle;
			cb(checked);
			invalidate();
			return true;
		});
		return false;
	}

	Function is setChecked(Boolean is next){
		if({ checked != next }, {
			:checked: next;
			invalidate();
		});
	}

	local Function of Int is trackHeightPx(){
		local Float is hPt: activeTheme:scaledTextPt(defaultPt: 14.0) + activeTheme:padPt(pct: 1.0);
		local Int is px: activeScale:px(pt: hPt);
		return if({ px < 14 }, { 14 }, { px });
	}

	local Function of Boolean is contains(Int is x, Int is y){
		local Rect is b: bounds();
		return x >= b:x && x < b:x + b:width && y >= b:y && y < b:y + b:height;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is h: :trackHeightPx();
		local Int is w: h * 2;
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is bw: activeTheme:borderPx(scaleFactor: activeScale:factor);
		local Int is bg: if({ hovered }, { activeTheme:hoverBg }, { activeTheme:panelBg });
		local Int is borderCol: if({ focused || checked }, { activeTheme:textAccent }, { activeTheme:panelBorder });
		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: bg);
		if({ bw > 0 }, {
			ctx:strokeRect(x: b:x, y: b:y, w: b:width, h: b:height, color: borderCol, thickness: bw);
		});

		local Int is pad: activeScale:px(pt: activeTheme:padPt(pct: 0.5));
		local Int is minPad: bw + 1;
		if({ pad < minPad }, { pad: minPad; });
		local Int is sq: b:height - pad * 2;
		if({ sq < 4 }, { sq: 4; });

		if({ checked }, {
			local Int is rx: b:x + b:width - pad - sq;
			local Int is ry: b:y + (b:height - sq) / 2;
			ctx:fillRect(x: rx, y: ry, w: sq, h: sq, color: activeTheme:textAccent);
		}, {
			local Int is lx: b:x + pad;
			local Int is ly: b:y + (b:height - sq) / 2;
			local Int is offStroke: if({ bw > 0 }, { bw }, { activeTheme:linePx(scaleFactor: activeScale:factor) });
			local Int is offCol: if({ hovered }, { activeTheme:textPrimary }, { activeTheme:textMuted });
			ctx:strokeRect(x: lx, y: ly, w: sq, h: sq, color: offCol, thickness: offStroke);
		});
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

	replace Function is clearHover(){
		if({ hovered }, {
			:hovered: false;
			invalidate();
		});
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods){
		if({ :contains(x: x, y: y) }, {
			:checked: !checked;
			local Function is cb: onToggle;
			cb(checked);
			invalidate();
			return true;
		});
		return false;
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ :contains(x: x, y: y) }, { return CursorShape:POINTER; });
		return CursorShape:DEFAULT;
	}
}