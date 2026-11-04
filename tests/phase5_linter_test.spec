Class is Phase5LinterTest{

	replace Array of String is using: [
		base:io:*,
		base:struct:Array,
		base:iterator:*,
		base:reflect:Type,
		base:reflect:Parameter,
		base:reflect:Member,
		base:reflect:ClassInfo,
		base:meta:*,
		compiler:Token,
		compiler:Lexer,
		compiler:Parser,
		compiler:Linter
	];

	replace Function is init(Map of String to String is args){
		output:line('======================================');
		output:line('        Phase 5 Pure-Spec Linter      ');
		output:line("======================================\n");

		local Linter is linter: Linter:init();

		# 1. Test clean code with tabs
		output:line('--- 1. Clean Code (Tabs) ---');
		local String is cleanCode: "class CleanPlayer{\n\tlocal Int is health: 100;\n\treplace local Function of Boolean is isAlive(){\n\t\treturn health > 0;\n\t}\n}";
		local Lexer is lexer1: Lexer:init(source: cleanCode);
		local Parser is parser1: Parser:init(tokens: lexer1:tokenize());
		local ProgramNode is prog1: parser1:parseProgram();

		local Array of LintIssue is cleanIssues: linter:lint(source: cleanCode, program: prog1);
		local Int is cleanWarnings: linter:countWarnings(issues: cleanIssues);
		output:line('Clean code warnings: ' . cleanWarnings);

		if (cleanWarnings == 0) {
			output:line('[PASS] Zero warnings on tab-indented code');
		}

		# 2. Test space-indented code
		output:line("\n--- 2. Space Indentation Detection ---");
		local String is spaceCode: "class BadPlayer{\n    local Int is health: 100;\n}";
		local Lexer is lexer2: Lexer:init(source: spaceCode);
		local Parser is parser2: Parser:init(tokens: lexer2:tokenize());
		local ProgramNode is prog2: parser2:parseProgram();

		local Array of LintIssue is spaceIssues: linter:lint(source: spaceCode, program: prog2);
		local Int is spaceWarnings: linter:countWarnings(issues: spaceIssues);
		output:line('Space-indented code warnings: ' . spaceWarnings);

		if (spaceWarnings == 1) {
			output:line('[PASS] Detected exactly 1 warning for space indentation');
			local LintIssue is issue: spaceIssues:get(index: 0);
			output:line('Reported issue: ' . issue:toString());
		}

		# 3. Test AST notices
		output:line("\n--- 3. Optional Parameter & Method AST Notices ---");
		local String is noticeCode: "class Game{\n\treplace local Function is run(){\n\t\tlocal Float is r: math:random();\n\t}\n}";
		local Lexer is lexer3: Lexer:init(source: noticeCode);
		local Parser is parser3: Parser:init(tokens: lexer3:tokenize());
		local ProgramNode is prog3: parser3:parseProgram();

		local Array of LintIssue is noticeIssues: linter:lint(source: noticeCode, program: prog3);
		local Int is noticeCount: linter:countNotices(issues: noticeIssues);
		output:line('Detected notices count: ' . noticeCount);

		if (noticeCount > 0) {
			output:line('[PASS] Successfully detected AST optional parameter notices');
			local LintIssue is nIssue: noticeIssues:get(index: 0);
			output:line('Sample notice: ' . nIssue:toString());
		}

		output:line("\nPhase 5 Pure-Spec Linter test completed successfully!");
	}

}
