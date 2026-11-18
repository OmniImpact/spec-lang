#! Package speclint:rules
#! Advises on getString method calls with explicit default parameter.

Class of LintRule is GetStringDefaultRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	replace Function of String is id(){
		return 'get-string-default';
	}

	replace Function of String is description(){
		return 'Advises on method call getString providing optional parameter default.';
	}

	replace Function of Boolean is isWarning(){
		return false;
	}

	replace Function is checkExpression(Expression is expr, Array of LintIssue is issues){
		match(on: expr, when: [
			Expression:Call: local Function(CallData is cd){
				if({ cd:name == 'getString' }, {
					local Boolean is hasDefault: false;
					cd:args:each(action: local Function(NamedArg is arg){
						if({ arg:name == 'default' }, {
							hasDefault: true;
						});
					});
					if({ hasDefault }, {
						issues:add(item: LintIssue:init(line: 0, isWarning: false, message: 'Method call \'getString\' provides optional parameter \'default\'.'));
					});
				});
			}
		], default: {});

		:traverseExpression(expr: expr, issues: issues);
	}
}
