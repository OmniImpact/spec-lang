#! Package speclint:rules
#! Flags unnecessary leading `:` (`self:`) on fields and method calls when not shadowed by a local or parameter.

Class of LintRule is UnnecessarySelfColonRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	local Map of String to String is localNames: Map:init();

	replace Function of String is id(){
		return 'unnecessary-self-colon';
	}

	replace Function of String is description(){
		return 'Flags leading `:` on self fields and calls when no local variable or parameter shadows the name.';
	}

	replace Function of Boolean is isWarning(){
		return false;
	}

	local Function is collectStmtLocals(Statement is stmt){
		match(on: stmt, when: [
			Statement:VarDecl: local Function(Array of String is _m, Type is _t, String is varName, Expression is initExpr, Boolean is hasInit){
				:localNames:set(key: varName, value: '1');
				if({ hasInit }, { :collectExprLocals(expr: initExpr); });
			},
			Statement:Expr: local Function(Expression is e){
				:collectExprLocals(expr: e);
			},
			Statement:Assign: local Function(Expression is t, Expression is v){
				:collectExprLocals(expr: t);
				:collectExprLocals(expr: v);
			},
			Statement:Return: local Function(Expression is e, Boolean is hasE){
				if({ hasE }, { :collectExprLocals(expr: e); });
			}
		], default: {});
	}

	local Function is collectExprLocals(Expression is expr){
		match(on: expr, when: [
			Expression:AnonFn: local Function(Type is _rt, [Parameter] is params, [Statement] is body){
				local Int is pi: 0;
				while({ pi < params:length() }, {
					:localNames:set(key: params:get(index: pi):name, value: '1');
					pi++;
				});
				local Int is si: 0;
				while({ si < body:length() }, {
					:collectStmtLocals(stmt: body:get(index: si));
					si++;
				});
			},
			Expression:Call: local Function(CallData is cd){
				:collectExprLocals(expr: cd:target);
				local Int is ai: 0;
				while({ ai < cd:args:length() }, {
					:collectExprLocals(expr: cd:args:get(index: ai):value);
					ai++;
				});
			},
			Expression:ArrayLit: local Function([Expression] is items){
				while([Int is ii: 0], { ii < items:length() }, {
					:collectExprLocals(expr: items:get(index: ii));
					ii++;
				});
			},
			Expression:MapLit: local Function([Expression] is ks, [Expression] is vs){
				while([Int is ki: 0], { ki < ks:length() }, {
					:collectExprLocals(expr: ks:get(index: ki));
					ki++;
				});
				while([Int is vi: 0], { vi < vs:length() }, {
					:collectExprLocals(expr: vs:get(index: vi));
					vi++;
				});
			},
			Expression:Binary: local Function(String is _op, Expression is l, Expression is r){
				:collectExprLocals(expr: l);
				:collectExprLocals(expr: r);
			},
			Expression:Unary: local Function(String is _op, Expression is e){
				:collectExprLocals(expr: e);
			},
			Expression:FieldAccess: local Function(Expression is t, String is _f){
				:collectExprLocals(expr: t);
			},
			Expression:Cast: local Function(Expression is inner, String is _t, [Expression] is args){
				:collectExprLocals(expr: inner);
				while([Int is ai: 0], { ai < args:length() }, {
					:collectExprLocals(expr: args:get(index: ai));
					ai++;
				});
			}
		], default: {});
	}

	local Function of Boolean is isSelfIdent(Expression is expr){
		local Boolean is res: false;
		match(on: expr, when: [
			Expression:Ident: local Function(String is name){
				if({ name == ':' }, { res: true; });
			}
		], default: {});
		return res;
	}

	replace Function is checkClass(ClassInfo is classDef, Array of LintIssue is issues){
		while([Int is mi: 0], { mi < classDef:members:length() }, {
			local Member is m: classDef:members:get(index: mi);
			if({ m:kind == MemberKind:METHOD }, {
				:localNames: Map();
				while([Int is pi: 0], { pi < m:params:length() }, {
					:localNames:set(key: m:params:get(index: pi):name, value: '1');
					pi++;
				});
				while([Int is si: 0], { si < m:body:length() }, {
					:collectStmtLocals(stmt: m:body:get(index: si));
					si++;
				});
				while([Int is si: 0], { si < m:body:length() }, {
					:checkStatement(stmt: m:body:get(index: si), issues: issues);
					si++;
				});
			});
			if({ m:kind == MemberKind:CLASS }, {
				:checkClass(classDef: m:nestedClass, issues: issues);
			});
			mi++;
		});
	}

	replace Function is checkExpression(Expression is expr, Array of LintIssue is issues){
		match(on: expr, when: [
			Expression:FieldAccess: local Function(Expression is target, String is fieldName){
				if({ :isSelfIdent(expr: target) && !:localNames:has(key: fieldName) }, {
					issues:add(item: LintIssue:init(
						ruleId: :id(),
						line: expr:line,
						isWarning: :isWarning(),
						message: "Unnecessary leading ':' on ':" . fieldName . "'; no local or parameter shadows '" . fieldName . "'."
					));
				});
			},
			Expression:Path: local Function(Array of String is segs){
				if({ segs:length() >= 2 && segs:get(index: 0, default: '') == ':' }, {
					local String is first: segs:get(index: 1, default: '');
					if({ first != '' && !:localNames:has(key: first) }, {
						issues:add(item: LintIssue:init(
							ruleId: :id(),
							line: expr:line,
							isWarning: :isWarning(),
							message: "Unnecessary leading ':' on ':" . first . "'; no local or parameter shadows '" . first . "'."
						));
					});
				});
			},
			Expression:Call: local Function(CallData is cd){
				if({ !cd:isBareCall && :isSelfIdent(expr: cd:target) && cd:name != '' && !:localNames:has(key: cd:name) }, {
					issues:add(item: LintIssue:init(
						ruleId: :id(),
						line: expr:line,
						isWarning: :isWarning(),
						message: "Unnecessary leading ':' on ':" . cd:name . "(...)'; use '" . cd:name . "(...)' directly."
					));
				});
			}
		], default: {});
		:traverseExpression(expr: expr, issues: issues);
	}
}
