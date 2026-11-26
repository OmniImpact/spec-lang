#! Package base:fabric
#! 2D software drawing context targeting a `SuitCanvas` (ARGB8888) and using `base:sys:Font`.

Class is DrawContext{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', Font],
		['base', 'struct', Array],
		['base', 'suit', SuitCanvas]
	];

	held Font is sharedFont: Font();
	held Font is sharedBoldFont: Font();
	held Font is sharedItalicFont: Font();
	held Font is sharedBoldItalicFont: Font();
	held Array of Int is sharedFontState: Array([0, 0, 0, 0]);
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

	Function of Font is styledFont(Boolean is bold: false, Boolean is italic: false){
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
	Function of Int is measureTextWidth(String is text, Int is pixelHeight: 15, Boolean is bold: false, Boolean is italic: false){
		local Font is f: :styledFont(bold: bold, italic: italic);
		if({ !f:isLoaded() }, { return 0; });
		return f:measureWidth(text: text, pixelHeight: pixelHeight);
	}

	## Measures the line height for [pixelHeight].
	Function of Int is measureTextHeight(Int is pixelHeight: 15){
		return pixelHeight;
	}

	## Draws UTF-8 [text] at ([x], [y]) using the loaded system TrueType font.
	Function is drawText(Int is x, Int is y, String is text, Int is color, Int is pixelHeight: 15, Boolean is bold: false, Boolean is italic: false){
		local Font is f: :styledFont(bold: bold, italic: italic);
		if({ !f:isLoaded() }, { return; });
		local Float is wOverride: if({ bold && !DrawContext:sharedBoldFont:isLoaded() }, { 0.75 }, { -1.0 });
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
}
