#! Package base:compiler:linter
#! Pure-Spec code linter enforcing tab-based indentation, formatting,
#! and AST idioms.

## Represents an issue or diagnostic notice detected by the Spec linter.
Class is LintIssue{
	namespace: ['base', 'compiler', 'linter'];

	## One-based line number where the issue was found (0 if general).
	Int is line: 0;

	## `true` if this is a standard violation warning, `false` for informational notices.
	Boolean is isWarning: false;

	## Informational description of the issue.
	String is message: '';

	## Initializes a lint issue.
	replace Function is init(Int is line, Boolean is isWarning, String is message){
		self:line: line;
		self:isWarning: isWarning;
		self:message: message;
	}

	## Returns whether this issue is a warning.
	##
	## @return: `true` if warning, `false` if notice.
	Function of Boolean is getIsWarning(){
		return self:isWarning;
	}

	## Formats the issue for terminal display.
	##
	## @return: Formatted display string.
	replace Function of String is toString(){
		local String is tag: if (self:isWarning) '[Warning]' else '[Notice] ';
		local String is loc: if (self:line > 0) 'Line ' . (self:line as String) . ': ' else '';
		return '  ' . tag . ' ' . loc . self:message;
	}
}

## Pure-Spec code linter enforcing tab-based indentation, formatting,
## and AST idioms.
Class is Linter{
	namespace: ['base', 'compiler', 'linter'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', StatementKind],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'io', Output],
		['base', 'struct', Array],
		['base', 'iterator']
	];

	replace Function is init(){
	}

	## Inspects indentation whitespace line-by-line.
	##
	## Checks: leading spaces after tabs, trailing whitespace, and closing-brace
	## alignment against the current nesting depth (string literals and
	## comments are masked so brace characters inside them are ignored).
	##
	## @param source: Raw source code string.
	## @param issues: Destination issues array.
	Function is lintIndentation(String is source, Array of LintIssue is issues){
		local Int is lineNum: 0;
		local Int is depth: 0;
		# Own the lines array: a fresh call result rides the claim pool,
    # and this loop's bodies claim repeatedly — 32 claims would evict it
    # mid-iteration. A var-decl init is a consumption position.
    local Array of String is srcLines: source:lines();
    srcLines:each(action: local Function(String is line){
			lineNum: lineNum + 1;
			local Int is tabs: line:countLeading(search: "\t");
			local String is rest: line:substring(start: tabs, end: line:length());
			local Int is spaces: rest:countLeading(search: ' ');
			if (spaces > 0) {
				local String is msg: 'Space-based indentation detected (' . (spaces as String) . ' space(s)). Spec standard requires tabs.';
				issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: msg));
			}
			if (line:length() > 0 && (line:charAt(index: line:length() - 1, default: ' ') == ' ' || line:charAt(index: line:length() - 1, default: ' ') == "\t")) {
				issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: 'Trailing whitespace detected.'));
			}

			# Mask strings and comments, then validate brace alignment.
			local String is masked: self:maskLine(line: line);
			local String is body: masked;
			local Boolean is trimming: true;
			While:condition(
				evaluate: local Function of Boolean(){ return trimming && body:length() > 0; },
				iteration: local Function(){
					local String is last: body:charAt(index: body:length() - 1, default: '');
					if (last == ' ' || last == "\t") {
						body: body:substring(start: 0, end: body:length() - 1);
					} else {
						trimming: false;
					}
				}
			);
			if (body:length() > 0 && body:charAt(index: 0, default: '') == '}') {
				local Int is expectedTabs: depth - 1;
				if (expectedTabs < 0) {
					expectedTabs: 0;
				}
				if (tabs != expectedTabs) {
					local String is msg: 'Closing brace indented at ' . (tabs as String) . ' tab(s); nesting depth expects ' . (expectedTabs as String) . '.';
					issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: msg));
				}
			}
			local Int is ci: 0;
			While:condition(
				evaluate: local Function of Boolean(){ return ci < masked:length(); },
				iteration: local Function(){
					local String is ch: masked:charAt(index: ci, default: '');
					if (ch == '{') {
						depth: depth + 1;
					} else if (ch == '}') {
						depth: depth - 1;
					}
					ci: ci + 1;
				}
			);
		});
	}

	## Returns a line with string contents and comments replaced by spaces so
	## that brace counting only sees structural characters.
	##
	## @param line: Raw source line.
	## @return: Masked line of identical length.
	Function of String is maskLine(String is line){
		local String is out: '';
		local String is quote: '';
		local Int is i: 0;
		While:condition(
			evaluate: local Function of Boolean(){ return i < line:length(); },
			iteration: local Function(){
				local String is ch: line:charAt(index: i, default: '');
				if (quote != '') {
					if (ch == "\\") {
						out: out . '  ';
						i: i + 1;
					} else if (ch == quote) {
						quote: '';
						out: out . ' ';
					} else {
						out: out . ' ';
					}
				} else if (ch == '"' || ch == '\'') {
					quote: ch;
					out: out . ' ';
				} else if (ch == '#') {
					i: line:length();
				} else {
					out: out . ch;
				}
				i: i + 1;
			}
		);
		return out;
	}

	## Inspects an expression node for optional arguments and idioms.
	##
	## @param expr: [Expression] AST node.
	## @param issues: Destination issues array.
	Function is lintExpression(Expression is expr, Array of LintIssue is issues){
		local ExpressionKind is kind: expr:kind;

		when (kind) {
			is ExpressionKind:CALL: {
				local String is method: expr:methodName;
				local Array of NamedArg is args: expr:methodArgs;

				when (method) {
					is 'getString': {
						local Boolean is hasDefault: false;
						args:each(action: local Function(NamedArg is arg){
							if (arg:name == 'default') {
								hasDefault: true;
							}
						});
						if (hasDefault) {
							issues:add(item: LintIssue:init(line: 0, isWarning: false, message: 'Method call \'getString\' provides optional parameter \'default\'.'));
						}
					}
					is 'random': {
						local String is msg: 'Method call \'math:random\' provides optional min/max range parameters.';
						if (args:length() == 0) {
							msg: 'Method call \'math:random\' omits optional min/max parameters (using default [0.0, 1.0)).';
						}
						issues:add(item: LintIssue:init(line: 0, isWarning: false, message: msg));
					}
					else: {}
				}

				self:lintExpression(expr: expr:methodTarget, issues: issues);
				args:each(action: local Function(NamedArg is arg){
					self:lintExpression(expr: arg:value, issues: issues);
				});
			}
			is ExpressionKind:BINARY: {
				self:lintExpression(expr: expr:leftExpr, issues: issues);
				self:lintExpression(expr: expr:rightExpr, issues: issues);
			}
			is ExpressionKind:UNARY: {
				self:lintExpression(expr: expr:unaryExpr, issues: issues);
			}
			is ExpressionKind:ARRAY: {
				expr:arrayItems:each(action: local Function(Expression is item){
					self:lintExpression(expr: item, issues: issues);
				});
			}
			else: {}
		}
	}

	## Inspects a statement node.
	##
	## @param stmt: [Statement] AST node.
	## @param issues: Destination issues array.
	Function is lintStatement(Statement is stmt, Array of LintIssue is issues){
		local StatementKind is kind: stmt:kind;

		when (kind) {
			is StatementKind:VAR_DECL: {
				if (stmt:hasInit) {
					self:lintExpression(expr: stmt:initExpr, issues: issues);
				}
			}
			is StatementKind:ASSIGN: {
				self:lintExpression(expr: stmt:assignTarget, issues: issues);
				self:lintExpression(expr: stmt:assignValue, issues: issues);
			}
			is StatementKind:IF: {
				self:lintExpression(expr: stmt:ifCondition, issues: issues);
				stmt:thenBranch:each(action: local Function(Statement is s){
					self:lintStatement(stmt: s, issues: issues);
				});
				if (stmt:hasElse) {
					stmt:elseBranch:each(action: local Function(Statement is s){
						self:lintStatement(stmt: s, issues: issues);
					});
				}
			}
			is StatementKind:RETURN: {
				if (stmt:hasReturnExpr) {
					self:lintExpression(expr: stmt:returnExpr, issues: issues);
				}
			}
			is StatementKind:CLASS: {
				self:lintClass(classDef: stmt:nestedClass, issues: issues);
			}
			is StatementKind:EXPR: {
				self:lintExpression(expr: stmt:exprStmt, issues: issues);
			}
			else: {}
		}
	}

	## Inspects all members of a class definition.
	##
	## @param classDef: [ClassInfo] definition.
	## @param issues: Destination issues array.
	Function is lintClass(ClassInfo is classDef, Array of LintIssue is issues){
		classDef:members:each(action: local Function(Member is m){
			when (m:kind) {
				is MemberKind:METHOD: {
					m:body:each(action: local Function(Statement is s){
						self:lintStatement(stmt: s, issues: issues);
					});
				}
				is MemberKind:CLASS: {
					self:lintClass(classDef: m:nestedClass, issues: issues);
				}
				else: {}
			}
		});
	}

	## Analyzes source code text and optional AST, returning all detected lint issues.
	##
	## @param source: Raw source code string.
	## @param program: Parsed [ProgramNode] AST.
	## @return: [Array] of [LintIssue] items.
	Function of Array of LintIssue is lint(String is source, ProgramNode is program){
		local Array of LintIssue is issues: [];

		# 1. Indentation Check
		self:lintIndentation(source: source, issues: issues);

		# 2. AST Checks
		program:classes:each(action: local Function(ClassInfo is c){
			self:lintClass(classDef: c, issues: issues);
		});

		return issues;
	}

	## Counts the total number of warnings in an issues list.
	##
	## @param issues: Issues array.
	## @return: Count of warnings.
	Function of Int is countWarnings(Array of LintIssue is issues){
		local Int is res: 0;
		issues:each(action: local Function(LintIssue is issue){
			if (issue:isWarning) {
				res: res + 1;
			}
		});
		return res;
	}

	## Counts the total number of notices in an issues list.
	##
	## @param issues: Issues array.
	## @return: Count of notices.
	Function of Int is countNotices(Array of LintIssue is issues){
		local Int is res: 0;
		issues:each(action: local Function(LintIssue is issue){
			if (!issue:isWarning) {
				res: res + 1;
			}
		});
		return res;
	}

	## Prints formatted lint diagnostics to standard output.
	##
	## @param filePath: Source file path.
	## @param issues: Array of detected [LintIssue] items.
	Function is report(String is filePath, Array of LintIssue is issues){
		output:line('Checking \'' . filePath . '\' for Spec code standards...');
		issues:each(action: local Function(LintIssue is issue){
			output:line(issue:toString());
		});

		local Int is warnings: self:countWarnings(issues: issues);
		local Int is notices: self:countNotices(issues: issues);
		output:line("\nLint summary for " . filePath . ': ' . (warnings as String) . ' warning(s), ' . (notices as String) . ' notice(s).');
		if (warnings == 0) {
			output:line('All standard checks passed successfully.');
		}
	}
}
