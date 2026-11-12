#! Package speclint:rules
#! Detects object instantiation inside loop bodies (E10 hoist advisory).

Class of LintRule is LoopConstructionRule{
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

	local Int is loopDepth: 0;

	replace Function is init(){
		self:loopDepth: 0;
	}

	replace Function of String is id(){
		return 'loop-construction';
	}

	replace Function of String is description(){
		return 'Warns when an instance is constructed inside a loop body (hoist advisory E10).';
	}

	replace Function of Boolean is isWarning(){
		return true;
	}

	replace Function is checkExpression(Expression is expr, Array of LintIssue is issues){
		if({ expr:kind == ExpressionKind:CALL }, {
			local String is method: expr:methodName;
			local Array of NamedArg is args: expr:methodArgs;

			if({ method == 'init' && self:loopDepth > 0 && self:isClassTarget(target: expr:methodTarget) }, {
				issues:add(item: LintIssue:init(line: 0, isWarning: true, message: 'Construction inside a loop body: hoist the instance out of the loop (E10).'));
			});

			self:checkExpression(expr: expr:methodTarget, issues: issues);
			local Boolean is isLoop: self:isLoopCall(expr: expr);
			args:each(action: local Function(NamedArg is arg){
				if({ isLoop && arg:value:kind == ExpressionKind:ANON_FN }, {
					local Int is savedDepth: self:loopDepth;
					self:loopDepth: self:loopDepth + 1;
					self:checkExpression(expr: arg:value, issues: issues);
					self:loopDepth: savedDepth;
				}, {
					self:checkExpression(expr: arg:value, issues: issues);
				});
			});
			return;
		});

		self:traverseExpression(expr: expr, issues: issues);
	}

	## True when [expr] is a loop driver call (Loops:*, Loop:*, or bare while/loop/repeat).
	Function of Boolean is isLoopCall(Expression is expr){
		local String is targetName: self:extractTargetName(target: expr:methodTarget);
		local String is method: expr:methodName;
		return targetName == 'Loops' || targetName == 'Loop' || method == 'while' || method == 'loop' || method == 'repeat';
	}

	## True when [target] is an upper-case class name.
	Function of Boolean is isClassTarget(Expression is target){
		local String is name: self:extractTargetName(target: target);
		return self:isUpperName(name: name);
	}
}
