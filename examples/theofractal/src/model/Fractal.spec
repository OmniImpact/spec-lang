#! Package theofractal:model
#! Base contract for all renderable fractals in TheoFractal.

Class is Fractal{
	replace [String] is namespace: ['theofractal', 'model'];

	merge [[String]] is using: [
		['theofractal', 'model', FractalViewport]
	];

	## Display name shown in the fractal selector dropdown.
	Function of String is name(){ '' }

	## True when world +Y points upward on screen (geometric/IFS fractals).
	Function of Boolean is isYUp(){ false }

	## Default camera viewport for this fractal.
	Function of FractalViewport is defaultViewport(){ FractalViewport() }

	## Samples normalized intensity values in `[0.0, 1.0]` (or `< 0.0` for background) into a `w * h` grid.
	Function of Array of Float is sampleGrid(FractalViewport is viewport, Int is w, Int is h){ Array() }
}
