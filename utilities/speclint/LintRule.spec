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
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
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
		match(on: stmt, when: [
			Statement:VarDecl: local Function(Array of String is modifiers, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit){
				if({ hasInit }, {
					self:checkExpression(expr: initExpr, issues: issues);
				});
			},
			Statement:Assign: local Function(Expression is assignTarget, Expression is assignValue){
				self:checkExpression(expr: assignTarget, issues: issues);
				self:checkExpression(expr: assignValue, issues: issues);
			},
			Statement:Return: local Function(Expression is returnExpr, Boolean is hasReturnExpr){
				if({ hasReturnExpr }, {
					self:checkExpression(expr: returnExpr, issues: issues);
				});
			},
			Statement:ClassDecl: local Function(ClassInfo is nestedClass){
				self:checkClass(classDef: nestedClass, issues: issues);
			},
			Statement:Expr: local Function(Expression is exprStmt){
				self:checkExpression(expr: exprStmt, issues: issues);
			},
			Statement:Forward: local Function(Array of NamedArg is forwardArgs){
				forwardArgs:each(action: local Function(NamedArg is arg){
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
		match(on: expr, when: [
			Expression:Call: local Function(CallData is cd){
				self:checkExpression(expr: cd:target, issues: issues);
				cd:args:each(action: local Function(NamedArg is arg){
					self:checkExpression(expr: arg:value, issues: issues);
				});
			},
			Expression:Binary: local Function(String is op, Expression is leftExpr, Expression is rightExpr){
				self:checkExpression(expr: leftExpr, issues: issues);
				self:checkExpression(expr: rightExpr, issues: issues);
			},
			Expression:Unary: local Function(String is op, Expression is operand){
				self:checkExpression(expr: operand, issues: issues);
			},
			Expression:ArrayLit: local Function(Array of Expression is items){
				items:each(action: local Function(Expression is item){
					self:checkExpression(expr: item, issues: issues);
				});
			},
			Expression:MapLit: local Function(Array of Expression is keys, Array of Expression is values){
				keys:each(action: local Function(Expression is k){
					self:checkExpression(expr: k, issues: issues);
				});
				values:each(action: local Function(Expression is v){
					self:checkExpression(expr: v, issues: issues);
				});
			},
			Expression:Cast: local Function(Expression is target, Type is targetType, Array of Expression is args){
				self:checkExpression(expr: target, issues: issues);
				args:each(action: local Function(Expression is a){
					self:checkExpression(expr: a, issues: issues);
				});
			},
			Expression:FieldAccess: local Function(Expression is target, String is field){
				self:checkExpression(expr: target, issues: issues);
			},
			Expression:Index: local Function(Expression is target, Expression is index){
				self:checkExpression(expr: target, issues: issues);
				self:checkExpression(expr: index, issues: issues);
			},
			Expression:AnonFn: local Function(Type is returnType, Array of Parameter is params, Array of Statement is body){
				body:each(action: local Function(Statement is st){
					self:checkStatement(stmt: st, issues: issues);
				});
			}
		], default: {});
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
		return match(on: target, when: [
			Expression:Ident: local Function of String(String is name){
				return name;
			},
			Expression:Path: local Function of String(Array of String is segs){
				if({ segs:length() > 0 }, {
					return segs:get(index: segs:length() - 1);
				});
				return '';
			},
			else: { ''; }
		], default: {});
	}
}
