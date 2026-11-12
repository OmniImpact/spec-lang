#! Package speclint:rules
#! Flags explicit calls to Conditional methods, encouraging the 'as Conditional()' import.

Class of LintRule is EncourageAsConditionalRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	local String is currentClass: '';

	replace Function is init(){
		self:currentClass: '';
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

	replace Function is checkClass(ClassInfo is classDef, Array of LintIssue is issues){
		self:currentClass: classDef:name;
		# Exclude Conditional definition itself and compiler-synthesized Enums
		if({ self:currentClass != 'Conditional' && classDef:baseClass != 'Enum' }, {
			self:traverseClass(classDef: classDef, issues: issues);
		});
	}

	replace Function is checkExpression(Expression is expr, Array of LintIssue is issues){
		if({ expr:kind == ExpressionKind:CALL }, {
			local String is targetName: self:extractTargetName(target: expr:methodTarget);
			if({ targetName == 'Conditional' }, {
				local String is method: expr:methodName;
				local String is msg: 'Direct call to \'Conditional:' . method . '\': import \'as Conditional()\' in using and use bare \'' . method . '(...)\'.';
				issues:add(item: LintIssue:init(line: expr:line, isWarning: false, message: msg));
			});
		});

		self:traverseExpression(expr: expr, issues: issues);
	}
}
