#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, and Linter.

## Represents an issue or diagnostic notice detected by the Spec linter.
class LintIssue{

	## One-based line number where the issue was found (0 if general).
	local Int is line: 0;

	## `true` if this is a standard violation warning, `false` for informational notices.
	local Boolean is isWarning: false;

	## Informational description of the issue.
	local String is message: "";

	## Initializes a lint issue.
	replace local Function is init(Int is line, Boolean is isWarning, String is message){
		self:line: line;
		self:isWarning: isWarning;
		self:message: message;
	}

	## Returns the line number.
	##
	## @return: Line number integer.
	replace local Function of Int is getLine(){
		return self:line;
	}

	## Returns whether this issue is a warning.
	##
	## @return: `true` if warning, `false` if notice.
	replace local Function of Boolean is getIsWarning(){
		return self:isWarning;
	}

	## Returns the diagnostic message.
	##
	## @return: Message string.
	replace local Function of String is getMessage(){
		return self:message;
	}

	## Formats the issue for terminal display.
	##
	## @return: Formatted display string.
	replace local Function of String is toString(){
		local String is tag: if (self:isWarning) "[Warning]" else "[Notice] ";
		local String is loc: if (self:line > 0) "Line " . self:line . ": " else "";
		return "  " . tag . " " . loc . self:message;
	}

}

## Pure-Spec code linter enforcing tab-based indentation, formatting, and AST idioms.
class Linter{

	replace local Array of String is using: [
		base:io:*,
		base:struct:Array,
		base:iterator:*,
		base:reflect:*,
		base:meta:*
	];

	replace local Function is init(){
	}

	## Inspects indentation whitespace line-by-line using String and Array higher-order methods.
	##
	## @param source: Raw source code string.
	## @param issues: Destination issues array.
	replace local Function is lintIndentation(String is source, Array of LintIssue is issues){
		local Int is lineNum: 0;
		source:lines():each(action: local Function(String is line){
			lineNum: lineNum + 1;
			local Int is tabs: line:countLeading(search: "\t");
			local String is rest: line:substring(start: tabs, end: line:length());
			local Int is spaces: rest:countLeading(search: " ");
			if (spaces > 0) {
				local String is msg: "Space-based indentation detected (" . spaces . " space(s)). Spec standard requires tabs.";
				issues:add(item: LintIssue:init(line: lineNum, isWarning: true, message: msg));
			}
		});
	}

	## Inspects an expression node for optional arguments and idioms.
	##
	## @param expr: [Expression] AST node.
	## @param issues: Destination issues array.
	replace local Function is lintExpression(Expression is expr, Array of LintIssue is issues){
		local String is kind: expr:getKind();

		when (kind) {
			is "CALL": {
				local String is method: expr:methodName;
				local Array of NamedArg is args: expr:methodArgs;

				when (method) {
					is "getString": {
						local Boolean is hasDefault: args:any(predicate: local Function of Boolean(NamedArg is arg){
							return arg:getName() is "default";
						});
						if (hasDefault) {
							issues:add(item: LintIssue:init(line: 0, isWarning: false, message: "Method call 'getString' provides optional parameter 'default'."));
						}
					}
					is "random": {
						local String is msg: if (args:length() is 0)
							"Method call 'math:random' omits optional min/max parameters (using default [0.0, 1.0))."
						else
							"Method call 'math:random' provides optional min/max range parameters.";
						issues:add(item: LintIssue:init(line: 0, isWarning: false, message: msg));
					}
					else: {}
				}

				self:lintExpression(expr: expr:methodTarget, issues: issues);
				args:each(action: local Function(NamedArg is arg){
					self:lintExpression(expr: arg:getValue(), issues: issues);
				});
			}
			is "BINARY": {
				self:lintExpression(expr: expr:leftExpr, issues: issues);
				self:lintExpression(expr: expr:rightExpr, issues: issues);
			}
			is "UNARY": {
				self:lintExpression(expr: expr:unaryExpr, issues: issues);
			}
			is "ARRAY": {
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
	replace local Function is lintStatement(Statement is stmt, Array of LintIssue is issues){
		local String is kind: stmt:getKind();

		when (kind) {
			is "VAR_DECL": {
				if (stmt:hasInit) {
					self:lintExpression(expr: stmt:initExpr, issues: issues);
				}
			}
			is "ASSIGN": {
				self:lintExpression(expr: stmt:assignTarget, issues: issues);
				self:lintExpression(expr: stmt:assignValue, issues: issues);
			}
			is "IF": {
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
			is "RETURN": {
				if (stmt:hasReturnExpr) {
					self:lintExpression(expr: stmt:returnExpr, issues: issues);
				}
			}
			is "CLASS": {
				self:lintClass(classDef: stmt:nestedClass, issues: issues);
			}
			is "EXPR": {
				self:lintExpression(expr: stmt:exprStmt, issues: issues);
			}
			else: {}
		}
	}

	## Inspects all members of a class definition.
	##
	## @param classDef: [Class] definition.
	## @param issues: Destination issues array.
	replace local Function is lintClass(Class is classDef, Array of LintIssue is issues){
		classDef:getMembers():each(action: local Function(Member is m){
			when (m:getMemberKind()) {
				is METHOD: {
					m:getBody():each(action: local Function(Statement is s){
						self:lintStatement(stmt: s, issues: issues);
					});
				}
				is CLASS: {
					self:lintClass(classDef: m:getNestedClass(), issues: issues);
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
	replace local Function of Array of LintIssue is lint(String is source, ProgramNode is program){
		local Array of LintIssue is issues: [];

		# 1. Indentation Check
		self:lintIndentation(source: source, issues: issues);

		# 2. AST Checks
		program:getClasses():each(action: local Function(Class is c){
			self:lintClass(classDef: c, issues: issues);
		});

		return issues;
	}

	## Counts the total number of warnings in an issues list.
	##
	## @param issues: Issues array.
	## @return: Count of warnings.
	replace local Function of Int is countWarnings(Array of LintIssue is issues){
		return issues:count(predicate: local Function of Boolean(LintIssue is issue){
			return issue:getIsWarning();
		});
	}

	## Counts the total number of notices in an issues list.
	##
	## @param issues: Issues array.
	## @return: Count of notices.
	replace local Function of Int is countNotices(Array of LintIssue is issues){
		return issues:count(predicate: local Function of Boolean(LintIssue is issue){
			return !issue:getIsWarning();
		});
	}

	## Prints formatted lint diagnostics to standard output.
	##
	## @param filePath: Source file path.
	## @param issues: Array of detected [LintIssue] items.
	replace local Function is report(String is filePath, Array of LintIssue is issues){
		output:line("Checking '" . filePath . "' for Spec code standards...");
		issues:each(action: local Function(LintIssue is issue){
			output:line(issue:toString());
		});

		local Int is warnings: self:countWarnings(issues: issues);
		local Int is notices: self:countNotices(issues: issues);
		output:line("\nLint summary for " . filePath . ": " . warnings . " warning(s), " . notices . " notice(s).");
		if (warnings is 0) {
			output:line("All standard checks passed successfully.");
		}
	}

}
