#! Package speclint:rules
#! Advises on random method calls regarding min/max parameters.

Class of LintRule is MathRandomRule{
	replace [String] is namespace: ['speclint', 'rules'];

	replace [[String]] is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	replace Function of String is id(){
		return 'math-random';
	}

	replace Function of String is description(){
		return 'Advises on method call math:random providing or omitting optional min/max range parameters.';
	}

	replace Function of Boolean is isWarning(){
		return false;
	}

	replace Function is checkExpression(Expression is expr, [LintIssue] is issues){
		match(on: expr, when: [
			Expression:Call: local Function(CallData is cd){
				if({ cd:name == 'random' }, {
					local String is msg: 'Method call \'math:random\' provides optional min/max range parameters.';
					if({ cd:args:length() == 0 }, {
						msg: 'Method call \'math:random\' omits optional min/max parameters (using default [0.0, 1.0)).';
					});
					issues:push(item: LintIssue:init(line: 0, isWarning: false, message: msg));
				});
			}
		], default: {});

		:traverseExpression(expr: expr, issues: issues);
	}
}
