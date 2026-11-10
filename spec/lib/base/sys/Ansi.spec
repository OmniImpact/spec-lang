#! Package base:sys
#! The terminal presentation wrapper: the escape builders are plain
#! Spec; the size queries delegate to the terminal-metric floor.

## ANSI escape sequences for 16-color, 256-color, and 24-bit TrueColor
## output, plus terminal cursor control.

Class is Ansi{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Terminal]
	];

	## Returns the raw ASCII ESC character.
	##
	## @return: Single-character ESC string.
	Function of String is esc(){
		return "\e";
	}

	## Returns the console width in columns, or 0 when stdout is not a terminal.
	##
	## @return: Width in columns.
	Function of Int is terminalWidth(){
		return base:sysinternal:Terminal:term_width();
	}

	## Returns the console height in rows, or 0 when stdout is not a terminal.
	##
	## @return: Height in rows.
	Function of Int is terminalHeight(){
		return base:sysinternal:Terminal:term_height();
	}

	## Returns the ANSI sequence to reset all terminal colors and attributes.
	##
	## @return: ANSI reset sequence.
	Function of String is reset(){
		return "\e[0m";
	}

	## Returns the ANSI sequence for bold text.
	##
	## @return: ANSI bold sequence.
	Function of String is bold(){
		return "\e[1m";
	}

	## Returns the ANSI sequence for dim text.
	##
	## @return: ANSI dim sequence.
	local Function of String is dim(){
		return "\e[2m";
	}

	## Returns the ANSI 256-color foreground sequence for palette index [code] (0..255).
	##
	## @param code: 256-color palette index (0..255).
	## @return: ANSI foreground sequence.
	Function of String is fg256(Int is code){
		return "\e[38;5;" . code . 'm';
	}

	## Returns the ANSI 256-color background sequence for palette index [code] (0..255).
	##
	## @param code: 256-color palette index (0..255).
	## @return: ANSI background sequence.
	Function of String is bg256(Int is code){
		return "\e[48;5;" . code . 'm';
	}

	## Wraps [text] in a 256-color foreground sequence followed by a reset code.
	##
	## @param code: 256-color palette index (0..255).
	## @param text: String content to colorize.
	## @return: Colorized string with trailing reset.
	Function of String is color256(Int is code, String is text){
		return "\e[38;5;" . code . 'm' . text . "\e[0m";
	}

	## Wraps [text] in 256-color foreground and background sequences plus a reset.
	##
	## @param fg: Foreground 256-color palette index (0..255).
	## @param bg: Background 256-color palette index (0..255).
	## @param text: String content to colorize.
	## @return: Colorized string with trailing reset.
	Function of String is paint256(Int is fg, Int is bg, String is text){
		return "\e[38;5;" . fg . ';48;5;' . bg . 'm' . text . "\e[0m";
	}

	## Computes a 256-color 6x6x6 RGB cube index (16..231) from coordinates in 0..5.
	##
	## @param r: Red cube level (0..5).
	## @param g: Green cube level (0..5).
	## @param b: Blue cube level (0..5).
	## @return: Palette index in range 16..231.
	Function of Int is cubeIndex(Int is r, Int is g, Int is b){
		return 16 + (36 * r) + (6 * g) + b;
	}

	## Computes a 256-color grayscale ramp index (232..255) from a level in 0..23.
	##
	## @param level: Grayscale level (0..23).
	## @return: Palette index in range 232..255.
	Function of Int is grayIndex(Int is level){
		return 232 + level;
	}

	## Returns the 24-bit TrueColor foreground sequence for [r], [g], [b] (0..255).
	##
	## @param r: Red channel (0..255).
	## @param g: Green channel (0..255).
	## @param b: Blue channel (0..255).
	## @return: ANSI TrueColor foreground sequence.
	Function of String is fgRgb(Int is r, Int is g, Int is b){
		return "\e[38;2;" . r . ';' . g . ';' . b . 'm';
	}

	## Returns the 24-bit TrueColor background sequence for [r], [g], [b] (0..255).
	##
	## @param r: Red channel (0..255).
	## @param g: Green channel (0..255).
	## @param b: Blue channel (0..255).
	## @return: ANSI TrueColor background sequence.
	local Function of String is bgRgb(Int is r, Int is g, Int is b){
		return "\e[48;2;" . r . ';' . g . ';' . b . 'm';
	}

	## Returns the sequence clearing the screen and homing the cursor.
	##
	## @return: ANSI clear-screen sequence.
	Function of String is clearScreen(){
		return "\e[2J\e[H";
	}

	## Returns the sequence moving the cursor to 1-based ([row], [col]).
	##
	## @param row: 1-based terminal row.
	## @param col: 1-based terminal column.
	## @return: ANSI cursor position sequence.
	Function of String is moveTo(Int is row, Int is col){
		return "\e[" . row . ';' . col . 'H';
	}

	## Returns the sequence hiding the terminal cursor.
	##
	## @return: ANSI hide-cursor sequence.
	Function of String is hideCursor(){
		return "\e[?25l";
	}

	## Returns the sequence showing the terminal cursor.
	##
	## @return: ANSI show-cursor sequence.
	Function of String is showCursor(){
		return "\e[?25h";
	}
}
