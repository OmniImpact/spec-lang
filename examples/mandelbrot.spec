#! Package examples
#! High-resolution 256-color Mandelbrot fractal renderer using smooth escape-time coloring,
#! trigonometric cube palettes, and Unicode block / half-block characters.

## Renders the Mandelbrot set to the console using 256-color ANSI sequences and Unicode blocks.
Class is Mandelbrot{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator'],
		['base', 'math'],
		['base', 'sys', Process],
		['base', 'sys', as Ansi()],
		['base', 'math', as Math()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	## Total number of complex-plane points sampled across all render modes.
	local Int is pointsRendered: 0;

	## Computes the smooth (fractional) escape iteration count for complex point `(cr, ci)`.
	##
	## Uses normalized iteration count: $\nu = n + 1 - \log_2(\log(|z|))$ so color transitions
	## are continuous without banding.
	##
	## @param cr: Real part of complex coordinate $c$.
	## @param ci: Imaginary part of complex coordinate $c$.
	## @param maxIter: Maximum iteration threshold.
	## @return: Smooth iteration value in `[0.0, maxIter]`, or `-1.0` if inside the Mandelbrot set.
	local Function of Float is smoothEscape(Float is cr, Float is ci, Int is maxIter){
		self:pointsRendered: self:pointsRendered + 1;

		# Cardioid and period-2 bulb quick rejection test
		local Float is q: ((cr - 0.25) * (cr - 0.25)) + (ci * ci);
		if(check: { (q * (q + (cr - 0.25))) <= (0.25 * ci * ci) }, then: {
			return -1.0;
		});
		if(check: { ((cr + 1.0) * (cr + 1.0)) + (ci * ci) <= 0.0625 }, then: {
			return -1.0;
		});

		local Float is zr: 0.0;
		local Float is zi: 0.0;
		local Float is zr2: 0.0;
		local Float is zi2: 0.0;
		local Int is iter: 0;

		while(
			evaluate: local Function of Boolean(){
				return (iter < maxIter) && ((zr2 + zi2) <= 16.0);
			},
			iteration: local Function(){
				zi: (2.0 * zr * zi) + ci;
				zr: (zr2 - zi2) + cr;
				zr2: zr * zr;
				zi2: zi * zi;
				iter: iter + 1;
			}
		);

		if(check: { iter >= maxIter }, then: {
			return -1.0;
		});

		local Float is mag: sqrt(value: zr2 + zi2);
		local Float is logMag: log(value: mag);
		local Float is nu: 0.0;
		if(check: { logMag > 0.0 }, then: {
			nu: log2(value: logMag);
		});
		return (toFloat(value: iter) + 1.0) - nu;
	}

	## Maps a smooth escape value to a 256-color palette index (16..231 cube or 16 for interior).
	##
	## Uses phase-shifted cosine waves (`math:cos`) to map smooth escape counts into the
	## 6x6x6 256-color RGB cube (`cubeIndex`).
	##
	## @param mu: Smooth iteration count (`< 0.0` if inside the set).
	## @return: 256-color palette code (16..231).
	local Function of Int is palette256(Float is mu){
		if(check: { mu < 0.0 }, then: {
			return 16;
		});
		local Float is t: mu * 0.18;
		local Float is rf: (0.5 + (0.5 * cos(value: t + 0.0))) * 5.0;
		local Float is gf: (0.5 + (0.5 * cos(value: t + 2.094))) * 5.0;
		local Float is bf: (0.5 + (0.5 * cos(value: t + 4.188))) * 5.0;

		local Int is r: toInt(value: round(value: self:clampFloat(v: rf, lo: 0.0, hi: 5.0)));
		local Int is g: toInt(value: round(value: self:clampFloat(v: gf, lo: 0.0, hi: 5.0)));
		local Int is b: toInt(value: round(value: self:clampFloat(v: bf, lo: 0.0, hi: 5.0)));
		return cubeIndex(r: r, g: g, b: b);
	}

	## Selects a textured Unicode shade character based on fractional escape density.
	##
	## @param mu: Smooth iteration count (`< 0.0` if inside the set).
	## @return: Single Unicode shade block character (` `, `░`, `▒`, `▓`, `█`).
	local Function of String is shadeGlyph(Float is mu){
		if(check: { mu < 0.0 }, then: {
			return ' ';
		});
		local Int is band: toInt(value: mu * 2.0) % 4;
		return if(check: { band == 0 }, then: {
			'░'
		}, else: {
			if(check: { band == 1 }, then: {
				'▒'
			}, else: {
				if(check: { band == 2 }, then: {
					'▓'
				}, else: {
					'█'
				})
			})
		});
	}

	## Clamps a float `v` into `[lo, hi]`.
	local Function of Float is clampFloat(Float is v, Float is lo, Float is hi){
		if(check: { v < lo }, then: {
		return lo;
		});
		if(check: { v > hi }, then: {
		return hi;
		});
		return v;
	}

	## Prints the render statistics block: points sampled, elapsed time, peak memory.
	##
	## @param width: Rendered width in characters.
	## @param height: Rendered height in rows.
	## @param maxIter: Escape iteration threshold used.
	## @param elapsedMs: Total wall-clock render time in milliseconds.
	local Function is printStats(Int is width, Int is height, Int is maxIter, Int is elapsedMs){
		local Int is peakKb: peakMemoryKb();
		local Int is peakMb: peakKb / 1024;
		local Int is elapsedSec: elapsedMs / 1000;
		local String is bar: self:repeatBar(count: width);

		line('');
		line(bold() . color256(code: 51, text: '╔═ Statistics ' . self:repeatBar(count: width - 14) . '╗'));
		line(color256(code: 51, text: '║ Resolution: ' . width . ' x ' . height . ', maxIter ' . maxIter));
		line(color256(code: 51, text: '║ Points sampled: ' . self:pointsRendered));
		line(color256(code: 51, text: '║ Render time: ' . elapsedMs . ' ms (' . elapsedSec . ' s)'));
		line(color256(code: 51, text: '║ Peak memory: ' . peakKb . ' KB (' . peakMb . ' MB)'));
		line(color256(code: 51, text: '║ Threads used: ' . threadCount()));
		line(bold() . color256(code: 51, text: '╚' . bar . '╝'));
	}

	## Builds a horizontal box bar of the given length.
	##
	## @param count: Number of `═` segments.
	## @return: Bar string.
	local Function of String is repeatBar(Int is count){
		local String is bar: '';
		local Int is i: 0;
		while(
			evaluate: local Function of Boolean(){ return i < count; },
			iteration: local Function(){
				bar: bar . '═';
				i: i + 1;
			}
		);
		return bar;
	}

	## Centers a title inside a `║ ... ║` border of the given total width.
	##
	## @param title: Title text.
	## @param width: Total rendered width including borders.
	## @return: Centered, bordered title line.
	local Function of String is centerTitle(String is title, Int is width){
		local String is line: '║';
		local Int is pad: width - 2 - title:length();
		if(check: { pad < 1 }, then: {
			pad: 1;
		});
		local Int is left: pad / 2;
		local Int is right: pad - left;
		local Int is i: 0;
		while(
			evaluate: local Function of Boolean(){ return i < left; },
			iteration: local Function(){ line: line . ' '; i: i + 1; }
		);
		line: line . title;
		i: 0;
		while(
			evaluate: local Function of Boolean(){ return i < right; },
			iteration: local Function(){ line: line . ' '; i: i + 1; }
		);
		return line . '║';
	}

	## Entry point rendering both a sub-pixel half-block (`▀`) 256-color Mandelbrot view
	## and a textured multi-shade (`█▓▒░`) zoom into the Seahorse Valley.
	replace Function is init(Map of String to String is args){
		# Width/height default to the console size; explicit args win.
		local Int is width: args:getInt(key: 'width', default: 0);
		local Int is height: args:getInt(key: 'height', default: 0);
		local Int is maxIter: args:getInt(key: 'iter', default: 80);
		local String is mode: args:getString(key: 'mode', default: 'both');
		local Int is startedAtMs: clockMs();

		if(check: { width <= 0 }, then: {
			width: terminalWidth();
			if(check: { width <= 0 }, then: {
				width: 78;
			});
			width: width - 1;
		});
		if(check: { height <= 0 }, then: {
			height: terminalHeight();
			if(check: { height <= 0 }, then: {
				height: 28;
			});
			height: height - 8;
			if(check: { height < 12 }, then: {
				height: 12;
			});
		});

		line(bold() . color256(code: 51, text: '╔' . self:repeatBar(count: width) . '╗'));
		line(bold() . color256(code: 51, text: self:centerTitle(title: 'Spec 256-Color Mandelbrot Set Renderer', width: width)));
		line(bold() . color256(code: 51, text: '╚' . self:repeatBar(count: width) . '╝'));

		if(check: { mode == 'both' || mode == 'shaded' }, then: {
			line(color256(code: 220, text: '▸ Mode 1: Multi-Glyph Shaded (\'█▓▒░\') 256-Color Full Mandelbrot Set [-2.4..1.0, -1.25..1.25]'));
			self:renderShaded(
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
			self:renderHalfBlock(
				width: width,
				rows: height / 2,
				maxIter: maxIter + 40,
				minRe: -0.82,
				maxRe: -0.70,
				minIm: 0.05,
				maxIm: 0.17
			);
		});

		self:printStats(width: width, height: height, maxIter: maxIter, elapsedMs: clockMs() - startedAtMs);
	}

	## Renders two vertical complex-plane samples per terminal row using the upper half-block `▀`
	## with 256-color foreground (top sample) and 256-color background (bottom sample).
	local Function is renderHalfBlock(Int is width, Int is rows, Int is maxIter, Float is minRe, Float is maxRe, Float is minIm, Float is maxIm){
		local Int is pixelHeight: rows * 2;
		local Float is wFloat: toFloat(value: width - 1);
		local Float is hFloat: toFloat(value: pixelHeight - 1);
		local Int is row: 0;

		while(
			evaluate: local Function of Boolean(){ return row < rows; },
			iteration: local Function(){
				local Int is yTop: row * 2;
				local Int is yBot: yTop + 1;
				local Float is ciTop: maxIm - ((toFloat(value: yTop) / hFloat) * (maxIm - minIm));
				local Float is ciBot: maxIm - ((toFloat(value: yBot) / hFloat) * (maxIm - minIm));

				local String is lineBuf: '';
				local Int is col: 0;
				while(
					evaluate: local Function of Boolean(){ return col < width; },
					iteration: local Function(){
						local Float is cr: minRe + ((toFloat(value: col) / wFloat) * (maxRe - minRe));
						local Float is muTop: self:smoothEscape(cr: cr, ci: ciTop, maxIter: maxIter);
						local Float is muBot: self:smoothEscape(cr: cr, ci: ciBot, maxIter: maxIter);

						local Int is fgCode: self:palette256(mu: muTop);
						local Int is bgCode: self:palette256(mu: muBot);

						lineBuf: lineBuf . paint256(fg: fgCode, bg: bgCode, text: '▀');
						col: col + 1;
					}
				);
				line(lineBuf);
				row: row + 1;
			}
		);
	}

	## Renders the complex plane using textured shade glyphs (`█`, `▓`, `▒`, `░`, ` `) and 256-color foregrounds.
	local Function is renderShaded(Int is width, Int is rows, Int is maxIter, Float is minRe, Float is maxRe, Float is minIm, Float is maxIm){
		local Float is wFloat: toFloat(value: width - 1);
		local Float is hFloat: toFloat(value: rows - 1);
		local Int is row: 0;

		while(
			evaluate: local Function of Boolean(){ return row < rows; },
			iteration: local Function(){
				local Float is ci: maxIm - ((toFloat(value: row) / hFloat) * (maxIm - minIm));
				local String is lineBuf: bg256(code: 16);
				local Int is col: 0;

				while(
					evaluate: local Function of Boolean(){ return col < width; },
					iteration: local Function(){
						local Float is cr: minRe + ((toFloat(value: col) / wFloat) * (maxRe - minRe));
						local Float is mu: self:smoothEscape(cr: cr, ci: ci, maxIter: maxIter);
						local Int is fgCode: self:palette256(mu: mu);
						local String is glyph: self:shadeGlyph(mu: mu);

						lineBuf: lineBuf . fg256(code: fgCode) . glyph;
						col: col + 1;
					}
				);
				lineBuf: lineBuf . reset();
				line(lineBuf);
				row: row + 1;
			}
		);
	}

}
