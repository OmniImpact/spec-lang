#! Package speclint:rules
#! Suggests `ClassName(...)` shorthand instead of explicit `ClassName:init(...)`.

Class of LintRule is InitShorthandRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'struct', Array],
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

	replace Function is checkClass(ClassInfo is classDef, Array of LintIssue is issues){
		local String is saved: :curClassName;
		:curClassName: classDef:name;
		classDef:members:each(action: local Function(Member is m){
			if({ m:kind == MemberKind:METHOD }, {
				if({ m:name != 'init' }, {
					local Int is si: 0;
					while({ si < m:body:length() }, {
						:checkStatement(stmt: m:body:get(index: si), issues: issues);
						si++;
					});
				});
			});
			if({ m:kind == MemberKind:CLASS }, {
				:checkClass(classDef: m:nestedClass, issues: issues);
			});
		});
		:curClassName: saved;
	}

	replace Function is checkExpression(Expression is expr, Array of LintIssue is issues){
		match(on: expr, when: [
			Expression:Call: local Function(CallData is cd){
				if({ cd:name == 'init' }, {
					match(on: cd:target, when: [
						Expression:Ident: local Function(String is tname){
							if({ tname != ':' && tname != :curClassName }, {
								issues:add(item: LintIssue:init(
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
