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
	##
	## @param line: Line coordinate.
	## @param isWarning: Severity flag.
	## @param message: Diagnostic message.
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
		if (self:isWarning) {
			if (self:line > 0) {
				return "  [Warning] Line " . self:line . ": " . self:message;
			}
			return "  [Warning] " . self:message;
		}
		if (self:line > 0) {
			return "  [Notice]  Line " . self:line . ": " . self:message;
		}
		return "  [Notice]  " . self:message;
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

	## Internal Loop: Inspects indentation whitespace line-by-line.
	class LineScanLoop extends Loop{
		local String is source: "";
		local Int is length: 0;
		local Int is pos: 0;
		local Int is lineNum: 1;
		local Boolean is atLineStart: true;
		local Int is leadingSpaces: 0;
		local Array of LintIssue is issues;

		replace local Function is init(String is source, Array of LintIssue is issues){
			self:source: source;
			self:length: source:length();
			self:pos: 0;
			self:lineNum: 1;
			self:atLineStart: true;
			self:leadingSpaces: 0;
			self:issues: issues;
		}

		replace local Function of Boolean is evaluate(){
			return self:pos < self:length;
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:source:charAt(index: self:pos, default: "");
			self:pos: self:pos + 1;

			if (ch == "\n") {
				self:lineNum: self:lineNum + 1;
				self:atLineStart: true;
				self:leadingSpaces: 0;
				return true;
			}

			if (self:atLineStart) {
				if (ch == " ") {
					self:leadingSpaces: self:leadingSpaces + 1;
				} else {
					if (ch != "\t" && ch != "\r") {
						if (self:leadingSpaces > 0) {
							local String is msg: "Space-based indentation detected (" . self:leadingSpaces . " space(s)). Spec standard requires tabs.";
							self:issues:add(item: LintIssue:init(line: self:lineNum, isWarning: true, message: msg));
						}
						self:atLineStart: false;
					}
				}
			}

			return true;
		}
	}

	## Internal Loop: Inspects method arguments in method calls.
	class ArgInspectLoop extends Loop{
		local Linter is linter;
		local Array of NamedArg is args;
		local Int is idx: 0;
		local Array of LintIssue is issues;

		replace local Function is init(Linter is linter, Array of NamedArg is args, Array of LintIssue is issues){
			self:linter: linter;
			self:args: args;
			self:idx: 0;
			self:issues: issues;
		}

		replace local Function of Boolean is evaluate(){
			return self:idx < self:args:length();
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local NamedArg is arg: self:args:get(index: self:idx);
			self:linter:lintExpression(expr: arg:getValue(), issues: self:issues);
			self:idx: self:idx + 1;
			return true;
		}
	}

	## Internal Loop: Inspects items in array literals.
	class ArrayItemsInspectLoop extends Loop{
		local Linter is linter;
		local Array of Expression is items;
		local Int is idx: 0;
		local Array of LintIssue is issues;

		replace local Function is init(Linter is linter, Array of Expression is items, Array of LintIssue is issues){
			self:linter: linter;
			self:items: items;
			self:idx: 0;
			self:issues: issues;
		}

		replace local Function of Boolean is evaluate(){
			return self:idx < self:items:length();
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local Expression is item: self:items:get(index: self:idx);
			self:linter:lintExpression(expr: item, issues: self:issues);
			self:idx: self:idx + 1;
			return true;
		}
	}

	## Internal Loop: Inspects statement lists.
	class StatementInspectLoop extends Loop{
		local Linter is linter;
		local Array of Statement is stmts;
		local Int is idx: 0;
		local Array of LintIssue is issues;

		replace local Function is init(Linter is linter, Array of Statement is stmts, Array of LintIssue is issues){
			self:linter: linter;
			self:stmts: stmts;
			self:idx: 0;
			self:issues: issues;
		}

		replace local Function of Boolean is evaluate(){
			return self:idx < self:stmts:length();
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local Statement is stmt: self:stmts:get(index: self:idx);
			self:linter:lintStatement(stmt: stmt, issues: self:issues);
			self:idx: self:idx + 1;
			return true;
		}
	}

	## Internal Loop: Inspects class members.
	class MemberInspectLoop extends Loop{
		local Linter is linter;
		local Array of Member is members;
		local Int is idx: 0;
		local Array of LintIssue is issues;

		replace local Function is init(Linter is linter, Array of Member is members, Array of LintIssue is issues){
			self:linter: linter;
			self:members: members;
			self:idx: 0;
			self:issues: issues;
		}

		replace local Function of Boolean is evaluate(){
			return self:idx < self:members:length();
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local Member is m: self:members:get(index: self:idx);
			if (m:getKind() == "METHOD") {
				While:run(loop: StatementInspectLoop:init(linter: self:linter, stmts: m:getBody(), issues: self:issues));
			}
			if (m:getKind() == "CLASS") {
				self:linter:lintClass(classDef: m:getNestedClass(), issues: self:issues);
			}
			self:idx: self:idx + 1;
			return true;
		}
	}

	## Internal Loop: Inspects program classes.
	class ClassInspectLoop extends Loop{
		local Linter is linter;
		local Array of Class is classes;
		local Int is idx: 0;
		local Array of LintIssue is issues;

		replace local Function is init(Linter is linter, Array of Class is classes, Array of LintIssue is issues){
			self:linter: linter;
			self:classes: classes;
			self:idx: 0;
			self:issues: issues;
		}

		replace local Function of Boolean is evaluate(){
			return self:idx < self:classes:length();
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local Class is c: self:classes:get(index: self:idx);
			self:linter:lintClass(classDef: c, issues: self:issues);
			self:idx: self:idx + 1;
			return true;
		}
	}

	## Internal Loop: Checks for default parameter in getString calls.
	class DefaultCheckLoop extends Loop{
		local Array of NamedArg is args;
		local Int is idx: 0;
		local Boolean is found: false;

		replace local Function is init(Array of NamedArg is args){
			self:args: args;
			self:idx: 0;
			self:found: false;
		}

		replace local Function of Boolean is evaluate(){
			return self:idx < self:args:length() && !self:found;
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local NamedArg is arg: self:args:get(index: self:idx);
			if (arg:getName() == "default") {
				self:found: true;
			}
			self:idx: self:idx + 1;
			return true;
		}
	}

	## Internal Loop: Counts warnings in an issue list.
	class WarningCountLoop extends Loop{
		local Array of LintIssue is issues;
		local Int is idx: 0;
		local Int is count: 0;

		replace local Function is init(Array of LintIssue is issues){
			self:issues: issues;
			self:idx: 0;
			self:count: 0;
		}

		replace local Function of Boolean is evaluate(){
			return self:idx < self:issues:length();
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local LintIssue is issue: self:issues:get(index: self:idx);
			if (issue:getIsWarning()) {
				self:count: self:count + 1;
			}
			self:idx: self:idx + 1;
			return true;
		}
	}

	## Internal Loop: Counts notices in an issue list.
	class NoticeCountLoop extends Loop{
		local Array of LintIssue is issues;
		local Int is idx: 0;
		local Int is count: 0;

		replace local Function is init(Array of LintIssue is issues){
			self:issues: issues;
			self:idx: 0;
			self:count: 0;
		}

		replace local Function of Boolean is evaluate(){
			return self:idx < self:issues:length();
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local LintIssue is issue: self:issues:get(index: self:idx);
			if (!issue:getIsWarning()) {
				self:count: self:count + 1;
			}
			self:idx: self:idx + 1;
			return true;
		}
	}

	## Internal Loop: Prints issues to standard output.
	class PrintLoop extends Loop{
		local Array of LintIssue is issues;
		local Int is idx: 0;

		replace local Function is init(Array of LintIssue is issues){
			self:issues: issues;
			self:idx: 0;
		}

		replace local Function of Boolean is evaluate(){
			return self:idx < self:issues:length();
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local LintIssue is issue: self:issues:get(index: self:idx);
			output:line(issue:toString());
			self:idx: self:idx + 1;
			return true;
		}
	}

	replace local Function is init(){
	}

	## Inspects an expression node for optional arguments and idioms.
	##
	## @param expr: [Expression] AST node.
	## @param issues: Destination issues array.
	replace local Function is lintExpression(Expression is expr, Array of LintIssue is issues){
		local String is kind: expr:getKind();

		if (kind == "CALL") {
			local String is method: expr:methodName;
			local Array of NamedArg is args: expr:methodArgs;

			if (method == "getString") {
				local DefaultCheckLoop is dLoop: DefaultCheckLoop:init(args: args);
				While:run(loop: dLoop);
				if (dLoop:found) {
					issues:add(item: LintIssue:init(line: 0, isWarning: false, message: "Method call 'getString' provides optional parameter 'default'."));
				}
			}

			if (method == "random") {
				if (args:length() == 0) {
					issues:add(item: LintIssue:init(line: 0, isWarning: false, message: "Method call 'math:random' omits optional min/max parameters (using default [0.0, 1.0))."));
				} else {
					issues:add(item: LintIssue:init(line: 0, isWarning: false, message: "Method call 'math:random' provides optional min/max range parameters."));
				}
			}

			self:lintExpression(expr: expr:methodTarget, issues: issues);
			While:run(loop: ArgInspectLoop:init(linter: self, args: args, issues: issues));
		}

		if (kind == "BINARY") {
			self:lintExpression(expr: expr:leftExpr, issues: issues);
			self:lintExpression(expr: expr:rightExpr, issues: issues);
		}

		if (kind == "UNARY") {
			self:lintExpression(expr: expr:unaryExpr, issues: issues);
		}

		if (kind == "ARRAY") {
			While:run(loop: ArrayItemsInspectLoop:init(linter: self, items: expr:arrayItems, issues: issues));
		}
	}

	## Inspects a statement node.
	##
	## @param stmt: [Statement] AST node.
	## @param issues: Destination issues array.
	replace local Function is lintStatement(Statement is stmt, Array of LintIssue is issues){
		local String is kind: stmt:getKind();

		if (kind == "VAR_DECL") {
			if (stmt:hasInit) {
				self:lintExpression(expr: stmt:initExpr, issues: issues);
			}
		}

		if (kind == "ASSIGN") {
			self:lintExpression(expr: stmt:assignTarget, issues: issues);
			self:lintExpression(expr: stmt:assignValue, issues: issues);
		}

		if (kind == "IF") {
			self:lintExpression(expr: stmt:ifCondition, issues: issues);
			While:run(loop: StatementInspectLoop:init(linter: self, stmts: stmt:thenBranch, issues: issues));
			if (stmt:hasElse) {
				While:run(loop: StatementInspectLoop:init(linter: self, stmts: stmt:elseBranch, issues: issues));
			}
		}

		if (kind == "RETURN") {
			if (stmt:hasReturnExpr) {
				self:lintExpression(expr: stmt:returnExpr, issues: issues);
			}
		}

		if (kind == "CLASS") {
			self:lintClass(classDef: stmt:nestedClass, issues: issues);
		}

		if (kind == "EXPR") {
			self:lintExpression(expr: stmt:exprStmt, issues: issues);
		}
	}

	## Inspects all members of a class definition.
	##
	## @param classDef: [Class] definition.
	## @param issues: Destination issues array.
	replace local Function is lintClass(Class is classDef, Array of LintIssue is issues){
		While:run(loop: MemberInspectLoop:init(linter: self, members: classDef:getMembers(), issues: issues));
	}

	## Analyzes source code text and optional AST, returning all detected lint issues.
	##
	## @param source: Raw source code string.
	## @param program: Parsed [ProgramNode] AST.
	## @return: [Array] of [LintIssue] items.
	replace local Function of Array of LintIssue is lint(String is source, ProgramNode is program){
		local Array of LintIssue is issues: [];

		# 1. Indentation Check
		While:run(loop: LineScanLoop:init(source: source, issues: issues));

		# 2. AST Checks
		While:run(loop: ClassInspectLoop:init(linter: self, classes: program:getClasses(), issues: issues));

		return issues;
	}

	## Counts the total number of warnings in an issues list.
	##
	## @param issues: Issues array.
	## @return: Count of warnings.
	replace local Function of Int is countWarnings(Array of LintIssue is issues){
		local WarningCountLoop is wLoop: WarningCountLoop:init(issues: issues);
		While:run(loop: wLoop);
		return wLoop:count;
	}

	## Counts the total number of notices in an issues list.
	##
	## @param issues: Issues array.
	## @return: Count of notices.
	replace local Function of Int is countNotices(Array of LintIssue is issues){
		local NoticeCountLoop is nLoop: NoticeCountLoop:init(issues: issues);
		While:run(loop: nLoop);
		return nLoop:count;
	}

	## Prints formatted lint diagnostics to standard output.
	##
	## @param filePath: Source file path.
	## @param issues: Array of detected [LintIssue] items.
	replace local Function is report(String is filePath, Array of LintIssue is issues){
		output:line("Checking '" . filePath . "' for Spec code standards...");
		While:run(loop: PrintLoop:init(issues: issues));

		local Int is warnings: self:countWarnings(issues: issues);
		local Int is notices: self:countNotices(issues: issues);
		output:line("\nLint summary for " . filePath . ": " . warnings . " warning(s), " . notices . " notice(s).");
		if (warnings == 0) {
			output:line("All standard checks passed successfully.");
		}
	}

}
