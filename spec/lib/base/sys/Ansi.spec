#! Package base:sys
#! The terminal presentation wrapper: the escape builders are plain
#! Spec; the size queries delegate to the terminal-metric floor.

## ANSI escape sequences for 16-color, 256-color, and 24-bit TrueColor
## output, plus terminal cursor control.

Class is Ansi{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
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

	## Returns `true` when stdout is an interactive terminal (TTY).
	##
	## @return: `true` if stdout is a terminal, `false` when piped/redirected.
	Function of Boolean is isTty(){
		return base:sysinternal:Terminal:term_is_tty() != 0;
	}

	## Enables virtual terminal escape processing and UTF-8 output (Windows)
	## or checks TTY status (POSIX). Returns `true` if VT output is ready.
	Function of Boolean is enableVirtualTerminal(){
		return base:sysinternal:Terminal:term_enable_vt() != 0;
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
	Function of String is bgRgb(Int is r, Int is g, Int is b){
		return "\e[48;2;" . r . ';' . g . ';' . b . 'm';
	}

	## Returns the sequence moving the cursor up [n] lines.
	Function of String is cursorUp(Int is n){
		return "\e[" . n . 'A';
	}

	## Returns the sequence moving the cursor down [n] lines.
	Function of String is cursorDown(Int is n){
		return "\e[" . n . 'B';
	}

	## Returns a carriage return (`\r`) moving to column 1 of the current line.
	Function of String is carriageReturn(){
		return "\r";
	}

	## Returns the sequence erasing the entire current line.
	Function of String is eraseLine(){
		return "\e[2K";
	}

	## Returns the sequence erasing from the cursor to the end of the screen.
	Function of String is eraseToEnd(){
		return "\e[0J";
	}

	## Begins a DEC Synchronized Output update (`\e[?2026h`).
	Function of String is beginSyncUpdate(){
		return "\e[?2026h";
	}

	## Ends a DEC Synchronized Output update (`\e[?2026l`).
	Function of String is endSyncUpdate(){
		return "\e[?2026l";
	}

	## Enters the alternate screen buffer (`\e[?1049h`).
	Function of String is enterAltScreen(){
		return "\e[?1049h";
	}

	## Exits the alternate screen buffer (`\e[?1049l`).
	Function of String is exitAltScreen(){
		return "\e[?1049l";
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

	## Returns the DECSCUSR sequence setting the terminal cursor shape.
	## (0 = default, 1 = blinking block, 2 = steady block, 3 = blinking underline,
	## 4 = steady underline, 5 = blinking bar, 6 = steady bar).
	##
	## @param style: DECSCUSR cursor style code (0..6).
	## @return: ANSI DECSCUSR sequence.
	Function of String is cursorStyle(Int is style){
		return "\e[" . style . ' q';
	}

	## Returns the OSC 12 sequence setting the terminal cursor color.
	##
	## @param color: Color specification (e.g. `#ffffff` or `white`).
	## @return: OSC 12 cursor-color sequence.
	Function of String is cursorColor(String is color){
		return "\e]12;" . color . "\e\\";
	}

	## Returns the OSC 112 sequence resetting the terminal cursor color to default.
	##
	## @return: OSC 112 reset-cursor-color sequence.
	Function of String is resetCursorColor(){
		return "\e]112\e\\";
	}
}
