#! Package base:scrap
#! Theme- and scale-aware toggle switch showing a left empty square when off and a right filled square when on.

Class of SewNode is Switch{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'suit', KeyCode],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext]
	];

	Boolean is checked: false;
	Boolean is enabled: true;
	Boolean is hovered: false;
	Boolean is focused: false;
	Function is onToggle: local Function(Boolean is _next){};

	replace Function is init(Boolean is checked: false, Boolean is enabled: true, Function is onToggle: local Function(Boolean is _next){}, String is tooltip: ''){
		:checked: checked;
		:enabled: enabled;
		:onToggle: onToggle;
		:hovered: false;
		:focused: false;
		:tooltip: tooltip;
	}

	replace Function of Boolean is canFocus(){
		return enabled;
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
		if({ enabled && focused && (KeyCode:isEnter(key: key) || key == KeyCode:SPACE) }, {
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

	local Function of Boolean is contains(Int is x, Int is y){
		local Rect is b: bounds();
		return x >= b:x && x < b:x + b:width && y >= b:y && y < b:y + b:height;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is h: activeScale:px(pt: activeTheme:buttonHeightPt);
		local Int is w: h * 2;
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is bw: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
		local Int is radPx: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
		local Int is shBlur: activeScale:px(pt: activeTheme:buttonShadowBlurPt);
		local Int is shOffX: activeScale:px(pt: activeTheme:buttonShadowOffsetXPt);
		local Int is shOffY: activeScale:px(pt: activeTheme:buttonShadowOffsetYPt);
		local Int is shCol: if({ shBlur > 0 || shOffX != 0 || shOffY != 0 }, { 1426063360 }, { 0 });
		local FillStyle is fill: activeTheme:resolveButtonFill(
			enabled: enabled, selected: checked, hovered: hovered, focused: focused
		);
		local Int is borderCol: if({ focused }, { activeTheme:textAccent }, { activeTheme:buttonBorderColorArgb() });
		ctx:drawStyledBoxFill(
			x: b:x, y: b:y, w: b:width, h: b:height,
			fill: fill, borderColor: borderCol, thickness: bw, radius: radPx,
			style: activeTheme:buttonBorderStyle,
			shadowOffsetX: shOffX, shadowOffsetY: shOffY, shadowBlur: shBlur, shadowColor: shCol
		);

		local Int is pad: activeScale:px(pt: activeTheme:padPt(pct: 0.5));
		local Int is minPad: bw + 1;
		if({ pad < minPad }, { pad: minPad; });
		local Int is sq: b:height - pad * 2;
		if({ sq < 4 }, { sq: 4; });
		local Int is innerRad: if({ radPx > pad }, { radPx - pad }, { 0 });
		if({ innerRad > sq / 2 }, { innerRad: sq / 2; });

		if({ checked }, {
			local Int is rx: b:x + b:width - pad - sq;
			local Int is ry: b:y + (b:height - sq) / 2;
			local Int is onStroke: if({ bw > 0 }, { bw }, { activeTheme:linePx(scaleFactor: activeScale:factor) });
			ctx:drawStyledBox(
				x: rx, y: ry, w: sq, h: sq,
				bgColor: activeTheme:textPrimary, borderColor: activeTheme:buttonBorderColorArgb(),
				thickness: onStroke, radius: innerRad, style: activeTheme:buttonBorderStyle
			);
		}, {
			local Int is lx: b:x + pad;
			local Int is ly: b:y + (b:height - sq) / 2;
			local Int is offW: sq / 2;
			if({ offW < 3 }, { offW: 3; });
			local Int is offRad: if({ innerRad > offW / 2 }, { offW / 2 }, { innerRad });
			local Int is offStroke: if({ bw > 0 }, { bw }, { activeTheme:linePx(scaleFactor: activeScale:factor) });
			local Int is offCol: if({ hovered }, { activeTheme:textPrimary }, { activeTheme:textMuted });
			ctx:drawStyledBox(
				x: lx, y: ly, w: offW, h: sq,
				bgColor: 0, borderColor: offCol, thickness: offStroke,
				radius: offRad, style: activeTheme:buttonBorderStyle
			);
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

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ enabled && :contains(x: x, y: y) }, {
			:checked: !checked;
			local Function is cb: onToggle;
			cb(checked);
			invalidate();
			return true;
		});
		return false;
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ enabled && :contains(x: x, y: y) }, { return CursorShape:POINTER; });
		return CursorShape:DEFAULT;
	}
}