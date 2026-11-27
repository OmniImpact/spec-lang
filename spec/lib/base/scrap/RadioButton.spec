#! Package base:scrap
#! Theme- and scale-aware circular radio button control with optional label, keyboard focus, and state effects.

Class of SewNode is RadioButton{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', Color],
		['base', 'fabric', FillMode],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext]
	];

	Boolean is selected: false;
	String is label: '';
	Boolean is enabled: true;
	Boolean is hovered: false;
	Boolean is focused: false;
	Function is onSelect: local Function(){};

	replace Function is init(
		Boolean is selected: false,
		String is label: '',
		Boolean is enabled: true,
		Function is onSelect: local Function(){},
		String is tooltip: ''
	){
		:selected: selected;
		:label: label;
		:enabled: enabled;
		:hovered: false;
		:focused: false;
		:onSelect: onSelect;
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

	Function is setSelected(Boolean is next){
		if({ selected != next }, {
			:selected: next;
			invalidate();
		});
	}

	local Function is selectSelf(){
		if({ !enabled }, { return; });
		:selected: true;
		local Function is cb: onSelect;
		cb();
		invalidate();
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		if({ enabled && focused && (key == 10 || key == 13 || key == 32) }, {
			:selectSelf();
			return true;
		});
		return false;
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Int is circleSizePx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0));
		return if({ px < 12 }, { 12 }, { px });
	}

	local Function of Boolean is contains(Int is x, Int is y){
		local Rect is b: bounds();
		return x >= b:x && x < b:x + b:width && y >= b:y && y < b:y + b:height;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is circPx: :circleSizePx();
		local Int is fpx: :fontPx();
		local Int is padX: activeScale:px(pt: activeTheme:paddingPt);
		local Int is textW: if({ label != '' }, { padX + DrawContext:measureWidth(text: label, pixelHeight: fpx) }, { 0 });
		local Int is textH: if({ label != '' }, { DrawContext:measureHeight(pixelHeight: fpx) }, { 0 });
		local Int is h: if({ textH > circPx }, { textH }, { circPx }) + activeScale:px(pt: activeTheme:paddingSmallPt) * 2;
		local Int is w: circPx + textW + activeScale:px(pt: activeTheme:paddingSmallPt);
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });

		local Int is circPx: :circleSizePx();
		local Int is cx: b:x;
		local Int is cy: b:y + (b:height - circPx) / 2;
		local Int is btnPx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
		local FillStyle is fill: activeTheme:resolveButtonFill(enabled: enabled, selected: selected, hovered: hovered, focused: focused);
		ctx:drawStyledBoxFill(
			x: cx, y: cy, w: circPx, h: circPx,
			fill: fill, borderColor: activeTheme:buttonBorderColorArgb(),
			thickness: btnPx, radius: circPx / 2, style: activeTheme:buttonBorderStyle
		);

		if({ selected }, {
			local Int is dotPx: (circPx * 46) / 100;
			if({ dotPx < 4 }, { dotPx: 4; });
			local Int is dx: cx + (circPx - dotPx) / 2;
			local Int is dy: cy + (circPx - dotPx) / 2;
			local Int is dotCol: if({ enabled }, { activeTheme:textPrimary }, { activeTheme:textMuted });
			ctx:fillRoundRectStyled(
				x: dx, y: dy, w: dotPx, h: dotPx,
				radius: dotPx / 2,
				fill: FillStyle(mode: FillMode:SOLID, colorA: Color:fromArgb(argb: dotCol))
			);
		});

		if({ label != '' }, {
			local Int is fpx: :fontPx();
			local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
			local Int is padX: activeScale:px(pt: activeTheme:paddingPt);
			local Int is tcol: if({ enabled }, { activeTheme:textPrimary }, { activeTheme:textMuted });
			ctx:drawText(x: cx + circPx + padX, y: b:y + (b:height - th) / 2, text: label, color: tcol, pixelHeight: fpx);
		});
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is h: enabled && :contains(x: x, y: y);
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
			:selectSelf();
			return true;
		});
		return false;
	}
}
