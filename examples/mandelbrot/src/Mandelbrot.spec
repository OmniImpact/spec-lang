#! High-resolution 256-color Mandelbrot fractal renderer using smooth escape-time
#! coloring, trigonometric cube palettes, and Unicode block / half-block characters.

## Terminal 256-color Mandelbrot renderer supporting shaded ASCII and half-block modes.
Class is Mandelbrot{

	replace Array of Array of String is using: [
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'cleo', CleoWidth],
		['base', 'cleo', as CleoWidth()],
		['base', 'cleo', BorderStyle],
		['base', 'cleo', TitlePlacement],
		['base', 'struct', Map],
		['base', 'math', as Math()],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		[FractalMath]
	];

	local FractalMath is fractal: FractalMath:init();

	## Prints render statistics (resolution, points sampled, elapsed time, memory, and thread count) via Cleo.
	local Function is printStats(Int is width, Int is height, Int is maxIter, Int is elapsedMs){
		local Int is peakKb: peakMemoryKb();
		local Int is peakMb: peakKb / 1024;
		local Int is elapsedSec: elapsedMs / 1000;

		local Cleo is ui: Cleo:init(
			title: ' mandelbrot ',
			titleColor: CleoColor:ansi(code: 255),
			titleBgColor: CleoColor:ansi(code: 236),
			width: CleoWidth:percent(pct: 100),
			outerBorder: BorderStyle:ROUNDED,
			dividerBorder: BorderStyle:THIN,
			borderColor: CleoColor:ansi(code: 240),
			dividerColor: CleoColor:ansi(code: 237)
		);
		local CleoSection is sSec: ui:addSection(
			title: ' Statistics ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);
		sSec:addLine(text: 'Resolution: ' . width . ' x ' . height . ' · maxIter ' . maxIter, color: CleoColor:ansi(code: 252), rightText: 'Points: ' . :fractal:pointsRendered);
		sSec:addLine(text: 'Render time: ' . elapsedMs . ' ms (' . elapsedSec . ' s)', color: CleoColor:ansi(code: 250), rightText: 'Peak memory: ' . peakMb . ' MB (' . peakKb . ' KB)');
		sSec:addLine(text: 'Threads available: ' . threadCount(), color: CleoColor:ansi(code: 245));
		ui:flushFinal();
	}

	## Returns a horizontal box-drawing bar of [count] `═` characters.
	local Function of String is repeatBar(Int is count){
		local String is bar: '';
		repeat(count: count, worker: {
			bar: bar . '═';
		});
		return bar;
	}

	## Centers [title] inside a bordered banner line of [width] columns.
	local Function of String is centerTitle(String is title, Int is width){
		local String is line: '║';
		local Int is pad: width - 2 - title:length();
		if({ pad < 1 }, {
			pad: 1;
		});
		local Int is left: pad / 2;
		local Int is right: pad - left;
		repeat(count: left, worker: { line: line . ' '; });
		line: line . title;
		repeat(count: right, worker: { line: line . ' '; });
		return line . '║';
	}

	## Entry point; reads optional [args] (`width`, `height`, `iter`, `mode`) and renders the fractal.
	replace Function is init(Map of String to String is args){
		local Int is width: args:getInt(key: 'width', default: 0);
		local Int is height: args:getInt(key: 'height', default: 0);
		local Int is maxIter: args:getInt(key: 'iter', default: 80);
		local String is mode: args:getString(key: 'mode', default: 'both');
		local Int is startedAtMs: clockMs();

		if({ width <= 0 }, {
			width: terminalWidth();
			if({ width <= 0 }, {
				width: 78;
			});
			width: width - 1;
		});
		if({ height <= 0 }, {
			height: terminalHeight();
			if({ height <= 0 }, {
				height: 28;
			});
			height: height - 8;
			if({ height < 12 }, {
				height: 12;
			});
		});

		line(bold() . color256(code: 51, text: '╔' . :repeatBar(count: width) . '╗'));
		line(bold() . color256(code: 51, text: :centerTitle(title: 'Spec 256-Color Mandelbrot Set Renderer', width: width)));
		line(bold() . color256(code: 51, text: '╚' . :repeatBar(count: width) . '╝'));

		if(check: { mode == 'both' || mode == 'shaded' }, then: {
			line(color256(code: 220, text: '▸ Mode 1: Multi-Glyph Shaded (\'█▓▒░\') 256-Color Full Mandelbrot Set [-2.4..1.0, -1.25..1.25]'));
			:renderShaded(
				width: width,
				rows: height,
				maxIter: maxIter,
				minRe: -2.4,
				maxRe: 1.0,
				minIm: -1.25,
				maxIm: 1.25
			);
		});

		if(check: { mode == 'both' || mode == 'halfblock' }, then: {
			line('');
			line(color256(code: 213, text: '▸ Mode 2: Sub-Pixel Half-Block (\'▀\') 256-Color Seahorse Valley Zoom [-0.82..-0.70, 0.05..0.17]'));
			:renderHalfBlock(
				width: width,
				rows: height / 2,
				maxIter: maxIter + 40,
				minRe: -0.82,
				maxRe: -0.70,
				minIm: 0.05,
				maxIm: 0.17
			);
		});

		:printStats(width: width, height: height, maxIter: maxIter, elapsedMs: clockMs() - startedAtMs);
	}

	## Renders the region `[minRe..maxRe, minIm..maxIm]` using 2x vertical sub-pixel `▀` half-blocks.
	local Function is renderHalfBlock(Int is width, Int is rows, Int is maxIter, Float is minRe, Float is maxRe, Float is minIm, Float is maxIm){
		local Int is pixelHeight: rows * 2;
		local Float is wFloat: toFloat(value: width - 1);
		local Float is hFloat: toFloat(value: pixelHeight - 1);
		local Int is row: 0;

		while({ row < rows }, {
			local Int is yTop: row * 2;
			local Int is yBot: yTop + 1;
			local Float is ciTop: maxIm - ((toFloat(value: yTop) / hFloat) * (maxIm - minIm));
			local Float is ciBot: maxIm - ((toFloat(value: yBot) / hFloat) * (maxIm - minIm));

			local String is lineBuf: '';
			local Int is col: 0;
			while({ col < width }, {
				local Float is cr: minRe + ((toFloat(value: col) / wFloat) * (maxRe - minRe));
				local Float is muTop: :fractal:smoothEscape(cr: cr, ci: ciTop, maxIter: maxIter);
				local Float is muBot: :fractal:smoothEscape(cr: cr, ci: ciBot, maxIter: maxIter);

				local Int is fgCode: :fractal:palette256(mu: muTop);
				local Int is bgCode: :fractal:palette256(mu: muBot);

				lineBuf: lineBuf . paint256(fg: fgCode, bg: bgCode, text: '▀');
				col: col + 1;
			});
			line(lineBuf);
			row: row + 1;
		});
	}

	## Renders the region `[minRe..maxRe, minIm..maxIm]` using shaded block glyphs (`░▒▓█`).
	local Function is renderShaded(Int is width, Int is rows, Int is maxIter, Float is minRe, Float is maxRe, Float is minIm, Float is maxIm){
		local Float is wFloat: toFloat(value: width - 1);
		local Float is hFloat: toFloat(value: rows - 1);
		local Int is row: 0;

		while({ row < rows }, {
			local Float is ci: maxIm - ((toFloat(value: row) / hFloat) * (maxIm - minIm));
			local String is lineBuf: bg256(code: 16);
			local Int is col: 0;

			while({ col < width }, {
				local Float is cr: minRe + ((toFloat(value: col) / wFloat) * (maxRe - minRe));
				local Float is mu: :fractal:smoothEscape(cr: cr, ci: ci, maxIter: maxIter);
				local Int is fgCode: :fractal:palette256(mu: mu);
				local String is glyph: :fractal:shadeGlyph(mu: mu);

				lineBuf: lineBuf . fg256(code: fgCode) . glyph;
				col: col + 1;
			});
			lineBuf: lineBuf . reset();
			line(lineBuf);
			row: row + 1;
		});
	}

}
