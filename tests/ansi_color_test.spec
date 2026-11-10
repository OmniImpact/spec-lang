#! Package examples
#! Demonstrates ANSI 256-color helpers, TrueColor gradients, inline Output:print, and UTF-8 block characters.

## Verification suite for ANSI 256-color and special character console output.
Class is AnsiColorTest{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator'],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Output()],
		['base', 'sys', as Loops()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Spec ANSI 256-Color & Special Character Test ===');

		# 1. Basic 16-color + 256-color blocks using Output:print
		Output:consOut(text: 'Standard 16 palette: ');
		local Int is c: 0;
		while(
			evaluate: local Function of Boolean(){ return c < 16; },
			iteration: local Function(){
				Output:consOut(text: Ansi:fg256(code: c) . '█' . Ansi:reset());
				c: c + 1;
			}
		);
		Output:line('');

		# 2. 6x6x6 Color Cube (indices 16..231) using special shade blocks
		Output:consOut(text: '256-Color Cube slice: ');
		local Int is g: 0;
		while(
			evaluate: local Function of Boolean(){ return g < 6; },
			iteration: local Function(){
				local Int is b: 0;
				while(
					evaluate: local Function of Boolean(){ return b < 6; },
					iteration: local Function(){
						local Int is idx: Ansi:cubeIndex(r: 5, g: g, b: b);
						Output:consOut(text: Ansi:color256(code: idx, text: '▓'));
						b: b + 1;
					}
				);
				g: g + 1;
			}
		);
		Output:line('');

		# 3. 24-Step Grayscale Ramp (indices 232..255)
		Output:consOut(text: 'Grayscale ramp:      ');
		local Int is lvl: 0;
		while(
			evaluate: local Function of Boolean(){ return lvl < 24; },
			iteration: local Function(){
				local Int is gIdx: Ansi:grayIndex(level: lvl);
				Output:consOut(text: Ansi:paint256(fg: gIdx, bg: 16, text: '▒'));
				lvl: lvl + 1;
			}
		);
		Output:line('');

		# 4. Direct \e escape and String:fromCharCode(code: 27) equivalence
		local Boolean is escMatch: ("\e" == String:fromCharCode(code: 27)) && (Ansi:esc() == "\e");
		Output:line("Escape '\\e' == String:fromCharCode(27): " . escMatch);
		Output:line(Ansi:bold() . Ansi:fgRgb(r: 80, g: 220, b: 100) . '★ TrueColor & UTF-8 Symbols: █ ▓ ▒ ░ ▀ ▄ ● ◆ ★' . Ansi:reset());
	}

}
