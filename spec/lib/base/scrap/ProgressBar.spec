#! Package base:scrap
#! Determinate and indeterminate progress bar widget derived from [Theme].

Class of SewNode is ProgressBar{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Math()],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale]
	];

	Float is value: 0.0;
	Boolean is indeterminate: false;
	Boolean is showLabel: false;
	String is label: '';
	Float is minWidthPt: 160.0;
	Float is heightPt: 14.0;

	Float is animPhase: 0.0;
	Int is lastTickMs: 0;

	replace Function is init(
		Float is value: 0.0,
		Boolean is indeterminate: false,
		Boolean is showLabel: false,
		String is label: '',
		Float is minWidthPt: 160.0,
		Float is heightPt: 14.0,
		String is tooltip: ''
	){
		:value: :clamp01(v: value);
		:indeterminate: indeterminate;
		:showLabel: showLabel;
		:label: label;
		:minWidthPt: minWidthPt;
		:heightPt: heightPt;
		:tooltip: tooltip;
	}

	local Function of Float is clamp01(Float is v){
		if({ v < 0.0 }, { return 0.0; });
		if({ v > 1.0 }, { return 1.0; });
		return v;
	}

	Function is setValue(Float is next){
		:value: :clamp01(v: next);
		:invalidate();
	}

	Function is setIndeterminate(Boolean is next){
		:indeterminate: next;
		:invalidate();
	}

	replace Function of Boolean is tick(Int is nowMs){
		if({ !indeterminate }, { return false; });
		if({ lastTickMs > 0 }, {
			local Int is dt: nowMs - lastTickMs;
			if({ dt > 0 && dt < 500 }, {
				:animPhase: animPhase + math:toFloat(value: dt) / 1400.0;
				while({ animPhase >= 1.0 }, { :animPhase: animPhase - 1.0; });
			});
		});
		:lastTickMs: nowMs;
		:invalidate();
		return true;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is w: activeScale:px(pt: minWidthPt);
		local Int is h: activeScale:px(pt: heightPt);
		if({ showLabel }, {
			local Int is minH: activeScale:px(pt: activeTheme:baseTextPt) + 6;
			if({ h < minH }, { h: minH; });
		});
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is bw: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
		local Int is rad: b:height / 2;
		ctx:drawStyledBox(
			x: b:x, y: b:y, w: b:width, h: b:height,
			bgColor: activeTheme:hoverBg, borderColor: activeTheme:buttonBorderColorArgb(),
			thickness: bw, radius: rad, style: activeTheme:buttonBorderStyle
		);

		local Int is ins: bw;
		local Int is trackX: b:x + ins;
		local Int is trackY: b:y + ins;
		local Int is trackW: b:width - ins * 2;
		local Int is trackH: b:height - ins * 2;
		if({ trackW > 0 && trackH > 0 }, {
			local Int is fillRad: trackH / 2;
			ctx:setClip(x: trackX, y: trackY, w: trackW, h: trackH);
			if({ indeterminate }, {
				local Int is segW: trackW / 3;
				if({ segW < 18 }, { segW: 18; });
				local Int is span: trackW + segW;
				local Int is sx: trackX + math:toInt(value: animPhase * math:toFloat(value: span)) - segW;
				ctx:fillRoundRect(x: sx, y: trackY, w: segW, h: trackH, radius: fillRad, color: activeTheme:textAccent);
			}, {
				local Int is fillW: math:toInt(value: math:round(value: math:toFloat(value: trackW) * value));
				if({ fillW > 0 }, {
					ctx:fillRoundRect(x: trackX, y: trackY, w: fillW, h: trackH, radius: fillRad, color: activeTheme:textAccent);
				});
			});
			ctx:clearClip();
		});

		if({ showLabel }, {
			local String is txt: if({ label != '' }, {
				label
			}, {
				if({ indeterminate }, { '...' }, { ('' . math:toInt(value: math:round(value: value * 100.0))) . '%' })
			});
			local Int is fpx: activeScale:px(pt: activeTheme:baseTextPt * 0.85);
			if({ fpx < 9 }, { fpx: 9; });
			local Int is tw: ctx:measureTextWidth(text: txt, pixelHeight: fpx);
			local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
			ctx:drawText(
				x: b:x + (b:width - tw) / 2,
				y: b:y + (b:height - th) / 2,
				text: txt,
				color: activeTheme:textPrimary,
				pixelHeight: fpx,
				bold: true,
				italic: false,
				mono: false
			);
		});
	}
}
