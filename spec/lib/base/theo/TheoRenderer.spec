#! Package base:theo
#! Full-screen synchronized ANSI renderer for [TheoBuffer].

Class is TheoRenderer{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', TheoBuffer],
		['base', 'theo', TheoCell],
		['base', 'theo', TheoColor],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Boolean is cursorVisible: false;
	Int is cursorX: 0;
	Int is cursorY: 0;

	replace Function is init(){
	}

	Function is enterAltScreenMode(){
		Output:consOut(text: enterAltScreen() . clearScreen() . hideCursor() . esc() . '[>1u');
	}

	Function is exitAltScreenMode(){
		Output:consOut(text: esc() . '[<u' . showCursor() . exitAltScreen());
	}

	Function is setCursor(Boolean is visible, Int is x: 0, Int is y: 0){
		:cursorVisible: visible;
		:cursorX: x;
		:cursorY: y;
	}

	## Renders the full [buffer] inside a synchronized update frame.
	Function is render(TheoBuffer is buffer){
		local String is frame: beginSyncUpdate() . hideCursor();
		local Int is y: 0;
		while({ y < buffer:height }, {
			frame: frame . moveTo(row: y + 1, col: 1);
			local TheoColor is curFg: TheoColor:none();
			local TheoColor is curBg: TheoColor:none();
			local Boolean is curBold: false;
			local Boolean is curUnder: false;
			local Boolean is curRev: false;
			local Int is x: 0;
			while({ x < buffer:width }, {
				local TheoCell is c: buffer:cellAt(x: x, y: y);
				if({ !c:fg:equals(other: curFg) || !c:bg:equals(other: curBg) || c:bold != curBold || c:underline != curUnder || c:reverse != curRev }, {
					frame: frame . reset();
					if({ c:bold }, { frame: frame . bold(); });
					if({ c:underline }, { frame: frame . esc() . '[4m'; });
					if({ c:reverse }, { frame: frame . esc() . '[7m'; });
					if({ c:fg:isSet() }, { frame: frame . c:fg:fgSeq(); });
					if({ c:bg:isSet() }, { frame: frame . c:bg:bgSeq(); });
					curFg: c:fg;
					curBg: c:bg;
					curBold: c:bold;
					curUnder: c:underline;
					curRev: c:reverse;
				});
				frame: frame . c:ch;
				x: x + 1;
			});
			frame: frame . reset();
			y: y + 1;
		});
		if({ cursorVisible }, {
			frame: frame . moveTo(row: cursorY + 1, col: cursorX + 1) . showCursor();
		});
		frame: frame . endSyncUpdate();
		Output:consOut(text: frame);
	}
}
