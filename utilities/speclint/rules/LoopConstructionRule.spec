#! Package speclint:rules
#! Detects object instantiation inside loop bodies (E10 hoist advisory).

Class of LintRule is LoopConstructionRule{
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
		local Boolean is handledCall: false;
		match(on: expr, when: [
			Expression:Call: local Function(CallData is cd){
				handledCall: true;
				local String is method: cd:name;

				if({ method == 'init' && self:loopDepth > 0 && self:isClassTarget(target: cd:target) }, {
					issues:add(item: LintIssue:init(line: 0, isWarning: true, message: 'Construction inside a loop body: hoist the instance out of the loop (E10).'));
				});

				self:checkExpression(expr: cd:target, issues: issues);
				local Boolean is isLoop: self:isLoopCall(call: cd);
				cd:args:each(action: local Function(NamedArg is arg){
					local Boolean is isAnon: match(on: arg:value, when: [
						Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){ true; },
						else: { false; }
					], default: {});
					if({ isLoop && isAnon }, {
						local Int is savedDepth: self:loopDepth;
						self:loopDepth: self:loopDepth + 1;
						self:checkExpression(expr: arg:value, issues: issues);
						self:loopDepth: savedDepth;
					}, {
						self:checkExpression(expr: arg:value, issues: issues);
					});
				});
			}
		], default: {});

		if({ !handledCall }, {
			self:traverseExpression(expr: expr, issues: issues);
		});
	}

	## True when [call] is a loop driver call (Loops:*, Loop:*, or bare while/loop/repeat).
	Function of Boolean is isLoopCall(CallData is call){
		local String is targetName: self:extractTargetName(target: call:target);
		local String is method: call:name;
		return targetName == 'Loops' || targetName == 'Loop' || method == 'while' || method == 'loop' || method == 'repeat';
	}

	## True when [target] is an upper-case class name.
	Function of Boolean is isClassTarget(Expression is target){
		local String is name: self:extractTargetName(target: target);
		return self:isUpperName(name: name);
	}
}
