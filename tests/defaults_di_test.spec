#! Part IV IV.6: the declaration-side defaults are the
#! dependency-injection surface. A parameter with a default
#! (`Math2 is m : Math2:init()`) auto-instantiates when the caller omits
#! it, partially binds by name, or takes a full injection — and the
#! default's construction gates against the DECLARING class's imports:
#! the plain type-import form grants it, the as-form does not (N29).

Class is DiService{
	replace Array of Array of String is using: [
		['dimath', Math2],
		['base', 'sys', as Output()]
	];

	Math2 is dep;
	Int is scale: 1;

	replace Function is init(Math2 is m : Math2:init(), Int is scale : 2){
		self:dep: m;
		self:scale: scale;
	}

	Function of Int is compute(Int is n){
		return self:dep:half(n) * self:scale;
	}
}

Class is DefaultsDiTest{
	replace Array of Array of String is using: [
		['dimath', Math2],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		local Int is pass: 0;
		local Int is fail: 0;

		# Omitted arguments: both defaults auto-instantiate/apply.
		local DiService is a: DiService:init();
		if(check: { a:compute(10) == 10 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			line('[FAIL] omitted defaults: ' . (a:compute(10) as String));
		});

		# Partial binding by name: only scale overridden.
		local DiService is b: DiService:init(scale: 3);
		if(check: { b:compute(10) == 15 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			line('[FAIL] partial default: ' . (b:compute(10) as String));
		});

		# Full injection: the caller supplies the dependency.
		local DiService is c: DiService:init(m: Math2:init(), scale: 5);
		if(check: { c:compute(10) == 25 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			line('[FAIL] full injection: ' . (c:compute(10) as String));
		});

		if(check: { fail == 0 }, then: {
			line('[PASS] defaults DI: ' . (pass as String) . ' checks');
		}, else: {
			line('[FAIL] defaults DI: ' . (fail as String) . ' failures');
		});
	}
}
