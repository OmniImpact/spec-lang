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
		:traverseProgram(program: program, issues: issues);
	}

	## Default AST program traversal.
	Function is traverseProgram(ProgramNode is program, Array of LintIssue is issues){
		local Int is ci: 0;
		while({ ci < program:classes:length() }, {
			:checkClass(classDef: program:classes:get(index: ci), issues: issues);
			ci++;
		});
	}

	## Inspects a class definition. Default implementation traverses all members.
	Function is checkClass(ClassInfo is classDef, Array of LintIssue is issues){
		:traverseClass(classDef: classDef, issues: issues);
	}

	## Default class member traversal.
	Function is traverseClass(ClassInfo is classDef, Array of LintIssue is issues){
		while([Int is mi: 0], { mi < classDef:members:length() }, {
			local Member is m: classDef:members:get(index: mi);
			match(on: m:kind, when: [
				MemberKind:METHOD: {
					while([Int is si: 0], { si < m:body:length() }, {
						:checkStatement(stmt: m:body:get(index: si), issues: issues);
						si++;
					});
				},
				MemberKind:CLASS: {
					:checkClass(classDef: m:nestedClass, issues: issues);
				},
				else: {}
			]);
			mi++;
		});
	}

	## Inspects a statement node. Default implementation traverses expressions.
	Function is checkStatement(Statement is stmt, Array of LintIssue is issues){
		:traverseStatement(stmt: stmt, issues: issues);
	}

	## Default statement traversal.
	Function is traverseStatement(Statement is stmt, Array of LintIssue is issues){
		match(on: stmt, when: [
			Statement:VarDecl: local Function(Array of String is modifiers, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit){
				if({ hasInit }, {
					:checkExpression(expr: initExpr, issues: issues);
				});
			},
			Statement:Assign: local Function(Expression is assignTarget, Expression is assignValue){
				:checkExpression(expr: assignTarget, issues: issues);
				:checkExpression(expr: assignValue, issues: issues);
			},
			Statement:Return: local Function(Expression is returnExpr, Boolean is hasReturnExpr){
				if({ hasReturnExpr }, {
					:checkExpression(expr: returnExpr, issues: issues);
				});
			},
			Statement:ClassDecl: local Function(ClassInfo is nestedClass){
				:checkClass(classDef: nestedClass, issues: issues);
			},
			Statement:Expr: local Function(Expression is exprStmt){
				:checkExpression(expr: exprStmt, issues: issues);
			},
			Statement:Forward: local Function([NamedArg] is forwardArgs){
				local Int is fi: 0;
				while({ fi < forwardArgs:length() }, {
					:checkExpression(expr: forwardArgs:get(index: fi):value, issues: issues);
					fi++;
				});
			}
		]);
	}

	## Inspects an expression node. Default implementation traverses child expressions.
	Function is checkExpression(Expression is expr, Array of LintIssue is issues){
		:traverseExpression(expr: expr, issues: issues);
	}

	## Default expression traversal.
	Function is traverseExpression(Expression is expr, Array of LintIssue is issues){
		match(on: expr, when: [
			Expression:Call: local Function(CallData is cd){
				:checkExpression(expr: cd:target, issues: issues);
				local Int is ai: 0;
				while({ ai < cd:args:length() }, {
					:checkExpression(expr: cd:args:get(index: ai):value, issues: issues);
					ai++;
				});
			},
			Expression:Binary: local Function(String is op, Expression is leftExpr, Expression is rightExpr){
				:checkExpression(expr: leftExpr, issues: issues);
				:checkExpression(expr: rightExpr, issues: issues);
			},
			Expression:Unary: local Function(String is op, Expression is operand){
				:checkExpression(expr: operand, issues: issues);
			},
			Expression:ArrayLit: local Function([Expression] is items){
				while([Int is ii: 0], { ii < items:length() }, {
					:checkExpression(expr: items:get(index: ii), issues: issues);
					ii++;
				});
			},
			Expression:MapLit: local Function([Expression] is keys, [Expression] is values){
				while([Int is ki: 0], { ki < keys:length() }, {
					:checkExpression(expr: keys:get(index: ki), issues: issues);
					ki++;
				});
				while([Int is vi: 0], { vi < values:length() }, {
					:checkExpression(expr: values:get(index: vi), issues: issues);
					vi++;
				});
			},
			Expression:Cast: local Function(Expression is target, String is targetType, [Expression] is args){
				:checkExpression(expr: target, issues: issues);
				while([Int is ai: 0], { ai < args:length() }, {
					:checkExpression(expr: args:get(index: ai), issues: issues);
					ai++;
				});
			},
			Expression:FieldAccess: local Function(Expression is target, String is field){
				:checkExpression(expr: target, issues: issues);
			},
			Expression:Index: local Function(Expression is target, Expression is index){
				:checkExpression(expr: target, issues: issues);
				:checkExpression(expr: index, issues: issues);
			},
			Expression:AnonFn: local Function(Type is returnType, [Parameter] is params, [Statement] is body){
				local Int is si: 0;
				while({ si < body:length() }, {
					:checkStatement(stmt: body:get(index: si), issues: issues);
					si++;
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
