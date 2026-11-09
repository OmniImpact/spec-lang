#! N22 (Part IV V1): Function assignability is directional.
#! A void-typed closure cannot feed a Function of Boolean param — the
#! typed invocation reads garbage through the return-value cast.

Class is N22FunctionTypedParam{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		local Function is voidClosure: { Output:line('side effect'); };
		Conditional:if(check: voidClosure, then: {
			Output:line('branched');
		});
	}
}
