#! Package base:scrap
#! Resolution-independent push button widget composing a borderless [Clickable] with a themed border.

Class of SewNode is ScrapButton{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'sew', SuitUnit],
		['base', 'sew', Pt],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', Clickable]
	];

	Clickable is inner: Clickable();

	replace Function is init(
		String is label: '',
		Function is onClick: local Function(){},
		Float is minWidthPt: 0.0,
		Float is heightPt: 0.0,
		SuitUnit is width: Pt(value: 0.0),
		SuitUnit is height: Pt(value: 0.0),
		Boolean is hasWidth: false,
		Boolean is hasHeight: false,
		Float is padXPt: 0.0,
		Boolean is selected: false,
		Boolean is enabled: true,
		String is tooltip: ''
	){
		:inner: Clickable(
			label: label,
			onClick: onClick,
			minWidthPt: minWidthPt,
			heightPt: heightPt,
			width: width,
			height: height,
			hasWidth: hasWidth,
			hasHeight: hasHeight,
			padXPt: padXPt,
			selected: selected,
			enabled: enabled,
			tooltip: tooltip
		);
		:tooltip: tooltip;
	}

	replace Function of Boolean is canFocus(){
		return inner:canFocus();
	}

	replace Function of Boolean is isFocused(){
		return inner:isFocused();
	}

	replace Function is setFocused(Boolean is next){
		inner:setFocused(next: next);
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		return inner:onKey(key: key, mods: mods);
	}

	replace Function of Boolean is isSelected(){
		return inner:isSelected();
	}

	Function is setSelected(Boolean is next){
		inner:setSelected(next: next);
	}

	Function is setLabel(String is next){
		inner:setLabel(next: next);
	}

	Function is setEnabled(Boolean is next){
		inner:setEnabled(next: next);
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		inner:applyTheme(theme: theme);
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		inner:setScale(scale: scale);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		inner:bindDirty(cb: cb);
	}

	replace Function of Size is measure(Constraints is c){
		desiredSize: inner:measure(c: c);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		inner:arrange(bounds: bounds);
	}

	replace Function is clearHover(){
		inner:clearHover();
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		return inner:onPointerMove(x: x, y: y);
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return inner:onPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is radPx: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
		local Int is shBlur: activeScale:px(pt: activeTheme:buttonShadowBlurPt);
		local Int is shOffX: activeScale:px(pt: activeTheme:buttonShadowOffsetXPt);
		local Int is shOffY: activeScale:px(pt: activeTheme:buttonShadowOffsetYPt);
		if({ shBlur > 0 || shOffX != 0 || shOffY != 0 }, {
			ctx:drawShadow(x: b:x, y: b:y, w: b:width, h: b:height, radius: radPx, offsetX: shOffX, offsetY: shOffY, blurRadius: shBlur, color: 1426063360);
		});
		inner:paint(ctx: ctx);
		local Int is linePx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
		if({ linePx > 0 }, {
			local Int is border: if({ inner:selected || inner:focused }, { activeTheme:textAccent }, { activeTheme:buttonBorder });
			ctx:drawStyledBox(
				x: b:x, y: b:y, w: b:width, h: b:height,
				bgColor: 0, borderColor: border, thickness: linePx,
				radius: radPx, style: activeTheme:buttonBorderStyle
			);
		});
	}
}
