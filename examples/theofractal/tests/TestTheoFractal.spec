#! specunit: suite

Class of SpecUnitTest is TestTheoFractal{
	replace [String] is namespace: ['theofractal', 'tests'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'theo', '*'],
		['base', 'sys', as Loops()],
		['theofractal', 'model', [FractalType, ColorTheme, FractalViewport, FractalRenderer]],
		['theofractal', 'util', FractalStrings],
		['theofractal', 'vm', ExplorerViewModel],
		['theofractal', 'view', [FractalCanvas, ExplorerFrame]]
	];

	Function is testInitialEmptyState(){
		local ExplorerViewModel is vm: ExplorerViewModel();
		Assert:isFalse(vm:hasFractal());
		Assert:isTrue(vm:selectedFractal == FractalType:NONE);
		Assert:isTrue(vm:selectedTheme == ColorTheme:GRAYSCALE);
		local Array of TheoColor is pixels: vm:ensurePixels(w: 40, h: 40);
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
		local TheoColor is bg: TheoColor:rgb(r: 10, g: 12, b: 18);
		local Int is ni: 0;
		while({ ni < names:length() }, {
			vm:selectFractal(name: names:get(index: ni));
			Assert:isTrue(vm:hasFractal());
			local Array of TheoColor is pixels: vm:ensurePixels(w: 48, h: 48);
			Assert:isTrue(pixels:length() == 48 * 48);
			local Int is litCount: 0;
			local Int is pi: 0;
			while({ pi < pixels:length() }, {
				if({ !pixels:get(index: pi):equals(other: bg) }, {
					litCount: litCount + 1;
				});
				pi: pi + 1;
			});
			Assert:isTrue(litCount > 10);
			ni: ni + 1;
		});
	}

	Function is testThemesAndColorMapping(){
		local FractalRenderer is r: FractalRenderer();
		local TheoColor is gray: r:colorForValue(t: 0.5, theme: ColorTheme:GRAYSCALE);
		Assert:isTrue(gray:c1 == gray:c2);
		Assert:isTrue(gray:c2 == gray:c3);

		local TheoColor is cool: r:colorForValue(t: 0.5, theme: ColorTheme:COOL);
		Assert:isTrue(cool:c3 > cool:c1);

		local TheoColor is warm: r:colorForValue(t: 0.5, theme: ColorTheme:WARM);
		Assert:isTrue(warm:c1 > warm:c3);

		local TheoColor is rain: r:colorForValue(t: 0.0, theme: ColorTheme:RAINBOW);
		Assert:isTrue(rain:c1 == 255);
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
		local TheoApp is app: TheoApp(theme: TheoTheme());
		local ExplorerViewModel is vm: ExplorerViewModel();
		local ExplorerFrame is frame: ExplorerFrame(app: app, vm: vm);
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
		Assert:isTrue(frame:hasBlockingOverlay());
		Assert:isTrue(frame:handleKey(event: KeyEvent(kind: KeyKind:ESC)));
		Assert:isFalse(frame:hasBlockingOverlay());

		frame:paint(buf: buf, renderer: renderer);
	}
}
