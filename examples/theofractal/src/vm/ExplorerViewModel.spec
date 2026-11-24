#! Package theofractal:vm
#! ViewModel managing selected fractal, color theme, camera viewport, and cached pixel rendering.

Class is ExplorerViewModel{
	replace [String] is namespace: ['theofractal', 'vm'];

	replace [[String]] is using: [
		['theofractal', 'model', [FractalType, ColorTheme, FractalViewport, FractalRenderer]],
		['theofractal', 'util', FractalStrings],
		['base', 'theo', TheoColor],
		['base', 'sys', as Conditional()]
	];

	FractalType is selectedFractal: FractalType:NONE;
	ColorTheme is selectedTheme: ColorTheme:GRAYSCALE;
	FractalViewport is viewport: FractalViewport();
	FractalRenderer is renderer: FractalRenderer();

	Array of TheoColor is cachedPixels: Array();
	Int is cachedW: 0;
	Int is cachedH: 0;
	Boolean is renderDirty: true;

	Function is onRenderChanged: {};

	Function of Boolean is hasFractal(){ selectedFractal != FractalType:NONE }

	local Function of Boolean is isYUpFractal(){
		return selectedFractal == FractalType:SIERPINSKI
			|| selectedFractal == FractalType:SNOWFLAKE
			|| selectedFractal == FractalType:BARNSLEY_FERN
			|| selectedFractal == FractalType:DRAGON;
	}

	local Function is markRenderDirty(){
		:renderDirty: true;
		onRenderChanged();
	}

	Function is selectFractal(String is name){
		local FractalType is next: match(when: [
			{ name == FractalStrings:OPT_SIERPINSKI }: { FractalType:SIERPINSKI },
			{ name == FractalStrings:OPT_SNOWFLAKE }: { FractalType:SNOWFLAKE },
			{ name == FractalStrings:OPT_MANDELBROT }: { FractalType:MANDELBROT },
			{ name == FractalStrings:OPT_BARNSLEY_FERN }: { FractalType:BARNSLEY_FERN },
			{ name == FractalStrings:OPT_JULIA }: { FractalType:JULIA },
			{ name == FractalStrings:OPT_BURNING_SHIP }: { FractalType:BURNING_SHIP },
			{ name == FractalStrings:OPT_DRAGON }: { FractalType:DRAGON },
			else: { FractalType:NONE }
		]);
		:selectedFractal: next;
		viewport:resetFor(kind: next);
		markRenderDirty();
	}

	Function is selectTheme(String is name){
		:selectedTheme: match(when: [
			{ name == FractalStrings:THEME_COOL }: { ColorTheme:COOL },
			{ name == FractalStrings:THEME_WARM }: { ColorTheme:WARM },
			{ name == FractalStrings:THEME_RAINBOW }: { ColorTheme:RAINBOW },
			else: { ColorTheme:GRAYSCALE }
		]);
		markRenderDirty();
	}

	Function is panLeft(){
		if({ !hasFractal() }, { return; });
		viewport:pan(dxFraction: -0.15, dyFraction: 0.0);
		markRenderDirty();
	}

	Function is panRight(){
		if({ !hasFractal() }, { return; });
		viewport:pan(dxFraction: 0.15, dyFraction: 0.0);
		markRenderDirty();
	}

	Function is panUp(){
		if({ !hasFractal() }, { return; });
		local Float is dir: if({ isYUpFractal() }, { 0.15 }, { -0.15 });
		viewport:pan(dxFraction: 0.0, dyFraction: dir);
		markRenderDirty();
	}

	Function is panDown(){
		if({ !hasFractal() }, { return; });
		local Float is dir: if({ isYUpFractal() }, { -0.15 }, { 0.15 });
		viewport:pan(dxFraction: 0.0, dyFraction: dir);
		markRenderDirty();
	}

	Function is zoomIn(){
		if({ !hasFractal() }, { return; });
		viewport:zoomBy(factor: 1.4);
		markRenderDirty();
	}

	Function is zoomOut(){
		if({ !hasFractal() }, { return; });
		viewport:zoomBy(factor: 1.0 / 1.4);
		markRenderDirty();
	}

	Function is resetView(){
		if({ !hasFractal() }, { return; });
		viewport:resetFor(kind: selectedFractal);
		markRenderDirty();
	}

	Function of Array of TheoColor is ensurePixels(Int is w, Int is h){
		if({ !hasFractal() || w <= 0 || h <= 0 }, {
			:cachedPixels: Array();
			:cachedW: 0;
			:cachedH: 0;
			:renderDirty: false;
			return cachedPixels;
		});
		if({ renderDirty || cachedW != w || cachedH != h }, {
			:cachedPixels: renderer:renderPixels(
				kind: selectedFractal,
				theme: selectedTheme,
				viewport: viewport,
				w: w,
				h: h
			);
			:cachedW: w;
			:cachedH: h;
			:renderDirty: false;
		});
		return cachedPixels;
	}
}
