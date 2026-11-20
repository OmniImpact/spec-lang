#! specunit: suite

Class of SpecUnitTest is TestTheoBuffer{
	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', as Assert()],
		['base', 'theo', TheoColor],
		['base', 'theo', TheoBuffer],
		['base', 'theo', TheoRenderer],
		['base', 'theo', KeyEvent],
		['base', 'theo', KeyReader]
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
}
