#! Package suitdemo
#! Suit demo: native Wayland window rendering a grayscale Julia set with WASD/QE navigation and stb_truetype shortcuts HUD.

Class is SuitDemo{
	replace [String] is namespace: ['suitdemo'];

	merge [[String]] is using: [
		['base', 'suit', [SuitCanvas, SuitFont, SuitWindow]],
		['base', 'struct', Map],
		['base', 'sys', [as Output(), as Time()]],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Float is centerX: 0.0;
	Float is centerY: 0.0;
	Float is baseSpan: 2.6;
	Float is zoom: 1.0;
	Int is maxIter: 96;

	local Function is renderJulia(SuitCanvas is canvas, SuitFont is font){
		local Int is w: canvas:width;
		local Int is h: canvas:height;
		if({ w <= 0 || h <= 0 }, { return; });

		local Float is spanX: baseSpan / zoom;
		local Float is aspect: (h as Float) / (w as Float);
		local Float is spanY: spanX * aspect;
		local Float is xMin: centerX - (spanX * 0.5);
		local Float is yMin: centerY - (spanY * 0.5);
		local Float is dx: spanX / (w as Float);
		local Float is dy: spanY / (h as Float);

		local Float is jc: -0.7;
		local Float is ji: 0.27015;

		local Int is py: 0;
		while({ py < h }, {
			local Float is ci0: yMin + ((py as Float) * dy);
			local Int is px: 0;
			while({ px < w }, {
				local Float is zr: xMin + ((px as Float) * dx);
				local Float is zi: ci0;
				local Float is zr2: zr * zr;
				local Float is zi2: zi * zi;
				local Int is iter: 0;
				while({ iter < maxIter && (zr2 + zi2) <= 4.0 }, {
					zi: (2.0 * zr * zi) + ji;
					zr: (zr2 - zi2) + jc;
					zr2: zr * zr;
					zi2: zi * zi;
					iter: iter + 1;
				});
				local Int is color: -16777216;
				if({ iter < maxIter }, {
					local Int is v: (iter * 255) / maxIter;
					color: -16777216 | (v << 16) | (v << 8) | v;
				});
				canvas:setPixel(x: px, y: py, color: color);
				px: px + 1;
			});
			py: py + 1;
		});

		if({ font:isLoaded() }, {
			canvas:fillRect(x: 12, y: 12, w: 430, h: 30, color: -15722972);
			font:drawText(
				canvas: canvas,
				x: 20,
				y: 17,
				text: 'WASD: Pan   Q/E: Zoom   Esc: Quit',
				size: 18,
				color: -1
			);
		});
	}

	local Function of Boolean is handleKey(Int is key, SuitWindow is win){
		local Float is panStep: (baseSpan / zoom) * 0.1;
		return match(when: [
			{ key == 119 }: { centerY: centerY - panStep; true },
			{ key == 115 }: { centerY: centerY + panStep; true },
			{ key == 97 }:  { centerX: centerX - panStep; true },
			{ key == 100 }: { centerX: centerX + panStep; true },
			{ key == 113 }: { zoom: zoom / 1.25; true },
			{ key == 101 }: { zoom: zoom * 1.25; true },
			{ key == 27 }:  { win:close(); false },
			else: { false }
		]);
	}

	replace Function is init(Map of String to String is args){
		local Int is durationMs: args:getString(key: 'duration-ms', default: '0'):parseInt(default: 0);
		local SuitWindow is win: SuitWindow(title: 'Suit Demo', width: 800, height: 600, decorated: true);
		if({ !win:open() }, {
			line(text: 'SuitDemo failed to open window: ' . win:lastError());
			return;
		});

		local Int is curW: win:width();
		local Int is curH: win:height();
		if({ curW <= 0 }, { curW: 800; });
		if({ curH <= 0 }, { curH: 600; });

		local SuitCanvas is canvas: SuitCanvas(width: curW, height: curH);
		local SuitFont is font: SuitFont();
		if({ !font:loadSystemFont() }, {
			line(text: 'SuitDemo font warning: ' . font:lastError());
		});

		local Boolean is dirty: true;
		local Int is startMs: monotonicMs();
		while({ win:poll() }, {
			local Int is ww: win:width();
			local Int is wh: win:height();
			if({ ww > 0 && wh > 0 && (ww != canvas:width || wh != canvas:height) }, {
				canvas:resize(width: ww, height: wh);
				dirty: true;
			});

			local Int is k: win:nextKey();
			while({ k != 0 }, {
				if({ handleKey(key: k, win: win) }, {
					dirty: true;
				});
				k: win:nextKey();
			});

			if({ dirty && win:isOpen() }, {
				renderJulia(canvas: canvas, font: font);
				win:present(canvas: canvas);
				dirty: false;
			});

			if({ durationMs > 0 && (monotonicMs() - startMs) >= durationMs }, {
				win:close();
			});
		});

		font:close();
		canvas:dispose();
	}
}
