#! Package base:theo
#! Reusable half-block (`'▀'`) pixel canvas widget backed by a packed `Color32` pixel buffer.

Class of Widget is PixelCanvas{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [Widget, TheoBuffer, TheoRenderer]]
	];

	[Int] is pixels: [];
	Int is pixelWidth: 0;
	Int is pixelHeight: 0;

	replace Function is init(){
		:pixels: [];
		:pixelWidth: 0;
		:pixelHeight: 0;
	}

	## Updates the backing packed `Color32` pixel buffer (`w * pixH` elements) and marks dirty.
	Function is setPixels(Int is w, Int is pixH, [Int] is pixels){
		:pixelWidth: w;
		:pixelHeight: pixH;
		:pixels: pixels;
		invalidate();
	}

	replace Function of Float is flexWeight(){ 1.0 }

	replace Function of Int is measureWidth(Int is maxW){ maxW }

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){ maxH }

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW <= 0 || boxH <= 0 }, { return; });
		if({ pixelWidth != boxW || pixelHeight != boxH * 2 || pixels:length() < boxW * boxH * 2 }, {
			buf:fillRect(x: boxX, y: boxY, w: boxW, h: boxH, fg: activeTheme:foreground, bg: activeTheme:background);
			return;
		});
		buf:blitRgb(x: boxX, y: boxY, w: boxW, h: boxH, pixels: pixels);
	}
}
