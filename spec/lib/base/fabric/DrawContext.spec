#! Package base:fabric
#! 2D software drawing context targeting a `SuitCanvas` (ARGB8888) and using `base:sys:Font`.

Class is DrawContext{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()],
		['base', 'sys', Font],
		['base', 'math', as Math()],
		['base', 'struct', Array],
		['base', 'suit', SuitCanvas],
		['base', 'fabric', Color]
	];

	held Font is sharedFont: Font();
	held Font is sharedBoldFont: Font();
	held Font is sharedItalicFont: Font();
	held Font is sharedBoldItalicFont: Font();
	held Font is sharedMonoFont: Font();
	held Font is sharedMonoBoldFont: Font();
	held Font is sharedMonoItalicFont: Font();
	held Font is sharedMonoBoldItalicFont: Font();
	held Array of Int is sharedFontState: Array([0, 0, 0, 0, 0, 0, 0, 0]);
	held DrawContext is shared: DrawContext(canvas: SuitCanvas(width: 1, height: 1));

	SuitCanvas is canvas: SuitCanvas(width: 1, height: 1);
	Boolean is hasClip: false;
	Int is clipX: 0;
	Int is clipY: 0;
	Int is clipW: 0;
	Int is clipH: 0;
	Array of Boolean is clipStackHas: Array();
	Array of Int is clipStackX: Array();
	Array of Int is clipStackY: Array();
	Array of Int is clipStackW: Array();
	Array of Int is clipStackH: Array();

	replace Function is init(SuitCanvas is canvas){
		:canvas: canvas;
		:hasClip: false;
		:clipStackHas: Array();
		:clipStackX: Array();
		:clipStackY: Array();
		:clipStackW: Array();
		:clipStackH: Array();
	}

	## Rebinds this context to [canvas] and resets clip state without allocating a new context.
	Function is rebind(SuitCanvas is canvas){
		:canvas: canvas;
		:hasClip: false;
		:clipStackHas: Array();
		:clipStackX: Array();
		:clipStackY: Array();
		:clipStackW: Array();
		:clipStackH: Array();
	}

	## Returns the process-wide shared default system `Font` (lazily loaded once).
	held Function of Font is defaultFont(){
		return DrawContext:shared:activeFont();
	}

	## Measures UTF-8 [text] width at [pixelHeight] using the shared singleton context (no canvas allocation).
	held Function of Int is measureWidth(String is text, Int is pixelHeight: 15){
		return DrawContext:shared:measureTextWidth(text: text, pixelHeight: pixelHeight);
	}

	## Measures line height for [pixelHeight] without allocating a context.
	held Function of Int is measureHeight(Int is pixelHeight: 15){
		return pixelHeight;
	}

	Function is setClip(Int is x, Int is y, Int is w, Int is h){
		clipStackHas:add(item: hasClip);
		clipStackX:add(item: clipX);
		clipStackY:add(item: clipY);
		clipStackW:add(item: clipW);
		clipStackH:add(item: clipH);
		local Int is nx: x;
		local Int is ny: y;
		local Int is nw: w;
		local Int is nh: h;
		if({ hasClip }, {
			local Int is nx2: nx + nw;
			local Int is ny2: ny + nh;
			local Int is cx2: clipX + clipW;
			local Int is cy2: clipY + clipH;
			if({ nx < clipX }, { nx: clipX; });
			if({ ny < clipY }, { ny: clipY; });
			if({ nx2 > cx2 }, { nx2: cx2; });
			if({ ny2 > cy2 }, { ny2: cy2; });
			nw: if({ nx2 > nx }, { nx2 - nx }, { 0 });
			nh: if({ ny2 > ny }, { ny2 - ny }, { 0 });
		});
		:hasClip: true;
		:clipX: nx;
		:clipY: ny;
		:clipW: nw;
		:clipH: nh;
	}

	Function is clearClip(){
		local Int is n: clipStackHas:length();
		if({ n > 0 }, {
			local Int is last: n - 1;
			:hasClip: clipStackHas:get(index: last);
			:clipX: clipStackX:get(index: last);
			:clipY: clipStackY:get(index: last);
			:clipW: clipStackW:get(index: last);
			:clipH: clipStackH:get(index: last);
			clipStackHas:removeAt(index: last);
			clipStackX:removeAt(index: last);
			clipStackY:removeAt(index: last);
			clipStackW:removeAt(index: last);
			clipStackH:removeAt(index: last);
		}, {
			:hasClip: false;
		});
	}

	Function of Font is activeFont(){
		if({ DrawContext:sharedFontState:get(index: 0) == 0 }, {
			DrawContext:sharedFontState:set(index: 0, item: 1);
			DrawContext:sharedFont:loadDefault();
		});
		return DrawContext:sharedFont;
	}

	Function of Font is styledFont(Boolean is bold: false, Boolean is italic: false, Boolean is mono: false){
		if({ mono }, {
			if({ bold && italic }, {
				if({ DrawContext:sharedFontState:get(index: 7) == 0 }, {
					DrawContext:sharedFontState:set(index: 7, item: 1);
					DrawContext:sharedMonoBoldItalicFont:loadMonoStyled(bold: true, italic: true);
				});
				if({ DrawContext:sharedMonoBoldItalicFont:isLoaded() }, { return DrawContext:sharedMonoBoldItalicFont; });
			});
			if({ bold }, {
				if({ DrawContext:sharedFontState:get(index: 5) == 0 }, {
					DrawContext:sharedFontState:set(index: 5, item: 1);
					DrawContext:sharedMonoBoldFont:loadMonoStyled(bold: true, italic: false);
				});
				if({ DrawContext:sharedMonoBoldFont:isLoaded() }, { return DrawContext:sharedMonoBoldFont; });
			});
			if({ italic }, {
				if({ DrawContext:sharedFontState:get(index: 6) == 0 }, {
					DrawContext:sharedFontState:set(index: 6, item: 1);
					DrawContext:sharedMonoItalicFont:loadMonoStyled(bold: false, italic: true);
				});
				if({ DrawContext:sharedMonoItalicFont:isLoaded() }, { return DrawContext:sharedMonoItalicFont; });
			});
			if({ DrawContext:sharedFontState:get(index: 4) == 0 }, {
				DrawContext:sharedFontState:set(index: 4, item: 1);
				DrawContext:sharedMonoFont:loadMonoStyled(bold: false, italic: false);
			});
			if({ DrawContext:sharedMonoFont:isLoaded() }, { return DrawContext:sharedMonoFont; });
		});
		if({ !bold && !italic }, { return :activeFont(); });
		if({ bold && italic }, {
			if({ DrawContext:sharedFontState:get(index: 3) == 0 }, {
				DrawContext:sharedFontState:set(index: 3, item: 1);
				DrawContext:sharedBoldItalicFont:loadStyled(bold: true, italic: true);
			});
			if({ DrawContext:sharedBoldItalicFont:isLoaded() }, { return DrawContext:sharedBoldItalicFont; });
		});
		if({ bold }, {
			if({ DrawContext:sharedFontState:get(index: 1) == 0 }, {
				DrawContext:sharedFontState:set(index: 1, item: 1);
				DrawContext:sharedBoldFont:loadStyled(bold: true, italic: false);
			});
			if({ DrawContext:sharedBoldFont:isLoaded() }, { return DrawContext:sharedBoldFont; });
		});
		if({ italic }, {
			if({ DrawContext:sharedFontState:get(index: 2) == 0 }, {
				DrawContext:sharedFontState:set(index: 2, item: 1);
				DrawContext:sharedItalicFont:loadStyled(bold: false, italic: true);
			});
			if({ DrawContext:sharedItalicFont:isLoaded() }, { return DrawContext:sharedItalicFont; });
		});
		return :activeFont();
	}

	## Clears the target canvas to fully transparent (`0x00000000`).
	Function is clearTransparent(){
		canvas:clear(color: 0);
	}

	## Fills an axis-aligned rectangle (respecting active clip bounds).
	Function is fillRect(Int is x, Int is y, Int is w, Int is h, Int is color){
		local Int is rx: x;
		local Int is ry: y;
		local Int is rw: w;
		local Int is rh: h;
		if({ hasClip }, {
			local Int is x2: rx + rw;
			local Int is y2: ry + rh;
			local Int is cx2: clipX + clipW;
			local Int is cy2: clipY + clipH;
			if({ rx < clipX }, { rx: clipX; });
			if({ ry < clipY }, { ry: clipY; });
			if({ x2 > cx2 }, { x2: cx2; });
			if({ y2 > cy2 }, { y2: cy2; });
			rw: x2 - rx;
			rh: y2 - ry;
		});
		if({ rw <= 0 || rh <= 0 }, { return; });
		local Int is srcA: (color >> 24) & 255;
		if({ srcA == 0 }, { return; });
		if({ srcA >= 255 }, {
			canvas:fillRect(x: rx, y: ry, w: rw, h: rh, color: color);
			return;
		});
		local Int is pixelsPtr: canvas:pixelsAddr();
		if({ pixelsPtr == 0 }, { return; });
		local Int is bw: canvas:width;
		local Int is srcR: (color >> 16) & 255;
		local Int is srcG: (color >> 8) & 255;
		local Int is srcB: color & 255;
		local Int is invA: 255 - srcA;
		local Int is py: ry;
		while({ py < ry + rh }, {
			local Int is px: rx;
			while({ px < rx + rw }, {
				local Int is off: (py * bw + px) * 4;
				local Int is dst: Mem:loadI32(ptr: pixelsPtr, byteOffset: off);
				local Int is outR: (srcR * srcA + ((dst >> 16) & 255) * invA) / 255;
				local Int is outG: (srcG * srcA + ((dst >> 8) & 255) * invA) / 255;
				local Int is outB: (srcB * srcA + (dst & 255) * invA) / 255;
				Mem:storeI32(ptr: pixelsPtr, byteOffset: off, val: (255 << 24) | (outR << 16) | (outG << 8) | outB);
				px: px + 1;
			});
			py: py + 1;
		});
	}

	## Draws a 1px outline around ([x], [y], [w], [h]).
	Function is strokeRect(Int is x, Int is y, Int is w, Int is h, Int is color, Int is thickness: 1){
		if({ w <= 0 || h <= 0 || thickness <= 0 }, { return; });
		local Int is t: if({ thickness * 2 > w }, { w / 2 }, { thickness });
		if({ t * 2 > h }, { t: h / 2; });
		if({ t < 1 }, { t: 1; });
		:fillRect(x: x, y: y, w: w, h: t, color: color);
		:fillRect(x: x, y: y + h - t, w: w, h: t, color: color);
		:fillRect(x: x, y: y, w: t, h: h, color: color);
		:fillRect(x: x + w - t, y: y, w: t, h: h, color: color);
	}

	local Function of Float is clamp01(Float is v){
		if({ v < 0.0 }, { return 0.0; });
		if({ v > 1.0 }, { return 1.0; });
		return v;
	}

	local Function of Float is roundBoxSd(Float is px, Float is py, Float is cx, Float is cy, Float is halfW, Float is halfH, Float is r){
		local Float is dxAbs: if({ px >= cx }, { px - cx }, { cx - px });
		local Float is dyAbs: if({ py >= cy }, { py - cy }, { cy - py });
		local Float is dx: dxAbs - (halfW - r);
		local Float is dy: dyAbs - (halfH - r);
		local Float is qx: if({ dx > 0.0 }, { dx }, { 0.0 });
		local Float is qy: if({ dy > 0.0 }, { dy }, { 0.0 });
		local Float is outD: sqrt(value: qx * qx + qy * qy);
		local Float is maxD: if({ dx > dy }, { dx }, { dy });
		local Float is inD: if({ maxD < 0.0 }, { maxD }, { 0.0 });
		return outD + inD - r;
	}

	## Fills a rounded rectangle with anti-aliased corners.
	Function is fillRoundRect(Int is x, Int is y, Int is w, Int is h, Int is radius, Int is color){
		if({ w <= 0 || h <= 0 }, { return; });
		if({ radius <= 0 }, {
			:fillRect(x: x, y: y, w: w, h: h, color: color);
			return;
		});
		local Int is maxR: if({ w < h }, { w / 2 }, { h / 2 });
		local Int is r: if({ radius > maxR }, { maxR }, { radius });
		if({ r <= 0 }, {
			:fillRect(x: x, y: y, w: w, h: h, color: color);
			return;
		});
		:fillRect(x: x + r, y: y, w: w - 2 * r, h: h, color: color);
		:fillRect(x: x, y: y + r, w: r, h: h - 2 * r, color: color);
		:fillRect(x: x + w - r, y: y + r, w: r, h: h - 2 * r, color: color);

		local Color is baseC: Color:fromArgb(argb: color);
		local Int is baseA: baseC:alpha();
		local Float is rf: r as Float;
		local Int is dy: 0;
		while({ dy < r }, {
			local Float is cyf: rf - 0.5 - (dy as Float);
			local Int is dx: 0;
			while({ dx < r }, {
				local Float is cxf: rf - 0.5 - (dx as Float);
				local Float is d: sqrt(value: cxf * cxf + cyf * cyf);
				local Float is cov: :clamp01(v: rf - d + 0.5);
				local Int is ab: (((baseA as Float) * cov) + 0.5) as Int;
				if({ ab > 0 }, {
					local Int is pxCol: if({ ab >= baseA }, { color }, { baseC:withAlphaByte(a: ab):toArgb() });
					:fillRect(x: x + dx, y: y + dy, w: 1, h: 1, color: pxCol);
					:fillRect(x: x + w - 1 - dx, y: y + dy, w: 1, h: 1, color: pxCol);
					:fillRect(x: x + dx, y: y + h - 1 - dy, w: 1, h: 1, color: pxCol);
					:fillRect(x: x + w - 1 - dx, y: y + h - 1 - dy, w: 1, h: 1, color: pxCol);
				});
				dx: dx + 1;
			});
			dy: dy + 1;
		});
	}

	## Strokes a rounded rectangle with anti-aliased corners, optionally using separate [topLeftColor] and [botRightColor].
	Function is strokeRoundRectSplit(Int is x, Int is y, Int is w, Int is h, Int is radius, Int is topLeftColor, Int is botRightColor, Int is thickness: 1){
		if({ w <= 0 || h <= 0 || thickness <= 0 }, { return; });
		local Int is halfMin: if({ w < h }, { w / 2 }, { h / 2 });
		local Int is t: if({ thickness > halfMin }, { halfMin }, { thickness });
		if({ t < 1 }, { t: 1; });
		if({ radius <= 0 }, {
			:fillRect(x: x, y: y, w: w - t, h: t, color: topLeftColor);
			:fillRect(x: x, y: y + t, w: t, h: h - t, color: topLeftColor);
			:fillRect(x: x + t, y: y + h - t, w: w - t, h: t, color: botRightColor);
			:fillRect(x: x + w - t, y: y + t, w: t, h: h - 2 * t, color: botRightColor);
			local Int is mdy: 0;
			while({ mdy < t }, {
				local Int is mdx: 0;
				while({ mdx < t }, {
					:fillRect(x: x + w - t + mdx, y: y + mdy, w: 1, h: 1, color: if({ mdx + mdy < t }, { topLeftColor }, { botRightColor }));
					:fillRect(x: x + mdx, y: y + h - t + mdy, w: 1, h: 1, color: if({ mdx + mdy < t }, { topLeftColor }, { botRightColor }));
					mdx: mdx + 1;
				});
				mdy: mdy + 1;
			});
			return;
		});
		local Int is r: if({ radius > halfMin }, { halfMin }, { radius });
		local Int is box: if({ r > t }, { r }, { t });
		if({ w > 2 * box }, {
			:fillRect(x: x + box, y: y, w: w - 2 * box, h: t, color: topLeftColor);
			:fillRect(x: x + box, y: y + h - t, w: w - 2 * box, h: t, color: botRightColor);
		});
		if({ h > 2 * box }, {
			:fillRect(x: x, y: y + box, w: t, h: h - 2 * box, color: topLeftColor);
			:fillRect(x: x + w - t, y: y + box, w: t, h: h - 2 * box, color: botRightColor);
		});

		local Color is tlC: Color:fromArgb(argb: topLeftColor);
		local Color is brC: Color:fromArgb(argb: botRightColor);
		local Int is tlA: tlC:alpha();
		local Int is brA: brC:alpha();
		local Float is rf: r as Float;
		local Float is inRf: (r - t) as Float;
		local Float is halfPi: pi() * 0.5;
		local Int is dy: 0;
		while({ dy < box }, {
			local Float is cyf: rf - 0.5 - (dy as Float);
			local Int is dx: 0;
			while({ dx < box }, {
				local Float is cxf: rf - 0.5 - (dx as Float);
				local Float is outerCov: 1.0;
				if({ dx < r && dy < r }, {
					local Float is dOut: sqrt(value: cxf * cxf + cyf * cyf);
					outerCov: :clamp01(v: rf - dOut + 0.5);
				});
				local Float is innerCov: 1.0;
				if({ dx >= t && dy >= t }, {
					if({ r > t }, {
						local Float is dIn: sqrt(value: cxf * cxf + cyf * cyf);
						innerCov: :clamp01(v: dIn - inRf + 0.5);
					}, {
						innerCov: 0.0;
					});
				});
				local Float is cov: if({ outerCov < innerCov }, { outerCov }, { innerCov });
				if({ cov > 0.0 }, {
					local Int is abTL: (((tlA as Float) * cov) + 0.5) as Int;
					if({ abTL > 0 }, {
						local Int is colTL: if({ abTL >= tlA }, { topLeftColor }, { tlC:withAlphaByte(a: abTL):toArgb() });
						:fillRect(x: x + dx, y: y + dy, w: 1, h: 1, color: colTL);
					});
					local Int is abBR: (((brA as Float) * cov) + 0.5) as Int;
					if({ abBR > 0 }, {
						local Int is colBR: if({ abBR >= brA }, { botRightColor }, { brC:withAlphaByte(a: abBR):toArgb() });
						:fillRect(x: x + w - 1 - dx, y: y + h - 1 - dy, w: 1, h: 1, color: colBR);
					});
					if({ topLeftColor == botRightColor }, {
						if({ abTL > 0 }, {
							local Int is colSame: if({ abTL >= tlA }, { topLeftColor }, { tlC:withAlphaByte(a: abTL):toArgb() });
							:fillRect(x: x + w - 1 - dx, y: y + dy, w: 1, h: 1, color: colSame);
							:fillRect(x: x + dx, y: y + h - 1 - dy, w: 1, h: 1, color: colSame);
						});
					}, {
						local Float is cxPos: if({ cxf > 0.0 }, { cxf }, { 0.0 });
						local Float is cyPos: if({ cyf > 0.0 }, { cyf }, { 0.0 });
						local Float is tMixTR: :clamp01(v: atan2(y: cxPos, x: cyPos) / halfPi);
						local Color is trC: tlC:mix(other: brC, t: tMixTR);
						local Int is abTR: (((trC:alpha() as Float) * cov) + 0.5) as Int;
						if({ abTR > 0 }, {
							:fillRect(x: x + w - 1 - dx, y: y + dy, w: 1, h: 1, color: trC:withAlphaByte(a: abTR):toArgb());
						});
						local Float is tMixBL: :clamp01(v: atan2(y: cyPos, x: cxPos) / halfPi);
						local Color is blC: tlC:mix(other: brC, t: tMixBL);
						local Int is abBL: (((blC:alpha() as Float) * cov) + 0.5) as Int;
						if({ abBL > 0 }, {
							:fillRect(x: x + dx, y: y + h - 1 - dy, w: 1, h: 1, color: blC:withAlphaByte(a: abBL):toArgb());
						});
					});
				});
				dx: dx + 1;
			});
			dy: dy + 1;
		});
	}

	## Strokes a rounded rectangle outline with anti-aliased corners.
	Function is strokeRoundRect(Int is x, Int is y, Int is w, Int is h, Int is radius, Int is color, Int is thickness: 1){
		:strokeRoundRectSplit(x: x, y: y, w: w, h: h, radius: radius, topLeftColor: color, botRightColor: color, thickness: thickness);
	}

	## Draws a soft drop shadow for a rounded rectangle with offset and blur radius.
	Function is drawShadow(Int is x, Int is y, Int is w, Int is h, Int is radius: 0, Int is offsetX: 0, Int is offsetY: 4, Int is blurRadius: 8, Int is color: 1426063360){
		if({ w <= 0 || h <= 0 }, { return; });
		local Int is sx: x + offsetX;
		local Int is sy: y + offsetY;
		if({ blurRadius <= 0 }, {
			:fillRoundRect(x: sx, y: sy, w: w, h: h, radius: radius, color: color);
			return;
		});
		local Int is blur: blurRadius;
		local Int is maxR: if({ w < h }, { w / 2 }, { h / 2 });
		local Int is r: if({ radius > maxR }, { maxR }, { if({ radius < 0 }, { 0 }, { radius }) });
		local Color is baseC: Color:fromArgb(argb: color);
		local Int is baseA: baseC:alpha();
		local Float is halfW: (w as Float) * 0.5;
		local Float is halfH: (h as Float) * 0.5;
		local Float is cx: (sx as Float) + halfW;
		local Float is cy: (sy as Float) + halfH;
		local Float is rf: r as Float;
		local Float is blurF: blur as Float;

		local Int is coreInset: blur + r;
		local Int is coreX: sx + coreInset;
		local Int is coreY: sy + coreInset;
		local Int is coreW: w - 2 * coreInset;
		local Int is coreH: h - 2 * coreInset;
		if({ coreW > 0 && coreH > 0 }, {
			:fillRect(x: coreX, y: coreY, w: coreW, h: coreH, color: color);
		});

		local Int is x0: sx - blur;
		local Int is y0: sy - blur;
		local Int is x1: sx + w + blur;
		local Int is y1: sy + h + blur;
		local Int is py: y0;
		while({ py < y1 }, {
			local Int is px: x0;
			while({ px < x1 }, {
				if({ coreW > 0 && coreH > 0 && px >= coreX && px < coreX + coreW && py >= coreY && py < coreY + coreH }, {
					px: coreX + coreW;
				}, {
					local Float is sd: :roundBoxSd(px: (px as Float) + 0.5, py: (py as Float) + 0.5, cx: cx, cy: cy, halfW: halfW, halfH: halfH, r: rf);
					local Float is u: :clamp01(v: 1.0 - (sd + blurF * 0.25) / (blurF * 1.25));
					if({ u > 0.0 }, {
						local Float is smooth: u * u * (3.0 - 2.0 * u);
						local Int is ab: (((baseA as Float) * smooth) + 0.5) as Int;
						if({ ab > 0 }, {
							:fillRect(x: px, y: py, w: 1, h: 1, color: baseC:withAlphaByte(a: ab):toArgb());
						});
					});
					px: px + 1;
				});
			});
			py: py + 1;
		});
	}

	## Draws a soft inner shadow clipped inside a rounded rectangle with offset and blur radius.
	Function is drawInnerShadow(Int is x, Int is y, Int is w, Int is h, Int is radius: 0, Int is offsetX: 0, Int is offsetY: 2, Int is blurRadius: 6, Int is color: 1426063360){
		if({ w <= 0 || h <= 0 || color == 0 }, { return; });
		local Int is blur: if({ blurRadius < 0 }, { 0 }, { blurRadius });
		local Int is maxR: if({ w < h }, { w / 2 }, { h / 2 });
		local Int is r: if({ radius > maxR }, { maxR }, { if({ radius < 0 }, { 0 }, { radius }) });
		local Color is baseC: Color:fromArgb(argb: color);
		local Int is baseA: baseC:alpha();
		if({ baseA <= 0 }, { return; });
		local Float is halfW: (w as Float) * 0.5;
		local Float is halfH: (h as Float) * 0.5;
		local Float is cx: (x as Float) + halfW;
		local Float is cy: (y as Float) + halfH;
		local Float is rf: r as Float;
		local Float is blurF: if({ blur > 0 }, { blur as Float }, { 1.0 });
		local Float is ox: offsetX as Float;
		local Float is oy: offsetY as Float;

		local Int is absOx: if({ offsetX < 0 }, { 0 - offsetX }, { offsetX });
		local Int is absOy: if({ offsetY < 0 }, { 0 - offsetY }, { offsetY });
		local Int is insetX: blur + r + absOx + 1;
		local Int is insetY: blur + r + absOy + 1;
		local Int is coreX: x + insetX;
		local Int is coreY: y + insetY;
		local Int is coreW: w - 2 * insetX;
		local Int is coreH: h - 2 * insetY;

		local Int is py: y;
		while({ py < y + h }, {
			local Int is px: x;
			while({ px < x + w }, {
				if({ coreW > 0 && coreH > 0 && px >= coreX && px < coreX + coreW && py >= coreY && py < coreY + coreH }, {
					px: coreX + coreW;
				}, {
					local Float is pxf: (px as Float) + 0.5;
					local Float is pyf: (py as Float) + 0.5;
					local Float is sdShape: :roundBoxSd(px: pxf, py: pyf, cx: cx, cy: cy, halfW: halfW, halfH: halfH, r: rf);
					local Float is shapeCov: :clamp01(v: 0.5 - sdShape);
					if({ shapeCov > 0.0 }, {
						local Float is sdShift: :roundBoxSd(px: pxf - ox, py: pyf - oy, cx: cx, cy: cy, halfW: halfW, halfH: halfH, r: rf);
						local Float is u: if({ blur <= 0 }, {
							if({ sdShift >= 0.0 }, { 1.0 }, { 0.0 })
						}, {
							:clamp01(v: (sdShift + blurF) / (blurF * 1.25))
						});
						if({ u > 0.0 }, {
							local Float is smooth: u * u * (3.0 - 2.0 * u);
							local Int is ab: (((baseA as Float) * smooth * shapeCov) + 0.5) as Int;
							if({ ab > 0 }, {
								:fillRect(x: px, y: py, w: 1, h: 1, color: baseC:withAlphaByte(a: ab):toArgb());
							});
						});
					});
					px: px + 1;
				});
			});
			py: py + 1;
		});
	}

	## Draws a styled box with optional drop shadow, inner shadow, background fill, corner radius, and border style (single/double/bevel/groove/inset/outset).
	Function is drawStyledBox(
		Int is x,
		Int is y,
		Int is w,
		Int is h,
		Int is bgColor,
		Int is borderColor,
		Int is thickness: 1,
		Int is radius: 0,
		String is style: 'single',
		Int is shadowOffsetX: 0,
		Int is shadowOffsetY: 0,
		Int is shadowBlur: 0,
		Int is shadowColor: 1426063360,
		Int is innerShadowOffsetX: 0,
		Int is innerShadowOffsetY: 0,
		Int is innerShadowBlur: 0,
		Int is innerShadowColor: 1426063360
	){
		if({ w <= 0 || h <= 0 }, { return; });
		if({ shadowColor != 0 && (shadowBlur > 0 || shadowOffsetX != 0 || shadowOffsetY != 0) }, {
			:drawShadow(x: x, y: y, w: w, h: h, radius: radius, offsetX: shadowOffsetX, offsetY: shadowOffsetY, blurRadius: shadowBlur, color: shadowColor);
		});
		if({ bgColor != 0 }, {
			:fillRoundRect(x: x, y: y, w: w, h: h, radius: radius, color: bgColor);
		});
		if({ innerShadowColor != 0 && (innerShadowBlur > 0 || innerShadowOffsetX != 0 || innerShadowOffsetY != 0) }, {
			:drawInnerShadow(x: x, y: y, w: w, h: h, radius: radius, offsetX: innerShadowOffsetX, offsetY: innerShadowOffsetY, blurRadius: innerShadowBlur, color: innerShadowColor);
		});
		if({ thickness <= 0 || borderColor == 0 }, { return; });
		local Color is bc: Color:fromArgb(argb: borderColor);
		local Color is whiteC: Color(r: 255, g: 255, b: 255);
		local Color is blackC: Color(r: 0, g: 0, b: 0);
		local Int is lightC: bc:mix(other: whiteC, t: 0.45):toArgb();
		local Int is darkC: bc:mix(other: blackC, t: 0.45):toArgb();
		if({ style == 'double' }, {
			local Int is t1: if({ thickness >= 3 }, { thickness / 3 }, { 1 });
			local Int is gap: if({ thickness >= 3 }, { thickness - t1 * 2 }, { 1 });
			local Int is off: t1 + gap;
			:strokeRoundRect(x: x, y: y, w: w, h: h, radius: radius, color: borderColor, thickness: t1);
			if({ w > off * 2 && h > off * 2 }, {
				local Int is inR: if({ radius > off }, { radius - off }, { 0 });
				:strokeRoundRect(x: x + off, y: y + off, w: w - off * 2, h: h - off * 2, radius: inR, color: borderColor, thickness: t1);
			});
			return;
		});
		if({ style == 'bevel' }, {
			local Int is t1: if({ thickness >= 2 }, { thickness / 2 }, { 1 });
			local Int is t2: if({ thickness - t1 > 0 }, { thickness - t1 }, { 1 });
			local Int is hiOuter: bc:mix(other: whiteC, t: 0.55):toArgb();
			local Int is loOuter: bc:mix(other: blackC, t: 0.55):toArgb();
			local Int is hiInner: bc:mix(other: whiteC, t: 0.22):toArgb();
			local Int is loInner: bc:mix(other: blackC, t: 0.22):toArgb();
			:strokeRoundRectSplit(x: x, y: y, w: w, h: h, radius: radius, topLeftColor: hiOuter, botRightColor: loOuter, thickness: t1);
			if({ w > t1 * 2 && h > t1 * 2 }, {
				local Int is inR: if({ radius > t1 }, { radius - t1 }, { 0 });
				:strokeRoundRectSplit(x: x + t1, y: y + t1, w: w - t1 * 2, h: h - t1 * 2, radius: inR, topLeftColor: hiInner, botRightColor: loInner, thickness: t2);
			});
			return;
		});
		if({ style == 'outset' }, {
			:strokeRoundRectSplit(x: x, y: y, w: w, h: h, radius: radius, topLeftColor: lightC, botRightColor: darkC, thickness: thickness);
			return;
		});
		if({ style == 'inset' }, {
			:strokeRoundRectSplit(x: x, y: y, w: w, h: h, radius: radius, topLeftColor: darkC, botRightColor: lightC, thickness: thickness);
			return;
		});
		if({ style == 'groove' }, {
			local Int is t1: if({ thickness >= 2 }, { thickness / 2 }, { 1 });
			local Int is t2: if({ thickness - t1 > 0 }, { thickness - t1 }, { 1 });
			:strokeRoundRectSplit(x: x, y: y, w: w, h: h, radius: radius, topLeftColor: darkC, botRightColor: lightC, thickness: t1);
			if({ w > t1 * 2 && h > t1 * 2 }, {
				local Int is inR: if({ radius > t1 }, { radius - t1 }, { 0 });
				:strokeRoundRectSplit(x: x + t1, y: y + t1, w: w - t1 * 2, h: h - t1 * 2, radius: inR, topLeftColor: lightC, botRightColor: darkC, thickness: t2);
			});
			return;
		});
		:strokeRoundRect(x: x, y: y, w: w, h: h, radius: radius, color: borderColor, thickness: thickness);
	}

	## Draws a horizontal or vertical divider line using [style] (none/single/double/bevel/groove/inset/outset).
	Function is drawDivider(Int is x, Int is y, Int is w, Int is h, Int is color, Int is thickness: 1, String is style: 'single'){
		if({ w <= 0 || h <= 0 || thickness <= 0 || color == 0 || style == 'none' }, { return; });
		if({ style == 'single' }, {
			:fillRect(x: x, y: y, w: w, h: h, color: color);
			return;
		});
		local Boolean is horiz: w >= h;
		local Color is bc: Color:fromArgb(argb: color);
		local Int is lightC: bc:lighten(amount: 0.38):toArgb();
		local Int is darkC: bc:darken(amount: 0.42):toArgb();
		local Int is span: if({ horiz }, { h }, { w });
		local Int is t1: if({ span >= 2 }, { span / 2 }, { 1 });
		local Int is t2: if({ span - t1 > 0 }, { span - t1 }, { 1 });
		if({ style == 'double' }, {
			if({ span < 3 }, {
				:fillRect(x: x, y: y, w: w, h: h, color: color);
				return;
			});
			local Int is dt: if({ span >= 3 }, { span / 3 }, { 1 });
			if({ horiz }, {
				:fillRect(x: x, y: y, w: w, h: dt, color: color);
				:fillRect(x: x, y: y + h - dt, w: w, h: dt, color: color);
			}, {
				:fillRect(x: x, y: y, w: dt, h: h, color: color);
				:fillRect(x: x + w - dt, y: y, w: dt, h: h, color: color);
			});
			return;
		});
		local Int is firstC: if({ style == 'bevel' || style == 'outset' }, { lightC }, { darkC });
		local Int is secondC: if({ style == 'bevel' || style == 'outset' }, { darkC }, { lightC });
		if({ span < 2 }, {
			:fillRect(x: x, y: y, w: w, h: h, color: firstC);
			return;
		});
		if({ horiz }, {
			:fillRect(x: x, y: y, w: w, h: t1, color: firstC);
			:fillRect(x: x, y: y + t1, w: w, h: t2, color: secondC);
		}, {
			:fillRect(x: x, y: y, w: t1, h: h, color: firstC);
			:fillRect(x: x + t1, y: y, w: t2, h: h, color: secondC);
		});
	}

	local Function is plotClipped(Int is x, Int is y, Int is color){
		if({ hasClip }, {
			if({ x < clipX || x >= clipX + clipW || y < clipY || y >= clipY + clipH }, { return; });
		});
		canvas:setPixel(x: x, y: y, color: color);
	}

	## Fills a solid circle centered at ([cx], [cy]) with radius [r].
	Function is fillCircle(Int is cx, Int is cy, Int is r, Int is color){
		if({ r <= 0 }, { return; });
		local Int is dy: 0 - r;
		local Int is r2: r * r;
		while({ dy <= r }, {
			local Int is dx: r;
			while({ dx > 0 && (dx * dx + dy * dy) > r2 }, {
				dx: dx - 1;
			});
			:fillRect(x: cx - dx, y: cy + dy, w: dx * 2 + 1, h: 1, color: color);
			dy: dy + 1;
		});
	}

	## Draws a 1px circle outline centered at ([cx], [cy]) with radius [r].
	Function is strokeCircle(Int is cx, Int is cy, Int is r, Int is color){
		if({ r <= 0 }, { return; });
		local Int is x: r;
		local Int is y: 0;
		local Int is err: 1 - x;
		while({ x >= y }, {
			:plotClipped(x: cx + x, y: cy + y, color: color);
			:plotClipped(x: cx + y, y: cy + x, color: color);
			:plotClipped(x: cx - y, y: cy + x, color: color);
			:plotClipped(x: cx - x, y: cy + y, color: color);
			:plotClipped(x: cx - x, y: cy - y, color: color);
			:plotClipped(x: cx - y, y: cy - x, color: color);
			:plotClipped(x: cx + y, y: cy - x, color: color);
			:plotClipped(x: cx + x, y: cy - y, color: color);
			y: y + 1;
			if({ err < 0 }, {
				err: err + 2 * y + 1;
			}, {
				x: x - 1;
				err: err + 2 * (y - x) + 1;
			});
		});
	}

	## Measures the pixel width of UTF-8 [text] at [pixelHeight] using the system font.
	Function of Int is measureTextWidth(String is text, Int is pixelHeight: 15, Boolean is bold: false, Boolean is italic: false, Boolean is mono: false){
		local Font is f: :styledFont(bold: bold, italic: italic, mono: mono);
		if({ !f:isLoaded() }, { return 0; });
		return f:measureWidth(text: text, pixelHeight: pixelHeight);
	}

	## Thread-safe text width measurement using an explicit 8-byte [scratchPtr].
	Function of Int is measureTextWidthWithScratch(String is text, Int is pixelHeight: 15, Boolean is bold: false, Boolean is italic: false, Boolean is mono: false, Int is scratchPtr: 0){
		local Font is f: :styledFont(bold: bold, italic: italic, mono: mono);
		if({ !f:isLoaded() }, { return 0; });
		return f:measureWidthWithScratch(text: text, pixelHeight: pixelHeight, scratchPtr: scratchPtr);
	}

	## Thread-safe O(N) single-pass cumulative advance measurement into [outAdvI32Ptr].
	Function is measurePrefixAdvances(String is text, Int is pixelHeight: 15, Boolean is bold: false, Boolean is italic: false, Boolean is mono: false, Int is outAdvI32Ptr: 0, Int is scratchPtr: 0){
		local Font is f: :styledFont(bold: bold, italic: italic, mono: mono);
		if({ !f:isLoaded() }, { return; });
		f:measurePrefixAdvances(text: text, pixelHeight: pixelHeight, outAdvI32Ptr: outAdvI32Ptr, scratchPtr: scratchPtr);
	}

	## Measures the line height for [pixelHeight].
	Function of Int is measureTextHeight(Int is pixelHeight: 15){
		return pixelHeight;
	}

	## Draws UTF-8 [text] at ([x], [y]) using the loaded system TrueType font.
	Function is drawText(Int is x, Int is y, String is text, Int is color, Int is pixelHeight: 15, Boolean is bold: false, Boolean is italic: false, Boolean is mono: false){
		local Font is f: :styledFont(bold: bold, italic: italic, mono: mono);
		if({ !f:isLoaded() }, { return; });
		local Boolean is hasBold: if({ mono }, { DrawContext:sharedMonoBoldFont:isLoaded() }, { DrawContext:sharedBoldFont:isLoaded() });
		local Float is wOverride: if({ bold && !hasBold }, { 0.75 }, { -1.0 });
		f:drawText(
			pixelsAddr: canvas:pixelsAddr(),
			bufW: canvas:width,
			bufH: canvas:height,
			x: x,
			y: y,
			text: text,
			pixelHeight: pixelHeight,
			argbColor: color,
			weight: wOverride,
			clipX: if({ hasClip }, { clipX }, { 0 }),
			clipY: if({ hasClip }, { clipY }, { 0 }),
			clipW: if({ hasClip }, { clipW }, { -1 }),
			clipH: if({ hasClip }, { clipH }, { -1 })
		);
	}

	## Alpha-blends a byte coverage mask ([maskAddr], [w]x[h]) tinted with ARGB [color] at ([x], [y]).
	Function is blendAlphaMask(Int is x, Int is y, Int is w, Int is h, Int is maskAddr, Int is color){
		local Int is pixelsPtr: canvas:pixelsAddr();
		if({ pixelsPtr == 0 || maskAddr == 0 || w <= 0 || h <= 0 }, { return; });
		local Int is bw: canvas:width;
		local Int is bh: canvas:height;
		local Int is x0: if({ x < 0 }, { 0 }, { x });
		local Int is y0: if({ y < 0 }, { 0 }, { y });
		local Int is x1: if({ x + w > bw }, { bw }, { x + w });
		local Int is y1: if({ y + h > bh }, { bh }, { y + h });
		if({ hasClip }, {
			if({ clipX > x0 }, { x0: clipX; });
			if({ clipY > y0 }, { y0: clipY; });
			if({ clipX + clipW < x1 }, { x1: clipX + clipW; });
			if({ clipY + clipH < y1 }, { y1: clipY + clipH; });
		});
		if({ x1 <= x0 || y1 <= y0 }, { return; });

		local Int is srcA: (color >> 24) & 255;
		local Int is srcR: (color >> 16) & 255;
		local Int is srcG: (color >> 8) & 255;
		local Int is srcB: color & 255;
		if({ srcA == 0 }, { return; });

		local Int is py: y0;
		while({ py < y1 }, {
			local Int is sy: py - y;
			local Int is px: x0;
			while({ px < x1 }, {
				local Int is sx: px - x;
				local Int is cov: Mem:loadByte(ptr: maskAddr, byteOffset: sy * w + sx) & 255;
				if({ cov > 0 }, {
					local Int is a: (cov * srcA) / 255;
					if({ a >= 255 }, {
						Mem:storeI32(ptr: pixelsPtr, byteOffset: (py * bw + px) * 4, val: (255 << 24) | (srcR << 16) | (srcG << 8) | srcB);
					}, {
						if({ a > 0 }, {
							local Int is dstOff: (py * bw + px) * 4;
							local Int is dst: Mem:loadI32(ptr: pixelsPtr, byteOffset: dstOff);
							local Int is dstR: (dst >> 16) & 255;
							local Int is dstG: (dst >> 8) & 255;
							local Int is dstB: dst & 255;
							local Int is invA: 255 - a;
							local Int is outR: (srcR * a + dstR * invA) / 255;
							local Int is outG: (srcG * a + dstG * invA) / 255;
							local Int is outB: (srcB * a + dstB * invA) / 255;
							Mem:storeI32(ptr: pixelsPtr, byteOffset: dstOff, val: (255 << 24) | (outR << 16) | (outG << 8) | outB);
						});
					});
				});
				px: px + 1;
			});
			py: py + 1;
		});
	}

	## Alpha-blends a pre-colored ARGB8888 buffer ([argbAddr], [w]x[h]) at ([x], [y]).
	Function is blendArgbBuffer(Int is x, Int is y, Int is w, Int is h, Int is argbAddr){
		local Int is pixelsPtr: canvas:pixelsAddr();
		if({ pixelsPtr == 0 || argbAddr == 0 || w <= 0 || h <= 0 }, { return; });
		local Int is bw: canvas:width;
		local Int is bh: canvas:height;
		local Int is x0: if({ x < 0 }, { 0 }, { x });
		local Int is y0: if({ y < 0 }, { 0 }, { y });
		local Int is x1: if({ x + w > bw }, { bw }, { x + w });
		local Int is y1: if({ y + h > bh }, { bh }, { y + h });
		if({ hasClip }, {
			if({ clipX > x0 }, { x0: clipX; });
			if({ clipY > y0 }, { y0: clipY; });
			if({ clipX + clipW < x1 }, { x1: clipX + clipW; });
			if({ clipY + clipH < y1 }, { y1: clipY + clipH; });
		});
		if({ x1 <= x0 || y1 <= y0 }, { return; });

		local Int is py: y0;
		while({ py < y1 }, {
			local Int is sy: py - y;
			local Int is px: x0;
			while({ px < x1 }, {
				local Int is sx: px - x;
				local Int is src: Mem:loadI32(ptr: argbAddr, byteOffset: (sy * w + sx) * 4);
				local Int is a: (src >> 24) & 255;
				if({ a >= 255 }, {
					Mem:storeI32(ptr: pixelsPtr, byteOffset: (py * bw + px) * 4, val: src);
				}, {
					if({ a > 0 }, {
						local Int is srcR: (src >> 16) & 255;
						local Int is srcG: (src >> 8) & 255;
						local Int is srcB: src & 255;
						local Int is dstOff: (py * bw + px) * 4;
						local Int is dst: Mem:loadI32(ptr: pixelsPtr, byteOffset: dstOff);
						local Int is dstR: (dst >> 16) & 255;
						local Int is dstG: (dst >> 8) & 255;
						local Int is dstB: dst & 255;
						local Int is invA: 255 - a;
						local Int is outR: (srcR * a + dstR * invA) / 255;
						local Int is outG: (srcG * a + dstG * invA) / 255;
						local Int is outB: (srcB * a + dstB * invA) / 255;
						Mem:storeI32(ptr: pixelsPtr, byteOffset: dstOff, val: (255 << 24) | (outR << 16) | (outG << 8) | outB);
					});
				});
				px: px + 1;
			});
			py: py + 1;
		});
	}
}
