#! specunit: suite

Class of SpecUnitTest is TestTheoBuffer{
	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', as Assert()],
		['base', 'theo', TheoColor],
		['base', 'theo', TheoBuffer],
		['base', 'theo', TheoRenderer],
		['base', 'theo', KeyEvent],
		['base', 'theo', MouseEvent],
		['base', 'theo', KeyReader],
		['base', 'theo', Panel],
		['base', 'theo', TextArea],
		['base', 'theo', CodeTextArea],
		['base', 'theo', SyntaxTheme],
		['base', 'theo', Button],
		['base', 'theo', Row],
		['base', 'theo', FocusTarget]
	];

	Function is testBufferDrawBoxAndClip(){
		local TheoBuffer is buf: TheoBuffer(width: 12, height: 4);
		buf:drawBox(x: 0, y: 0, w: 12, h: 4, borderColor: TheoColor:ansi(code: 240));
		buf:setClip(x: 1, y: 1, w: 10, h: 2);
		buf:drawText(x: 1, y: 1, text: 'Hello World!');
		buf:clearClip();

		Assert:areEqualString('╭──────────╮', buf:rowText(y: 0));
		Assert:areEqualString('│Hello Worl│', buf:rowText(y: 1));
		Assert:areEqualString('│          │', buf:rowText(y: 2));
		Assert:areEqualString('╰──────────╯', buf:rowText(y: 3));
	}

	Function is testKeyEventAndRendererTypes(){
		local KeyEvent is ev: KeyEvent(kind: 'char', key: 'm', ctrl: true);
		Assert:isTrue(ev:isChar());
		Assert:isTrue(ev:ctrl);
		Assert:areEqualString('m', ev:key);

		local TheoRenderer is r: TheoRenderer();
		r:setCursor(visible: true, x: 2, y: 1);
		Assert:isTrue(r:cursorVisible);
	}

	Function is testPanelScrollbarsAndTextAreaCursor(){
		local FocusTarget is ft: FocusTarget(initial: true);
		ft:focused: true;
		local TextArea is ta: TextArea(
			value: "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8",
			focusTarget: ft
		);
		local Panel is panel: Panel(
			border: true,
			padding: 0,
			scrollable: true,
			child: ta
		);
		local TheoBuffer is buf: TheoBuffer(width: 12, height: 6);
		local TheoRenderer is renderer: TheoRenderer();
		panel:layout(x: 0, y: 0, w: 12, h: 6);
		panel:paint(buf: buf, renderer: renderer);

		# Cursor in TextArea is blinking thin bar (style 5) in white (#ffffff)
		Assert:isTrue(renderer:cursorVisible);
		Assert:areEqualInt(5, renderer:cursorStyle);
		Assert:areEqualString('#ffffff', renderer:cursorColor);

		# Vertical scrollbar at x=10 (inside right border at x=11), y=1..4
		# 8 lines, viewport 4 -> thumbLen=2, at scrollY=0 thumb is rows 1..2 (light gray 250), track is rows 3..4 (gray 240)
		Assert:areEqualString('▐', buf:cellAt(x: 10, y: 1):ch);
		Assert:areEqualInt(250, buf:cellAt(x: 10, y: 1):fg:c1);
		Assert:areEqualInt(250, buf:cellAt(x: 10, y: 2):fg:c1);
		Assert:areEqualString('▐', buf:cellAt(x: 10, y: 3):ch);
		Assert:areEqualInt(240, buf:cellAt(x: 10, y: 3):fg:c1);
		Assert:areEqualInt(240, buf:cellAt(x: 10, y: 4):fg:c1);

		# Custom ASCII scrollbar chars and colors + horizontal scrollbar
		local TextArea is wideTa: TextArea(
			value: "0123456789abcdef\nrow2",
			focusTarget: ft
		);
		local Panel is customPanel: Panel(
			border: false,
			padding: 0,
			scrollable: true,
			scrollTrackChar: '|',
			scrollThumbChar: '#',
			scrollHTrackChar: '-',
			scrollHThumbChar: '=',
			scrollTrackColor: TheoColor:ansi(code: 235),
			scrollThumbColor: TheoColor:ansi(code: 255),
			child: wideTa
		);
		buf:clear();
		customPanel:layout(x: 0, y: 0, w: 10, h: 4);
		customPanel:paint(buf: buf, renderer: renderer);

		# Vertical scrollbar at x=9: 2 lines fit in 3 rows -> full thumb '#'
		Assert:areEqualString('#', buf:cellAt(x: 9, y: 0):ch);
		Assert:areEqualInt(255, buf:cellAt(x: 9, y: 0):fg:c1);
		# Horizontal scrollbar at y=3: 16 chars in 9-col viewport -> thumb '=' and track '-'
		Assert:areEqualString('=', buf:cellAt(x: 0, y: 3):ch);
		Assert:areEqualInt(255, buf:cellAt(x: 0, y: 3):fg:c1);
		Assert:areEqualString('-', buf:cellAt(x: 8, y: 3):ch);
		Assert:areEqualInt(235, buf:cellAt(x: 8, y: 3):fg:c1);
	}

	Function is testMouseClickHoverAndWheel(){
		local FocusTarget is taFocus: FocusTarget(initial: true);
		taFocus:focused: true;
		local FocusTarget is btnFocus: FocusTarget();
		local Boolean is clicked: false;
		local TextArea is ta: TextArea(
			value: "hello\n\tworld\nline3\nline4\nline5\nline6",
			focusTarget: taFocus
		);
		local Button is btn: Button(
			label: ' Save ',
			focusTarget: btnFocus,
			onClick: { clicked: true; }
		);
		local Row is root: Row(
			gap: 1,
			children: [btn]
		);
		local TheoBuffer is buf: TheoBuffer(width: 20, height: 6);
		local TheoRenderer is renderer: TheoRenderer();

		# Test Button hover and click
		root:layout(x: 0, y: 0, w: 20, h: 1);
		Assert:isTrue(root:handleMouse(event: MouseEvent(kind: 'move', x: 2, y: 0)));
		Assert:isTrue(btn:hovered);
		root:paint(buf: buf, renderer: renderer);
		Assert:areEqualInt(242, buf:cellAt(x: 1, y: 0):bg:c1);

		# Moving mouse outside button clears hover
		Assert:isTrue(root:handleMouse(event: MouseEvent(kind: 'move', x: 15, y: 0)));
		Assert:isFalse(btn:hovered);
		buf:clear();
		root:paint(buf: buf, renderer: renderer);
		Assert:areEqualInt(237, buf:cellAt(x: 1, y: 0):bg:c1);

		# Clicking button triggers onClick and focuses it
		Assert:isTrue(root:handleMouse(event: MouseEvent(kind: 'press', x: 2, y: 0, button: 0)));
		Assert:isTrue(clicked);

		# Test TextArea click-to-move-cursor (with tab) and wheel scroll
		ta:layout(x: 0, y: 0, w: 20, h: 3);
		Assert:isTrue(ta:handleMouse(event: MouseEvent(kind: 'press', x: 6, y: 1, button: 0)));
		Assert:areEqualInt(1, ta:cursorRow);
		Assert:areEqualInt(3, ta:cursorCol);

		Assert:isTrue(ta:handleMouse(event: MouseEvent(kind: 'wheelDown', x: 1, y: 1)));
		Assert:areEqualInt(3, ta:scrollY);
		Assert:isTrue(ta:handleMouse(event: MouseEvent(kind: 'wheelUp', x: 1, y: 1)));
		Assert:areEqualInt(0, ta:scrollY);
	}

	Function is testCodeTextAreaSyntaxHighlightingAndOffscreenState(){
		local TheoRenderer is renderer: TheoRenderer();
		local TheoBuffer is buf: TheoBuffer(width: 40, height: 3);

		# 1. JSON with warm default theme (key=179, string=180, number=215, boolean=202)
		local CodeTextArea is jsonTa: CodeTextArea(
			value: "{\"name\": \"theo\", \"n\": 42, \"ok\": true}",
			filePath: 'config.json'
		);
		jsonTa:layout(x: 0, y: 0, w: 40, h: 3);
		jsonTa:paint(buf: buf, renderer: renderer);
		Assert:areEqualInt(179, buf:cellAt(x: 1, y: 0):fg:c1);
		Assert:areEqualInt(180, buf:cellAt(x: 10, y: 0):fg:c1);
		Assert:areEqualInt(215, buf:cellAt(x: 22, y: 0):fg:c1);
		Assert:areEqualInt(202, buf:cellAt(x: 32, y: 0):fg:c1);

		# 2. Spec highlighting (keyword=208, type=214, comment=137)
		buf:clear();
		local CodeTextArea is specTa: CodeTextArea(
			value: "Class is Foo\n# comment",
			filePath: 'Foo.spec'
		);
		specTa:layout(x: 0, y: 0, w: 40, h: 3);
		specTa:paint(buf: buf, renderer: renderer);
		Assert:areEqualInt(208, buf:cellAt(x: 0, y: 0):fg:c1);
		Assert:areEqualInt(214, buf:cellAt(x: 9, y: 0):fg:c1);
		Assert:areEqualInt(137, buf:cellAt(x: 0, y: 1):fg:c1);

		# 3. Off-screen C block comment scrolled past line 0, plus custom SyntaxTheme
		buf:clear();
		local SyntaxTheme is customTheme: SyntaxTheme(comment: TheoColor:ansi(code: 100), keyword: TheoColor:ansi(code: 111));
		local CodeTextArea is cTa: CodeTextArea(
			value: "/* start\nstill comment\n*/\nint x = 1;",
			filePath: 'main.c',
			syntaxTheme: customTheme,
			useThemeSyntax: false
		);
		cTa:scrollY: 1;
		cTa:followCursor: false;
		cTa:layout(x: 0, y: 0, w: 40, h: 3);
		cTa:paint(buf: buf, renderer: renderer);
		Assert:areEqualInt(100, buf:cellAt(x: 0, y: 0):fg:c1);
		Assert:areEqualInt(111, buf:cellAt(x: 0, y: 2):fg:c1);

		# 4. Markdown heading and off-screen fenced code block
		buf:clear();
		local CodeTextArea is mdTa: CodeTextArea(
			value: "# Title\n```\ncode\n```",
			filePath: 'README.md'
		);
		mdTa:scrollY: 2;
		mdTa:followCursor: false;
		mdTa:layout(x: 0, y: 0, w: 40, h: 2);
		mdTa:paint(buf: buf, renderer: renderer);
		Assert:areEqualInt(180, buf:cellAt(x: 0, y: 0):fg:c1);
		Assert:areEqualInt(245, buf:cellAt(x: 0, y: 1):fg:c1);
	}
}
