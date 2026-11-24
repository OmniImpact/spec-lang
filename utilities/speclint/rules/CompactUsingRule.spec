#! Package speclint:rules
#! Suggests compact grouped syntax when importing several items separately from the same package.

Class of LintRule is CompactUsingRule{
	replace [String] is namespace: ['speclint', 'rules'];

	replace [[String]] is using: [
		['speclint', [LintRule, LintIssue]],
		['base', 'compiler', 'ast', [ClassInfo, Member, MemberKind, Expression, NamedArg]],
		['base', 'struct', [Array, Map]],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
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

	replace Function is checkClass(ClassInfo is classDef, [LintIssue] is issues){
		times(count: classDef:members:length(), worker: local Function(Int is mi){
			local Member is m: classDef:members:get(index: mi);
			if({ m:name == 'using' && m:hasInit }, {
				local Map of String to Int is pkgCounts: Map:init();
				local Map of String to Int is pkgFirstLine: Map:init();
				local Map of String to String is pkgDisplay: Map:init();
				local [String] is pkgOrder: [];

				match(on: m:initExpr, when: [
					Expression:ArrayLit: local Function([Expression] is items){
						times(count: items:length(), worker: local Function(Int is ii){
							local Expression is item: items:get(index: ii);
							match(on: item, when: [
								Expression:ArrayLit: local Function([Expression] is segs){
									local [String] is nsSegs: [];
									local Boolean is hasTarget: false;
									local Boolean is isWildcard: false;
									times(count: segs:length(), worker: local Function(Int is si){
										match(on: segs:get(index: si), when: [
											Expression:StringLit: local Function(String is s){
												if({ s == '*' }, {
													isWildcard: true;
												}, {
													nsSegs:push(item: s);
												});
											},
											Expression:Ident: local Function(String is _name){
												hasTarget: true;
											},
											Expression:UsingAs: local Function(String is _cn, [NamedArg] is _args){
												hasTarget: true;
											},
											Expression:ArrayLit: local Function([Expression] is _grp){
												hasTarget: true;
											}
										], default: {});
									});
									if({ nsSegs:length() > 0 && hasTarget && !isWildcard }, {
										local String is key: '';
										times(count: nsSegs:length(), worker: local Function(Int is ni){
											if({ ni > 0 }, { key: key . ':'; });
											key: key . nsSegs:get(index: ni);
										});
										if({ !pkgCounts:has(key: key) }, {
											pkgOrder:push(item: key);
											pkgCounts:set(key: key, value: 1);
											pkgFirstLine:set(key: key, value: item:line);
											local String is dispStr: '';
											times(count: nsSegs:length(), worker: local Function(Int is ni){
												if({ ni > 0 }, { dispStr: dispStr . ', '; });
												dispStr: dispStr . "'" . nsSegs:get(index: ni) . "'";
											});
											pkgDisplay:set(key: key, value: dispStr);
										}, {
											pkgCounts:set(key: key, value: pkgCounts:get(key: key, default: 0) + 1);
										});
									});
								}
							], default: {});
						});
					}
				], default: {});

				each(list: pkgOrder, action: local Function(String is key){
					local Int is count: pkgCounts:get(key: key, default: 0);
					if({ count >= 3 }, {
						local Int is line: pkgFirstLine:get(key: key, default: m:line);
						local String is disp: pkgDisplay:getString(key: key, default: key);
						issues:push(item: LintIssue:init(
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
