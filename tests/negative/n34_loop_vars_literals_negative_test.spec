#! specunit: negative
#! expect: requires inline literal closures

#! N34 (the runtime constructs landing): the [vars] loop forms scope
#! their closures at the call site — compile-time only. A closure held
#! as a variable was built before the loop's parameters existed and
#! cannot capture them; the combination must be rejected instead of
#! running with free identifiers.

Class is N34LoopVarsLiterals{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		local Function of Boolean is cond: local Function of Boolean(){ return true; };
		local Function is body: local Function(){ Output:line('x'); };
		Loops([Int is i: 0], evaluate: cond, iterate: body);
	}
}
