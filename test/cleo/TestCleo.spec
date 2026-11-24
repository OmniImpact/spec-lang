#! specunit: suite
#! Unit tests for base:cleo components (text width, width resolution, sections,
#! blinking/color-changing shape throbbers, two-stage progress, and image canvas).

Class of SpecUnitTest is TestCleo{

	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'cleo', CleoWidth],
		['base', 'cleo', as CleoWidth()],
		['base', 'cleo', CleoText],
		['base', 'cleo', as CleoText()],
		['base', 'cleo', CleoImage],
		['base', 'cleo', BorderStyle],
		['base', 'cleo', BorderGlyphs],
		['base', 'cleo', as BorderGlyphs()],
		['base', 'cleo', ThrobberShape],
		['base', 'cleo', ThrobberEffect],
		['base', 'cleo', TitlePlacement],
		['base', 'struct', Array],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Loops()]
	];

	Function is testDisplayWidthIgnoresAnsi(){
		local String is colored: Ansi:color256(code: 42, text: 'hello');
		Assert:areEqualInt(5, CleoText:displayWidth(text: colored));
		Assert:areEqualInt(3, CleoText:displayWidth(text: '✔ ⠸'));
		Assert:areEqualInt(4, CleoText:displayWidth(text: '中文'));
		local String is trunc: CleoText:truncate(text: 'abcdefghij', maxCols: 6);
		Assert:areEqualInt(6, CleoText:displayWidth(text: trunc));
		Assert:isTrue(trunc:contains(needle: '...'));
		local String is padded: CleoText:padRight(text: 'hi', width: 5);
		Assert:areEqualInt(5, CleoText:displayWidth(text: padded));
		Assert:areEqualString('===', CleoText:repeatStr(s: '=', count: 3));
	}

	Function is testWidthResolution(){
		local CleoWidth is pct: CleoWidth:percent(pct: 100);
		Assert:areEqualInt(100, pct:resolve(termWidth: 100));
		local CleoWidth is half: CleoWidth:percent(pct: 50);
		Assert:areEqualInt(50, half:resolve(termWidth: 100));
		local CleoWidth is pxW: CleoWidth:px(pixels: 640, cellPx: 8);
		Assert:areEqualInt(80, pxW:resolve(termWidth: 120));
		local CleoWidth is clampedMin: CleoWidth:cols(count: 5);
		Assert:areEqualInt(20, clampedMin:resolve(termWidth: 80, minCols: 20));
		local CleoWidth is clampedMax: CleoWidth:cols(count: 150);
		Assert:areEqualInt(90, clampedMax:resolve(termWidth: 120, minCols: 20, maxCols: 90));
	}

	Function is testBorderStylesAndGlyphs(){
		local BorderGlyphs is ascii: BorderGlyphs:forStyle(style: BorderStyle:ASCII);
		Assert:areEqualString('+', ascii:topLeft);
		Assert:areEqualString('-', ascii:top);
		Assert:areEqualString('|', ascii:left);

		local BorderGlyphs is dbl: BorderGlyphs:forStyle(style: BorderStyle:DOUBLE);
		Assert:areEqualString('╔', dbl:topLeft);
		Assert:areEqualString('═', dbl:top);

		local BorderGlyphs is none: BorderGlyphs:forStyle(style: BorderStyle:NONE);
		Assert:areEqualString('', none:topLeft);

		local Cleo is noBorderOut: Cleo:init(
			width: CleoWidth:cols(count: 40),
			outerBorder: BorderStyle:NONE,
			dividerBorder: BorderStyle:NONE
		);
		noBorderOut:addLine(text: 'plain line');
		local Array of String is nbLines: noBorderOut:buildFrameLines();
		Assert:areEqualInt(1, nbLines:length());
		Assert:isTrue(nbLines:get(index: 0, default: ''):contains(needle: 'plain line'));
	}

	Function is testSectionsAndProgressRendering(){
		local Cleo is out: Cleo:init(
			title: ' SpecUnit ',
			titleColor: CleoColor:ansi(code: 255),
			titleBgColor: CleoColor:ansi(code: 236),
			width: CleoWidth:cols(count: 60),
			outerBorder: BorderStyle:ROUNDED,
			dividerBorder: BorderStyle:THIN,
			borderColor: CleoColor:ansi(code: 240),
			dividerColor: CleoColor:ansi(code: 237)
		);
		local CleoSection is wSec: out:addSection(
			title: ' Workers ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 238),
			fgColor: CleoColor:ansi(code: 250)
		);
		local CleoSection is emptySec: out:addSection(
			title: ' Empty ',
			titlePlacement: TitlePlacement:HEADER_ROW
		);
		local Int is s0: wSec:addShapeThrobber(
			shape: ThrobberShape:DOT,
			effect: ThrobberEffect:BLINK,
			color: CleoColor:ansi(code: 250),
			text: 'test/cleo/TestCleo.spec'
		);
		local CleoSection is pSec: out:addSection(
			title: ' Suite Progress ',
			titlePlacement: TitlePlacement:INLINE_BORDER
		);
		local Int is p0: pSec:addProgressArea(text: 'Running suites...');
		pSec:updateProgress(index: p0, text: '50/100 completed', stage1: 0.5, stage2: 0.75);
		wSec:resolveSlot(index: s0, badge: '✔', text: 'test/cleo/TestCleo.spec');

		local Array of String is lines: out:buildFrameLines();
		Assert:isTrue(lines:length() >= 7);
		Assert:isTrue(lines:get(index: 0, default: ''):contains(needle: 'SpecUnit'));

		# Empty section should not appear until it has a slot
		local Boolean is sawEmpty: false;
		local Int is li: 0;
		while({ li < lines:length() }, {
			sawEmpty: sawEmpty || lines:get(index: li, default: ''):contains(needle: 'Empty');
			li: li + 1;
		});
		Assert:isFalse(sawEmpty);

		emptySec:addLine(text: 'now populated', rightText: 'ok');
		local Array of String is lines2: out:buildFrameLines();
		local Boolean is sawNow: false;
		local Int is l2i: 0;
		while({ l2i < lines2:length() }, {
			sawNow: sawNow || lines2:get(index: l2i, default: ''):contains(needle: 'Empty');
			l2i: l2i + 1;
		});
		Assert:isTrue(sawNow);
	}

	Function is testShapeThrobbersAndReopen(){
		local Cleo is out: Cleo:init(
			width: CleoWidth:cols(count: 50),
			outerBorder: BorderStyle:THIN,
			dividerBorder: BorderStyle:DASHED
		);
		local CleoSection is sec: out:addSection(title: ' Jobs ');
		local Int is t0: sec:addShapeThrobber(
			shape: ThrobberShape:CIRCLE_DOT,
			effect: ThrobberEffect:BLINK,
			color: CleoColor:ansi(code: 250),
			text: 'compiling'
		);
		local Array of String is f0: out:buildFrameLines();
		local Boolean is sawDotCircle: false;
		local Int is i0: 0;
		while({ i0 < f0:length() }, {
			sawDotCircle: sawDotCircle || f0:get(index: i0, default: ''):contains(needle: '◉');
			i0: i0 + 1;
		});
		Assert:isTrue(sawDotCircle);

		out:tickCount: 1;
		local Array of String is f1: out:buildFrameLines();
		local Boolean is sawCircle: false;
		local Int is i1: 0;
		while({ i1 < f1:length() }, {
			sawCircle: sawCircle || f1:get(index: i1, default: ''):contains(needle: '○');
			i1: i1 + 1;
		});
		Assert:isTrue(sawCircle);

		sec:resolveSlot(index: t0, badge: '●', text: 'passed', color: CleoColor:ansi(code: 255));
		local Array of String is f2: out:buildFrameLines();
		local Boolean is sawFilled: false;
		local Int is i2: 0;
		while({ i2 < f2:length() }, {
			local String is row2: f2:get(index: i2, default: '');
			sawFilled: sawFilled || (row2:contains(needle: '●') && row2:contains(needle: 'passed'));
			i2: i2 + 1;
		});
		Assert:isTrue(sawFilled);

		sec:reopenThrobber(index: t0, text: 're-running');
		local Array of String is f3: out:buildFrameLines();
		local Boolean is sawRerun: false;
		local Int is i3: 0;
		while({ i3 < f3:length() }, {
			sawRerun: sawRerun || f3:get(index: i3, default: ''):contains(needle: 're-running');
			i3: i3 + 1;
		});
		Assert:isTrue(sawRerun);
	}

	Function is testTwoStageProgressClamping(){
		local Cleo is out: Cleo:init(width: CleoWidth:cols(count: 50));
		local Int is p0: out:addProgressArea(text: 'Init', showTwoStagePercent: true);
		out:updateProgress(index: p0, text: 'Clamped', stage1: 1.5, stage2: 0.25);
		local Array of String is lines: out:buildFrameLines();
		local Boolean is sawPct: false;
		local Int is pi: 0;
		while({ pi < lines:length() }, {
			sawPct: sawPct || lines:get(index: pi, default: ''):contains(needle: '100%');
			pi: pi + 1;
		});
		Assert:isTrue(sawPct);
	}

	Function is testImageCanvas(){
		local CleoImage is img: CleoImage:init(pixelWidth: 4, pixelHeight: 4);
		img:setPixel(x: 0, y: 0, r: 255, g: 0, b: 0);
		img:setPixel(x: 0, y: 1, r: 0, g: 0, b: 255);
		local Array of String is rows: img:renderLines();
		Assert:areEqualInt(2, rows:length());
		Assert:isTrue(rows:get(index: 0, default: ''):contains(needle: '▀'));

		local Cleo is out: Cleo:init(width: CleoWidth:cols(count: 40));
		local CleoSection is sec: out:addSection(title: ' Art ');
		sec:addImage(image: img);
		sec:addAsciiImage(lines: Array([' /\\ ', '/__\\']));
		local Array of String is fl: out:buildFrameLines();
		Assert:isTrue(fl:length() >= 6);
	}
}
