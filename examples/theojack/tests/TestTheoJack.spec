#! specunit: suite

Class of SpecUnitTest is TestTheoJack{
	replace [String] is namespace: ['theojack', 'tests'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'theo', [TheoBuffer, TheoRenderer, TheoScreen, KeyEvent, FocusTarget]],
		['base', 'sys', [as File(), as Loops(), as Process()]],
		['theojack', 'model', [Card, CardStyle, Rank, Suit]],
		['theojack', 'util', [HomeStrings, OptionsStorage]],
		['theojack', 'view', [CardView, HomeFrame, OptionsFrame]]
	];

	Function is testHomeScreenCenteredAndEqualWidth(){
		local Boolean is quitCalled: false;
		local Boolean is optionsOpened: false;
		local HomeFrame is home: HomeFrame(
			onOpenOptions: { optionsOpened: true; },
			onQuit: { quitCalled: true; }
		);
		local [FocusTarget] is fts: [home:playFocus, home:rulesFocus, home:optionsFocus, home:aboutFocus, home:quitFocus, home:aboutCloseFocus];
		times(count: fts:length(), worker: local Function(Int is i){
			fts:get(index: i):bindOwner(handler: local Function(Any is _t){
				times(count: fts:length(), worker: local Function(Int is j){
					fts:get(index: j):focused: j == i;
				});
			});
		});
		local TheoScreen is scr: TheoScreen(root: home);
		local TheoBuffer is buf: TheoBuffer(width: 80, height: 24);
		local TheoRenderer is ren: TheoRenderer();

		home:layout(x: 0, y: 0, w: 80, h: 24);
		home:paint(buf: buf, renderer: ren);

		Assert:areEqualInt(11, home:heroCard:measureWidth(maxW: 80));
		Assert:areEqualInt(11, home:measureWidth(maxW: 80) - 11 - 3);
		Assert:areEqualInt(9, home:measureHeight(maxW: 80, maxH: 24));
		# Card (height 7) is vertically centered against the 9-row menu (offset +1)
		Assert:areEqualInt(((24 - 9) / 2) + 1, home:heroCard:boxY);

		# Play -> Rules -> Options -> About -> Quit
		Assert:isTrue(home:playFocus:focused);
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: 'down')));
		Assert:isTrue(home:rulesFocus:focused);
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: 'down')));
		Assert:isTrue(home:optionsFocus:focused);
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: 'enter')));
		Assert:isTrue(optionsOpened);

		# Down to About, Enter opens the About Overlay
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: 'down')));
		Assert:isTrue(home:aboutFocus:focused);
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: 'enter')));
		Assert:isTrue(home:isAboutOpen());
		Assert:isTrue(home:aboutCloseFocus:focused);

		# While About overlay is open, 'q' is blocked from reaching HomeFrame:onKey
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: 'char', key: 'q')));
		Assert:isFalse(quitCalled);

		# Esc closes About overlay and restores focus to About button
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: 'esc')));
		Assert:isFalse(home:isAboutOpen());
		Assert:isTrue(home:aboutFocus:focused);

		# Down focuses Quit, Enter activates Quit
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: 'down')));
		Assert:isTrue(home:quitFocus:focused);
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: 'enter')));
		Assert:isTrue(quitCalled);
	}

	Function is testCardRenderingAndOptionsPersistence(){
		local String is tmpPath: "/tmp/theojack_opts_{{getPid()}}.json";
		if({ fileExists(path: tmpPath) }, { fileRemove(path: tmpPath); });
		local OptionsStorage is storage: OptionsStorage(filePath: tmpPath);
		Assert:isTrue(storage:loadCardStyle() == CardStyle:WIREFRAME);

		local HomeFrame is home: HomeFrame();
		local TheoScreen is scr: TheoScreen(root: home);
		local OptionsFrame is opts: OptionsFrame(
			storage: storage,
			initialStyle: home:heroCard:style,
			onCancel: { scr:pop(); },
			onSave: local Function(CardStyle is saved){
				home:setCardStyle(next: saved);
				scr:pop();
			}
		);
		scr:push(frame: opts);
		Assert:areEqualInt(2, scr:stack:length());

		# Open Card Style dropdown via Enter, move down to Metallic, Enter selects it
		opts:layout(x: 0, y: 0, w: 80, h: 24);
		opts:styleFocus:focused: true;
		Assert:isTrue(opts:handleKey(event: KeyEvent(kind: 'enter')));
		Assert:isTrue(opts:hasOpenOverlay());
		Assert:isTrue(opts:overlays:get(index: 0):content:boxW >= 14);
		Assert:isTrue(opts:handleKey(event: KeyEvent(kind: 'down')));
		Assert:isTrue(opts:handleKey(event: KeyEvent(kind: 'down')));
		Assert:isTrue(opts:handleKey(event: KeyEvent(kind: 'down')));
		Assert:isTrue(opts:handleKey(event: KeyEvent(kind: 'enter')));
		Assert:isFalse(opts:hasOpenOverlay());
		Assert:isTrue(opts:previewCard:style == CardStyle:METALLIC);
		local TheoBuffer is buf: TheoBuffer(width: 80, height: 24);
		local TheoRenderer is ren: TheoRenderer();
		opts:layout(x: 0, y: 0, w: 80, h: 24);
		opts:paint(buf: buf, renderer: ren);

		# Save persists JSON, pops back, and updates HomeFrame card style
		opts:saveAndClose();
		Assert:areEqualInt(1, scr:stack:length());
		Assert:isTrue(home:heroCard:style == CardStyle:METALLIC);
		Assert:isTrue(storage:loadCardStyle() == CardStyle:METALLIC);

		# Card 10 of Diamonds renders without shifting border
		local CardView is tenDia: CardView(card: Card(rank: Rank:TEN, suit: Suit:DIAMONDS), style: CardStyle:BLACK);
		tenDia:layout(x: 0, y: 0, w: 11, h: 7);
		buf:clear();
		tenDia:paint(buf: buf, renderer: ren);
		Assert:areEqualString('╭', buf:cellAt(x: 0, y: 0):ch);
		Assert:areEqualString('1', buf:cellAt(x: 2, y: 1):ch);
		Assert:areEqualString('0', buf:cellAt(x: 3, y: 1):ch);
		Assert:areEqualString('♦', buf:cellAt(x: 5, y: 3):ch);
		Assert:areEqualString('╮', buf:cellAt(x: 10, y: 0):ch);

		fileRemove(path: tmpPath);
	}
}
