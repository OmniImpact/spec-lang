#! Package base:scrap
#! Borderless clickable widget participating in Sew layout and Theme propagation.

Class of SewNode is Clickable{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'suit', KeyCode],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', SuitUnit],
		['base', 'sew', Pt],
		['base', 'fabric', Theme],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext]
	];

	String is label: '';
	Function is onClick: local Function(){};
	Float is minWidthPt: 0.0;
	Float is heightPt: 0.0;
	SuitUnit is widthUnit: Pt(value: 0.0);
	SuitUnit is heightUnit: Pt(value: 0.0);
	Boolean is hasWidthUnit: false;
	Boolean is hasHeightUnit: false;
	Float is padXPt: 0.0;
	Boolean is selected: false;
	Boolean is enabled: true;
	Boolean is hovered: false;
	Boolean is focused: false;
	Boolean is roundLeft: true;
	Boolean is roundRight: true;
	Boolean is roundTop: true;
	Boolean is roundBottom: true;
	Boolean is insetLeft: true;
	Boolean is insetRight: true;
	Boolean is insetTop: true;
	Boolean is insetBottom: true;

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
		:label: label;
		:onClick: onClick;
		:minWidthPt: minWidthPt;
		:heightPt: heightPt;
		:widthUnit: width;
		:heightUnit: height;
		:hasWidthUnit: hasWidth;
		:hasHeightUnit: hasHeight;
		:padXPt: padXPt;
		:selected: selected;
		:enabled: enabled;
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
			local Function is cb: onClick;
			cb();
			return true;
		});
		return false;
	}

	replace Function of Boolean is isSelected(){
		return selected;
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
		local Float is pxPt: if({ padXPt > 0.0 }, { padXPt }, { activeTheme:paddingMediumPt });
		local Int is padPx: activeScale:px(pt: pxPt * 2.0);
		local Int is minW: if({ hasWidthUnit }, { :unitPx(unit: widthUnit) }, {
			activeScale:px(pt: if({ minWidthPt > 0.0 }, { minWidthPt }, { activeTheme:buttonMinWidthPt }))
		});
		local Int is w: if({ tw + padPx > minW }, { tw + padPx }, { minW });
		local Int is h: if({ hasHeightUnit }, { :unitPx(unit: heightUnit) }, {
			activeScale:px(pt: if({ heightPt > 0.0 }, { heightPt }, { activeTheme:buttonHeightPt }))
		});
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
			invalidate();
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

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ enabled && :contains(x: x, y: y) }, { return CursorShape:POINTER; });
		return CursorShape:DEFAULT;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local FillStyle is fill: activeTheme:resolveButtonFill(enabled: enabled, selected: selected, hovered: hovered, focused: focused);
		local Int is btnPx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
		local Int is iL: if({ insetLeft }, { btnPx }, { 0 });
		local Int is iR: if({ insetRight }, { btnPx }, { 0 });
		local Int is iT: if({ insetTop }, { btnPx }, { 0 });
		local Int is iB: if({ insetBottom }, { btnPx }, { 0 });
		local Int is fx: b:x + iL;
		local Int is fy: b:y + iT;
		local Int is fw: b:width - iL - iR;
		local Int is fh: b:height - iT - iB;
		local Int is radPx: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
		local Int is fillRad: if({ radPx > btnPx }, { radPx - btnPx }, { 0 });
		if({ fw > 0 && fh > 0 }, {
			if({ !roundLeft && !roundRight && !roundTop && !roundBottom }, {
				ctx:fillRoundRectStyled(x: fx, y: fy, w: fw, h: fh, radius: 0, fill: fill);
			}, {
			if({ roundLeft && roundRight && roundTop && roundBottom }, {
				ctx:fillRoundRectStyled(x: fx, y: fy, w: fw, h: fh, radius: fillRad, fill: fill);
			}, {
				local Int is padL: if({ roundLeft }, { 0 }, { fillRad });
				local Int is padR: if({ roundRight }, { 0 }, { fillRad });
				local Int is padT: if({ roundTop }, { 0 }, { fillRad });
				local Int is padB: if({ roundBottom }, { 0 }, { fillRad });
				ctx:setClip(x: fx, y: fy, w: fw, h: fh);
				ctx:fillRoundRectStyled(x: fx - padL, y: fy - padT, w: fw + padL + padR, h: fh + padT + padB, radius: fillRad, fill: fill);
				ctx:clearClip();
			}); });
		});
		local Int is fpx: :fontPx();
		local Int is tw: ctx:measureTextWidth(text: label, pixelHeight: fpx);
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is tx: b:x + (b:width - tw) / 2;
		local Int is ty: b:y + (b:height - th) / 2;
		local Int is fg: if({ !enabled }, { activeTheme:textMuted }, { activeTheme:textPrimary });
		ctx:drawText(x: tx, y: ty, text: label, color: fg, pixelHeight: fpx);
	}
}
