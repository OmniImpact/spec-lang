#! Package theofractal:vm
#! ViewModel managing active [Fractal], [ColorTheme], [FractalViewport], Help dialog state, shortcuts, and pixel cache.

Class is ExplorerViewModel{
	replace [String] is namespace: ['theofractal', 'vm'];

	merge [[String]] is using: [
		['theofractal', 'model', [Fractal, FractalRegistry, ColorTheme, FractalViewport, FractalRenderer]],
		['theofractal', 'util', as ColorPalette()],
		['base', 'math', as Math()],
		['base', 'sys', as Time()]
	];

	FractalRegistry is registry: FractalRegistry();
	Array of Fractal is activeFractal: Array();
	ColorTheme is selectedTheme: ColorTheme:GRAYSCALE;
	Boolean is antialiasing: false;
	Boolean is paletteRotate: false;
	Float is paletteOffset: 0.0;
	Int is rotateStartMs: 0;
	FractalViewport is viewport: FractalViewport();
	FractalRenderer is renderer: FractalRenderer();

	Boolean is helpOpen: false;

	[Float] is cachedSamples: [];
	[Int] is cachedPixels: [];
	Int is cachedW: 0;
	Int is cachedH: 0;
	Boolean is renderDirty: true;
	Boolean is paletteDirty: true;

	Int is lastIterations: 0;
	Int is lastThreadCount: 1;
	Float is lastRenderMs: 0.0;
	Float is lastFps: 0.0;
	Int is lastFrameNs: 0;

	Function is onRenderChanged: {};
	Function is onHelpChanged: {};
	Function is onMetricsChanged: {};
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
		renderDirty: true;
		onRenderChanged();
	}

	Function is selectFractal(String is name){
		activeFractal: registry:findByName(name: name);
		if({ activeFractal:length() > 0 }, {
			viewport:copyFrom(other: activeFractal:get(index: 0):defaultViewport());
		});
		markRenderDirty();
	}

	Function is selectTheme(String is name){
		selectedTheme: themeFromName(name: name);
		paletteDirty: true;
		onRenderChanged();
	}

	Function is setPaletteRotate(Boolean is enabled){
		if({ paletteRotate == enabled }, { return; });
		paletteRotate: enabled;
		if({ enabled }, {
			rotateStartMs: monotonicMs() - toInt(value: paletteOffset * 6000.0);
		});
		paletteDirty: true;
		onRenderChanged();
	}

	Function of Boolean is tickPalette(){
		if({ !paletteRotate || !hasFractal() }, { return false; });
		local Int is elapsed: (monotonicMs() - rotateStartMs) % 6000;
		if({ elapsed < 0 }, { elapsed: elapsed + 6000; });
		paletteOffset: toFloat(value: elapsed) / 6000.0;
		paletteDirty: true;
		return true;
	}

	local Function of String is formatTenths(Float is v){
		local Float is clamped: if({ v < 0.0 }, { 0.0 }, { v });
		local Int is tenths: toInt(value: round(value: clamped * 10.0));
		local Int is whole: tenths / 10;
		local Int is frac: tenths % 10;
		return (whole as String) . '.' . (frac as String);
	}

	Function of String is metricsTitle(){
		if({ !hasFractal() }, { return ' Metrics: idle '; });
		return ' Iter: ' . (lastIterations as String)
			. ' | Thr: ' . (lastThreadCount as String)
			. ' | ' . formatTenths(v: lastRenderMs) . 'ms'
			. ' | ' . formatTenths(v: lastFps) . ' fps ';
	}

	Function is setAntialiasing(Boolean is enabled){
		if({ antialiasing == enabled }, { return; });
		antialiasing: enabled;
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
		helpOpen: true;
		onHelpChanged();
	}

	Function is closeHelp(){
		if({ !helpOpen }, { return; });
		helpOpen: false;
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
		if({ key == 'p' || key == 'P' }, { setPaletteRotate(enabled: !paletteRotate); return true; });
		if({ key == 'h' || key == 'H' || key == '?' }, { openHelp(); return true; });
		return false;
	}

	Function of [Int] is ensurePixels(Int is w, Int is h){
		if({ !hasFractal() || w <= 0 || h <= 0 }, {
			cachedSamples: [];
			cachedPixels: [];
			cachedW: 0;
			cachedH: 0;
			renderDirty: false;
			paletteDirty: false;
			lastIterations: 0;
			lastThreadCount: 1;
			lastRenderMs: 0.0;
			lastFps: 0.0;
			lastFrameNs: 0;
			onMetricsChanged();
			return cachedPixels;
		});
		local Boolean is needSample: renderDirty || cachedW != w || cachedH != h;
		if({ needSample || paletteDirty }, {
			local Int is t0: monotonicNs();
			if({ lastFrameNs > 0 && t0 > lastFrameNs }, {
				local Float is instFps: 1000000000.0 / toFloat(value: t0 - lastFrameNs);
				if({ lastFps <= 0.0 }, {
					lastFps: instFps;
				}, {
					lastFps: lastFps * 0.8 + instFps * 0.2;
				});
			});
			lastFrameNs: t0;

			local Fractal is frac: activeFractal:get(index: 0);
			if({ needSample }, {
				cachedSamples: renderer:sampleFractal(
					fractal: frac,
					viewport: viewport,
					w: w,
					h: h,
					antialiasing: antialiasing
				);
				cachedW: w;
				cachedH: h;
				renderDirty: false;
				lastIterations: frac:lastIterations;
				lastThreadCount: frac:lastThreadCount;
			});
			cachedPixels: renderer:colorizeSamples(
				samples: cachedSamples,
				theme: selectedTheme,
				offset: paletteOffset
			);
			paletteDirty: false;
			local Int is elapsedNs: monotonicNs() - t0;
			lastRenderMs: toFloat(value: elapsedNs) / 1000000.0;
			onMetricsChanged();
		});
		return cachedPixels;
	}
}
