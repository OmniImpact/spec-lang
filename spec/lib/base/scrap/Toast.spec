#! Package base:scrap
#! Notification / Toast banner widget with severity stripe, auto-hide timer, and dismiss button.

Class of SewNode is Toast{
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

	String is title: '';
	String is message: '';
	Int is kind: 0;
	Boolean is visible: true;
	Int is autoHideMs: 0;
	Float is minWidthPt: 220.0;
	Function is onDismiss: local Function(){};

	Int is elapsedMs: 0;
	Int is lastTickMs: 0;
	Boolean is hoveredClose: false;

	replace Function is init(
		String is title: '',
		String is message: '',
		Int is kind: 0,
		Boolean is visible: true,
		Int is autoHideMs: 0,
		Float is minWidthPt: 220.0,
		Function is onDismiss: local Function(){}
	){
		:title: title;
		:message: message;
		:kind: kind;
		:visible: visible;
		:autoHideMs: autoHideMs;
		:minWidthPt: minWidthPt;
		:onDismiss: onDismiss;
	}

	Function is show(String is title, String is message, Int is kind: 0){
		:title: title;
		:message: message;
		:kind: kind;
		:visible: true;
		:elapsedMs: 0;
		:lastTickMs: 0;
		:invalidate();
	}

	Function is dismiss(){
		if({ !visible }, { return; });
		:visible: false;
		local Function is cb: :onDismiss;
		cb();
		:invalidate();
	}

	local Function of Int is stripeColor(){
		if({ kind == 1 }, { return -13716885; });
		if({ kind == 2 }, { return -2651608; });
		if({ kind == 3 }, { return -2668478; });
		return activeTheme:textAccent;
	}

	replace Function of Boolean is tick(Int is nowMs){
		if({ !visible || autoHideMs <= 0 }, { return false; });
		if({ lastTickMs > 0 }, {
			local Int is dt: nowMs - lastTickMs;
			if({ dt > 0 && dt < 1000 }, {
				:elapsedMs: elapsedMs + dt;
				if({ elapsedMs >= autoHideMs }, {
					:lastTickMs: nowMs;
					:dismiss();
					return true;
				});
			});
		});
		:lastTickMs: nowMs;
		return false;
	}

	replace Function of Size is measure(Constraints is c){
		if({ !visible }, {
			desiredSize: Size(width: 0, height: 0);
			return desiredSize;
		});
		local Int is fpx: activeScale:px(pt: activeTheme:baseTextPt);
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is w: activeScale:px(pt: minWidthPt);
		local Int is h: pad * 2 + fpx + 4;
		if({ title != '' && message != '' }, {
			h: h + fpx + 2;
		});
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		if({ !visible }, { return; });
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is rad: activeScale:px(pt: activeTheme:panelCornerRadiusPt);
		ctx:drawStyledBox(
			x: b:x, y: b:y, w: b:width, h: b:height,
			bgColor: activeTheme:surfaceBg, borderColor: activeTheme:panelBorderColorArgb(),
			thickness: bw, radius: rad, style: activeTheme:panelBorderStyle
		);
		local Int is stripeW: activeScale:px(pt: 4.0);
		if({ stripeW < 3 }, { stripeW: 3; });
		ctx:fillRect(x: b:x + bw, y: b:y + bw, w: stripeW, h: b:height - bw * 2, color: :stripeColor());

		local Int is fpx: activeScale:px(pt: activeTheme:baseTextPt);
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is tx: b:x + bw + stripeW + pad;
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is textW: b:width - (tx - b:x) - pad * 2 - 14;
		if({ textW > 0 }, {
			ctx:setClip(x: tx, y: b:y + bw, w: textW, h: b:height - bw * 2);
			if({ title != '' && message != '' }, {
				ctx:drawText(x: tx, y: b:y + pad, text: title, color: activeTheme:textPrimary, pixelHeight: fpx, bold: true, italic: false, mono: false);
				ctx:drawText(x: tx, y: b:y + pad + th + 3, text: message, color: activeTheme:textMuted, pixelHeight: fpx);
			}, {
				local String is single: if({ title != '' }, { title }, { message });
				ctx:drawText(x: tx, y: b:y + (b:height - th) / 2, text: single, color: activeTheme:textPrimary, pixelHeight: fpx, bold: title != '', italic: false, mono: false);
			});
			ctx:clearClip();
		});

		local Int is xW: ctx:measureTextWidth(text: '×', pixelHeight: fpx);
		local Int is xCol: if({ hoveredClose }, { activeTheme:textAccent }, { activeTheme:textMuted });
		ctx:drawText(
			x: b:x + b:width - pad - xW,
			y: b:y + pad,
			text: '×',
			color: xCol,
			pixelHeight: fpx
		);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		if({ !visible || !:containsPoint(x: x, y: y) }, {
			if({ hoveredClose }, { :hoveredClose: false; :invalidate(); });
			return false;
		});
		local Rect is b: bounds();
		local Int is closeBox: activeScale:px(pt: 24.0);
		local Boolean is overX: x >= b:x + b:width - closeBox;
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
		if({ !visible || !:containsPoint(x: x, y: y) }, { return false; });
		local Rect is b: bounds();
		local Int is closeBox: activeScale:px(pt: 24.0);
		if({ x >= b:x + b:width - closeBox }, {
			:dismiss();
		});
		return true;
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ visible && :containsPoint(x: x, y: y) }, {
			local Rect is b: bounds();
			local Int is closeBox: activeScale:px(pt: 24.0);
			if({ x >= b:x + b:width - closeBox }, { return CursorShape:POINTER; });
		});
		return CursorShape:DEFAULT;
	}
}
