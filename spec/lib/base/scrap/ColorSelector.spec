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
	Float is hueDeg: 210.0;
	Float is sat: 0.7;
	Float is light: 0.65;
	Int is dragTarget: 0;
	Function is onChange: local Function(Color is _c){};
	Function is onCommit: local Function(Color is _c){};

	replace Function is init(
		Color is color: Color(r: 100, g: 180, b: 255),
		Color is currentColor: Color(r: 100, g: 180, b: 255),
		Boolean is hasCurrent: false,
		Boolean is compact: false,
		Function is onChange: local Function(Color is _c){},
		Function is onCommit: local Function(Color is _c){}
	){
		:currentColor: currentColor;
		:hasCurrent: hasCurrent;
		:compact: compact;
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
		invalidate();
	}

	Function is setCurrentColor(Color is next, Boolean is hasCurrent: true){
		:currentColor: next;
		:hasCurrent: hasCurrent;
		invalidate();
	}

	local Function is syncFromHsl(){
		:color: Color:fromHsl(hDeg: hueDeg, s: sat, l: light);
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
			local Int is h: barH * 3 + gap * 3 + prevH;
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

		## Row 0: Hue, Row 1: Saturation, Row 2: Brightness/Lightness
		local Int is row: 0;
		while({ row < 3 }, {
			local Int is ry: b:y + row * (barH + gap);
			local String is lbl: if({ row == 0 }, { 'H' }, { if({ row == 1 }, { 'S' }, { 'L' }) });
			ctx:drawText(x: b:x, y: ry + (barH - th) / 2, text: lbl, color: activeTheme:textMuted, pixelHeight: fpx);
			local Int is xi: 0;
			while({ xi < barW }, {
				local Float is t: (xi as Float) / ((barW - 1) as Float);
				local Color is segC: if({ row == 0 }, {
					Color:fromHsl(hDeg: t * 360.0, s: 1.0, l: 0.5)
				}, {
					if({ row == 1 }, {
						Color:fromHsl(hDeg: hueDeg, s: t, l: light)
					}, {
						Color:fromHsl(hDeg: hueDeg, s: sat, l: t)
					})
				});
				ctx:fillRect(x: barX + xi, y: ry, w: 1, h: barH, color: segC:toArgb());
				xi: xi + 1;
			});
			if({ bw > 0 }, {
				ctx:strokeRect(x: barX, y: ry, w: barW, h: barH, color: activeTheme:buttonBorder, thickness: bw);
			});
			local Float is norm: if({ row == 0 }, { hueDeg / 360.0 }, { if({ row == 1 }, { sat }, { light }) });
			local Int is knobX: barX + ((norm * ((barW - 1) as Float)) + 0.5) as Int;
			:drawSlottedThumb(ctx: ctx, cx: knobX, topY: ry, barH: barH);
			row: row + 1;
		});

		## Row 3: Preview (current left | new right) + hex code
		local Int is py: b:y + 3 * (barH + gap);
		local Int is prevW: activeScale:px(pt: 56.0);
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
		ctx:drawText(x: b:x + prevW + activeScale:px(pt: 8.0), y: py + (prevH - th) / 2, text: color:toHex(), color: activeTheme:textPrimary, pixelHeight: fpx);
	}

	local Function is drawRingSlottedHandle(DrawContext is ctx, Int is cx, Int is cy, Float is angleRad, Int is rIn, Int is rOut){
		local Float is ux: cos(value: angleRad);
		local Float is uy: sin(value: angleRad);
		local Float is px: 0.0 - uy;
		local Float is py: ux;
		local Int is halfSlot: activeScale:px(pt: 2.5);
		if({ halfSlot < 2 }, { halfSlot: 2; });
		local Int is railCol: activeTheme:textPrimary;
		local Int is outlineCol: activeTheme:windowBg;

		local Int is r: rIn - 2;
		while({ r <= rOut + 2 }, {
			local Float is rf: r as Float;
			local Boolean is isCap: (r < rIn) || (r > rOut);
			local Int is off: 0 - (halfSlot + 2);
			while({ off <= halfSlot + 2 }, {
				local Int is aOff: if({ off < 0 }, { 0 - off }, { off });
				local Boolean is drawPx: isCap || (aOff >= halfSlot);
				if({ drawPx }, {
					local Int is col: if({ aOff > halfSlot + 1 || r == rIn - 2 || r == rOut + 2 }, { outlineCol }, { railCol });
					local Int is gx: cx + ((rf * ux + (off as Float) * px) + 0.5) as Int;
					local Int is gy: cy + ((rf * uy + (off as Float) * py) + 0.5) as Int;
					ctx:fillRect(x: gx, y: gy, w: 1, h: 1, color: col);
				});
				off: off + 1;
			});
			r: r + 1;
		});
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
		local Int is cx: b:x + b:width / 2;
		local Int is cy: b:y + ringD / 2;
		local Float is piVal: pi();

		local Int is dy: 0 - outerR;
		while({ dy <= outerR }, {
			local Int is dx: 0 - outerR;
			while({ dx <= outerR }, {
				local Int is d2: dx * dx + dy * dy;
				local Int is r: (sqrt(value: d2 as Float) + 0.5) as Int;
				if({ r >= outerInR && r <= outerR }, {
					local Float is deg: (atan2(y: dy as Float, x: dx as Float) * 180.0) / piVal;
					if({ deg < 0.0 }, { deg: deg + 360.0; });
					local Color is hc: Color:fromHsl(hDeg: deg, s: 1.0, l: 0.5);
					ctx:fillRect(x: cx + dx, y: cy + dy, w: 1, h: 1, color: hc:toArgb());
				}, {
				if({ r >= innerInR && r <= innerOutR }, {
					if({ dy <= 0 }, {
						local Float is ang: atan2(y: (0 - dy) as Float, x: (0 - dx) as Float);
						local Float is t: Color:clamp01(v: ang / piVal);
						local Color is sc: Color:fromHsl(hDeg: hueDeg, s: t, l: light);
						ctx:fillRect(x: cx + dx, y: cy + dy, w: 1, h: 1, color: sc:toArgb());
					}, {
						local Float is ang: atan2(y: dy as Float, x: (0 - dx) as Float);
						local Float is t: Color:clamp01(v: ang / piVal);
						local Color is lc: Color:fromHsl(hDeg: hueDeg, s: sat, l: t);
						ctx:fillRect(x: cx + dx, y: cy + dy, w: 1, h: 1, color: lc:toArgb());
					});
				}, {
				if({ r <= centerR }, {
					local Int is pcol: if({ hasCurrent && dx < 0 }, { currentColor:toArgb() }, { color:toArgb() });
					ctx:fillRect(x: cx + dx, y: cy + dy, w: 1, h: 1, color: pcol);
				}); }); });
				dx: dx + 1;
			});
			dy: dy + 1;
		});

		## Rotating slotted handles on Hue, Top Saturation, Bottom Lightness
		local Float is hueRad: (hueDeg * piVal) / 180.0;
		:drawRingSlottedHandle(ctx: ctx, cx: cx, cy: cy, angleRad: hueRad, rIn: outerInR, rOut: outerR);

		local Float is satRad: (sat - 1.0) * piVal;
		:drawRingSlottedHandle(ctx: ctx, cx: cx, cy: cy, angleRad: satRad, rIn: innerInR, rOut: innerOutR);

		local Float is lightRad: (1.0 - light) * piVal;
		:drawRingSlottedHandle(ctx: ctx, cx: cx, cy: cy, angleRad: lightRad, rIn: innerInR, rOut: innerOutR);

		## Readouts below: Hex, RGB, HSL
		local Int is ty0: b:y + ringD + gap;
		local Int is lineStep: fpx + activeScale:px(pt: 3.0);
		local Int is hInt: (hueDeg + 0.5) as Int;
		local Int is sInt: (sat * 100.0 + 0.5) as Int;
		local Int is lInt: (light * 100.0 + 0.5) as Int;
		local String is sHex: 'Hex: ' . color:toHex();
		local String is sRgb: 'RGB: ' . (color:red() as String) . ', ' . (color:green() as String) . ', ' . (color:blue() as String);
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
			if({ isPress }, {
				local Int is row: 0;
				while({ row < 3 }, {
					local Int is ry: b:y + row * (barH + gap);
					if({ x >= barX && x <= barX + barW && y >= ry - 4 && y <= ry + barH + 4 }, {
						:dragTarget: row + 1;
					});
					row: row + 1;
				});
			});
			if({ dragTarget >= 1 && dragTarget <= 3 }, {
				local Float is t: Color:clamp01(v: ((x - barX) as Float) / ((barW - 1) as Float));
				if({ dragTarget == 1 }, { :hueDeg: t * 360.0; });
				if({ dragTarget == 2 }, { :sat: t; });
				if({ dragTarget == 3 }, { :light: t; });
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

		if({ isPress }, {
			if({ r >= (outerInR - 4) as Float && r <= (outerR + 4) as Float }, {
				:dragTarget: 1;
			}, {
			if({ r >= (innerInR - 4) as Float && r <= (innerOutR + 4) as Float }, {
				:dragTarget: if({ dy <= 0 }, { 2 }, { 3 });
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
			local Int is clampedDy: if({ dy > 0 }, { 0 }, { dy });
			local Float is ang: atan2(y: (0 - clampedDy) as Float, x: (0 - dx) as Float);
			:sat: Color:clamp01(v: ang / piVal);
			:syncFromHsl();
			return true;
		});
		if({ dragTarget == 3 }, {
			local Int is clampedDy: if({ dy < 0 }, { 0 }, { dy });
			local Float is ang: atan2(y: clampedDy as Float, x: (0 - dx) as Float);
			:light: Color:clamp01(v: ang / piVal);
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
