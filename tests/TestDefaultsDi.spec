#! SpecUnit sweep (from defaults_di_test.spec): Part IV IV.6 — the
#! declaration-side defaults are the dependency-injection surface. A
#! parameter with a default auto-instantiates when the caller omits
#! it, partially binds by name, or takes a full injection.

Class of SpecUnitTest is TestDefaultsDi{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['dimath', Math2]
	];

	## Omitted arguments: both defaults auto-instantiate/apply.
	Function is testOmittedDefaults(){
		local DiService is a: DiService:init();
		Assert:areEqualInt(10, a:compute(10));
	}

	## Partial binding by name: only scale overridden.
	Function is testPartialBindingByName(){
		local DiService is b: DiService:init(scale: 3);
		Assert:areEqualInt(15, b:compute(10));
	}

	## Full injection: the caller supplies the dependency.
	Function is testFullInjection(){
		local DiService is c: DiService:init(m: Math2:init(), scale: 5);
		Assert:areEqualInt(25, c:compute(10));
	}
}

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
