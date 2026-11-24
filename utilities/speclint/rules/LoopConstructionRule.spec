#! Package speclint:rules
#! Detects object instantiation inside loop bodies (E10 hoist advisory).

Class of LintRule is LoopConstructionRule{
	replace [String] is namespace: ['speclint', 'rules'];

	replace [[String]] is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Int is loopDepth: 0;

	replace Function is init(){
		:loopDepth: 0;
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

	replace Function is checkExpression(Expression is expr, [LintIssue] is issues){
		local Boolean is handledCall: false;
		match(on: expr, when: [
			Expression:Call: local Function(CallData is cd){
				handledCall: true;
				local String is method: cd:name;

				if({ method == 'init' && :loopDepth > 0 && :isClassTarget(target: cd:target) }, {
					issues:push(item: LintIssue:init(line: 0, isWarning: true, message: 'Construction inside a loop body: hoist the instance out of the loop (E10).'));
				});

				:checkExpression(expr: cd:target, issues: issues);
				local Boolean is isLoop: :isLoopCall(call: cd);
				local Int is ai: 0;
				while({ ai < cd:args:length() }, {
					local NamedArg is arg: cd:args:get(index: ai);
					local Boolean is isAnon: match(on: arg:value, when: [
						Expression:AnonFn: local Function(Type is rt, [Parameter] is ps, [Statement] is bd){ true; },
						else: { false; }
					], default: {});
					if({ isLoop && isAnon }, {
						local Int is savedDepth: :loopDepth;
						:loopDepth: :loopDepth + 1;
						:checkExpression(expr: arg:value, issues: issues);
						:loopDepth: savedDepth;
					}, {
						:checkExpression(expr: arg:value, issues: issues);
					});
					ai++;
				});
			}
		], default: {});

		if({ !handledCall }, {
			:traverseExpression(expr: expr, issues: issues);
		});
	}

	## True when [call] is a loop driver call (Loops:*, Loop:*, or bare while/loop/repeat).
	Function of Boolean is isLoopCall(CallData is call){
		local String is targetName: :extractTargetName(target: call:target);
		local String is method: call:name;
		return targetName == 'Loops' || targetName == 'Loop' || method == 'while' || method == 'loop' || method == 'repeat';
	}

	## True when [target] is an upper-case class name.
	Function of Boolean is isClassTarget(Expression is target){
		local String is name: :extractTargetName(target: target);
		return :isUpperName(name: name);
	}
}
