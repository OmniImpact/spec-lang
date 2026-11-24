#! Package theofractal:model
#! Registry of available [Fractal] implementations and selector option names.

Class is FractalRegistry{
	replace [String] is namespace: ['theofractal', 'model'];

	merge [[String]] is using: [
		['theofractal', 'model', Fractal],
		['theofractal', 'model', 'fractals', [SierpinskiFractal, SnowflakeFractal, MandelbrotFractal, BarnsleyFernFractal, JuliaFractal, BurningShipFractal, DragonFractal]],
		['theofractal', 'util', FractalStrings]
	];

	Array of Fractal is fractals: Array([
		SierpinskiFractal(),
		SnowflakeFractal(),
		MandelbrotFractal(),
		BarnsleyFernFractal(),
		JuliaFractal(),
		BurningShipFractal(),
		DragonFractal()
	]);

	## Returns dropdown option labels starting with `"Select Fractal"`, followed by each registered fractal's name.
	Function of [String] is optionNames(){
		local [String] is out: [FractalStrings:OPT_SELECT_FRACTAL];
		local Int is i: 0;
		while({ i < fractals:length() }, {
			out:push(item: fractals:get(index: i):name());
			i: i + 1;
		});
		return out;
	}

	## Returns a 0-or-1-element array containing the [Fractal] matching [name], or empty if none.
	Function of Array of Fractal is findByName(String is name){
		local Int is i: 0;
		while({ i < fractals:length() }, {
			local Fractal is f: fractals:get(index: i);
			if({ f:name() == name }, {
				return Array([f]);
			});
			i: i + 1;
		});
		return Array();
	}
}
