#! specunit: suite

Class of SpecUnitTest is TestTheoFractal{
	replace [String] is namespace: ['theofractal', 'tests'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'theo', '*'],
		['base', 'sys', as Loops()],
		['theofractal', 'model', [Fractal, FractalRegistry, ColorTheme, FractalViewport]],
		['theofractal', 'util', [as ColorPalette(), FractalStrings]],
		['theofractal', 'vm', ExplorerViewModel],
		['theofractal', 'view', [FractalCanvas, ExplorerFrame]]
	];

	Function is testInitialEmptyState(){
		local ExplorerViewModel is vm: ExplorerViewModel();
		Assert:isFalse(vm:hasFractal());
		Assert:isTrue(vm:activeFractalName() == '');
		Assert:isTrue(vm:selectedTheme == ColorTheme:GRAYSCALE);
		Assert:isFalse(vm:helpOpen);
		local [Int] is pixels: vm:ensurePixels(w: 40, h: 40);
		Assert:isTrue(pixels:length() == 0);
	}

	Function is testAllFractalsRenderNonEmpty(){
		local ExplorerViewModel is vm: ExplorerViewModel();
		local [String] is names: [
			FractalStrings:OPT_SIERPINSKI,
			FractalStrings:OPT_SNOWFLAKE,
			FractalStrings:OPT_MANDELBROT,
			FractalStrings:OPT_BARNSLEY_FERN,
			FractalStrings:OPT_JULIA,
			FractalStrings:OPT_BURNING_SHIP,
			FractalStrings:OPT_DRAGON
		];
		local Int is bg: Color32:pack(r: 10, g: 12, b: 18);
		local Int is ni: 0;
		while({ ni < names:length() }, {
			vm:selectFractal(name: names:get(index: ni));
			Assert:isTrue(vm:hasFractal());
			local [Int] is pixels: vm:ensurePixels(w: 48, h: 48);
			Assert:isTrue(pixels:length() == 48 * 48);
			local Int is litCount: 0;
			local Int is pi: 0;
			while({ pi < pixels:length() }, {
				if({ pixels:get(index: pi) != bg }, {
					litCount: litCount + 1;
				});
				pi: pi + 1;
			});
			Assert:isTrue(litCount > 10);
			ni: ni + 1;
		});
	}

	Function is testThemesAndColorMapping(){
		local TheoColor is gray: colorForValue(t: 0.5, theme: ColorTheme:GRAYSCALE);
		Assert:isTrue(gray:c1 == gray:c2);
		Assert:isTrue(gray:c2 == gray:c3);

		local TheoColor is cool: colorForValue(t: 0.5, theme: ColorTheme:COOL);
		Assert:isTrue(cool:c3 > cool:c1);

		local TheoColor is warm: colorForValue(t: 0.5, theme: ColorTheme:WARM);
		Assert:isTrue(warm:c1 > warm:c3);

		local TheoColor is rain: colorForValue(t: 0.0, theme: ColorTheme:RAINBOW);
		Assert:isTrue(rain:c1 == 255);

		local TheoColor is forest: colorForValue(t: 0.5, theme: ColorTheme:FOREST);
		Assert:isTrue(forest:c2 > forest:c1 && forest:c2 > forest:c3);

		local TheoColor is sunsetPurple: colorForValue(t: 0.25, theme: ColorTheme:SUNSET);
		Assert:isTrue(sunsetPurple:c3 > sunsetPurple:c1 && sunsetPurple:c1 > sunsetPurple:c2);
		local TheoColor is sunsetOrange: colorForValue(t: 0.72, theme: ColorTheme:SUNSET);
		Assert:isTrue(sunsetOrange:c1 > sunsetOrange:c2 && sunsetOrange:c2 > sunsetOrange:c3);
	}

	Function is testViewportPanAndZoom(){
		local ExplorerViewModel is vm: ExplorerViewModel();
		vm:selectFractal(name: FractalStrings:OPT_MANDELBROT);
		local Float is cx0: vm:viewport:centerX;
		local Float is cy0: vm:viewport:centerY;
		local Float is z0: vm:viewport:zoom;

		vm:panLeft();
		Assert:isTrue(vm:viewport:centerX < cx0);
		vm:panRight();
		Assert:isTrue(vm:viewport:centerX > cx0 - 0.001 && vm:viewport:centerX < cx0 + 0.001);

		vm:panUp();
		Assert:isTrue(vm:viewport:centerY < cy0);
		vm:panDown();
		Assert:isTrue(vm:viewport:centerY > cy0 - 0.001 && vm:viewport:centerY < cy0 + 0.001);

		vm:zoomIn();
		Assert:isTrue(vm:viewport:zoom > z0);
		vm:zoomOut();
		Assert:isTrue(vm:viewport:zoom > z0 - 0.01 && vm:viewport:zoom < z0 + 0.01);

		vm:panLeft();
		vm:zoomIn();
		vm:resetView();
		Assert:isTrue(vm:viewport:centerX == cx0);
		Assert:isTrue(vm:viewport:zoom == z0);
	}

	Function is testBottomDropdownOpensUpAndShortcutsWork(){
		local Boolean is quitCalled: false;
		local ExplorerViewModel is vm: ExplorerViewModel(onQuit: { quitCalled: true; });
		local ExplorerFrame is frame: ExplorerFrame(vm: vm);
		frame:layout(x: 0, y: 0, w: 80, h: 24);

		local Dropdown is picker: frame:fractalPickers:get(index: 0);
		Assert:isTrue(picker:boxY >= 20);
		local Overlay is menuOv: picker:menuOverlays:get(index: 0);
		Assert:isTrue(menuOv:content:boxY < picker:boxY);

		local TheoBuffer is buf: TheoBuffer(width: 80, height: 24);
		local TheoRenderer is renderer: TheoRenderer();
		frame:paint(buf: buf, renderer: renderer);

		vm:selectFractal(name: FractalStrings:OPT_SIERPINSKI);
		local Float is cy0: vm:viewport:centerY;
		local Float is z0: vm:viewport:zoom;

		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'w')));
		Assert:isTrue(vm:viewport:centerY > cy0);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 's')));
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'e')));
		Assert:isTrue(vm:viewport:zoom > z0);
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'q')));

		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'h')));
		Assert:isTrue(vm:helpOpen);
		Assert:isTrue(frame:hasBlockingOverlay());
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:ESC)));
		Assert:isFalse(vm:helpOpen);
		Assert:isFalse(frame:hasBlockingOverlay());

		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'q', ctrl: true)));
		Assert:isTrue(quitCalled);

		frame:paint(buf: buf, renderer: renderer);
		Assert:isTrue(buf:cellAt(x: 73, y: 18):ch == '▲');
	}

	Function is testSwitchAndAntialiasing(){
		local ExplorerViewModel is vm: ExplorerViewModel();
		Assert:isFalse(vm:antialiasing);

		local ExplorerFrame is frame: ExplorerFrame(vm: vm);
		frame:layout(x: 0, y: 0, w: 90, h: 24);
		local Switch is aa: frame:aaSwitches:get(index: 0);
		Assert:isFalse(aa:checked);

		aa:focusTarget:requestFocus();
		Assert:isTrue(aa:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: ' ')));
		Assert:isTrue(aa:checked);
		Assert:isTrue(vm:antialiasing);

		vm:selectFractal(name: FractalStrings:OPT_MANDELBROT);
		local [Int] is aaPixels: vm:ensurePixels(w: 32, h: 32);
		Assert:isTrue(aaPixels:length() == 32 * 32);

		aa:toggle();
		Assert:isFalse(aa:checked);
		Assert:isFalse(vm:antialiasing);

		vm:selectFractal(name: FractalStrings:OPT_BARNSLEY_FERN);
		vm:zoomIn();
		vm:zoomIn();
		vm:zoomIn();
		vm:zoomIn();
		local [Int] is zoomedFern: vm:ensurePixels(w: 48, h: 48);
		local Int is bg: Color32:pack(r: 10, g: 12, b: 18);
		local Int is lit: 0;
		local Int is zi: 0;
		while({ zi < zoomedFern:length() }, {
			if({ zoomedFern:get(index: zi) != bg }, {
				lit: lit + 1;
			});
			zi: zi + 1;
		});
		Assert:isTrue(lit > 50);
	}

	Function is testDeepZoomAndFidelity(){
		local ExplorerViewModel is vm: ExplorerViewModel();
		vm:selectFractal(name: FractalStrings:OPT_MANDELBROT);
		vm:viewport:centerX: -0.7436438870371587;
		vm:viewport:centerY: 0.13182590420531197;
		vm:viewport:zoomBy(factor: 1000000000.0);
		Assert:isTrue(vm:viewport:zoom > 500000000.0);
		local [Int] is deepMandel: vm:ensurePixels(w: 32, h: 32);
		Assert:isTrue(deepMandel:length() == 32 * 32);

		vm:selectFractal(name: FractalStrings:OPT_SNOWFLAKE);
		vm:viewport:centerX: 0.0;
		vm:viewport:centerY: 1.0;
		vm:viewport:zoomBy(factor: 100000000.0);
		local [Int] is deepSnow: vm:ensurePixels(w: 32, h: 32);
		Assert:isTrue(deepSnow:length() == 32 * 32);

		vm:selectFractal(name: FractalStrings:OPT_SIERPINSKI);
		vm:viewport:centerX: 0.0;
		vm:viewport:centerY: 1.0;
		vm:viewport:zoomBy(factor: 100000000.0);
		local [Int] is deepSierp: vm:ensurePixels(w: 32, h: 32);
		Assert:isTrue(deepSierp:length() == 32 * 32);

		vm:selectFractal(name: FractalStrings:OPT_DRAGON);
		vm:viewport:centerX: 0.0;
		vm:viewport:centerY: 0.0;
		vm:viewport:zoomBy(factor: 100000000.0);
		local [Int] is deepDragon: vm:ensurePixels(w: 32, h: 32);
		Assert:isTrue(deepDragon:length() == 32 * 32);

		vm:selectFractal(name: FractalStrings:OPT_BARNSLEY_FERN);
		vm:viewport:centerX: 0.0;
		vm:viewport:centerY: 1.6;
		vm:viewport:zoomBy(factor: 1000000.0);
		local [Int] is deepFern: vm:ensurePixels(w: 32, h: 32);
		Assert:isTrue(deepFern:length() == 32 * 32);
		local Int is fernBg: Color32:pack(r: 10, g: 12, b: 18);
		local Int is fernLit: 0;
		local Int is fi: 0;
		while({ fi < deepFern:length() }, {
			if({ deepFern:get(index: fi) != fernBg }, { fernLit: fernLit + 1; });
			fi: fi + 1;
		});
		Assert:isTrue(fernLit > 10);
	}

	Function is testMetricsAndPaletteRotation(){
		local ExplorerViewModel is vm: ExplorerViewModel();
		local ExplorerFrame is frame: ExplorerFrame(vm: vm);
		frame:layout(x: 0, y: 0, w: 90, h: 24);
		Assert:isTrue(vm:metricsTitle() == ' Metrics: idle ');

		vm:selectFractal(name: FractalStrings:OPT_MANDELBROT);
		local TheoBuffer is buf: TheoBuffer(width: 90, height: 24);
		local TheoRenderer is renderer: TheoRenderer();
		frame:paint(buf: buf, renderer: renderer);

		Assert:isTrue(vm:lastIterations >= 100);
		Assert:isTrue(vm:lastThreadCount >= 1);
		Assert:isTrue(vm:lastRenderMs >= 0.0);
		local String is title: vm:metricsTitle();
		Assert:isTrue(title:contains(needle: 'Iter: '));
		Assert:isTrue(title:contains(needle: 'Thr: '));
		Assert:isTrue(title:contains(needle: 'ms | '));
		Assert:isTrue(title:contains(needle: ' fps'));

		local Switch is rot: frame:rotateSwitches:get(index: 0);
		Assert:isFalse(rot:checked);
		Assert:isFalse(vm:paletteRotate);
		Assert:isFalse(frame:onTick());

		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'p')));
		Assert:isTrue(vm:paletteRotate);
		Assert:isTrue(rot:checked);
		Assert:isTrue(frame:onTick());

		local Int is c0: color32ForValue(t: 0.25, theme: ColorTheme:RAINBOW, offset: 0.0);
		local Int is cMid: color32ForValue(t: 0.25, theme: ColorTheme:RAINBOW, offset: 0.5);
		local Int is cFull: color32ForValue(t: 0.25, theme: ColorTheme:RAINBOW, offset: 1.0);
		Assert:isTrue(c0 != cMid);
		Assert:isTrue(c0 == cFull);

		# Coverage AA must blend toward background (10, 12, 18) without shifting palette hue
		local Int is aaEdge: color32ForSample(paletteT: 0.0, coverage: 0.25, edgeGlow: 0.0, theme: ColorTheme:RAINBOW, offset: 0.0);
		Assert:isTrue(Color32:red(color: aaEdge) > 65 && Color32:red(color: aaEdge) < 80);
		Assert:isTrue(Color32:green(color: aaEdge) >= 12 && Color32:green(color: aaEdge) < 35);

		# Edge glow must brighten on top of the rotated base color
		local Int is baseRot: color32ForSample(paletteT: 0.25, coverage: 1.0, edgeGlow: 0.0, theme: ColorTheme:COOL, offset: 0.3);
		local Int is glowRot: color32ForSample(paletteT: 0.25, coverage: 1.0, edgeGlow: 1.0, theme: ColorTheme:COOL, offset: 0.3);
		Assert:isTrue(Color32:red(color: glowRot) > Color32:red(color: baseRot));
	}
}
