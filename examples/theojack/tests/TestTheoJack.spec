#! specunit: suite

Class of SpecUnitTest is TestTheoJack{
	replace [String] is namespace: ['theojack', 'tests'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'theo', [TheoBuffer, TheoRenderer, TheoScreen, KeyEvent, TextGraphic, FocusTarget]],
		['base', 'sys', as Loops()],
		['theojack', 'util', HomeStrings],
		['theojack', 'view', HomeFrame]
	];

	Function is testHomeScreenCenteredAndEqualWidth(){
		local Boolean is quitCalled: false;
		local HomeFrame is home: HomeFrame(onQuit: { quitCalled: true; });
		local [FocusTarget] is fts: [home:playFocus, home:rulesFocus, home:aboutFocus, home:quitFocus];
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

		local TextGraphic is card: TextGraphic(graphic: HomeStrings:HERO_CARD);
		Assert:areEqualInt(HomeStrings:CARD_WIDTH, card:measureWidth(maxW: 80));
		Assert:areEqualInt(HomeStrings:CARD_WIDTH, home:measureWidth(maxW: 80) - HomeStrings:CARD_WIDTH - 3);
		Assert:areEqualInt(7, home:measureHeight(maxW: 80, maxH: 24));

		# Pressing Down 3 times focuses Quit, Enter activates Quit
		Assert:isTrue(home:playFocus:focused);
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: 'down')));
		Assert:isTrue(home:rulesFocus:focused);
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: 'down')));
		Assert:isTrue(home:aboutFocus:focused);
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: 'down')));
		Assert:isTrue(home:quitFocus:focused);
		Assert:isTrue(home:handleKey(event: KeyEvent(kind: 'enter')));
		Assert:isTrue(quitCalled);
	}
}
