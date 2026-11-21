#! SpecUnit suite for the speclint utility: regression net for
#! the modular lint rules, reflection discovery, and standards walk.

Class of SpecUnitTest is TestSpeclint{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['speclint', Linter],
		['speclint', LintIssue],
		['speclint', LintRule],
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
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction is go(){\n\t\tlocal Int is x: 1;\n\t}\n}\n");
		Assert:areEqualInt(0, issues:length());
	}

	Function is testSpaceIndentationWarns(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction is go(){\n\t\t  local Int is x: 1;\n\t}\n}\n");
		Assert:areEqualInt(1, :countKind(issues: issues, wantWarnings: true));
	}

	Function is testTrailingWhitespaceWarns(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction is go(){ \n\t}\n}\n");
		Assert:areEqualInt(1, :countKind(issues: issues, wantWarnings: true));
		local LintIssue is first: issues:get(index: 0);
		Assert:areEqualString('Trailing whitespace detected.', first:message);
	}

	Function is testClosingBraceDepthWarns(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction is go(){\n}\n}\n");
		Assert:areEqualInt(1, :countKind(issues: issues, wantWarnings: true));
	}

	Function is testTabIndentedCloserWarns(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction is go(){\n\t\t\t}\n}\n");
		Assert:areEqualInt(1, :countKind(issues: issues, wantWarnings: true));
	}

	Function is testElseContinuationIsAccepted(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction is go(){\n\t\titems:each(action: local Function(X is r){\n\t\t\tif(check: { r:p }, then: {\n\t\t\t\ta: a + 1;\n\t\t\t}, else: {\n\t\t\t\tb: b + 1;\n\t\t\t});\n\t\t});\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: issues, wantWarnings: true));
	}

	Function is testMultilineStringDataIsSkipped(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction of String is c(){\n\t\treturn '''select *\n    from t\n{\n}\n\t''';\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: issues, wantWarnings: true));
	}

	Function is testGetStringDefaultIsNotice(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction of String is pick(Map of String to String is m){\n\t\treturn m:getString(key: 'k', default: 'x');\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(1, :countKind(issues: issues, wantWarnings: false));
	}

	Function is testRandomWithoutRangeIsNotice(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction of Float is roll(){\n\t\treturn m:random();\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(1, :countKind(issues: issues, wantWarnings: false));
	}

	Function is testLoopConstructionWarns(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction is go(){\n\t\twhile(evaluate: { true }, iteration: {\n\t\t\tlocal Widget is w: Widget:init();\n\t\t});\n\t}\n}\n");
		Assert:areEqualInt(1, :countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(1, :countKind(issues: issues, wantWarnings: false));
	}

	Function is testEncourageAsConditionalNotice(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction is go(){\n\t\tConditional:if(check: { true }, then: {\n\t\t\tlocal Int is x: 1;\n\t\t});\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(1, :countKind(issues: issues, wantWarnings: false));
	}

	Function is testEncourageAsLoopsNotice(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction is go(){\n\t\tLoops:while(evaluate: { true }, iterate: {\n\t\t\tlocal Int is x: 1;\n\t\t});\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(1, :countKind(issues: issues, wantWarnings: false));
	}

	Function is testBareIfStaysClean(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction is go(){\n\t\tif(check: { true }, then: {\n\t\t\tlocal Int is x: 1;\n\t\t});\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(0, :countKind(issues: issues, wantWarnings: false));
	}

	Function is testModularRuleDiscovery(){
		local Linter is linter: Linter:init();
		Assert:isTrue(linter:rules:length() >= 8);
	}

	Function is testBracketIndentationWarns(){
		local Array of LintIssue is bad: :lintSource(src: "Class is F{\n\tArray of Int is xs: [\n\t1,\n\t2\n\t\t];\n}\n");
		Assert:isTrue(:countKind(issues: bad, wantWarnings: true) >= 2);
		local Array of LintIssue is good: :lintSource(src: "Class is F{\n\tArray of Int is xs: [\n\t\t1,\n\t\t2\n\t];\n}\n");
		Assert:areEqualInt(0, :countKind(issues: good, wantWarnings: true));
	}

	Function is testUnnecessarySelfColonNotice(){
		local Array of LintIssue is unshadowed: :lintSource(src: "Class is F{\n\tInt is x: 0;\n\tFunction of Int is get(){\n\t\treturn :x;\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: unshadowed, wantWarnings: true));
		Assert:areEqualInt(1, :countKind(issues: unshadowed, wantWarnings: false));
		local Array of LintIssue is shadowed: :lintSource(src: "Class is F{\n\tInt is x: 0;\n\tFunction of Int is get(Int is x){\n\t\treturn :x;\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: shadowed, wantWarnings: false));
	}

	Function is testInitShorthandNotice(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction is go(){\n\t\tlocal Widget is w: Widget:init();\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(1, :countKind(issues: issues, wantWarnings: false));
	}

	## Held-error-state fields (the removed Json side channel's shape) are
	## flagged wherever they reappear.
	Function is testHeldErrorStateNotice(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tBoolean is parseFailed: false;\n\tString is parseError: '';\n\tInt is errorCount: 0;\n}\n");
		local Int is n: 0;
		issues:each(action: local Function(LintIssue is issue){
			if({ issue:message:contains(needle: 'facility-held error state') }, {
				n: n + 1;
			});
		});
		Assert:areEqualInt(2, n);
	}

	Function is testUnusedUsingWarns(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\treplace Array of Array of String is using: [\n\t\t['base', 'struct', Map]\n\t];\n\tFunction is go(){\n\t\tlocal Int is x: 1;\n\t}\n}\n");
		Assert:areEqualInt(1, :countKind(issues: issues, wantWarnings: true));
	}

	Function is testBlankLinesNotice(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\n\n\n\tFunction is go(){\n\t\tlocal Int is x: 1;\n\t}\n}");
		Assert:areEqualInt(0, :countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(2, :countKind(issues: issues, wantWarnings: false));
	}

	Function is testTemplateStringNotice(){
		local Array of LintIssue is issues: :lintSource(src: "Class is F{\n\tFunction of String is greet(String is name){\n\t\treturn 'hi ' . name;\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(1, :countKind(issues: issues, wantWarnings: false));
	}

	Function is testMergeUsingNotice(){
		local Array of LintIssue is bad: :lintSource(src: "Class is F{\n\treplace Array of Array of String is using: [\n\t\t['base', 'sys', as Conditional()],\n\t\t['base', 'sys', as Loops()]\n\t];\n\tFunction is go(){\n\t\tlocal Int is x: 1;\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: bad, wantWarnings: true));
		Assert:areEqualInt(1, :countKind(issues: bad, wantWarnings: false));
		local Array of LintIssue is good: :lintSource(src: "Class is F{\n\tmerge Array of Array of String is using: [\n\t\t['base', 'struct', Map]\n\t];\n\tFunction is go(Map of String to Int is m){\n\t\tlocal Int is x: 1;\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: good, wantWarnings: false));
	}

	Function is testCompactUsingNotice(){
		local Array of LintIssue is bad: :lintSource(src: "Class is F{\n\tmerge Array of Array of String is using: [\n\t\t['base', 'theo', Panel],\n\t\t['base', 'theo', Row],\n\t\t['base', 'theo', Button]\n\t];\n\tFunction is go(Panel is p, Row is r, Button is b){\n\t\tlocal Int is x: 1;\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: bad, wantWarnings: true));
		Assert:areEqualInt(1, :countKind(issues: bad, wantWarnings: false));
		local Array of LintIssue is good: :lintSource(src: "Class is F{\n\tmerge Array of Array of String is using: [\n\t\t['base', 'theo', [Panel, Row, Button]]\n\t];\n\tFunction is go(Panel is p, Row is r, Button is b){\n\t\tlocal Int is x: 1;\n\t}\n}\n");
		Assert:areEqualInt(0, :countKind(issues: good, wantWarnings: false));
	}
}
