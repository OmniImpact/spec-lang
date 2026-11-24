#! Package speclint:rules
#! Suggests `merge` instead of `replace` on `using` when manually importing `as Conditional()` or `as Loops()`.

Class of LintRule is MergeUsingRule{
	replace [String] is namespace: ['speclint', 'rules'];

	replace [[String]] is using: [
		['speclint', [LintRule, LintIssue]],
		['base', 'compiler', 'ast', [ClassInfo, Member, MemberKind, Expression, NamedArg]],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	replace Function of String is id(){
		'merge-using';
	}

	replace Function of String is description(){
		'Suggests using `merge` instead of `replace` on `using` when a subclass of Class manually imports `as Conditional()` or `as Loops()`.';
	}

	replace Function of Boolean is isWarning(){
		false;
	}

	local Function of Boolean is hasDefaultControlFlowImport(Expression is initExpr){
		local Boolean is found: false;
		match(on: initExpr, when: [
			Expression:ArrayLit: local Function([Expression] is items){
				while([Int is ii: 0], { !found && ii < items:length() }, {
					match(on: items:get(index: ii), when: [
						Expression:ArrayLit: local Function([Expression] is segs){
							while([Int is si: 0], { !found && si < segs:length() }, {
								local Expression is seg: segs:get(index: si);
								match(on: seg, when: [
									Expression:UsingAs: local Function(String is className, [NamedArg] is _args){
										if({ seg:usingAsAlias == '' && (className == 'Conditional' || className == 'Loops') }, {
											found: true;
										});
									},
									Expression:ArrayLit: local Function([Expression] is grpItems){
										while([Int is gi: 0], { !found && gi < grpItems:length() }, {
											local Expression is g: grpItems:get(index: gi);
											match(on: g, when: [
												Expression:UsingAs: local Function(String is gclassName, [NamedArg] is _gargs){
													if({ g:usingAsAlias == '' && (gclassName == 'Conditional' || gclassName == 'Loops') }, {
														found: true;
													});
												}
											], default: {});
											gi++;
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
		found;
	}

	replace Function is checkClass(ClassInfo is classDef, [LintIssue] is issues){
		if({ classDef:name != 'Class' && classDef:name != 'Conditional' && classDef:name != 'Loops' && classDef:baseClass != 'Enum' }, {
			while([Int is mi: 0], { mi < classDef:members:length() }, {
				local Member is m: classDef:members:get(index: mi);
				if({ m:name == 'using' && m:hasInit && m:hasModifier(kw: Keyword:REPLACE) && !m:hasModifier(kw: Keyword:MERGE) }, {
					if({ :hasDefaultControlFlowImport(initExpr: m:initExpr) }, {
						issues:push(item: LintIssue(
							ruleId: :id(),
							line: m:line,
							isWarning: :isWarning(),
							message: "Use 'merge' instead of 'replace' on 'using' to inherit 'as Conditional()' and 'as Loops()' from Class automatically."
						));
					});
				});
				if({ m:kind == MemberKind:CLASS }, {
					:checkClass(classDef: m:nestedClass, issues: issues);
				});
				mi++;
			});
		});
	}
}
