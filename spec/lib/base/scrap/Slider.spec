#! Package base:scrap
#! Horizontal integer range slider widget participating in Sew layout, Theme, and FocusNav.

Class of SewNode is Slider{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', DrawContext]
	];

	Int is minVal: 0;
	Int is maxVal: 100;
	Int is value: 100;
	Float is minWidthPt: 140.0;
	Function is onChange: local Function(Int is _val){};
	Boolean is dragging: false;
	Boolean is hovered: false;
	Boolean is focused: false;

	replace Function is init(
		Int is minVal: 0,
		Int is maxVal: 100,
		Int is value: 100,
		Float is minWidthPt: 140.0,
		Function is onChange: local Function(Int is _val){},
		String is tooltip: ''
	){
		:minVal: minVal;
		:maxVal: if({ maxVal > minVal }, { maxVal }, { minVal + 1 });
		:value: :clampVal(v: value);
		:minWidthPt: minWidthPt;
		:onChange: onChange;
		:dragging: false;
		:hovered: false;
		:focused: false;
		:tooltip: tooltip;
	}

	local Function of Int is clampVal(Int is v){
		if({ v < minVal }, { return minVal; });
		if({ v > maxVal }, { return maxVal; });
		return v;
	}

	Function is setValue(Int is next){
		local Int is c: :clampVal(v: next);
		if({ c != value }, {
			:value: c;
			invalidate();
		});
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

	local Function of Boolean is contains(Int is x, Int is y){
		local Rect is b: bounds();
		return x >= b:x && x < b:x + b:width && y >= b:y && y < b:y + b:height;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is w: activeScale:px(pt: minWidthPt);
		local Int is h: activeScale:px(pt: activeTheme:buttonHeightPt);
		if({ h < 18 }, { h: 18; });
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	local Function of Boolean is updateFromX(Int is x){
		local Rect is b: bounds();
		local Int is padX: activeScale:px(pt: 6.0);
		local Int is trackW: b:width - padX * 2;
		if({ trackW <= 0 }, { return false; });
		local Int is rel: x - (b:x + padX);
		if({ rel < 0 }, { rel: 0; });
		if({ rel > trackW }, { rel: trackW; });
		local Int is span: maxVal - minVal;
		local Int is next: minVal + ((rel * span + trackW / 2) / trackW);
		next: :clampVal(v: next);
		if({ next != value }, {
			:value: next;
			local Function is cb: onChange;
			cb(value);
			invalidate();
			return true;
		});
		return false;
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is inside: :contains(x: x, y: y);
		if({ inside != hovered }, {
			:hovered: inside;
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
		if({ :contains(x: x, y: y) }, {
			:dragging: true;
			:updateFromX(x: x);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ dragging || :contains(x: x, y: y) }, {
			:dragging: true;
			return :updateFromX(x: x);
		});
		return false;
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		if({ dragging }, {
			:dragging: false;
			return true;
		});
		return false;
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		if({ !focused }, { return false; });
		local Int is step: if({ (mods & 1) != 0 }, { 5 }, { 1 });
		if({ key == 1003 || key == 1002 }, {
			local Int is next: :clampVal(v: value - step);
			if({ next != value }, {
				:value: next;
				local Function is cb: onChange;
				cb(value);
				invalidate();
			});
			return true;
		});
		if({ key == 1004 || key == 1001 }, {
			local Int is next: :clampVal(v: value + step);
			if({ next != value }, {
				:value: next;
				local Function is cb: onChange;
				cb(value);
				invalidate();
			});
			return true;
		});
		if({ key == 1005 }, {
			:setValue(next: minVal);
			local Function is cb: onChange;
			cb(value);
			return true;
		});
		if({ key == 1006 }, {
			:setValue(next: maxVal);
			local Function is cb: onChange;
			cb(value);
			return true;
		});
		return false;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is padX: activeScale:px(pt: 6.0);
		local Int is trackW: b:width - padX * 2;
		if({ trackW <= 4 }, { return; });
		local Int is trackH: activeScale:px(pt: 4.0);
		if({ trackH < 4 }, { trackH: 4; });
		local Int is tx: b:x + padX;
		local Int is ty: b:y + (b:height - trackH) / 2;
		local Int is bw: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
		local Int is radPx: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
		local Int is trackRad: if({ radPx > trackH / 2 }, { trackH / 2 }, { radPx });
		local Int is shBlur: activeScale:px(pt: activeTheme:buttonShadowBlurPt);
		local Int is shOffX: activeScale:px(pt: activeTheme:buttonShadowOffsetXPt);
		local Int is shOffY: activeScale:px(pt: activeTheme:buttonShadowOffsetYPt);
		local Int is shCol: if({ shBlur > 0 || shOffX != 0 || shOffY != 0 }, { 1426063360 }, { 0 });
		local String is bStyle: activeTheme:buttonBorderStyle;

		ctx:fillRoundRect(x: tx, y: ty, w: trackW, h: trackH, radius: trackRad, color: activeTheme:panelBg);
		local Int is span: maxVal - minVal;
		local Int is fillW: if({ span > 0 }, { ((value - minVal) * trackW) / span }, { 0 });
		if({ fillW > 0 }, {
			ctx:setClip(x: tx, y: ty, w: fillW, h: trackH);
			ctx:fillRoundRect(x: tx, y: ty, w: trackW, h: trackH, radius: trackRad, color: activeTheme:textAccent);
			ctx:clearClip();
		});
		if({ bw > 0 && bStyle != 'none' }, {
			local Int is borderCol: if({ focused }, { activeTheme:textAccent }, { activeTheme:buttonBorder });
			ctx:drawStyledBox(
				x: tx, y: ty, w: trackW, h: trackH,
				bgColor: 0, borderColor: borderCol, thickness: bw,
				radius: trackRad, style: bStyle
			);
		});

		local Int is thumbW: activeScale:px(pt: 10.0);
		if({ thumbW < 8 }, { thumbW: 8; });
		local Int is thumbH: activeScale:px(pt: 14.0);
		if({ thumbH < 12 }, { thumbH: 12; });
		local Int is kx: tx + fillW - thumbW / 2;
		local Int is ky: b:y + (b:height - thumbH) / 2;
		local Int is kBg: if({ hovered || dragging }, { activeTheme:hoverBg }, { activeTheme:menuBg });
		local Int is kBorder: if({ focused || dragging }, { activeTheme:textAccent }, { activeTheme:buttonBorder });
		ctx:drawStyledBox(
			x: kx, y: ky, w: thumbW, h: thumbH,
			bgColor: kBg, borderColor: kBorder, thickness: bw,
			radius: radPx, style: bStyle,
			shadowOffsetX: shOffX, shadowOffsetY: shOffY, shadowBlur: shBlur, shadowColor: shCol
		);
	}
}
