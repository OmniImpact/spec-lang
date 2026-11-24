#! Package theofractal:model
#! 2D camera viewport (center and zoom) for fractal exploration.

Class is FractalViewport{
	replace [String] is namespace: ['theofractal', 'model'];

	Float is centerX: 0.0;
	Float is centerY: 0.0;
	Float is baseSpan: 2.5;
	Float is zoom: 1.0;

	replace Function is init(
		Float is centerX: 0.0,
		Float is centerY: 0.0,
		Float is baseSpan: 2.5,
		Float is zoom: 1.0
	){
		:centerX: centerX;
		:centerY: centerY;
		:baseSpan: baseSpan;
		:zoom: zoom;
	}

	Function is copyFrom(FractalViewport is other){
		:centerX: other:centerX;
		:centerY: other:centerY;
		:baseSpan: other:baseSpan;
		:zoom: other:zoom;
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
