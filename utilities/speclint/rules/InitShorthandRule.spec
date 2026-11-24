#! Package speclint:rules
#! Suggests `ClassName(...)` shorthand instead of explicit `ClassName:init(...)`.

Class of LintRule is InitShorthandRule{
	replace [String] is namespace: ['speclint', 'rules'];

	replace [[String]] is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'struct', Array],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	local String is curClassName: '';

	replace Function of String is id(){
		return 'init-shorthand';
	}

	replace Function of String is description(){
		return 'Suggests `ClassName(...)` constructor shorthand instead of `ClassName:init(...)`.';
	}

	replace Function of Boolean is isWarning(){
		return false;
	}

	replace Function is checkClass(ClassInfo is classDef, [LintIssue] is issues){
		local String is saved: :curClassName;
		:curClassName: classDef:name;
		while([Int is mi: 0], { mi < classDef:members:length() }, {
			local Member is m: classDef:members:get(index: mi);
			if({ m:kind == MemberKind:METHOD }, {
				if({ m:name != 'init' }, {
					while([Int is si: 0], { si < m:body:length() }, {
						:checkStatement(stmt: m:body:get(index: si), issues: issues);
						si++;
					});
				});
			});
			if({ m:kind == MemberKind:CLASS }, {
				:checkClass(classDef: m:nestedClass, issues: issues);
			});
			mi++;
		});
		:curClassName: saved;
	}

	replace Function is checkExpression(Expression is expr, [LintIssue] is issues){
		match(on: expr, when: [
			Expression:Call: local Function(CallData is cd){
				if({ cd:name == 'init' }, {
					match(on: cd:target, when: [
						Expression:Ident: local Function(String is tname){
							if({ tname != ':' && tname != :curClassName }, {
								issues:push(item: LintIssue:init(
									ruleId: :id(),
									line: expr:line,
									isWarning: :isWarning(),
									message: "Use constructor shorthand '" . tname . "(...)' instead of '" . tname . ":init(...)'."
								));
							});
						}
					], default: {});
				});
			}
		], default: {});
		:traverseExpression(expr: expr, issues: issues);
	}
}
