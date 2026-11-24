#! Package theofractal:model
#! Supported fractal kinds in TheoFractal.

Enum is FractalType{
	replace [String] is namespace: ['theofractal', 'model'];

	NONE,
	SIERPINSKI,
	SNOWFLAKE,
	MANDELBROT,
	BARNSLEY_FERN,
	JULIA,
	BURNING_SHIP,
	DRAGON
}
