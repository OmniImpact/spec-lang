#! specunit: suite

Class of SpecUnitTest is TestTheoFramework{
	replace [String] is namespace: ['test', 'lang'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'theo', '*'],
		['base', 'sys', Parallel]
	];

	Function is testBlitRgbAndPixelCanvas(){
		local PixelCanvas is canvas: PixelCanvas();
		local Int is red: Color32:pack(r: 255, g: 0, b: 0);
		local Int is blue: Color32:pack(r: 0, g: 0, b: 255);
		canvas:setPixels(w: 2, pixH: 2, pixels: [red, red, blue, blue]);
		canvas:layout(x: 0, y: 0, w: 2, h: 1);
		local TheoBuffer is buf: TheoBuffer(width: 2, height: 1);
		local TheoRenderer is renderer: TheoRenderer();
		canvas:paint(buf: buf, renderer: renderer);
		local TheoCell is c: buf:cellAt(x: 0, y: 0);
		Assert:isTrue(c:ch == '▀');
		Assert:isTrue(c:fg:c1 == 255 && c:fg:c3 == 0);
		Assert:isTrue(c:bg:c1 == 0 && c:bg:c3 == 255);
	}

	Function is testDropdownNarrowWidthAndRunHeadless(){
		local Frame is frame: Frame();
		local Int is clicks: 0;
		local Dropdown is dd: Dropdown(host: frame, options: ['Alpha', 'Beta'], width: 3);
		local Button is btn: Button(label: 'Go', onClick: { clicks: clicks + 1; });
		frame:rootWidget: Col(children: Array([dd, btn]));
		frame:built: true;

		local TheoScreen is screen: TheoScreen(root: frame);
		local TheoApp is app: TheoApp();
		local [KeyEvent] is keys: [
			KeyEvent(kind: KeyKind:TAB),
			KeyEvent(kind: KeyKind:ENTER)
		];
		local TheoBuffer is buf: app:runHeadless(screen: screen, keys: keys, width: 20, height: 6);
		Assert:isTrue(clicks == 1);
		Assert:isTrue(buf:width == 20 && buf:height == 6);
	}

	Function is testParallelRunScoped(){
		local Int is sum: Parallel():runScoped(
			threads: 2,
			iterations: 4,
			worker: local Function of Int(Int is tid, Int is cnt){ cnt }
		);
		Assert:isTrue(sum == 4);
	}
}
