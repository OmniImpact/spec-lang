#! Package base:fabric
#! 2D software drawing context targeting a `SuitCanvas` (ARGB8888) and using `base:sys:Font`.

Class is DrawContext{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()],
		['base', 'sys', Font],
		['base', 'struct', Array],
		['base', 'suit', SuitCanvas]
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

	replace Function is init(SuitCanvas is canvas){
		:canvas: canvas;
		:hasClip: false;
	}

	## Rebinds this context to [canvas] and resets clip state without allocating a new context.
	Function is rebind(SuitCanvas is canvas){
		:canvas: canvas;
		:hasClip: false;
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
		:hasClip: true;
		:clipX: x;
		:clipY: y;
		:clipW: w;
		:clipH: h;
	}

	Function is clearClip(){
		:hasClip: false;
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
		canvas:fillRect(x: rx, y: ry, w: rw, h: rh, color: color);
	}

	## Draws a 1px outline around ([x], [y], [w], [h]).
	Function is strokeRect(Int is x, Int is y, Int is w, Int is h, Int is color){
		if({ w <= 0 || h <= 0 }, { return; });
		canvas:fillRect(x: x, y: y, w: w, h: 1, color: color);
		canvas:fillRect(x: x, y: y + h - 1, w: w, h: 1, color: color);
		canvas:fillRect(x: x, y: y, w: 1, h: h, color: color);
		canvas:fillRect(x: x + w - 1, y: y, w: 1, h: h, color: color);
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
