#! Package base:fabric
#! 2D software drawing context targeting a `SuitCanvas` (ARGB8888) and using `base:sys:Font`.

Class is DrawContext{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', Font],
		['base', 'suit', SuitCanvas]
	];

	Font is defaultFont: Font();
	Boolean is defaultFontTried: false;

	SuitCanvas is canvas: SuitCanvas(width: 1, height: 1);

	replace Function is init(SuitCanvas is canvas){
		:canvas: canvas;
	}

	local Function of Font is activeFont(){
		if({ !defaultFontTried }, {
			defaultFontTried: true;
			defaultFont:loadDefault();
		});
		return defaultFont;
	}

	## Clears the target canvas to fully transparent (`0x00000000`).
	Function is clearTransparent(){
		canvas:clear(color: 0);
	}

	## Fills an axis-aligned rectangle.
	Function is fillRect(Int is x, Int is y, Int is w, Int is h, Int is color){
		canvas:fillRect(x: x, y: y, w: w, h: h, color: color);
	}

	## Draws a 1px outline around ([x], [y], [w], [h]).
	Function is strokeRect(Int is x, Int is y, Int is w, Int is h, Int is color){
		if({ w <= 0 || h <= 0 }, { return; });
		canvas:fillRect(x: x, y: y, w: w, h: 1, color: color);
		canvas:fillRect(x: x, y: y + h - 1, w: w, h: 1, color: color);
		canvas:fillRect(x: x, y: y, w: 1, h: h, color: color);
		canvas:fillRect(x: x + w - 1, y: y, w: 1, h: h, color: color);
	}

	## Measures the pixel width of UTF-8 [text] at [pixelHeight] using the system font.
	Function of Int is measureTextWidth(String is text, Int is pixelHeight: 15){
		local Font is f: :activeFont();
		if({ !f:isLoaded() }, { return 0; });
		return f:measureWidth(text: text, pixelHeight: pixelHeight);
	}

	## Measures the line height for [pixelHeight].
	Function of Int is measureTextHeight(Int is pixelHeight: 15){
		return pixelHeight;
	}

	## Draws UTF-8 [text] at ([x], [y]) using the loaded system TrueType font.
	Function is drawText(Int is x, Int is y, String is text, Int is color, Int is pixelHeight: 15){
		local Font is f: :activeFont();
		if({ !f:isLoaded() }, { return; });
		f:drawText(
			pixelsAddr: canvas:pixelsAddr(),
			bufW: canvas:width,
			bufH: canvas:height,
			x: x,
			y: y,
			text: text,
			pixelHeight: pixelHeight,
			argbColor: color
		);
	}
}
