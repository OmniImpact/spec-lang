#! Package base:theo
#! Decodes raw terminal stdin bytes and VT/ANSI escape sequences into [KeyEvent]s.

Class is KeyReader{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [KeyEvent, KeyKind, KeyAction, MouseEvent, MouseKind]],
		['base', 'sys', as Input()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	MouseEvent is lastMouse: MouseEvent();

	replace Function is init(){
		:lastMouse: MouseEvent();
	}

	local Function of String is byteToStr(Int is b){
		local Int is buf: Mem:alloc(bytes: 2);
		Mem:storeByte(ptr: buf, byteOffset: 0, val: b);
		Mem:storeByte(ptr: buf, byteOffset: 1, val: 0);
		local String is s: Mem:strFromBytes(srcAddr: buf, len: 1);
		Mem:free(ptr: buf);
		return s;
	}

	## Polls stdin up to [timeoutMs] ms and decodes the next [KeyEvent] (or `kind == KeyKind:NONE`).
	Function of KeyEvent is pollKey(Int is timeoutMs: 16){
		local Int is b: pollByte(timeoutMs: timeoutMs);
		if({ b < 0 }, {
			return KeyEvent(kind: KeyKind:NONE);
		});
		if({ b == 13 }, {
			return KeyEvent(kind: KeyKind:ENTER);
		});
		if({ b == 9 }, {
			return KeyEvent(kind: KeyKind:TAB);
		});
		if({ b == 127 || b == 8 }, {
			return KeyEvent(kind: KeyKind:BACKSPACE);
		});
		if({ b == 27 }, {
			local Int is b1: pollByte(timeoutMs: 15);
			if({ b1 < 0 }, {
				return KeyEvent(kind: KeyKind:ESC);
			});
			if({ b1 == 91 }, {
				local Int is b2: pollByte(timeoutMs: 15);
				if({ b2 == 65 }, { return KeyEvent(kind: KeyKind:UP); });
				if({ b2 == 66 }, { return KeyEvent(kind: KeyKind:DOWN); });
				if({ b2 == 67 }, { return KeyEvent(kind: KeyKind:RIGHT); });
				if({ b2 == 68 }, { return KeyEvent(kind: KeyKind:LEFT); });
				if({ b2 == 72 }, { return KeyEvent(kind: KeyKind:HOME); });
				if({ b2 == 70 }, { return KeyEvent(kind: KeyKind:END); });
				if({ b2 == 90 }, { return KeyEvent(kind: KeyKind:BACKTAB); });
				if({ b2 == 60 }, {
					# SGR mouse event: ESC [ < btn ; col ; row M/m
					local Int is btn: 0;
					local Int is col: 0;
					local Int is row: 0;
					local Int is field: 0;
					local Int is cur: pollByte(timeoutMs: 15);
					while({ cur >= 0 && ((cur >= 48 && cur <= 57) || cur == 59) }, {
						if({ cur == 59 }, {
							field: field + 1;
						}, {
							local Int is d: cur - 48;
							if({ field == 0 }, { btn: (btn * 10) + d; });
							if({ field == 1 }, { col: (col * 10) + d; });
							if({ field == 2 }, { row: (row * 10) + d; });
						});
						cur: pollByte(timeoutMs: 15);
					});
					if({ cur == 77 || cur == 109 }, {
						local Boolean is isShift: ((btn / 4) % 2) == 1;
						local Boolean is isAlt: ((btn / 8) % 2) == 1;
						local Boolean is isCtrl: ((btn / 16) % 2) == 1;
						local Boolean is isMotion: ((btn / 32) % 2) == 1;
						local Boolean is isWheel: ((btn / 64) % 2) == 1;
						local Int is lowBtn: btn % 4;
						local MouseKind is mKind: MouseKind:PRESS;
						if({ isWheel }, {
							mKind: if({ lowBtn == 0 }, { MouseKind:WHEEL_UP }, { MouseKind:WHEEL_DOWN });
						}, {
							if({ isMotion }, {
								mKind: MouseKind:MOVE;
							}, {
								if({ cur == 109 }, { mKind: MouseKind:RELEASE; });
							});
						});
						local Int is mx: col - 1;
						if({ mx < 0 }, { mx: 0; });
						local Int is my: row - 1;
						if({ my < 0 }, { my: 0; });
						:lastMouse: MouseEvent(
							kind: mKind,
							x: mx,
							y: my,
							button: lowBtn,
							ctrl: isCtrl,
							alt: isAlt,
							shift: isShift
						);
						return KeyEvent(kind: KeyKind:MOUSE);
					});
				});
				if({ b2 >= 48 && b2 <= 57 }, {
					# Parse CSI numeric params: `<code>~` or `<code>;<mod>[:<event>]u` (Kitty keyboard protocol)
					local Int is p1: b2 - 48;
					local Int is p2: 0;
					local Int is p3: 1;
					local Boolean is hasSemi: false;
					local Boolean is inEventSub: false;
					local Boolean is skipSub: false;
					local Int is term: 0;
					local Int is cur: pollByte(timeoutMs: 15);
					while({ cur >= 0 && ((cur >= 48 && cur <= 57) || cur == 59 || cur == 58) }, {
						if({ cur == 59 }, {
							hasSemi: true;
							inEventSub: false;
							skipSub: false;
						}, {
							if({ cur == 58 }, {
								if({ hasSemi }, {
									inEventSub: true;
									p3: 0;
								}, {
									skipSub: true;
								});
							}, {
								local Int is dig: cur - 48;
								if({ inEventSub }, {
									p3: (p3 * 10) + dig;
								}, {
									if({ hasSemi }, {
										p2: (p2 * 10) + dig;
									}, {
										if({ !skipSub }, { p1: (p1 * 10) + dig; });
									});
								});
							});
						});
						cur: pollByte(timeoutMs: 15);
					});
					term: cur;
					if({ term == 126 }, {
						if({ p1 == 3 }, { return KeyEvent(kind: KeyKind:DELETE); });
						if({ p1 == 5 }, { return KeyEvent(kind: KeyKind:PAGE_UP); });
						if({ p1 == 6 }, { return KeyEvent(kind: KeyKind:PAGE_DOWN); });
						if({ p1 == 1 || p1 == 7 }, { return KeyEvent(kind: KeyKind:HOME); });
						if({ p1 == 4 || p1 == 8 }, { return KeyEvent(kind: KeyKind:END); });
					});
					if({ term == 117 }, {
						local Int is modBits: if({ hasSemi && p2 > 0 }, { p2 - 1 }, { 0 });
						local Boolean is isCtrl: (modBits % 8) >= 4;
						local Boolean is isAlt: (modBits % 4) >= 2;
						local KeyAction is act: KeyAction:PRESS;
						if({ p3 == 2 }, { act: KeyAction:REPEAT; });
						if({ p3 == 3 }, { act: KeyAction:RELEASE; });
						if({ p1 == 13 && !isCtrl && !isAlt }, { return KeyEvent(kind: KeyKind:ENTER, action: act); });
						if({ p1 == 9 && !isCtrl && !isAlt }, { return KeyEvent(kind: KeyKind:TAB, action: act); });
						if({ p1 == 27 && !isCtrl && !isAlt }, { return KeyEvent(kind: KeyKind:ESC, action: act); });
						if({ p1 == 127 || p1 == 8 }, { return KeyEvent(kind: KeyKind:BACKSPACE, ctrl: isCtrl, alt: isAlt, action: act); });
						if({ p1 >= 32 && p1 < 127 }, {
							return KeyEvent(kind: KeyKind:CHAR, key: byteToStr(b: p1), ctrl: isCtrl, alt: isAlt, action: act);
						});
					});
				});
				return KeyEvent(kind: KeyKind:ESC);
			});
			if({ b1 >= 32 && b1 < 127 }, {
				return KeyEvent(kind: KeyKind:CHAR, key: byteToStr(b: b1), alt: true);
			});
			return KeyEvent(kind: KeyKind:ESC);
		});
		if({ b >= 1 && b <= 26 }, {
			return KeyEvent(kind: KeyKind:CHAR, key: byteToStr(b: 96 + b), ctrl: true);
		});
		if({ b >= 32 && b < 127 }, {
			return KeyEvent(kind: KeyKind:CHAR, key: byteToStr(b: b));
		});
		# UTF-8 multi-byte sequence
		if({ b >= 192 }, {
			local Int is need: 2;
			if({ b >= 224 }, { need: 3; });
			if({ b >= 240 }, { need: 4; });
			local Int is buf: Mem:alloc(bytes: 5);
			Mem:storeByte(ptr: buf, byteOffset: 0, val: b);
			local Int is got: 1;
			if({ need >= 2 }, {
				local Int is u1: pollByte(timeoutMs: 10);
				if({ u1 >= 0 }, { Mem:storeByte(ptr: buf, byteOffset: 1, val: u1); got: 2; });
			});
			if({ need >= 3 && got == 2 }, {
				local Int is u2: pollByte(timeoutMs: 10);
				if({ u2 >= 0 }, { Mem:storeByte(ptr: buf, byteOffset: 2, val: u2); got: 3; });
			});
			if({ need >= 4 && got == 3 }, {
				local Int is u3: pollByte(timeoutMs: 10);
				if({ u3 >= 0 }, { Mem:storeByte(ptr: buf, byteOffset: 3, val: u3); got: 4; });
			});
			local String is ch: Mem:strFromBytes(srcAddr: buf, len: got);
			Mem:free(ptr: buf);
			return KeyEvent(kind: KeyKind:CHAR, key: ch);
		});
		return KeyEvent(kind: KeyKind:NONE);
	}
}
