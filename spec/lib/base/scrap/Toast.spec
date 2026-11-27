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
		['base', 'sew', Scale],
		['base', 'scrap', ScrapButton]
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
	ScrapButton is closeBtn: ScrapButton();

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
		:closeBtn: ScrapButton(
			label: '×',
			minWidthPt: 18.0,
			heightPt: 18.0,
			padXPt: 3.0,
			tooltip: 'Dismiss',
			onClick: local Function(){ :dismiss(); }
		);
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		closeBtn:applyTheme(theme: theme);
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		closeBtn:setScale(scale: scale);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		closeBtn:bindDirty(cb: cb);
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

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		if({ !visible }, { return; });
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Size is cs: closeBtn:measure(c: Constraints(minW: 0, maxW: bounds:width, minH: 0, maxH: bounds:height));
		local Int is bx: bounds:x + bounds:width - bw - pad - cs:width;
		local Int is by: bounds:y + bw + pad / 2;
		closeBtn:arrange(bounds: Rect(x: bx, y: by, width: cs:width, height: cs:height));
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
		local Int is btnW: closeBtn:bounds():width;
		local Int is textW: b:width - (tx - b:x) - pad * 2 - btnW;
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
		closeBtn:paint(ctx: ctx);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		if({ !visible || !:containsPoint(x: x, y: y) }, {
			closeBtn:clearHover();
			return false;
		});
		closeBtn:onPointerMove(x: x, y: y);
		return true;
	}

	replace Function is clearHover(){
		closeBtn:clearHover();
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ !visible || !:containsPoint(x: x, y: y) }, { return false; });
		if({ closeBtn:onPointerClickMod(x: x, y: y, mods: mods) }, { return true; });
		return true;
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ visible && :containsPoint(x: x, y: y) }, {
			return closeBtn:cursorAt(x: x, y: y);
		});
		return CursorShape:DEFAULT;
	}
}
