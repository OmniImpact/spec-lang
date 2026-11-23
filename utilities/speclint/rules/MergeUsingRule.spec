#! Package speclint:rules
#! Suggests `merge` instead of `replace` on `using` when manually importing `as Conditional()` or `as Loops()`.

Class of LintRule is MergeUsingRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', [LintRule, LintIssue]],
		['base', 'compiler', 'ast', [ClassInfo, Member, MemberKind, Expression, NamedArg]],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
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
			Expression:ArrayLit: local Function(Array of Expression is items){
				items:each(action: local Function(Expression is item){
					match(on: item, when: [
						Expression:ArrayLit: local Function(Array of Expression is segs){
							segs:each(action: local Function(Expression is seg){
								match(on: seg, when: [
									Expression:UsingAs: local Function(String is className, [NamedArg] is _args){
										if({ seg:usingAsAlias == '' && (className == 'Conditional' || className == 'Loops') }, {
											found: true;
										});
									},
									Expression:ArrayLit: local Function(Array of Expression is grpItems){
										grpItems:each(action: local Function(Expression is g){
											match(on: g, when: [
												Expression:UsingAs: local Function(String is gclassName, [NamedArg] is _gargs){
													if({ g:usingAsAlias == '' && (gclassName == 'Conditional' || gclassName == 'Loops') }, {
														found: true;
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
			}
		], default: {});
		found;
	}

	replace Function is checkClass(ClassInfo is classDef, Array of LintIssue is issues){
		if({ classDef:name != 'Class' && classDef:name != 'Conditional' && classDef:name != 'Loops' && classDef:baseClass != 'Enum' }, {
			classDef:members:each(action: local Function(Member is m){
				if({ m:name == 'using' && m:hasInit && m:hasModifier(kw: Keyword:REPLACE) && !m:hasModifier(kw: Keyword:MERGE) }, {
					if({ :hasDefaultControlFlowImport(initExpr: m:initExpr) }, {
						issues:add(item: LintIssue:init(
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
			});
		});
	}
}
