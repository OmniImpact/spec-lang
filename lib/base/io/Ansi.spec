#! Package base:io
#! Provides ANSI terminal escape sequences, 16/256/TrueColor helpers, and cursor controls.

## Provides ANSI escape sequences for 16-color, 256-color, 24-bit TrueColor, and terminal cursor control.
Class is Ansi{

	## Returns the raw ASCII ESC character (`0x1B` / `\e`).
	##
	## @return: Single-character ESC string.
	replace local Function of String is esc(){
		return "\e";
	}

	## Returns the ANSI sequence to reset all terminal colors and attributes (`\e[0m`).
	##
	## @return: ANSI reset sequence string.
	replace local Function of String is reset(){
		return "\e[0m";
	}

	## Returns the ANSI sequence for bold text (`\e[1m`).
	##
	## @return: ANSI bold sequence string.
	replace local Function of String is bold(){
		return "\e[1m";
	}

	## Returns the ANSI sequence for dim text (`\e[2m`).
	##
	## @return: ANSI dim sequence string.
	replace local Function of String is dim(){
		return "\e[2m";
	}

	## Returns the ANSI 256-color foreground sequence for color index `code` (0..255).
	##
	## @param code: 256-color palette index (0..255).
	## @return: ANSI foreground sequence (`\e[38;5;<code>m`).
	replace local Function of String is fg256(Int is code){
		return "\e[38;5;" . code . "m";
	}

	## Returns the ANSI 256-color background sequence for color index `code` (0..255).
	##
	## @param code: 256-color palette index (0..255).
	## @return: ANSI background sequence (`\e[48;5;<code>m`).
	replace local Function of String is bg256(Int is code){
		return "\e[48;5;" . code . "m";
	}

	## Wraps `text` in a 256-color foreground sequence followed by a reset code.
	##
	## @param code: 256-color palette index (0..255).
	## @param text: String content to colorize.
	## @return: Colorized string with trailing reset.
	replace local Function of String is color256(Int is code, String is text){
		return "\e[38;5;" . code . "m" . text . "\e[0m";
	}

	## Wraps `text` in both 256-color foreground and background sequences followed by a reset code.
	##
	## @param fg: Foreground 256-color palette index (0..255).
	## @param bg: Background 256-color palette index (0..255).
	## @param text: String content to colorize.
	## @return: Colorized string with trailing reset.
	replace local Function of String is paint256(Int is fg, Int is bg, String is text){
		return "\e[38;5;" . fg . ";48;5;" . bg . "m" . text . "\e[0m";
	}

	## Computes a 256-color 6x6x6 RGB cube index (16..231) from cube coordinates `r`, `g`, `b` in `0..5`.
	##
	## @param r: Red cube level (0..5).
	## @param g: Green cube level (0..5).
	## @param b: Blue cube level (0..5).
	## @return: Palette index in range 16..231.
	replace local Function of Int is cubeIndex(Int is r, Int is g, Int is b){
		return 16 + (36 * r) + (6 * g) + b;
	}

	## Computes a 256-color grayscale ramp index (232..255) from a level in `0..23`.
	##
	## @param level: Grayscale level (0..23).
	## @return: Palette index in range 232..255.
	replace local Function of Int is grayIndex(Int is level){
		return 232 + level;
	}

	## Returns the 24-bit TrueColor foreground sequence for `r`, `g`, `b` (0..255).
	##
	## @param r: Red channel (0..255).
	## @param g: Green channel (0..255).
	## @param b: Blue channel (0..255).
	## @return: ANSI TrueColor foreground sequence (`\e[38;2;<r>;<g>;<b>m`).
	replace local Function of String is fgRgb(Int is r, Int is g, Int is b){
		return "\e[38;2;" . r . ";" . g . ";" . b . "m";
	}

	## Returns the 24-bit TrueColor background sequence for `r`, `g`, `b` (0..255).
	##
	## @param r: Red channel (0..255).
	## @param g: Green channel (0..255).
	## @param b: Blue channel (0..255).
	## @return: ANSI TrueColor background sequence (`\e[48;2;<r>;<g>;<b>m`).
	replace local Function of String is bgRgb(Int is r, Int is g, Int is b){
		return "\e[48;2;" . r . ";" . g . ";" . b . "m";
	}

	## Returns the ANSI sequence to clear the entire screen and move cursor to home (`1,1`).
	##
	## @return: ANSI clear screen sequence.
	replace local Function of String is clearScreen(){
		return "\e[2J\e[H";
	}

	## Returns the ANSI sequence to move the cursor to 1-based (`row`, `col`).
	##
	## @param row: 1-based terminal row.
	## @param col: 1-based terminal column.
	## @return: ANSI cursor position sequence.
	replace local Function of String is moveTo(Int is row, Int is col){
		return "\e[" . row . ";" . col . "H";
	}

	## Returns the ANSI sequence to hide the terminal cursor.
	##
	## @return: ANSI hide cursor sequence.
	replace local Function of String is hideCursor(){
		return "\e[?25l";
	}

	## Returns the ANSI sequence to show the terminal cursor.
	##
	## @return: ANSI show cursor sequence.
	replace local Function of String is showCursor(){
		return "\e[?25h";
	}

}
