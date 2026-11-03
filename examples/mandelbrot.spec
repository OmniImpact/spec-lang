#! Package examples
#! High-resolution 256-color Mandelbrot fractal renderer using smooth escape-time coloring,
#! trigonometric cube palettes, and Unicode block / half-block characters.

## Renders the Mandelbrot set to the console using 256-color ANSI sequences and Unicode blocks.
class Mandelbrot{

	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:math:*,
		base:io:*
	];

	## Computes the smooth (fractional) escape iteration count for complex point `(cr, ci)`.
	##
	## Uses normalized iteration count: $\nu = n + 1 - \log_2(\log(|z|))$ so color transitions
	## are continuous without banding.
	##
	## @param cr: Real part of complex coordinate $c$.
	## @param ci: Imaginary part of complex coordinate $c$.
	## @param maxIter: Maximum iteration threshold.
	## @return: Smooth iteration value in `[0.0, maxIter]`, or `-1.0` if inside the Mandelbrot set.
	replace local Function of Float is smoothEscape(Float is cr, Float is ci, Int is maxIter){
		# Cardioid and period-2 bulb quick rejection test
		local Float is q: ((cr - 0.25) * (cr - 0.25)) + (ci * ci);
		if ((q * (q + (cr - 0.25))) <= (0.25 * ci * ci)) {
			return -1.0;
		}
		if (((cr + 1.0) * (cr + 1.0)) + (ci * ci) <= 0.0625) {
			return -1.0;
		}

		local Float is zr: 0.0;
		local Float is zi: 0.0;
		local Float is zr2: 0.0;
		local Float is zi2: 0.0;
		local Int is iter: 0;

		While:condition(
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

		if (iter >= maxIter) {
			return -1.0;
		}

		local Float is mag: math:sqrt(value: zr2 + zi2);
		local Float is logMag: math:log(value: mag);
		local Float is nu: 0.0;
		if (logMag > 0.0) {
			nu: math:log2(value: logMag);
		}
		return (math:toFloat(value: iter) + 1.0) - nu;
	}

	## Maps a smooth escape value to a 256-color palette index (16..231 cube or 16 for interior).
	##
	## Uses phase-shifted cosine waves (`math:cos`) to map smooth escape counts into the
	## 6x6x6 256-color RGB cube (`Ansi:cubeIndex`).
	##
	## @param mu: Smooth iteration count (`< 0.0` if inside the set).
	## @return: 256-color palette code (16..231).
	replace local Function of Int is palette256(Float is mu){
		if (mu < 0.0) {
			return 16;
		}
		local Float is t: mu * 0.18;
		local Float is rf: (0.5 + (0.5 * math:cos(value: t + 0.0))) * 5.0;
		local Float is gf: (0.5 + (0.5 * math:cos(value: t + 2.094))) * 5.0;
		local Float is bf: (0.5 + (0.5 * math:cos(value: t + 4.188))) * 5.0;

		local Int is r: math:toInt(value: math:round(value: self:clampFloat(v: rf, lo: 0.0, hi: 5.0)));
		local Int is g: math:toInt(value: math:round(value: self:clampFloat(v: gf, lo: 0.0, hi: 5.0)));
		local Int is b: math:toInt(value: math:round(value: self:clampFloat(v: bf, lo: 0.0, hi: 5.0)));
		return Ansi:cubeIndex(r: r, g: g, b: b);
	}

	## Selects a textured Unicode shade character based on fractional escape density.
	##
	## @param mu: Smooth iteration count (`< 0.0` if inside the set).
	## @return: Single Unicode shade block character (` `, `░`, `▒`, `▓`, `█`).
	replace local Function of String is shadeGlyph(Float is mu){
		if (mu < 0.0) {
			return " ";
		}
		local Int is band: math:toInt(value: mu * 2.0) % 4;
		return when (band) {
			is 0: "░";
			is 1: "▒";
			is 2: "▓";
			else: "█";
		};
	}

	## Clamps a float `v` into `[lo, hi]`.
	replace local Function of Float is clampFloat(Float is v, Float is lo, Float is hi){
		if (v < lo) { return lo; }
		if (v > hi) { return hi; }
		return v;
	}

	## Entry point rendering both a sub-pixel half-block (`▀`) 256-color Mandelbrot view
	## and a textured multi-shade (`█▓▒░`) zoom into the Seahorse Valley.
	replace local Function is init(Map of String to String is args){
		local Int is width: args:getInt(key: "width", default: 78);
		local Int is height: args:getInt(key: "height", default: 28);
		local Int is maxIter: args:getInt(key: "iter", default: 80);
		local String is mode: args:getString(key: "mode", default: "both");

		output:line(Ansi:bold() . Ansi:color256(code: 51, text: "╔══════════════════════════════════════════════════════════════════════════════╗"));
		output:line(Ansi:bold() . Ansi:color256(code: 51, text: "║     Spec 256-Color Mandelbrot Set Renderer (Smooth Escape + UTF-8 Blocks)    ║"));
		output:line(Ansi:bold() . Ansi:color256(code: 51, text: "╚══════════════════════════════════════════════════════════════════════════════╝"));

		if (mode == "both" || mode == "shaded") {
			output:line(Ansi:color256(code: 220, text: "▸ Mode 1: Multi-Glyph Shaded ('█▓▒░') 256-Color Full Mandelbrot Set [-2.4..1.0, -1.25..1.25]"));
			self:renderShaded(
				width: width,
				rows: height,
				maxIter: maxIter,
				minRe: -2.4,
				maxRe: 1.0,
				minIm: -1.25,
				maxIm: 1.25
			);
		}

		if (mode == "both" || mode == "halfblock") {
			output:line("");
			output:line(Ansi:color256(code: 213, text: "▸ Mode 2: Sub-Pixel Half-Block ('▀') 256-Color Seahorse Valley Zoom [-0.82..-0.70, 0.05..0.17]"));
			self:renderHalfBlock(
				width: width,
				rows: height / 2,
				maxIter: maxIter + 40,
				minRe: -0.82,
				maxRe: -0.70,
				minIm: 0.05,
				maxIm: 0.17
			);
		}
	}

	## Renders two vertical complex-plane samples per terminal row using the upper half-block `▀`
	## with 256-color foreground (top sample) and 256-color background (bottom sample).
	replace local Function is renderHalfBlock(Int is width, Int is rows, Int is maxIter, Float is minRe, Float is maxRe, Float is minIm, Float is maxIm){
		local Int is pixelHeight: rows * 2;
		local Float is wFloat: math:toFloat(value: width - 1);
		local Float is hFloat: math:toFloat(value: pixelHeight - 1);
		local Int is row: 0;

		While:condition(
			evaluate: local Function of Boolean(){ return row < rows; },
			iteration: local Function(){
				local Int is yTop: row * 2;
				local Int is yBot: yTop + 1;
				local Float is ciTop: maxIm - ((math:toFloat(value: yTop) / hFloat) * (maxIm - minIm));
				local Float is ciBot: maxIm - ((math:toFloat(value: yBot) / hFloat) * (maxIm - minIm));

				local String is lineBuf: "";
				local Int is col: 0;
				While:condition(
					evaluate: local Function of Boolean(){ return col < width; },
					iteration: local Function(){
						local Float is cr: minRe + ((math:toFloat(value: col) / wFloat) * (maxRe - minRe));
						local Float is muTop: self:smoothEscape(cr: cr, ci: ciTop, maxIter: maxIter);
						local Float is muBot: self:smoothEscape(cr: cr, ci: ciBot, maxIter: maxIter);

						local Int is fgCode: self:palette256(mu: muTop);
						local Int is bgCode: self:palette256(mu: muBot);

						lineBuf: lineBuf . Ansi:paint256(fg: fgCode, bg: bgCode, text: "▀");
						col: col + 1;
					}
				);
				output:line(lineBuf);
				row: row + 1;
			}
		);
	}

	## Renders the complex plane using textured shade glyphs (`█`, `▓`, `▒`, `░`, ` `) and 256-color foregrounds.
	replace local Function is renderShaded(Int is width, Int is rows, Int is maxIter, Float is minRe, Float is maxRe, Float is minIm, Float is maxIm){
		local Float is wFloat: math:toFloat(value: width - 1);
		local Float is hFloat: math:toFloat(value: rows - 1);
		local Int is row: 0;

		While:condition(
			evaluate: local Function of Boolean(){ return row < rows; },
			iteration: local Function(){
				local Float is ci: maxIm - ((math:toFloat(value: row) / hFloat) * (maxIm - minIm));
				local String is lineBuf: Ansi:bg256(code: 16);
				local Int is col: 0;

				While:condition(
					evaluate: local Function of Boolean(){ return col < width; },
					iteration: local Function(){
						local Float is cr: minRe + ((math:toFloat(value: col) / wFloat) * (maxRe - minRe));
						local Float is mu: self:smoothEscape(cr: cr, ci: ci, maxIter: maxIter);
						local Int is fgCode: self:palette256(mu: mu);
						local String is glyph: self:shadeGlyph(mu: mu);

						lineBuf: lineBuf . Ansi:fg256(code: fgCode) . glyph;
						col: col + 1;
					}
				);
				lineBuf: lineBuf . Ansi:reset();
				output:line(lineBuf);
				row: row + 1;
			}
		);
	}

}
