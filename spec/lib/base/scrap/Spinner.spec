#! Package base:scrap
#! Antialiased circular ring progress / throbber widget using the same theme background, border, and fill as [ProgressBar].

Class of SewNode is Spinner{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'math', as Math()],
		['base', 'fabric', Color],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale]
	];

	Float is sizePt: 26.0;
	Boolean is indeterminate: true;
	Float is progress: 0.0;
	Boolean is showLabel: false;
	String is label: '';

	Float is animPhase: 0.0;
	Int is lastTickMs: 0;

	replace Function is init(
		Float is sizePt: 26.0,
		Boolean is indeterminate: true,
		Float is progress: 0.0,
		Boolean is showLabel: false,
		String is label: '',
		String is tooltip: ''
	){
		:sizePt: sizePt;
		:indeterminate: indeterminate;
		:progress: :clamp01(v: progress);
		:showLabel: showLabel;
		:label: label;
		:tooltip: tooltip;
	}

	local Function of Float is clamp01(Float is v){
		if({ v < 0.0 }, { return 0.0; });
		if({ v > 1.0 }, { return 1.0; });
		return v;
	}

	Function is setProgress(Float is next){
		:progress: :clamp01(v: next);
		:invalidate();
	}

	replace Function of Boolean is tick(Int is nowMs){
		if({ !indeterminate }, { return false; });
		if({ lastTickMs > 0 }, {
			local Int is dt: nowMs - lastTickMs;
			if({ dt > 0 && dt < 500 }, {
				:animPhase: animPhase + (dt as Float) / 1100.0;
				while({ animPhase >= 1.0 }, { :animPhase: animPhase - 1.0; });
			});
		});
		:lastTickMs: nowMs;
		:invalidate();
		return true;
	}

	local Function of Float is fClamp01(Float is v){
		if({ v < 0.0 }, { return 0.0; });
		if({ v > 1.0 }, { return 1.0; });
		return v;
	}

	local Function of Int is blendArgb(Int is c0, Int is c1, Float is t){
		local Float is k: :fClamp01(v: t);
		local Int is a0: (c0 >> 24) & 255;
		local Int is r0: (c0 >> 16) & 255;
		local Int is g0: (c0 >> 8) & 255;
		local Int is b0: c0 & 255;
		local Int is a1: (c1 >> 24) & 255;
		local Int is r1: (c1 >> 16) & 255;
		local Int is g1: (c1 >> 8) & 255;
		local Int is b1: c1 & 255;
		local Int is a: a0 + ((((a1 - a0) as Float) * k) + 0.5) as Int;
		local Int is r: r0 + ((((r1 - r0) as Float) * k) + 0.5) as Int;
		local Int is g: g0 + ((((g1 - g0) as Float) * k) + 0.5) as Int;
		local Int is b: b0 + ((((b1 - b0) as Float) * k) + 0.5) as Int;
		return (a << 24) | (r << 16) | (g << 8) | b;
	}

	local Function of Int is scaleAlpha(Int is argb, Float is alpha){
		local Float is k: :fClamp01(v: alpha);
		local Int is srcA: (argb >> 24) & 255;
		local Int is a: ((((srcA as Float) * k)) + 0.5) as Int;
		if({ a <= 0 }, { return 0; });
		if({ a > 255 }, { a: 255; });
		return (a << 24) | (argb & 16777215);
	}

	replace Function of Size is measure(Constraints is c){
		local Int is sz: activeScale:px(pt: sizePt);
		if({ sz < 16 }, { sz: 16; });
		local Int is w: sz;
		if({ label != '' }, {
			local Int is fpx: activeScale:px(pt: activeTheme:baseTextPt);
			local Int is gap: activeScale:px(pt: activeTheme:paddingSmallPt);
			w: w + gap + (label:length() * fpx * 6) / 10;
		});
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: sz));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is sz: activeScale:px(pt: sizePt);
		if({ sz < 16 }, { sz: 16; });

		local Float is cx: (b:x as Float) + (sz as Float) * 0.5;
		local Float is cy: (b:y as Float) + (b:height as Float) * 0.5;
		local Float is outerR: (sz as Float) * 0.45;
		local Float is innerR: outerR * 0.60;
		local Int is bwPx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
		local Float is borderW: if({ bwPx > 0 }, { bwPx as Float }, { 1.0 });

		local Int is trackCol: activeTheme:hoverBg;
		local Int is fillCol: activeTheme:accent:mix(other: activeTheme:surface, t: 0.42):toArgb();
		local Int is borderCol: activeTheme:buttonBorderColorArgb();

		local Float is twoPi: 6.283185307;
		local Float is startAng: if({ indeterminate }, { animPhase * twoPi }, { 0.0 });
		local Float is sweepAng: if({ indeterminate }, { 1.75 }, { progress * twoPi });
		local Float is midR: (outerR + innerR) * 0.5;
		local Float is aaAng: if({ midR > 1.0 }, { 1.0 / midR }, { 0.08 });

		local Int is rCeil: (outerR + 2.0) as Int;
		local Int is cxInt: cx as Int;
		local Int is cyInt: cy as Int;
		local Int is py: cyInt - rCeil;
		local Int is yEnd: cyInt + rCeil;
		local Int is xStart: cxInt - rCeil;
		local Int is xEnd: cxInt + rCeil;

		while({ py <= yEnd }, {
			local Float is dy: ((py as Float) + 0.5) - cy;
			local Int is px: xStart;
			while({ px <= xEnd }, {
				local Float is dx: ((px as Float) + 0.5) - cx;
				local Float is dist: Math:sqrt(value: dx * dx + dy * dy);
				local Float is outerCov: :fClamp01(v: (outerR + 0.5) - dist);
				local Float is innerCov: :fClamp01(v: dist - (innerR - 0.5));
				local Float is ringCov: outerCov * innerCov;

				if({ ringCov > 0.01 }, {
					# Angle clockwise from 12 o'clock (-Y axis)
					local Float is ang: Math:atan2(y: dx, x: 0.0 - dy);
					if({ ang < 0.0 }, { ang: ang + twoPi; });

					local Float is rel: ang - startAng;
					while({ rel < 0.0 }, { rel: rel + twoPi; });
					while({ rel >= twoPi }, { rel: rel - twoPi; });

					local Float is arcCov: 0.0;
					if({ sweepAng >= twoPi - 0.001 }, {
						arcCov: 1.0;
					}, {
					if({ sweepAng > 0.001 }, {
						local Float is covStart: :fClamp01(v: rel / aaAng + 0.5);
						local Float is covEnd: :fClamp01(v: (sweepAng - rel) / aaAng + 0.5);
						if({ rel <= sweepAng + aaAng }, {
							arcCov: if({ covStart < covEnd }, { covStart }, { covEnd });
						});
					}); });

					local Int is interiorCol: :blendArgb(c0: trackCol, c1: fillCol, t: arcCov);
					local Float is bOuter: :fClamp01(v: dist - (outerR - borderW - 0.5));
					local Float is bInner: :fClamp01(v: (innerR + borderW + 0.5) - dist);
					local Float is bCov: if({ bOuter > bInner }, { bOuter }, { bInner });
					local Int is pxCol: :blendArgb(c0: interiorCol, c1: borderCol, t: bCov);
					local Int is outArgb: :scaleAlpha(argb: pxCol, alpha: ringCov);
					if({ outArgb != 0 }, {
						ctx:fillRect(x: px, y: py, w: 1, h: 1, color: outArgb);
					});
				});
				px: px + 1;
			});
			py: py + 1;
		});

		if({ showLabel && !indeterminate }, {
			local Int is pct: ((progress * 100.0) + 0.5) as Int;
			local String is pctTxt: (pct as String) . '%';
			local Int is fpx: activeScale:px(pt: activeTheme:baseTextPt * 0.78);
			if({ fpx < 8 }, { fpx: 8; });
			local Int is tw: ctx:measureTextWidth(text: pctTxt, pixelHeight: fpx);
			local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
			ctx:drawText(
				x: (cx as Int) - tw / 2,
				y: (cy as Int) - th / 2,
				text: pctTxt,
				color: activeTheme:textPrimary,
				pixelHeight: fpx,
				bold: true,
				italic: false,
				mono: false
			);
		});

		if({ label != '' }, {
			local Int is fpx: activeScale:px(pt: activeTheme:baseTextPt);
			local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
			local Int is gap: activeScale:px(pt: activeTheme:paddingSmallPt);
			ctx:drawText(
				x: b:x + sz + gap,
				y: b:y + (b:height - th) / 2,
				text: label,
				color: activeTheme:textMuted,
				pixelHeight: fpx
			);
		});
	}
}
