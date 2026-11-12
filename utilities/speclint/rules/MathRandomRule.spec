#! Package speclint:rules
#! Advises on random method calls regarding min/max parameters.

Class of LintRule is MathRandomRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
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

	replace Function is checkExpression(Expression is expr, Array of LintIssue is issues){
		if({ expr:kind == ExpressionKind:CALL && expr:methodName == 'random' }, {
			local String is msg: 'Method call \'math:random\' provides optional min/max range parameters.';
			if({ expr:methodArgs:length() == 0 }, {
				msg: 'Method call \'math:random\' omits optional min/max parameters (using default [0.0, 1.0)).';
			});
			issues:add(item: LintIssue:init(line: 0, isWarning: false, message: msg));
		});

		self:traverseExpression(expr: expr, issues: issues);
	}
}
