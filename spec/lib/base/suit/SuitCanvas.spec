#! Package base:suit
#! Off-screen ARGB8888 pixel canvas for Suit rendering.

Class is SuitCanvas{
	replace [String] is namespace: ['base', 'suit'];

	merge [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()]
	];

	Int is width: 0;
	Int is height: 0;
	Int is pixelsPtr: 0;
	Int is byteSize: 0;

	replace Function is init(Int is width: 800, Int is height: 600){
		resize(width: width, height: height);
	}

	## Resizes (reallocating if needed) the backing ARGB8888 buffer.
	Function is resize(Int is width, Int is height){
		if({ width <= 0 || height <= 0 }, { return; });
		if({ :width == width && :height == height && pixelsPtr != 0 }, { return; });
		local Int is needed: width * height * 4;
		if({ pixelsPtr == 0 }, {
			pixelsPtr: Mem:alloc(bytes: needed);
			byteSize: needed;
		}, {
			if({ needed > byteSize }, {
				pixelsPtr: Mem:realloc(ptr: pixelsPtr, bytes: needed);
				byteSize: needed;
			});
		});
		:width: width;
		:height: height;
	}

	## Packs 8-bit R, G, B, A channels into an ARGB8888 integer.
	Function of Int is argb(Int is r, Int is g, Int is b, Int is a: 255){
		return ((a & 255) << 24) | ((r & 255) << 16) | ((g & 255) << 8) | (b & 255);
	}

	## Writes a single ARGB8888 pixel at ([x], [y]) with bounds clipping.
	Function is setPixel(Int is x, Int is y, Int is color){
		if({ pixelsPtr == 0 || x < 0 || y < 0 || x >= width || y >= height }, { return; });
		Mem:storeI32(ptr: pixelsPtr, byteOffset: ((y * width) + x) * 4, val: color);
	}

	## Fills a rectangle ([x], [y], [w], [h]) with [color].
	Function is fillRect(Int is x, Int is y, Int is w, Int is h, Int is color){
		if({ pixelsPtr == 0 || w <= 0 || h <= 0 }, { return; });
		local Int is x0: if({ x < 0 }, { 0 }, { x });
		local Int is y0: if({ y < 0 }, { 0 }, { y });
		local Int is x1: if({ x + w > width }, { width }, { x + w });
		local Int is y1: if({ y + h > height }, { height }, { y + h });
		local Int is py: y0;
		while({ py < y1 }, {
			local Int is rowOff: py * width;
			local Int is px: x0;
			while({ px < x1 }, {
				Mem:storeI32(ptr: pixelsPtr, byteOffset: (rowOff + px) * 4, val: color);
				px: px + 1;
			});
			py: py + 1;
		});
	}

	## Clears the entire canvas to [color].
	Function is clear(Int is color){
		fillRect(x: 0, y: 0, w: width, h: height, color: color);
	}

	## Returns the raw pointer to the ARGB8888 pixel buffer.
	Function of Int is pixelsAddr(){
		return pixelsPtr;
	}

	## Frees the backing pixel buffer.
	Function is dispose(){
		if({ pixelsPtr != 0 }, {
			Mem:free(ptr: pixelsPtr);
			pixelsPtr: 0;
			byteSize: 0;
		});
	}
}
