#! Package speclint
#! Stateful source masking for indentation, brace, and whitespace lint rules.

Class is SourceMasker{
	namespace: ['speclint'];

	replace Array of Array of String is using: [
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	## Quote state carried across lines: '' outside any string, or the
	## active quote — `'` a raw string, `"` an escaped string, `'''` a raw
	## multi-line string.
	String is quote: '';

	replace Function is init(){
		:quote: '';
	}

	## Resets state before masking a new source file.
	Function is reset(){
		:quote: '';
	}

	## Returns whether the current position is inside a multi-line string.
	Function of Boolean is isInsideString(){
		return :quote != '';
	}

	## Masks strings and comments in a single line with spaces, preserving length.
	##
	## @param line: Raw source line.
	## @return: Masked line with identical length.
	Function of String is maskLine(String is line){
		local String is out: '';
		local Int is i: 0;
		while({ i < line:length() }, {
			local String is ch: line:charAt(index: i, default: '');
			if({ :quote != '' }, {
				if({ :quote == "'''" && :matchTriple(line: line, index: i) }, {
					:quote: '';
					out: out . '   ';
					i: i + 2;
				}, {
					if({ :quote != "'''" && ch == "\\" }, {
						out: out . '  ';
						i: i + 1;
					}, {
						if({ ch == :quote }, {
							:quote: '';
							out: out . ' ';
						}, {
							out: out . ' ';
						});
					});
				});
			}, {
				match(on: ch, when: [
					['"', '\'']: {
						if({ :matchTriple(line: line, index: i) }, {
							:quote: "'''";
							out: out . '   ';
							i: i + 2;
						}, {
							:quote: ch;
							out: out . ' ';
						});
					},
					'#': {
						i: line:length();
					},
					else: {
						out: out . ch;
					}
				]);
			});
			i: i + 1;
		});
		return out;
	}

	## True when [index] starts a `'''` sequence in [line].
	Function of Boolean is matchTriple(String is line, Int is index){
		return index + 2 < line:length()
			&& line:charAt(index: index, default: '') == '\''
			&& line:charAt(index: index + 1, default: '') == '\''
			&& line:charAt(index: index + 2, default: '') == '\'';
	}
}
