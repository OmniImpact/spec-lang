#! Package speclint:rules
#! Flags `using` imports (and `as ... is alias` bindings) that are never referenced in the class.

Class of LintRule is UnusedUsingRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Type],
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

	local Map of String to String is refs: Map:init();

	replace Function of String is id(){
		return 'unused-using';
	}

	replace Function of String is description(){
		return 'Flags unused class imports and unused `as ... is alias` bindings in `using`.';
	}

	replace Function of Boolean is isWarning(){
		return true;
	}

	local Function is markType(Type is t){
		if({ t:name != '' }, {
			:refs:set(key: t:name, value: '1');
		});
		t:params:each(action: local Function(Type is sub){
			:markType(t: sub);
		});
	}

	local Function is markStmt(Statement is stmt){
		match(on: stmt, when: [
			Statement:VarDecl: local Function(Array of String is _m, Type is t, String is _vn, Expression is initExpr, Boolean is hasInit){
				:markType(t: t);
				if({ hasInit }, { :markExpr(expr: initExpr); });
			},
			Statement:Expr: local Function(Expression is e){
				:markExpr(expr: e);
			},
			Statement:Assign: local Function(Expression is t, Expression is v){
				:markExpr(expr: t);
				:markExpr(expr: v);
			},
			Statement:Return: local Function(Expression is e, Boolean is hasE){
				if({ hasE }, { :markExpr(expr: e); });
			},
			Statement:ClassDecl: local Function(ClassInfo is nc){
				:collectClassRefs(cls: nc);
			}
		], default: {});
	}

	local Function is markExpr(Expression is expr){
		match(on: expr, when: [
			Expression:Ident: local Function(String is name){
				if({ name != '' && name != ':' }, {
					:refs:set(key: name, value: '1');
				});
			},
			Expression:Path: local Function(Array of String is segs){
				segs:each(action: local Function(String is s){
					if({ s != '' && s != ':' }, {
						:refs:set(key: s, value: '1');
					});
				});
			},
			Expression:Cast: local Function(Expression is inner, String is target, Array of Expression is args){
				:refs:set(key: target, value: '1');
				:markExpr(expr: inner);
				args:each(action: local Function(Expression is a){ :markExpr(expr: a); });
			},
			Expression:FieldAccess: local Function(Expression is target, String is _f){
				:markExpr(expr: target);
			},
			Expression:Index: local Function(Expression is target, Expression is idx){
				:markExpr(expr: target);
				:markExpr(expr: idx);
			},
			Expression:Call: local Function(CallData is cd){
				:markExpr(expr: cd:target);
				if({ cd:name != '' }, {
					:refs:set(key: cd:name, value: '1');
				});
				cd:args:each(action: local Function(NamedArg is a){
					:markExpr(expr: a:value);
				});
			},
			Expression:Binary: local Function(String is _op, Expression is l, Expression is r){
				:markExpr(expr: l);
				:markExpr(expr: r);
			},
			Expression:Unary: local Function(String is _op, Expression is e){
				:markExpr(expr: e);
			},
			Expression:ArrayLit: local Function(Array of Expression is items){
				items:each(action: local Function(Expression is it){ :markExpr(expr: it); });
			},
			Expression:MapLit: local Function(Array of Expression is ks, Array of Expression is vs){
				ks:each(action: local Function(Expression is k){ :markExpr(expr: k); });
				vs:each(action: local Function(Expression is v){ :markExpr(expr: v); });
			},
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is params, Array of Statement is body){
				:markType(t: rt);
				params:each(action: local Function(Parameter is p){
					:markType(t: p:paramType);
					if({ p:hasDefault }, { :markExpr(expr: p:defaultExpr); });
				});
				body:each(action: local Function(Statement is s){ :markStmt(stmt: s); });
			}
		], default: {});
	}

	local Function is collectClassRefs(ClassInfo is cls){
		cls:baseClasses:each(action: local Function(String is bc){
			:refs:set(key: bc, value: '1');
		});
		cls:members:each(action: local Function(Member is m){
			if({ m:name == 'using' || m:name == 'namespace' }, { return; });
			if({ m:kind == MemberKind:FIELD }, {
				:markType(t: m:memberType);
				if({ m:hasInit }, { :markExpr(expr: m:initExpr); });
			});
			if({ m:kind == MemberKind:METHOD }, {
				:markType(t: m:memberType);
				m:params:each(action: local Function(Parameter is p){
					:markType(t: p:paramType);
					if({ p:hasDefault }, { :markExpr(expr: p:defaultExpr); });
				});
				m:body:each(action: local Function(Statement is s){ :markStmt(stmt: s); });
			});
			if({ m:kind == MemberKind:CLASS }, {
				:collectClassRefs(cls: m:nestedClass);
			});
		});
	}

	replace Function is checkClass(ClassInfo is classDef, Array of LintIssue is issues){
		:refs: Map:init();
		:collectClassRefs(cls: classDef);
		classDef:members:each(action: local Function(Member is m){
			if({ m:name == 'using' && m:hasInit }, {
				match(on: m:initExpr, when: [
					Expression:ArrayLit: local Function(Array of Expression is items){
						items:each(action: local Function(Expression is item){
							match(on: item, when: [
								Expression:ArrayLit: local Function(Array of Expression is segs){
									segs:each(action: local Function(Expression is seg){
										match(on: seg, when: [
											Expression:Ident: local Function(String is name){
												if({ name != '' && !:refs:has(key: name) }, {
													issues:add(item: LintIssue:init(
														ruleId: :id(),
														line: seg:line,
														isWarning: :isWarning(),
														message: "Unused import '" . name . "' in 'using'."
													));
												});
											},
											Expression:UsingAs: local Function(String is className, Array of NamedArg is _args){
												local String is alias: seg:usingAsAlias;
												if({ alias != '' && !:refs:has(key: alias) }, {
													issues:add(item: LintIssue:init(
														ruleId: :id(),
														line: seg:line,
														isWarning: :isWarning(),
														message: "Unused import alias '" . alias . "' for 'as " . className . "() is " . alias . "'."
													));
												});
											}
										], default: {});
									});
								}
							], default: {});
						});
					}
				], default: {});
			});
			if({ m:kind == MemberKind:CLASS }, {
				:checkClass(classDef: m:nestedClass, issues: issues);
			});
		});
	}
}
