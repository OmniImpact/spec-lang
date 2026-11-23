#! Package speclint:rules
#! Suggests compact grouped syntax when importing several items separately from the same package.

Class of LintRule is CompactUsingRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', [LintRule, LintIssue]],
		['base', 'compiler', 'ast', [ClassInfo, Member, MemberKind, Expression, NamedArg]],
		['base', 'struct', [Array, Map]],
		['base', 'sys', as Conditional()]
	];

	replace Function of String is id(){
		'compact-using';
	}

	replace Function of String is description(){
		'Suggests compact grouped import syntax when importing 3 or more items separately from the same package.';
	}

	replace Function of Boolean is isWarning(){
		false;
	}

	replace Function is checkClass(ClassInfo is classDef, Array of LintIssue is issues){
		classDef:members:each(action: local Function(Member is m){
			if({ m:name == 'using' && m:hasInit }, {
				local Map of String to Int is pkgCounts: Map:init();
				local Map of String to Int is pkgFirstLine: Map:init();
				local Map of String to String is pkgDisplay: Map:init();
				local Array of String is pkgOrder: Array();

				match(on: m:initExpr, when: [
					Expression:ArrayLit: local Function(Array of Expression is items){
						items:each(action: local Function(Expression is item){
							match(on: item, when: [
								Expression:ArrayLit: local Function(Array of Expression is segs){
									local Array of String is nsSegs: Array();
									local Boolean is hasTarget: false;
									local Boolean is isWildcard: false;
									segs:each(action: local Function(Expression is seg){
										match(on: seg, when: [
											Expression:StringLit: local Function(String is s){
												if({ s == '*' }, {
													isWildcard: true;
												}, {
													nsSegs:add(item: s);
												});
											},
											Expression:Ident: local Function(String is _name){
												hasTarget: true;
											},
											Expression:UsingAs: local Function(String is _cn, [NamedArg] is _args){
												hasTarget: true;
											},
											Expression:ArrayLit: local Function(Array of Expression is _grp){
												hasTarget: true;
											}
										], default: {});
									});
									if({ nsSegs:length() > 0 && hasTarget && !isWildcard }, {
										local String is key: nsSegs:join(separator: ':');
										if({ !pkgCounts:has(key: key) }, {
											pkgOrder:add(item: key);
											pkgCounts:set(key: key, value: 1);
											pkgFirstLine:set(key: key, value: item:line);
											local Array of String is quoted: Array();
											nsSegs:each(action: local Function(String is ns){
												quoted:add(item: "'" . ns . "'");
											});
											pkgDisplay:set(key: key, value: quoted:join(separator: ', '));
										}, {
											pkgCounts:set(key: key, value: pkgCounts:get(key: key, default: 0) + 1);
										});
									});
								}
							], default: {});
						});
					}
				], default: {});

				pkgOrder:each(action: local Function(String is key){
					local Int is count: pkgCounts:get(key: key, default: 0);
					if({ count >= 3 }, {
						local Int is line: pkgFirstLine:get(key: key, default: m:line);
						local String is disp: pkgDisplay:getString(key: key, default: key);
						issues:add(item: LintIssue:init(
							ruleId: :id(),
							line: line,
							isWarning: :isWarning(),
							message: "Importing " . (count as String) . " items separately from '" . key . "'; use compact grouped syntax: [" . disp . ", [A, B, ...]]."
						));
					});
				});
			});
			if({ m:kind == MemberKind:CLASS }, {
				:checkClass(classDef: m:nestedClass, issues: issues);
			});
		});
	}
}
