#! SpecUnit suite for the speclint utility: the first regression net
#! the lint rules have ever had. Drives the Linter directly — lex +
#! parse + lint, the exact path bin/speclint runs — over inline
#! fixtures, asserting each rule fires and that clean fixtures stay
#! clean. The indentation rules read raw text; the AST idioms (E10
#! loop construction, getString-default, random) need parseable Spec,
#! so those fixtures are full minimal classes. The single-quoted
#! fixture strings keep the tab/space bytes literal; the double-quoted
#! expected-message strings carry the escapes.

Class of SpecUnitTest is TestSpeclint{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['speclint', Linter],
		['speclint', LintIssue],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'ast', ProgramNode]
	];

	## Runs the full lint path over [src] as if it were a file.
	##
	## @param src: The fixture source.
	## @return: The issues the standards walk found.
	Function of Array of LintIssue is lintSource(String is src){
		local Lexer is lexer: Lexer:init(source: src);
		local Parser is parser: Parser:init(tokens: []);
		parser:setLexer(lexer: lexer);
		parser:setSourceFile(file: 'fixture.spec');
		local ProgramNode is program: parser:parseProgram();
		local Linter is linter: Linter:init();
		return linter:lint(source: src, program: program);
	}

	## Counts the issues of one severity.
	##
	## @param issues: The issues to filter.
	## @param wantWarnings: True counts warnings, false counts notices.
	## @return: The count of that severity.
	Function of Int is countKind(Array of LintIssue is issues, Boolean is wantWarnings){
		local Int is n: 0;
		issues:each(action: local Function(LintIssue is issue){
			if({ issue:isWarning == wantWarnings }, {
				n: n + 1;
			});
		});
		return n;
	}

	Function is testCleanFixtureStaysClean(){
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction is go(){\n\t\tlocal Int is x: 1;\n\t}\n}\n");
		Assert:areEqualInt(0, issues:length());
	}

	Function is testSpaceIndentationWarns(){
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction is go(){\n\t\t  local Int is x: 1;\n\t}\n}\n");
		Assert:areEqualInt(1, self:countKind(issues: issues, wantWarnings: true));
	}

	Function is testTrailingWhitespaceWarns(){
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction is go(){ \n\t}\n}\n");
		Assert:areEqualInt(1, self:countKind(issues: issues, wantWarnings: true));
		local LintIssue is first: issues:get(index: 0);
		Assert:areEqualString('Trailing whitespace detected.', first:message);
	}

	Function is testClosingBraceDepthWarns(){
		# The rule validates closing braces that start the LINE (masked
		# char 0 == '}'): a column-0 '}' while the nesting depth expects
		# one more tab is the misalignment shape it detects.
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction is go(){\n}\n}\n");
		Assert:areEqualInt(1, self:countKind(issues: issues, wantWarnings: true));
	}

	Function is testGetStringDefaultIsNotice(){
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction of String is pick(Map of String to String is m){\n\t\treturn m:getString(key: 'k', default: 'x');\n\t}\n}\n");
		Assert:areEqualInt(0, self:countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(1, self:countKind(issues: issues, wantWarnings: false));
	}

	Function is testRandomWithoutRangeIsNotice(){
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction of Float is roll(){\n\t\treturn m:random();\n\t}\n}\n");
		Assert:areEqualInt(0, self:countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(1, self:countKind(issues: issues, wantWarnings: false));
	}

	Function is testLoopConstructionWarns(){
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction is go(){\n\t\tLoops:repeat(count: 3, worker: {\n\t\t\tlocal Widget is w: Widget:init();\n\t\t});\n\t}\n}\n");
		Assert:areEqualInt(1, self:countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(0, self:countKind(issues: issues, wantWarnings: false));
	}
}
