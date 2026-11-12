#! Package speclint
#! Base class and contract for all speclint rules.

Class is LintRule{
	namespace: ['speclint'];

	replace Array of Array of String is using: [
		['speclint', LintIssue],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', StatementKind],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'struct', Array],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(){
	}

	## Unique identifier for this rule.
	Function of String is id(){
		return '';
	}

	## Human-readable description of what this rule checks.
	Function of String is description(){
		return '';
	}

	## Whether this rule emits warnings (true) or informational notices (false).
	Function of Boolean is isWarning(){
		return true;
	}

	## Inspects raw source code text. Override to enforce formatting/indentation.
	Function is checkSource(String is source, Array of LintIssue is issues){
		return;
	}

	## Inspects the parsed AST program. Default implementation traverses all classes.
	Function is checkProgram(ProgramNode is program, Array of LintIssue is issues){
		self:traverseProgram(program: program, issues: issues);
	}

	## Default AST program traversal.
	Function is traverseProgram(ProgramNode is program, Array of LintIssue is issues){
		program:classes:each(action: local Function(ClassInfo is c){
			self:checkClass(classDef: c, issues: issues);
		});
	}

	## Inspects a class definition. Default implementation traverses all members.
	Function is checkClass(ClassInfo is classDef, Array of LintIssue is issues){
		self:traverseClass(classDef: classDef, issues: issues);
	}

	## Default class member traversal.
	Function is traverseClass(ClassInfo is classDef, Array of LintIssue is issues){
		classDef:members:each(action: local Function(Member is m){
			match(on: m:kind, when: [
				MemberKind:METHOD: {
					m:body:each(action: local Function(Statement is s){
						self:checkStatement(stmt: s, issues: issues);
					});
				},
				MemberKind:CLASS: {
					self:checkClass(classDef: m:nestedClass, issues: issues);
				}
			]);
		});
	}

	## Inspects a statement node. Default implementation traverses expressions.
	Function is checkStatement(Statement is stmt, Array of LintIssue is issues){
		self:traverseStatement(stmt: stmt, issues: issues);
	}

	## Default statement traversal.
	Function is traverseStatement(Statement is stmt, Array of LintIssue is issues){
		local StatementKind is kind: stmt:kind;
		match(on: kind, when: [
			StatementKind:VAR_DECL: {
				if({ stmt:hasInit }, {
					self:checkExpression(expr: stmt:initExpr, issues: issues);
				});
			},
			StatementKind:ASSIGN: {
				self:checkExpression(expr: stmt:assignTarget, issues: issues);
				self:checkExpression(expr: stmt:assignValue, issues: issues);
			},
			StatementKind:RETURN: {
				if({ stmt:hasReturnExpr }, {
					self:checkExpression(expr: stmt:returnExpr, issues: issues);
				});
			},
			StatementKind:CLASS: {
				self:checkClass(classDef: stmt:nestedClass, issues: issues);
			},
			StatementKind:EXPR: {
				self:checkExpression(expr: stmt:exprStmt, issues: issues);
			},
			StatementKind:FORWARD: {
				stmt:forwardArgs:each(action: local Function(NamedArg is arg){
					self:checkExpression(expr: arg:value, issues: issues);
				});
			}
		]);
	}

	## Inspects an expression node. Default implementation traverses child expressions.
	Function is checkExpression(Expression is expr, Array of LintIssue is issues){
		self:traverseExpression(expr: expr, issues: issues);
	}

	## Default expression traversal.
	Function is traverseExpression(Expression is expr, Array of LintIssue is issues){
		local ExpressionKind is kind: expr:kind;
		match(on: kind, when: [
			ExpressionKind:CALL: {
				self:checkExpression(expr: expr:methodTarget, issues: issues);
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					self:checkExpression(expr: arg:value, issues: issues);
				});
			},
			ExpressionKind:BINARY: {
				self:checkExpression(expr: expr:leftExpr, issues: issues);
				self:checkExpression(expr: expr:rightExpr, issues: issues);
			},
			ExpressionKind:UNARY: {
				self:checkExpression(expr: expr:unaryExpr, issues: issues);
			},
			ExpressionKind:ARRAY: {
				expr:arrayItems:each(action: local Function(Expression is item){
					self:checkExpression(expr: item, issues: issues);
				});
			},
			ExpressionKind:MAP: {
				expr:mapKeys:each(action: local Function(Expression is k){
					self:checkExpression(expr: k, issues: issues);
				});
				expr:mapValues:each(action: local Function(Expression is v){
					self:checkExpression(expr: v, issues: issues);
				});
			},
			ExpressionKind:CAST: {
				self:checkExpression(expr: expr:leftExpr, issues: issues);
				expr:castArgs:each(action: local Function(Expression is a){
					self:checkExpression(expr: a, issues: issues);
				});
			},
			ExpressionKind:FIELD_ACCESS: {
				self:checkExpression(expr: expr:leftExpr, issues: issues);
			},
			ExpressionKind:INDEX: {
				self:checkExpression(expr: expr:leftExpr, issues: issues);
				expr:castArgs:each(action: local Function(Expression is a){
					self:checkExpression(expr: a, issues: issues);
				});
			},
			ExpressionKind:ANON_FN: {
				expr:anonBody:each(action: local Function(Statement is st){
					self:checkStatement(stmt: st, issues: issues);
				});
			}
		]);
	}

	## True when [name] starts with an uppercase letter (type naming convention).
	Function of Boolean is isUpperName(String is name){
		if({ name:length() == 0 }, {
			return false;
		});
		local String is first: name:charAt(index: 0, default: '');
		return match(on: first, when: [
			['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']: { true },
			['N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']: { true },
			else: { false }
		]);
	}

	## Extracts the bare name from an IDENT or PATH expression.
	Function of String is extractTargetName(Expression is target){
		local String is name: '';
		match(on: target:kind, when: [
			ExpressionKind:IDENT: {
				name: target:str;
			},
			ExpressionKind:PATH: {
				local Array of String is segs: target:pathSegments;
				if({ segs:length() > 0 }, {
					name: segs:get(index: segs:length() - 1);
				});
			}
		]);
		return name;
	}
}
