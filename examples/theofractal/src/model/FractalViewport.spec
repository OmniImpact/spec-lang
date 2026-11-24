#! Package theofractal:model
#! 2D camera viewport (center and zoom) for fractal exploration.

Class is FractalViewport{
	replace [String] is namespace: ['theofractal', 'model'];

	replace [[String]] is using: [
		['theofractal', 'model', FractalType],
		['base', 'sys', as Conditional()]
	];

	Float is centerX: -0.5;
	Float is centerY: 0.0;
	Float is baseSpan: 2.6;
	Float is zoom: 1.0;

	Function is resetFor(FractalType is kind){
		:zoom: 1.0;
		match(when: [
			{ kind == FractalType:MANDELBROT }: {
				:centerX: -0.5;
				:centerY: 0.0;
				:baseSpan: 2.6;
			},
			{ kind == FractalType:JULIA }: {
				:centerX: 0.0;
				:centerY: 0.0;
				:baseSpan: 2.6;
			},
			{ kind == FractalType:BURNING_SHIP }: {
				:centerX: -0.45;
				:centerY: -0.55;
				:baseSpan: 2.8;
			},
			{ kind == FractalType:SIERPINSKI }: {
				:centerX: 0.0;
				:centerY: -0.05;
				:baseSpan: 2.1;
			},
			{ kind == FractalType:SNOWFLAKE }: {
				:centerX: 0.0;
				:centerY: 0.0;
				:baseSpan: 2.4;
			},
			{ kind == FractalType:BARNSLEY_FERN }: {
				:centerX: 0.0;
				:centerY: 5.0;
				:baseSpan: 10.8;
			},
			{ kind == FractalType:DRAGON }: {
				:centerX: 0.25;
				:centerY: 0.2;
				:baseSpan: 2.0;
			},
			else: {
				:centerX: 0.0;
				:centerY: 0.0;
				:baseSpan: 2.5;
			}
		]);
	}

	Function of Float is spanY(){ baseSpan / zoom }

	Function is pan(Float is dxFraction, Float is dyFraction){
		local Float is step: spanY();
		:centerX: centerX + dxFraction * step;
		:centerY: centerY + dyFraction * step;
	}

	Function is zoomBy(Float is factor){
		local Float is next: zoom * factor;
		if({ next < 0.05 }, { next: 0.05; });
		if({ next > 1000000.0 }, { next: 1000000.0; });
		:zoom: next;
	}
}
