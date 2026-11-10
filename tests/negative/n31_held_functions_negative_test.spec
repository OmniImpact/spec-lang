#! N31 (PLAN-ENUM Stage 1): the held-function strictness walls.
#! - an instance receiver never reaches a held function
#! - bare references to held functions are not supported (call form only)
#! - held functions cannot be root-contract members (no vtable)
#! - held functions do not overload
#! - a held function body has no instance (no self)
#! - a held function cannot call a non-held sibling through the class name

Class is N31HeldFn{
	namespace: ['test'];

	held Int is scale: 2;

	held Function of Int is twice(Int is n){
		return n * N31HeldFn:scale;
	}

	# 3. root-contract members take a receiver; held functions never do.
	held Function of String is toString(){
		return 'bad';
	}

	# 4. held functions do not overload: one name, one signature.
	held Function of Int is twice(Int is a, Int is b){
		return a + b;
	}

	# 5. a held function body has no instance.
	held Function of Int is usesSelf(){
		return self:scale;
	}

	# 6. the instance method `plain` is not reachable through the
	#    class name — held dispatch does not rescue it.
	Function of Int is plain(){
		return N31HeldFn:plain();
	}
}

Class is N31HeldFnUser{
	namespace: ['test'];

	replace Function is init(N31HeldFn is w){
		# 1. an instance receiver never reaches a held function.
		Output:line(text: (w:twice(n: 3) as String));
		# 2. bare references to held functions are not supported.
		local Int is fnRef: N31HeldFn:twice;
		Output:line(text: (fnRef as String));
	}

	replace Array of Array of String is using: [
		['base', 'io', as Output()]
	];
}
