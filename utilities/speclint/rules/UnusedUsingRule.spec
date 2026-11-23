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
		local Int is pi: 0;
		while({ pi < t:params:length() }, {
			:markType(t: t:params:get(index: pi));
			pi++;
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
			Expression:Cast: local Function(Expression is inner, String is target, [Expression] is args){
				:refs:set(key: target, value: '1');
				:markExpr(expr: inner);
				while([Int is ai: 0], { ai < args:length() }, {
					:markExpr(expr: args:get(index: ai));
					ai++;
				});
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
				local Int is ai: 0;
				while({ ai < cd:args:length() }, {
					:markExpr(expr: cd:args:get(index: ai):value);
					ai++;
				});
			},
			Expression:Binary: local Function(String is _op, Expression is l, Expression is r){
				:markExpr(expr: l);
				:markExpr(expr: r);
			},
			Expression:Unary: local Function(String is _op, Expression is e){
				:markExpr(expr: e);
			},
			Expression:ArrayLit: local Function([Expression] is items){
				while([Int is ii: 0], { ii < items:length() }, {
					:markExpr(expr: items:get(index: ii));
					ii++;
				});
			},
			Expression:MapLit: local Function([Expression] is ks, [Expression] is vs){
				while([Int is ki: 0], { ki < ks:length() }, {
					:markExpr(expr: ks:get(index: ki));
					ki++;
				});
				while([Int is vi: 0], { vi < vs:length() }, {
					:markExpr(expr: vs:get(index: vi));
					vi++;
				});
			},
			Expression:AnonFn: local Function(Type is rt, [Parameter] is params, [Statement] is body){
				:markType(t: rt);
				local Int is pi: 0;
				while({ pi < params:length() }, {
					local Parameter is p: params:get(index: pi);
					:markType(t: p:paramType);
					if({ p:hasDefault }, { :markExpr(expr: p:defaultExpr); });
					pi++;
				});
				local Int is si: 0;
				while({ si < body:length() }, {
					:markStmt(stmt: body:get(index: si));
					si++;
				});
			}
		], default: {});
	}

	local Function is collectClassRefs(ClassInfo is cls){
		cls:baseClasses:each(action: local Function(String is bc){
			:refs:set(key: bc, value: '1');
		});
		while([Int is mi: 0], { mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:name != 'using' && m:name != 'namespace' }, {
				if({ m:kind == MemberKind:FIELD }, {
					:markType(t: m:memberType);
					if({ m:hasInit }, { :markExpr(expr: m:initExpr); });
				});
				if({ m:kind == MemberKind:METHOD }, {
					:markType(t: m:memberType);
					while([Int is pi: 0], { pi < m:params:length() }, {
						local Parameter is p: m:params:get(index: pi);
						:markType(t: p:paramType);
						if({ p:hasDefault }, { :markExpr(expr: p:defaultExpr); });
						pi++;
					});
					while([Int is si: 0], { si < m:body:length() }, {
						:markStmt(stmt: m:body:get(index: si));
						si++;
					});
				});
				if({ m:kind == MemberKind:CLASS }, {
					:collectClassRefs(cls: m:nestedClass);
				});
			});
			mi++;
		});
	}

	replace Function is checkClass(ClassInfo is classDef, Array of LintIssue is issues){
		:refs: Map();
		:collectClassRefs(cls: classDef);
		while([Int is mi: 0], { mi < classDef:members:length() }, {
			local Member is m: classDef:members:get(index: mi);
			if({ m:name == 'using' && m:hasInit }, {
				match(on: m:initExpr, when: [
					Expression:ArrayLit: local Function([Expression] is items){
						while([Int is ii: 0], { ii < items:length() }, {
							match(on: items:get(index: ii), when: [
								Expression:ArrayLit: local Function([Expression] is segs){
									while([Int is si: 0], { si < segs:length() }, {
										local Expression is seg: segs:get(index: si);
										match(on: seg, when: [
											Expression:Ident: local Function(String is name){
												if({ name != '' && !:refs:has(key: name) }, {
													issues:add(item: LintIssue(
														ruleId: :id(),
														line: seg:line,
														isWarning: :isWarning(),
														message: "Unused import '" . name . "' in 'using'."
													));
												});
											},
											Expression:UsingAs: local Function(String is className, [NamedArg] is _args){
												local String is alias: seg:usingAsAlias;
												if({ alias != '' && !:refs:has(key: alias) }, {
													issues:add(item: LintIssue(
														ruleId: :id(),
														line: seg:line,
														isWarning: :isWarning(),
														message: "Unused import alias '" . alias . "' for 'as " . className . "() is " . alias . "'."
													));
												});
											}
										], default: {});
										si++;
									});
								}
							], default: {});
							ii++;
						});
					}
				], default: {});
			});
			if({ m:kind == MemberKind:CLASS }, {
				:checkClass(classDef: m:nestedClass, issues: issues);
			});
			mi++;
		});
	}
}
