#! Package base:scrap
#! Compact pill/tag badge widget with optional close button.

Class of SewNode is Badge{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale]
	];

	String is text: '';
	Boolean is accent: false;
	Boolean is closable: false;
	Int is customBgColor: 0;
	Int is customTextColor: 0;
	Function is onClose: local Function(){};

	Boolean is hoveredClose: false;

	replace Function is init(
		String is text: '',
		Boolean is accent: false,
		Boolean is closable: false,
		Int is bgColor: 0,
		Int is textColor: 0,
		String is tooltip: '',
		Function is onClose: local Function(){}
	){
		:text: text;
		:accent: accent;
		:closable: closable;
		:customBgColor: bgColor;
		:customTextColor: textColor;
		:tooltip: tooltip;
		:onClose: onClose;
	}

	Function is setText(String is next){
		:text: next;
		:invalidate();
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:baseTextPt * 0.85);
		return if({ px < 9 }, { 9 }, { px });
	}

	local Function of Int is closeZoneW(){
		if({ !closable }, { return 0; });
		return activeScale:px(pt: 14.0);
	}

	replace Function of Size is measure(Constraints is c){
		local Int is fpx: :fontPx();
		local Int is padX: activeScale:px(pt: activeTheme:paddingPt);
		local Int is padY: activeScale:px(pt: activeTheme:paddingSmallPt);
		local Int is tw: (text:length() * fpx * 6) / 10 + 4;
		local Int is cw: :closeZoneW();
		local Int is w: tw + padX * 2 + cw;
		local Int is h: fpx + padY * 2;
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is bw: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
		local Int is rad: b:height / 2;
		local Int is bg: if({ customBgColor != 0 }, {
			customBgColor
		}, {
			if({ accent }, { activeTheme:textAccent }, { activeTheme:hoverBg })
		});
		local Int is fg: if({ customTextColor != 0 }, {
			customTextColor
		}, {
			if({ accent }, { activeTheme:surfaceBg }, { activeTheme:textPrimary })
		});
		local Int is brd: if({ accent }, { activeTheme:textAccent }, { activeTheme:buttonBorderColorArgb() });
		ctx:drawStyledBox(
			x: b:x, y: b:y, w: b:width, h: b:height,
			bgColor: bg, borderColor: brd,
			thickness: bw, radius: rad, style: activeTheme:buttonBorderStyle
		);
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is padX: activeScale:px(pt: activeTheme:paddingPt);
		ctx:drawText(
			x: b:x + padX,
			y: b:y + (b:height - th) / 2,
			text: text,
			color: fg,
			pixelHeight: fpx,
			bold: accent,
			italic: false,
			mono: false
		);
		if({ closable }, {
			local Int is cw: :closeZoneW();
			local Int is xW: ctx:measureTextWidth(text: '×', pixelHeight: fpx);
			local Int is xCol: if({ hoveredClose }, { activeTheme:textAccent }, { fg });
			ctx:drawText(
				x: b:x + b:width - padX / 2 - cw / 2 - xW / 2,
				y: b:y + (b:height - th) / 2,
				text: '×',
				color: xCol,
				pixelHeight: fpx
			);
		});
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		if({ !closable || !:containsPoint(x: x, y: y) }, {
			if({ hoveredClose }, { :hoveredClose: false; :invalidate(); });
			return false;
		});
		local Rect is b: bounds();
		local Int is cw: :closeZoneW() + activeScale:px(pt: activeTheme:paddingSmallPt);
		local Boolean is overX: x >= b:x + b:width - cw;
		if({ overX != hoveredClose }, {
			:hoveredClose: overX;
			:invalidate();
		});
		return true;
	}

	replace Function is clearHover(){
		if({ hoveredClose }, { :hoveredClose: false; :invalidate(); });
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ !closable || !:containsPoint(x: x, y: y) }, { return false; });
		local Rect is b: bounds();
		local Int is cw: :closeZoneW() + activeScale:px(pt: activeTheme:paddingSmallPt);
		if({ x >= b:x + b:width - cw }, {
			local Function is cb: :onClose;
			cb();
			return true;
		});
		return false;
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ closable && :containsPoint(x: x, y: y) }, {
			local Rect is b: bounds();
			local Int is cw: :closeZoneW() + activeScale:px(pt: activeTheme:paddingSmallPt);
			if({ x >= b:x + b:width - cw }, { return CursorShape:POINTER; });
		});
		return CursorShape:DEFAULT;
	}
}
