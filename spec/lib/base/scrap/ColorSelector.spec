#! Package base:scrap
#! Standalone HSL/RGB color selector supporting `compact: true` (3 slotted bars + preview/hex) and default (concentric hue/sat/lightness rings + center preview + Hex/RGB/HSL).

Class of SewNode is ColorSelector{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'math', as Math()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', Color],
		['base', 'fabric', DrawContext]
	];

	Color is color: Color(r: 100, g: 180, b: 255);
	Color is currentColor: Color(r: 100, g: 180, b: 255);
	Boolean is hasCurrent: false;
	Boolean is compact: false;
	Boolean is showAlpha: false;
	Float is hueDeg: 210.0;
	Float is sat: 0.7;
	Float is light: 0.65;
	Float is alpha: 1.0;
	Int is dragTarget: 0;
	Function is onChange: local Function(Color is _c){};
	Function is onCommit: local Function(Color is _c){};

	replace Function is init(
		Color is color: Color(r: 100, g: 180, b: 255),
		Color is currentColor: Color(r: 100, g: 180, b: 255),
		Boolean is hasCurrent: false,
		Boolean is compact: false,
		Boolean is showAlpha: false,
		Function is onChange: local Function(Color is _c){},
		Function is onCommit: local Function(Color is _c){}
	){
		:currentColor: currentColor;
		:hasCurrent: hasCurrent;
		:compact: compact;
		:showAlpha: showAlpha;
		:onChange: onChange;
		:onCommit: onCommit;
		:dragTarget: 0;
		:setColor(next: color);
	}

	Function is setColor(Color is next){
		:color: next;
		local Float is s: next:saturation();
		local Float is l: next:lightness();
		if({ s > 0.001 }, {
			:hueDeg: next:hueDeg();
		});
		:sat: s;
		:light: l;
		:alpha: if({ showAlpha }, { next:alphaF() }, { 1.0 });
		invalidate();
	}

	Function is setCurrentColor(Color is next, Boolean is hasCurrent: true){
		:currentColor: next;
		:hasCurrent: hasCurrent;
		invalidate();
	}

	local Function is syncFromHsl(){
		local Int is ab: if({ showAlpha }, { ((alpha * 255.0) + 0.5) as Int }, { 255 });
		:color: Color:fromHsl(hDeg: hueDeg, s: sat, l: light, a: ab);
		local Function is cb: onChange;
		cb(color);
		invalidate();
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 13.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	replace Function of Size is measure(Constraints is c){
		if({ compact }, {
			local Int is w: activeScale:px(pt: 200.0);
			local Int is barH: activeScale:px(pt: 16.0);
			local Int is gap: activeScale:px(pt: 6.0);
			local Int is prevH: activeScale:px(pt: 20.0);
			local Int is barCount: if({ showAlpha }, { 4 }, { 3 });
			local Int is h: barH * barCount + gap * barCount + prevH;
			desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
			return desiredSize;
		});
		local Int is ringD: activeScale:px(pt: 170.0);
		local Int is fpx: :fontPx();
		local Int is gap: activeScale:px(pt: 6.0);
		local Int is textH: (fpx + activeScale:px(pt: 3.0)) * 3;
		local Int is w: ringD + activeScale:px(pt: 16.0);
		if({ w < activeScale:px(pt: 196.0) }, { w: activeScale:px(pt: 196.0); });
		local Int is h: ringD + gap + textH;
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	local Function is drawSlottedThumb(DrawContext is ctx, Int is cx, Int is topY, Int is barH){
		local Int is slotW: activeScale:px(pt: 4.0);
		if({ slotW < 3 }, { slotW: 3; });
		local Int is wall: activeScale:px(pt: 2.0);
		if({ wall < 2 }, { wall: 2; });
		local Int is padY: activeScale:px(pt: 2.0);
		if({ padY < 2 }, { padY: 2; });
		local Int is x0: cx - slotW / 2 - wall;
		local Int is y0: topY - padY;
		local Int is w0: slotW + wall * 2;
		local Int is h0: barH + padY * 2;
		local Int is outerCol: activeTheme:textPrimary;
		local Int is innerCol: activeTheme:windowBg;
		ctx:fillRect(x: x0, y: y0, w: w0, h: wall, color: outerCol);
		ctx:fillRect(x: x0, y: y0 + h0 - wall, w: w0, h: wall, color: outerCol);
		ctx:fillRect(x: x0, y: y0, w: wall, h: h0, color: outerCol);
		ctx:fillRect(x: x0 + w0 - wall, y: y0, w: wall, h: h0, color: outerCol);
		ctx:strokeRect(x: x0, y: y0, w: w0, h: h0, color: innerCol, thickness: 1);
	}

	local Function of Color is checkerAt(Int is px, Int is py){
		local Int is chk: ((px / 4) + (py / 4)) & 1;
		return if({ chk == 0 }, { Color(r: 200, g: 200, b: 200) }, { Color(r: 130, g: 130, b: 130) });
	}

	local Function is drawCheckerRect(DrawContext is ctx, Int is x, Int is y, Int is w, Int is h){
		local Int is cy: 0;
		while({ cy < h }, {
			local Int is ch: if({ cy + 4 <= h }, { 4 }, { h - cy });
			local Int is cx: 0;
			while({ cx < w }, {
				local Int is cw: if({ cx + 4 <= w }, { 4 }, { w - cx });
				local Color is cc: :checkerAt(px: x + cx, py: y + cy);
				ctx:fillRect(x: x + cx, y: y + cy, w: cw, h: ch, color: cc:toArgb());
				cx: cx + 4;
			});
			cy: cy + 4;
		});
	}

	local Function is drawCompact(DrawContext is ctx, Rect is b){
		local Int is barH: activeScale:px(pt: 16.0);
		local Int is gap: activeScale:px(pt: 6.0);
		local Int is prevH: activeScale:px(pt: 20.0);
		local Int is labelW: activeScale:px(pt: 16.0);
		local Int is barX: b:x + labelW;
		local Int is barW: b:width - labelW - activeScale:px(pt: 4.0);
		if({ barW < 20 }, { return; });
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is bw: activeTheme:borderPx(scaleFactor: activeScale:factor);
		local Int is barCount: if({ showAlpha }, { 4 }, { 3 });
		local Color is baseCol: Color:fromHsl(hDeg: hueDeg, s: sat, l: light);

		## Row 0: Hue, Row 1: Saturation, Row 2: Lightness, optional Row 3: Alpha
		local Int is row: 0;
		while({ row < barCount }, {
			local Int is ry: b:y + row * (barH + gap);
			local String is lbl: if({ row == 0 }, { 'H' }, { if({ row == 1 }, { 'S' }, { if({ row == 2 }, { 'L' }, { 'A' }) }) });
			ctx:drawText(x: b:x, y: ry + (barH - th) / 2, text: lbl, color: activeTheme:textMuted, pixelHeight: fpx);
			if({ row == 3 }, {
				:drawCheckerRect(ctx: ctx, x: barX, y: ry, w: barW, h: barH);
			});
			local Int is xi: 0;
			while({ xi < barW }, {
				local Float is t: (xi as Float) / ((barW - 1) as Float);
				local Color is segC: if({ row == 0 }, {
					Color:fromHsl(hDeg: t * 360.0, s: 1.0, l: 0.5)
				}, {
					if({ row == 1 }, {
						Color:fromHsl(hDeg: hueDeg, s: t, l: light)
					}, {
						if({ row == 2 }, {
							Color:fromHsl(hDeg: hueDeg, s: sat, l: t)
						}, {
							baseCol:withAlpha(a: t)
						})
					})
				});
				ctx:fillRect(x: barX + xi, y: ry, w: 1, h: barH, color: segC:toArgb());
				xi: xi + 1;
			});
			if({ bw > 0 }, {
				ctx:strokeRect(x: barX, y: ry, w: barW, h: barH, color: activeTheme:buttonBorder, thickness: bw);
			});
			local Float is norm: if({ row == 0 }, { hueDeg / 360.0 }, { if({ row == 1 }, { sat }, { if({ row == 2 }, { light }, { alpha }) }) });
			local Int is knobX: barX + ((norm * ((barW - 1) as Float)) + 0.5) as Int;
			:drawSlottedThumb(ctx: ctx, cx: knobX, topY: ry, barH: barH);
			row: row + 1;
		});

		## Preview (current left | new right) + hex code
		local Int is py: b:y + barCount * (barH + gap);
		local Int is prevW: activeScale:px(pt: 56.0);
		if({ showAlpha }, {
			:drawCheckerRect(ctx: ctx, x: b:x, y: py, w: prevW, h: prevH);
		});
		if({ hasCurrent }, {
			local Int is halfW: prevW / 2;
			ctx:fillRect(x: b:x, y: py, w: halfW, h: prevH, color: currentColor:toArgb());
			ctx:fillRect(x: b:x + halfW, y: py, w: prevW - halfW, h: prevH, color: color:toArgb());
		}, {
			ctx:fillRect(x: b:x, y: py, w: prevW, h: prevH, color: color:toArgb());
		});
		if({ bw > 0 }, {
			ctx:strokeRect(x: b:x, y: py, w: prevW, h: prevH, color: activeTheme:buttonBorder, thickness: bw);
		});
		local String is hexTxt: if({ showAlpha }, { color:toHexAlpha() }, { color:toHex() });
		ctx:drawText(x: b:x + prevW + activeScale:px(pt: 8.0), y: py + (prevH - th) / 2, text: hexTxt, color: activeTheme:textPrimary, pixelHeight: fpx);
	}

	local Function is drawRingSlottedHandle(DrawContext is ctx, Int is cx, Int is cy, Float is angleRad, Int is rIn, Int is rOut, Float is shiftX: 0.0, Float is shiftY: 0.0){
		local Float is ux: cos(value: angleRad);
		local Float is uy: sin(value: angleRad);
		local Float is px: 0.0 - uy;
		local Float is py: ux;
		local Float is halfSlot: activeScale:px(pt: 2.0) as Float;
		if({ halfSlot < 2.0 }, { halfSlot: 2.0; });
		local Float is wall: 2.0;
		local Float is rShift: shiftX * ux + shiftY * uy;
		local Float is rMin: (rIn as Float) - 1.5 - rShift;
		local Float is rMax: (rOut as Float) + 1.5 - rShift;
		local Float is sMin: (rIn as Float) + 1.5 - rShift;
		local Float is sMax: (rOut as Float) - 1.5 - rShift;
		local Float is halfOuter: halfSlot + wall;
		local Color is railCol: Color:fromArgb(argb: activeTheme:textPrimary);
		local Color is outlineCol: Color:fromArgb(argb: activeTheme:windowBg);

		local Float is cxBase: (cx as Float) + shiftX;
		local Float is cyBase: (cy as Float) + shiftY;
		local Float is rMid: (rMin + rMax) * 0.5;
		local Int is hcx: ((cxBase + rMid * ux) + 0.5) as Int;
		local Int is hcy: ((cyBase + rMid * uy) + 0.5) as Int;
		local Int is boxR: ((rMax - rMin) * 0.5 + halfOuter + 3.0) as Int;

		local Int is sy: hcy - boxR;
		while({ sy <= hcy + boxR }, {
			local Int is sx: hcx - boxR;
			while({ sx <= hcx + boxR }, {
				local Float is dx: (sx as Float) - cxBase;
				local Float is dy: (sy as Float) - cyBase;
				local Float is along: dx * ux + dy * uy;
				local Float is perp: dx * px + dy * py;
				local Float is absPerp: if({ perp < 0.0 }, { 0.0 - perp }, { perp });

				local Float is dAlong: if({ (rMax - along) < (along - rMin) }, { rMax - along }, { along - rMin });
				local Float is dPerp: halfOuter - absPerp;
				local Float is outerDist: if({ dAlong < dPerp }, { dAlong }, { dPerp });

				local Float is sdAlong: if({ (sMax - along) < (along - sMin) }, { sMax - along }, { along - sMin });
				local Float is sdPerp: halfSlot - absPerp;
				local Float is slotDist: if({ sdAlong < sdPerp }, { sdAlong }, { sdPerp });

				local Float is negSlot: 0.0 - slotDist;
				local Float is frameDist: if({ outerDist < negSlot }, { outerDist }, { negSlot });
				if({ frameDist >= -0.75 }, {
					:paintAaBorderedPixel(ctx: ctx, px: sx, py: sy, fillC: railCol, borderC: outlineCol, edgeDist: frameDist, bw: 0.85);
				});
				sx: sx + 1;
			});
			sy: sy + 1;
		});
	}

	local Function is paintAaBorderedPixel(DrawContext is ctx, Int is px, Int is py, Color is fillC, Color is borderC, Float is edgeDist, Float is bw){
		if({ edgeDist < -0.75 }, { return; });
		if({ edgeDist >= bw + 0.5 }, {
			ctx:fillRect(x: px, y: py, w: 1, h: 1, color: fillC:toArgb());
			return;
		});
		local Float is bMix: Color:clamp01(v: (bw + 0.5) - edgeDist);
		local Color is blended: fillC:mix(other: borderC, t: bMix);
		local Float is cov: Color:clamp01(v: (edgeDist + 0.75) / 1.25);
		local Int is ab: ((cov * 255.0) + 0.5) as Int;
		if({ ab <= 0 }, { return; });
		ctx:fillRect(x: px, y: py, w: 1, h: 1, color: blended:withAlphaByte(a: ab):toArgb());
	}

	local Function of Float is innerRingEdgeAngle(Int is innerInR, Float is halfGapF){
		local Float is halfSlot: activeScale:px(pt: 2.0) as Float;
		if({ halfSlot < 2.0 }, { halfSlot: 2.0; });
		local Float is halfOuter: halfSlot + 2.0;
		local Float is rMin: (innerInR as Float) - 1.5;
		if({ rMin < 1.0 }, { rMin: 1.0; });
		local Float is ratio: (halfGapF + halfOuter) / rMin;
		if({ ratio > 0.45 }, { ratio: 0.45; });
		if({ ratio < 0.0 }, { ratio: 0.0; });
		return asin(value: ratio);
	}

	local Function is drawThirdRingHandle(DrawContext is ctx, Int is cx, Int is cy, Float is t, Float is aStart, Float is aEnd, Int is rIn, Int is rOut, Float is halfGapF){
		local Float is ct: Color:clamp01(v: t);
		local Float is ang: aStart + ct * (aEnd - aStart);
		local Float is sx: 0.0;
		local Float is sy: 0.0;
		if({ ct < 0.5 }, {
			local Float is w: 1.0 - 2.0 * ct;
			local Float is w2: w * w;
			sx: w2 * halfGapF * (0.0 - sin(value: aStart));
			sy: w2 * halfGapF * cos(value: aStart);
		}, {
			local Float is w: 2.0 * ct - 1.0;
			local Float is w2: w * w;
			sx: w2 * halfGapF * sin(value: aEnd);
			sy: w2 * halfGapF * (0.0 - cos(value: aEnd));
		});
		:drawRingSlottedHandle(ctx: ctx, cx: cx, cy: cy, angleRad: ang, rIn: rIn, rOut: rOut, shiftX: sx, shiftY: sy);
	}

	local Function of Float is sectorGapDist(Float is dx, Float is dy, Float is aStart, Float is aEnd, Float is halfGapF){
		local Float is dStart: dx * (0.0 - sin(value: aStart)) + dy * cos(value: aStart) - halfGapF;
		local Float is dEnd: dx * sin(value: aEnd) - dy * cos(value: aEnd) - halfGapF;
		return if({ dStart < dEnd }, { dStart }, { dEnd });
	}

	local Function of Float is sectorT(Float is dx, Float is dy, Float is aStart, Float is trim, Float is span){
		local Float is piVal: pi();
		local Float is twoPi: 2.0 * piVal;
		local Float is rel: atan2(y: dy, x: dx) - aStart;
		while({ rel < -0.75 }, { rel: rel + twoPi; });
		while({ rel >= twoPi - 0.75 }, { rel: rel - twoPi; });
		return Color:clamp01(v: (rel - trim) / span);
	}

	local Function is drawFull(DrawContext is ctx, Rect is b){
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is gap: activeScale:px(pt: 6.0);
		local Int is textH: (fpx + activeScale:px(pt: 3.0)) * 3;
		local Int is availH: b:height - gap - textH;
		local Int is ringD: if({ b:width < availH }, { b:width }, { availH });
		if({ ringD < 60 }, { return; });

		local Int is outerR: ringD / 2 - 4;
		local Int is outerInR: (outerR * 74) / 100;
		local Int is innerOutR: (outerR * 68) / 100;
		local Int is innerInR: (outerR * 44) / 100;
		local Int is centerR: (outerR * 36) / 100;
		local Float is ringGap: (outerInR - innerOutR) as Float;
		if({ ringGap < 4.0 }, { ringGap: 4.0; });
		local Float is halfGapF: ringGap * 0.5;
		local Float is bw: activeTheme:borderPx(scaleFactor: activeScale:factor) as Float;
		if({ bw < 1.0 }, { bw: 1.0; });
		local Color is borderC: Color:fromArgb(argb: activeTheme:buttonBorder);
		local Int is cx: b:x + b:width / 2;
		local Int is cy: b:y + ringD / 2;
		local Float is piVal: pi();
		local Float is thirdSpan: (2.0 * piVal) / 3.0;
		local Float is satStart: -5.0 * piVal / 6.0;
		local Float is satEnd: -piVal / 6.0;
		local Float is alpStart: -piVal / 6.0;
		local Float is alpEnd: piVal / 2.0;
		local Float is litStart: piVal / 2.0;
		local Float is litEnd: 7.0 * piVal / 6.0;
		local Color is baseCol: Color:fromHsl(hDeg: hueDeg, s: sat, l: light);

		local Int is dy: 0 - (outerR + 1);
		while({ dy <= outerR + 1 }, {
			local Int is dx: 0 - (outerR + 1);
			while({ dx <= outerR + 1 }, {
				local Int is d2: dx * dx + dy * dy;
				local Float is rf: sqrt(value: d2 as Float);
				local Float is outerEdge: (outerR as Float) - rf;
				local Float is outerInEdge: rf - (outerInR as Float);
				local Float is hueDist: if({ outerEdge < outerInEdge }, { outerEdge }, { outerInEdge });
				if({ hueDist >= -0.75 }, {
					local Float is deg: (atan2(y: dy as Float, x: dx as Float) * 180.0) / piVal;
					if({ deg < 0.0 }, { deg: deg + 360.0; });
					local Color is hc: Color:fromHsl(hDeg: deg, s: 1.0, l: 0.5);
					:paintAaBorderedPixel(ctx: ctx, px: cx + dx, py: cy + dy, fillC: hc, borderC: borderC, edgeDist: hueDist, bw: bw);
				}, {
					local Float is inOutEdge: (innerOutR as Float) - rf;
					local Float is inInEdge: rf - (innerInR as Float);
					local Float is inRadDist: if({ inOutEdge < inInEdge }, { inOutEdge }, { inInEdge });
					if({ showAlpha }, {
						local Float is dSat: :sectorGapDist(dx: dx as Float, dy: dy as Float, aStart: satStart, aEnd: satEnd, halfGapF: halfGapF);
						local Float is dAlp: :sectorGapDist(dx: dx as Float, dy: dy as Float, aStart: alpStart, aEnd: alpEnd, halfGapF: halfGapF);
						local Float is dLit: :sectorGapDist(dx: dx as Float, dy: dy as Float, aStart: litStart, aEnd: litEnd, halfGapF: halfGapF);
						local Float is maxGap: if({ dSat >= dAlp && dSat >= dLit }, { dSat }, { if({ dAlp >= dLit }, { dAlp }, { dLit }) });
						local Float is thirdDist: if({ inRadDist < maxGap }, { inRadDist }, { maxGap });
						if({ thirdDist >= -0.75 }, {
							if({ dSat >= dAlp && dSat >= dLit }, {
								local Float is t: :sectorT(dx: dx as Float, dy: dy as Float, aStart: satStart, trim: 0.0, span: thirdSpan);
								local Color is sc: Color:fromHsl(hDeg: hueDeg, s: t, l: light);
								:paintAaBorderedPixel(ctx: ctx, px: cx + dx, py: cy + dy, fillC: sc, borderC: borderC, edgeDist: thirdDist, bw: bw);
							}, {
								if({ dAlp >= dLit }, {
									local Float is t: :sectorT(dx: dx as Float, dy: dy as Float, aStart: alpStart, trim: 0.0, span: thirdSpan);
									local Color is chkBg: :checkerAt(px: cx + dx, py: cy + dy);
									local Color is ac: chkBg:mix(other: baseCol, t: 1.0 - t);
									:paintAaBorderedPixel(ctx: ctx, px: cx + dx, py: cy + dy, fillC: ac, borderC: borderC, edgeDist: thirdDist, bw: bw);
								}, {
									local Float is t: :sectorT(dx: dx as Float, dy: dy as Float, aStart: litStart, trim: 0.0, span: thirdSpan);
									local Color is lc: Color:fromHsl(hDeg: hueDeg, s: sat, l: t);
									:paintAaBorderedPixel(ctx: ctx, px: cx + dx, py: cy + dy, fillC: lc, borderC: borderC, edgeDist: thirdDist, bw: bw);
								});
							});
						}, {
							local Float is centerDist: (centerR as Float) - rf;
							if({ centerDist >= -0.75 }, {
								local Color is pcol: if({ hasCurrent && dx < 0 }, { currentColor }, { color });
								local Color is chkBg: :checkerAt(px: cx + dx, py: cy + dy);
								local Color is pcolDraw: chkBg:mix(other: pcol, t: pcol:alphaF());
								:paintAaBorderedPixel(ctx: ctx, px: cx + dx, py: cy + dy, fillC: pcolDraw, borderC: borderC, edgeDist: centerDist, bw: bw);
							});
						});
					}, {
						local Int is absDyInt: if({ dy < 0 }, { 0 - dy }, { dy });
						local Float is absDy: absDyInt as Float;
						local Float is gapEdge: absDy - halfGapF;
						local Float is halfRingDist: if({ inRadDist < gapEdge }, { inRadDist }, { gapEdge });
						if({ halfRingDist >= -0.75 }, {
							if({ dy <= 0 }, {
								local Float is adjDy: ((0 - dy) as Float) - halfGapF;
								if({ adjDy < 0.0 }, { adjDy: 0.0; });
								local Float is ang: atan2(y: adjDy, x: (0 - dx) as Float);
								local Float is t: Color:clamp01(v: ang / piVal);
								local Color is sc: Color:fromHsl(hDeg: hueDeg, s: t, l: light);
								:paintAaBorderedPixel(ctx: ctx, px: cx + dx, py: cy + dy, fillC: sc, borderC: borderC, edgeDist: halfRingDist, bw: bw);
							}, {
								local Float is adjDy: (dy as Float) - halfGapF;
								if({ adjDy < 0.0 }, { adjDy: 0.0; });
								local Float is ang: atan2(y: adjDy, x: (0 - dx) as Float);
								local Float is t: Color:clamp01(v: ang / piVal);
								local Color is lc: Color:fromHsl(hDeg: hueDeg, s: sat, l: t);
								:paintAaBorderedPixel(ctx: ctx, px: cx + dx, py: cy + dy, fillC: lc, borderC: borderC, edgeDist: halfRingDist, bw: bw);
							});
						}, {
							local Float is centerDist: (centerR as Float) - rf;
							if({ centerDist >= -0.75 }, {
								local Color is pcol: if({ hasCurrent && dx < 0 }, { currentColor }, { color });
								:paintAaBorderedPixel(ctx: ctx, px: cx + dx, py: cy + dy, fillC: pcol, borderC: borderC, edgeDist: centerDist, bw: bw);
							});
						});
					});
				});
				dx: dx + 1;
			});
			dy: dy + 1;
		});

		## Rotating slotted handles on Hue + inner segments
		local Float is hueRad: (hueDeg * piVal) / 180.0;
		:drawRingSlottedHandle(ctx: ctx, cx: cx, cy: cy, angleRad: hueRad, rIn: outerInR, rOut: outerR);

		if({ showAlpha }, {
			:drawThirdRingHandle(ctx: ctx, cx: cx, cy: cy, t: sat, aStart: satStart, aEnd: satEnd, rIn: innerInR, rOut: innerOutR, halfGapF: halfGapF);
			:drawThirdRingHandle(ctx: ctx, cx: cx, cy: cy, t: light, aStart: litStart, aEnd: litEnd, rIn: innerInR, rOut: innerOutR, halfGapF: halfGapF);
			:drawThirdRingHandle(ctx: ctx, cx: cx, cy: cy, t: 1.0 - alpha, aStart: alpStart, aEnd: alpEnd, rIn: innerInR, rOut: innerOutR, halfGapF: halfGapF);
		}, {
			local Float is satRad: (sat - 1.0) * piVal;
			local Float is satCos: cos(value: satRad);
			:drawRingSlottedHandle(ctx: ctx, cx: cx, cy: cy, angleRad: satRad, rIn: innerInR, rOut: innerOutR, shiftY: 0.0 - halfGapF * satCos * satCos);

			local Float is lightRad: (1.0 - light) * piVal;
			local Float is lightCos: cos(value: lightRad);
			:drawRingSlottedHandle(ctx: ctx, cx: cx, cy: cy, angleRad: lightRad, rIn: innerInR, rOut: innerOutR, shiftY: halfGapF * lightCos * lightCos);
		});

		## Readouts below: Hex, RGB/RGBA, HSL
		local Int is ty0: b:y + ringD + gap;
		local Int is lineStep: fpx + activeScale:px(pt: 3.0);
		local Int is hInt: (hueDeg + 0.5) as Int;
		local Int is sInt: (sat * 100.0 + 0.5) as Int;
		local Int is lInt: (light * 100.0 + 0.5) as Int;
		local Int is aInt: (alpha * 100.0 + 0.5) as Int;
		local String is sHex: 'Hex: ' . if({ showAlpha }, { color:toHexAlpha() }, { color:toHex() });
		local String is sRgb: if({ showAlpha }, {
			'RGBA: ' . (color:red() as String) . ', ' . (color:green() as String) . ', ' . (color:blue() as String) . ', ' . (aInt as String) . '%'
		}, {
			'RGB: ' . (color:red() as String) . ', ' . (color:green() as String) . ', ' . (color:blue() as String)
		});
		local String is sHsl: 'HSL: ' . (hInt as String) . 'deg, ' . (sInt as String) . '%, ' . (lInt as String) . '%';
		ctx:drawText(x: b:x + activeScale:px(pt: 4.0), y: ty0, text: sHex, color: activeTheme:textPrimary, pixelHeight: fpx);
		ctx:drawText(x: b:x + activeScale:px(pt: 4.0), y: ty0 + lineStep, text: sRgb, color: activeTheme:textMuted, pixelHeight: fpx);
		ctx:drawText(x: b:x + activeScale:px(pt: 4.0), y: ty0 + lineStep * 2, text: sHsl, color: activeTheme:textMuted, pixelHeight: fpx);
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		if({ compact }, {
			:drawCompact(ctx: ctx, b: b);
		}, {
			:drawFull(ctx: ctx, b: b);
		});
	}

	local Function of Boolean is handlePointer(Int is x, Int is y, Boolean is isPress){
		local Rect is b: bounds();
		if({ compact }, {
			local Int is barH: activeScale:px(pt: 16.0);
			local Int is gap: activeScale:px(pt: 6.0);
			local Int is labelW: activeScale:px(pt: 16.0);
			local Int is barX: b:x + labelW;
			local Int is barW: b:width - labelW - activeScale:px(pt: 4.0);
			if({ barW <= 1 }, { return false; });
			local Int is barCount: if({ showAlpha }, { 4 }, { 3 });
			if({ isPress }, {
				local Int is row: 0;
				while({ row < barCount }, {
					local Int is ry: b:y + row * (barH + gap);
					if({ x >= barX && x <= barX + barW && y >= ry - 4 && y <= ry + barH + 4 }, {
						:dragTarget: row + 1;
					});
					row: row + 1;
				});
			});
			if({ dragTarget >= 1 && dragTarget <= barCount }, {
				local Float is t: Color:clamp01(v: ((x - barX) as Float) / ((barW - 1) as Float));
				if({ dragTarget == 1 }, { :hueDeg: t * 360.0; });
				if({ dragTarget == 2 }, { :sat: t; });
				if({ dragTarget == 3 }, { :light: t; });
				if({ dragTarget == 4 }, { :alpha: t; });
				:syncFromHsl();
				return true;
			});
			return false;
		});

		local Int is gap: activeScale:px(pt: 6.0);
		local Int is fpx: :fontPx();
		local Int is textH: (fpx + activeScale:px(pt: 3.0)) * 3;
		local Int is availH: b:height - gap - textH;
		local Int is ringD: if({ b:width < availH }, { b:width }, { availH });
		if({ ringD < 60 }, { return false; });
		local Int is outerR: ringD / 2 - 4;
		local Int is outerInR: (outerR * 74) / 100;
		local Int is innerOutR: (outerR * 68) / 100;
		local Int is innerInR: (outerR * 44) / 100;
		local Int is cx: b:x + b:width / 2;
		local Int is cy: b:y + ringD / 2;
		local Int is dx: x - cx;
		local Int is dy: y - cy;
		local Float is r: sqrt(value: (dx * dx + dy * dy) as Float);
		local Float is piVal: pi();
		local Float is ringGap: (outerInR - innerOutR) as Float;
		if({ ringGap < 4.0 }, { ringGap: 4.0; });
		local Float is halfGapF: ringGap * 0.5;
		local Float is thirdSpan: (2.0 * piVal) / 3.0;
		local Float is satStart: -5.0 * piVal / 6.0;
		local Float is alpStart: -piVal / 6.0;
		local Float is litStart: piVal / 2.0;

		if({ isPress }, {
			if({ r >= (outerInR - 4) as Float && r <= (outerR + 4) as Float }, {
				:dragTarget: 1;
			}, {
			if({ r >= (innerInR - 4) as Float && r <= (innerOutR + 4) as Float }, {
				if({ showAlpha }, {
					local Float is ang: atan2(y: dy as Float, x: dx as Float);
					if({ ang >= satStart && ang < alpStart }, {
						:dragTarget: 2;
					}, {
						if({ ang >= alpStart && ang < litStart }, {
							:dragTarget: 4;
						}, {
							:dragTarget: 3;
						});
					});
				}, {
					:dragTarget: if({ dy <= 0 }, { 2 }, { 3 });
				});
			}); });
		});

		if({ dragTarget == 1 }, {
			local Float is deg: (atan2(y: dy as Float, x: dx as Float) * 180.0) / piVal;
			if({ deg < 0.0 }, { deg: deg + 360.0; });
			:hueDeg: deg;
			:syncFromHsl();
			return true;
		});
		if({ dragTarget == 2 }, {
			if({ showAlpha }, {
				:sat: :sectorT(dx: dx as Float, dy: dy as Float, aStart: satStart, trim: 0.0, span: thirdSpan);
			}, {
				local Float is adjDy: ((0 - dy) as Float) - halfGapF;
				if({ adjDy < 0.0 }, { adjDy: 0.0; });
				local Float is ang: atan2(y: adjDy, x: (0 - dx) as Float);
				:sat: Color:clamp01(v: ang / piVal);
			});
			:syncFromHsl();
			return true;
		});
		if({ dragTarget == 3 }, {
			if({ showAlpha }, {
				:light: :sectorT(dx: dx as Float, dy: dy as Float, aStart: litStart, trim: 0.0, span: thirdSpan);
			}, {
				local Float is adjDy: (dy as Float) - halfGapF;
				if({ adjDy < 0.0 }, { adjDy: 0.0; });
				local Float is ang: atan2(y: adjDy, x: (0 - dx) as Float);
				:light: Color:clamp01(v: ang / piVal);
			});
			:syncFromHsl();
			return true;
		});
		if({ dragTarget == 4 && showAlpha }, {
			local Float is t: :sectorT(dx: dx as Float, dy: dy as Float, aStart: alpStart, trim: 0.0, span: thirdSpan);
			:alpha: 1.0 - t;
			:syncFromHsl();
			return true;
		});
		return false;
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return :handlePointer(x: x, y: y, isPress: true);
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ dragTarget > 0 }, {
			return :handlePointer(x: x, y: y, isPress: false);
		});
		return false;
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		if({ dragTarget > 0 }, {
			:dragTarget: 0;
			local Function is cb: onCommit;
			cb(color);
			return true;
		});
		return false;
	}
}
