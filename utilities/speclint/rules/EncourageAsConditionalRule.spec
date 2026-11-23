#! Package speclint:rules
#! Flags explicit calls to Conditional methods, encouraging the 'as Conditional()' import.

Class of LintRule is EncourageAsConditionalRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	local String is currentClass: '';

	replace Function is init(){
		:currentClass: '';
	}

	replace Function of String is id(){
		return 'encourage-as-conditional';
	}

	replace Function of String is description(){
		return 'Flags qualified calls to Conditional methods, encouraging bare syntax with \'as Conditional()\'.';
	}

	replace Function of Boolean is isWarning(){
		return false;
	}

	replace Function is checkClass(ClassInfo is classDef, [LintIssue] is issues){
		:currentClass: classDef:name;
		# Exclude Conditional definition itself and compiler-synthesized Enums
		if({ :currentClass != 'Conditional' && classDef:baseClass != 'Enum' }, {
			:traverseClass(classDef: classDef, issues: issues);
		});
	}

	replace Function is checkExpression(Expression is expr, [LintIssue] is issues){
		match(on: expr, when: [
			Expression:Call: local Function(CallData is cd){
				local String is targetName: :extractTargetName(target: cd:target);
				if({ targetName == 'Conditional' }, {
					local String is msg: 'Direct call to \'Conditional:' . cd:name . '\': import \'as Conditional()\' in using and use bare \'' . cd:name . '(...)\'.';
					issues:push(item: LintIssue:init(line: expr:line, isWarning: false, message: msg));
				});
			}
		], default: {});

		:traverseExpression(expr: expr, issues: issues);
	}
}
