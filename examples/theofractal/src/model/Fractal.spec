#! Package theofractal:model
#! Base contract for all renderable fractals in TheoFractal.

Class is Fractal{
	replace [String] is namespace: ['theofractal', 'model'];

	merge [[String]] is using: [
		['theofractal', 'model', [FractalViewport, SampleGrid]]
	];

	Int is lastIterations: 0;
	Int is lastThreadCount: 1;

	## Display name shown in the fractal selector dropdown.
	Function of String is name(){ '' }

	## True when world +Y points upward on screen (geometric/IFS fractals).
	Function of Boolean is isYUp(){ false }

	## Default camera viewport for this fractal.
	Function of FractalViewport is defaultViewport(){ FractalViewport() }

	## Samples normalized intensity values in `[0.0, 1.0]` (or `< 0.0` for background) into a `w * h` grid.
	Function of [Float] is sampleGrid(FractalViewport is viewport, Int is w, Int is h){ [] }

	## Samples separated `(paletteT, coverage, edgeGlow)` channels into a [SampleGrid] of size `w * h`.
	Function of SampleGrid is sampleGridChannels(FractalViewport is viewport, Int is w, Int is h){
		local [Float] is raw: sampleGrid(viewport: viewport, w: w, h: h);
		local [Float] is pal: [];
		local [Float] is cov: [];
		local [Float] is glow: [];
		local Int is n: raw:length();
		local Int is i: 0;
		while({ i < n }, {
			local Float is v: raw:get(index: i);
			if({ v < 0.0 }, {
				pal:push(item: -1.0);
				cov:push(item: 0.0);
				glow:push(item: 0.0);
			}, {
				pal:push(item: v);
				cov:push(item: 1.0);
				glow:push(item: v * 0.15);
			});
			i: i + 1;
		});
		return SampleGrid(paletteT: pal, coverage: cov, edgeGlow: glow);
	}
}
