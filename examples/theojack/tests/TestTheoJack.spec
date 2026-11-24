#! specunit: suite

Class of SpecUnitTest is TestTheoJack{
	replace [String] is namespace: ['theojack', 'tests'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'theo', [TheoBuffer, TheoRenderer, TheoScreen, KeyEvent, KeyKind, MouseEvent, MouseKind, FocusTarget, ShortcutKey]],
		['base', 'sys', [as File(), as Loops(), as Process()]],
		['theojack', 'model', [Card, CardStyle, GamePhase, Hand, Rank, Suit]],
		['theojack', 'util', [HomeStrings, OptionsStorage, RulesLoader]],
		['theojack', 'vm', [GameViewModel, HomeViewModel, OptionsViewModel, RulesViewModel]],
		['theojack', 'view', [CardView, HomeFrame, OptionsFrame, RulesFrame, GameFrame]]
	];

	Function is testHomeScreenCenteredAndEqualWidth(){
		local Boolean is quitCalled: false;
		local Boolean is rulesOpened: false;
		local Boolean is optionsOpened: false;
		local HomeViewModel is vm: HomeViewModel(
			onOpenRules: { rulesOpened: true; },
			onOpenOptions: { optionsOpened: true; },
			onQuit: { quitCalled: true; }
		);
		local HomeFrame is home: HomeFrame(vm: vm);
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
		Assert:areEqualInt(7, home:heroCard:boxH);
		Assert:areEqualString('H', buf:cellAt(x: 38, y: 0):ch);

		# Play -> Rules -> Options -> About
		Assert:isTrue(home:playFocus:focused);
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: KeyKind:DOWN)));
		Assert:isTrue(home:rulesFocus:focused);
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: KeyKind:ENTER)));
		Assert:isTrue(rulesOpened);

		Assert:isTrue(home:handleKey(event: KeyEvent(kind: KeyKind:DOWN)));
		Assert:isTrue(home:optionsFocus:focused);
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: KeyKind:ENTER)));
		Assert:isTrue(optionsOpened);

		# Down to About, Enter opens the About Overlay
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: KeyKind:DOWN)));
		Assert:isTrue(home:aboutFocus:focused);
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: KeyKind:ENTER)));
		Assert:isTrue(home:isAboutOpen());
		Assert:isTrue(home:aboutCloseFocus:focused);

		# While About overlay is open, 'q' is blocked from reaching HomeFrame:onKey
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'q')));
		Assert:isFalse(quitCalled);

		# Esc closes About overlay and restores focus to About button
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: KeyKind:ESC)));
		Assert:isFalse(home:isAboutOpen());
		Assert:isTrue(home:aboutFocus:focused);

		# 'q' triggers Quit from HomeFrame
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'q')));
		Assert:isTrue(quitCalled);

		# ShortcutKey wrapper matches modifier + key cleanly
		local ShortcutKey is sk: ShortcutKey:ctrl(key: 's');
		Assert:isTrue(sk:matches(event: KeyEvent(kind: KeyKind:CHAR, key: 's', ctrl: true)));
		Assert:isFalse(sk:matches(event: KeyEvent(kind: KeyKind:CHAR, key: 's', ctrl: false)));
		Assert:areEqualString('Ctrl+S', sk:displayText());
	}

	Function is testCardRenderingAndOptionsPersistence(){
		local String is tmpPath: "/tmp/theojack_opts_{{getPid()}}.json";
		if({ fileExists(path: tmpPath) }, { fileRemove(path: tmpPath); });
		local OptionsStorage is storage: OptionsStorage(filePath: tmpPath);
		Assert:isTrue(storage:loadCardStyle() == CardStyle:WIREFRAME);

		local HomeViewModel is hvm: HomeViewModel();
		local HomeFrame is home: HomeFrame(vm: hvm);
		local TheoScreen is scr: TheoScreen(root: home);
		local OptionsViewModel is ovm: OptionsViewModel(
			storage: storage,
			initialStyle: hvm:cardStyle:current(),
			initialAmount: storage:startingAmount,
			initialRounds: storage:numRounds,
			onCancel: { scr:pop(); },
			onSave: local Function(CardStyle is saved){
				hvm:setCardStyle(next: saved);
				scr:pop();
			}
		);
		local OptionsFrame is opts: OptionsFrame(vm: ovm);
		scr:push(frame: opts);
		Assert:areEqualInt(2, scr:stack:length());

		# Open Card Style dropdown via Enter, move down to Metallic, Enter selects it
		opts:layout(x: 0, y: 0, w: 80, h: 24);
		opts:styleFocus:focused: true;
		Assert:isTrue(opts:handleKey(event: KeyEvent(kind: KeyKind:ENTER)));
		Assert:isTrue(opts:hasOpenOverlay());
		Assert:isTrue(opts:overlays:get(index: 0):content:boxW >= 14);
		Assert:isTrue(opts:handleKey(event: KeyEvent(kind: KeyKind:DOWN)));
		Assert:isTrue(opts:handleKey(event: KeyEvent(kind: KeyKind:DOWN)));
		Assert:isTrue(opts:handleKey(event: KeyEvent(kind: KeyKind:DOWN)));
		Assert:isTrue(opts:handleKey(event: KeyEvent(kind: KeyKind:ENTER)));
		Assert:isFalse(opts:hasOpenOverlay());
		Assert:isTrue(opts:previewCard:style == CardStyle:METALLIC);

		ovm:selectAmountText(raw: '1250');
		ovm:selectRounds(next: 20);
		local TheoBuffer is buf: TheoBuffer(width: 80, height: 24);
		local TheoRenderer is ren: TheoRenderer();
		opts:layout(x: 0, y: 0, w: 80, h: 24);
		opts:paint(buf: buf, renderer: ren);

		# Save persists JSON, pops back, and updates HomeFrame card style
		ovm:save();
		Assert:areEqualInt(1, scr:stack:length());
		Assert:isTrue(home:heroCard:style == CardStyle:METALLIC);
		Assert:isTrue(storage:loadCardStyle() == CardStyle:METALLIC);
		Assert:areEqualInt(1250, storage:startingAmount);
		Assert:areEqualInt(20, storage:numRounds);

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

	Function is testRulesScreenLoadsJsonAndScrolls(){
		local HomeFrame is home: HomeFrame();
		local TheoScreen is scr: TheoScreen(root: home);
		local RulesViewModel is rvm: RulesViewModel(
			cardStyle: CardStyle:METALLIC,
			onDone: { scr:pop(); }
		);
		local RulesFrame is rules: RulesFrame(vm: rvm);
		scr:push(frame: rules);
		Assert:areEqualInt(2, scr:stack:length());

		local TheoBuffer is buf: TheoBuffer(width: 80, height: 20);
		local TheoRenderer is ren: TheoRenderer();
		rules:layout(x: 0, y: 0, w: 80, h: 20);
		rules:paint(buf: buf, renderer: ren);

		# Scrollbar sits flush against top (y=1) and right (x=78) inner border
		Assert:areEqualString('▐', buf:cellAt(x: 78, y: 1):ch);
		Assert:areEqualString('▐', buf:cellAt(x: 78, y: 15):ch);

		# Scroll down inside RulesFrame, then press 'd' (Done) to pop back
		Assert:isTrue(rules:handleKey(event: KeyEvent(kind: KeyKind:DOWN)));
		Assert:isTrue(rules:handleKey(event: KeyEvent(kind: KeyKind:CHAR, key: 'd')));
		Assert:areEqualInt(1, scr:stack:length());
	}

	Function is testGamePlayDealStandAndWinLoseOverlay(){
		local Hand is h: Hand();
		h:add(card: Card(rank: Rank:ACE, suit: Suit:SPADES));
		h:add(card: Card(rank: Rank:KING, suit: Suit:HEARTS));
		Assert:areEqualInt(21, h:score());
		Assert:isTrue(h:isBlackjack());
		h:add(card: Card(rank: Rank:FIVE, suit: Suit:CLUBS));
		Assert:areEqualInt(16, h:score());

		local HomeFrame is home: HomeFrame();
		local TheoScreen is scr: TheoScreen(root: home);
		local GameViewModel is gvm: GameViewModel(
			startingAmount: 500,
			maxRounds: 5,
			cardStyle: CardStyle:BLACK,
			onHome: { scr:pop(); }
		);
		local GameFrame is gf: GameFrame(vm: gvm);
		scr:push(frame: gf);
		local TheoBuffer is buf: TheoBuffer(width: 80, height: 24);
		local TheoRenderer is ren: TheoRenderer();
		gf:layout(x: 0, y: 0, w: 80, h: 24);
		gf:paint(buf: buf, renderer: ren);

		# Verify Dealer title on right edge (x=79) and Player title on left edge (x=0)
		local Boolean is foundDealerR: false;
		local Int is ry: 3;
		while({ ry < 11 }, {
			if({ buf:cellAt(x: 79, y: ry):ch == 'D' }, { foundDealerR: true; });
			ry: ry + 1;
		});
		Assert:isTrue(foundDealerR);

		local Boolean is foundPlayerL: false;
		ry: 11;
		while({ ry < 19 }, {
			if({ buf:cellAt(x: 0, y: ry):ch == 'P' }, { foundPlayerL: true; });
			ry: ry + 1;
		});
		Assert:isTrue(foundPlayerL);

		# Hover over -$10 button (at x=2..10, y=20..22) -> shows non-blocking tooltip above it
		Assert:isTrue(gf:handleMouse(event: MouseEvent(kind: MouseKind:MOVE, x: 4, y: 21)));
		Assert:isTrue(gf:hasOpenOverlay());
		Assert:isFalse(gf:hasBlockingOverlay());

		# Moving mouse away hides the tooltip
		Assert:isTrue(gf:handleMouse(event: MouseEvent(kind: MouseKind:MOVE, x: 0, y: 0)));
		Assert:isFalse(gf:hasOpenOverlay());

		# Hover again and click -$10 while tooltip is open (non-blocking)
		Assert:isTrue(gf:handleMouse(event: MouseEvent(kind: MouseKind:MOVE, x: 4, y: 21)));
		Assert:isTrue(gf:hasOpenOverlay());
		Assert:isTrue(gf:handleMouse(event: MouseEvent(kind: MouseKind:PRESS, button: 0, x: 4, y: 21)));

		# Bet +10 -> 20, Deal -> either PLAYER_TURN or immediate ROUND_OVER (Blackjack)
		gvm:adjustBet(delta: 10);
		Assert:areEqualInt(20, gvm:game:currentBet);
		gvm:deal();
		if({ gvm:game:phase == GamePhase:PLAYER_TURN }, {
			gvm:stand();
		});
		Assert:isTrue(gvm:game:phase == GamePhase:ROUND_OVER);
		Assert:isTrue(gf:hasOpenOverlay());

		gf:layout(x: 0, y: 0, w: 80, h: 24);
		gf:paint(buf: buf, renderer: ren);
	}
}
