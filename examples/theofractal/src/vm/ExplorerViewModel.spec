#! Package theofractal:vm
#! ViewModel managing active [Fractal], [ColorTheme], [FractalViewport], Help dialog state, shortcuts, and pixel cache.

Class is ExplorerViewModel{
	replace [String] is namespace: ['theofractal', 'vm'];

	replace [[String]] is using: [
		['theofractal', 'model', [Fractal, FractalRegistry, ColorTheme, FractalViewport, FractalRenderer]],
		['theofractal', 'util', as ColorPalette()],
		['base', 'theo', TheoColor],
		['base', 'sys', as Conditional()]
	];

	FractalRegistry is registry: FractalRegistry();
	Array of Fractal is activeFractal: Array();
	ColorTheme is selectedTheme: ColorTheme:GRAYSCALE;
	Boolean is antialiasing: false;
	FractalViewport is viewport: FractalViewport();
	FractalRenderer is renderer: FractalRenderer();

	Boolean is helpOpen: false;

	Array of TheoColor is cachedPixels: Array();
	Int is cachedW: 0;
	Int is cachedH: 0;
	Boolean is renderDirty: true;

	Function is onRenderChanged: {};
	Function is onHelpChanged: {};
	Function is onQuit: {};

	replace Function is init(Function is onQuit: {}){
		:onQuit: onQuit;
	}

	Function of [String] is fractalOptions(){ registry:optionNames() }

	Function of Boolean is hasFractal(){ activeFractal:length() > 0 }

	Function of String is activeFractalName(){
		if({ activeFractal:length() == 0 }, { return ''; });
		return activeFractal:get(index: 0):name();
	}

	local Function is markRenderDirty(){
		:renderDirty: true;
		onRenderChanged();
	}

	Function is selectFractal(String is name){
		:activeFractal: registry:findByName(name: name);
		if({ activeFractal:length() > 0 }, {
			viewport:copyFrom(other: activeFractal:get(index: 0):defaultViewport());
		});
		markRenderDirty();
	}

	Function is selectTheme(String is name){
		:selectedTheme: themeFromName(name: name);
		markRenderDirty();
	}

	Function is setAntialiasing(Boolean is enabled){
		if({ antialiasing == enabled }, { return; });
		:antialiasing: enabled;
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
		local Float is dir: if({ activeFractal:get(index: 0):isYUp() }, { 0.15 }, { -0.15 });
		viewport:pan(dxFraction: 0.0, dyFraction: dir);
		markRenderDirty();
	}

	Function is panDown(){
		if({ !hasFractal() }, { return; });
		local Float is dir: if({ activeFractal:get(index: 0):isYUp() }, { -0.15 }, { 0.15 });
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
		viewport:copyFrom(other: activeFractal:get(index: 0):defaultViewport());
		markRenderDirty();
	}

	Function is openHelp(){
		if({ helpOpen }, { return; });
		:helpOpen: true;
		onHelpChanged();
	}

	Function is closeHelp(){
		if({ !helpOpen }, { return; });
		:helpOpen: false;
		onHelpChanged();
	}

	Function is quit(){
		onQuit();
	}

	Function of Boolean is handleShortcut(String is key, Boolean is ctrl){
		if({ ctrl && (key == 'q' || key == 'Q') }, {
			quit();
			return true;
		});
		if({ key == 'a' || key == 'A' }, { panLeft(); return true; });
		if({ key == 'd' || key == 'D' }, { panRight(); return true; });
		if({ key == 'w' || key == 'W' }, { panUp(); return true; });
		if({ key == 's' || key == 'S' }, { panDown(); return true; });
		if({ key == 'q' || key == 'Q' }, { zoomOut(); return true; });
		if({ key == 'e' || key == 'E' }, { zoomIn(); return true; });
		if({ key == 'r' || key == 'R' }, { resetView(); return true; });
		if({ key == 'h' || key == 'H' || key == '?' }, { openHelp(); return true; });
		return false;
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
				fractal: activeFractal:get(index: 0),
				theme: selectedTheme,
				viewport: viewport,
				w: w,
				h: h,
				antialiasing: antialiasing
			);
			:cachedW: w;
			:cachedH: h;
			:renderDirty: false;
		});
		return cachedPixels;
	}
}
