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
			Expression:AnonFn: local Function(Type is _rt, Array of Parameter is params, Array of Statement is body){
				params:each(action: local Function(Parameter is p){
					:localNames:set(key: p:name, value: '1');
				});
				body:each(action: local Function(Statement is s){
					:collectStmtLocals(stmt: s);
				});
			},
			Expression:Call: local Function(CallData is cd){
				:collectExprLocals(expr: cd:target);
				cd:args:each(action: local Function(NamedArg is a){
					:collectExprLocals(expr: a:value);
				});
			},
			Expression:ArrayLit: local Function(Array of Expression is items){
				items:each(action: local Function(Expression is it){ :collectExprLocals(expr: it); });
			},
			Expression:MapLit: local Function(Array of Expression is ks, Array of Expression is vs){
				ks:each(action: local Function(Expression is k){ :collectExprLocals(expr: k); });
				vs:each(action: local Function(Expression is v){ :collectExprLocals(expr: v); });
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
			Expression:Cast: local Function(Expression is inner, String is _t, Array of Expression is args){
				:collectExprLocals(expr: inner);
				args:each(action: local Function(Expression is a){ :collectExprLocals(expr: a); });
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
		classDef:members:each(action: local Function(Member is m){
			if({ m:kind == MemberKind:METHOD }, {
				:localNames: Map:init();
				m:params:each(action: local Function(Parameter is p){
					:localNames:set(key: p:name, value: '1');
				});
				m:body:each(action: local Function(Statement is s){
					:collectStmtLocals(stmt: s);
				});
				m:body:each(action: local Function(Statement is s){
					:checkStatement(stmt: s, issues: issues);
				});
			});
			if({ m:kind == MemberKind:CLASS }, {
				:checkClass(classDef: m:nestedClass, issues: issues);
			});
			if({ m:kind == MemberKind:CLASS }, {
				:checkClass(classDef: m:nestedClass, issues: issues);
			});
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
