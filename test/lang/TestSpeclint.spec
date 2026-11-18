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
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction is go(){\n}\n}\n");
		Assert:areEqualInt(1, self:countKind(issues: issues, wantWarnings: true));
	}

	Function is testTabIndentedCloserWarns(){
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction is go(){\n\t\t\t}\n}\n");
		Assert:areEqualInt(1, self:countKind(issues: issues, wantWarnings: true));
	}

	Function is testElseContinuationIsAccepted(){
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction is go(){\n\t\titems:each(action: local Function(X is r){\n\t\t\tif(check: { r:p }, then: {\n\t\t\t\ta: a + 1;\n\t\t\t}, else: {\n\t\t\t\tb: b + 1;\n\t\t\t});\n\t\t});\n\t}\n}\n");
		Assert:areEqualInt(0, self:countKind(issues: issues, wantWarnings: true));
	}

	Function is testMultilineStringDataIsSkipped(){
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction of String is c(){\n\t\treturn '''select *\n    from t\n{\n}\n\t''';\n\t}\n}\n");
		Assert:areEqualInt(0, self:countKind(issues: issues, wantWarnings: true));
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
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction is go(){\n\t\twhile(evaluate: { true }, iteration: {\n\t\t\tlocal Widget is w: Widget:init();\n\t\t});\n\t}\n}\n");
		Assert:areEqualInt(1, self:countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(0, self:countKind(issues: issues, wantWarnings: false));
	}

	Function is testEncourageAsConditionalNotice(){
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction is go(){\n\t\tConditional:if(check: { true }, then: {\n\t\t\tlocal Int is x: 1;\n\t\t});\n\t}\n}\n");
		Assert:areEqualInt(0, self:countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(1, self:countKind(issues: issues, wantWarnings: false));
	}

	Function is testEncourageAsLoopsNotice(){
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction is go(){\n\t\tLoops:while(evaluate: { true }, iterate: {\n\t\t\tlocal Int is x: 1;\n\t\t});\n\t}\n}\n");
		Assert:areEqualInt(0, self:countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(1, self:countKind(issues: issues, wantWarnings: false));
	}

	Function is testBareIfStaysClean(){
		local Array of LintIssue is issues: self:lintSource(src: "Class is F{\n\tFunction is go(){\n\t\tif(check: { true }, then: {\n\t\t\tlocal Int is x: 1;\n\t\t});\n\t}\n}\n");
		Assert:areEqualInt(0, self:countKind(issues: issues, wantWarnings: true));
		Assert:areEqualInt(0, self:countKind(issues: issues, wantWarnings: false));
	}

	Function is testModularRuleDiscovery(){
		local Linter is linter: Linter:init();
		Assert:isTrue(linter:rules:length() >= 8);
	}
}
