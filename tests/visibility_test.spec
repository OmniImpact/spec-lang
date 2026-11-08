#! Package examples:regression
#! Tracks member visibility: public by default, local (private), contained (protected, final).

## Visibility semantics.
##
## Guarded behavior:
## - Unmarked members are public: callable externally and overridable.
## - `local` members are callable only within the declaring class.
## - `contained` members are callable from the declaring class and subclasses.
## - All checks print "[PASS]"; any "[FAIL]" is a regression.

Class is VisBase{

	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	## Public by default: overridable and externally callable.
	Function of Int is openValue(){
		return 10;
	}

	## Private: only VisBase internals may touch this.
	local Function of Int is secret(){
		return 20;
	}

	## Protected, final: subclasses may use it, never override it.
	contained Function of Int is helper(){
		return 30;
	}

	## Uses the private member internally.
	Function of Int is publicViaSecret(){
		return self:secret() + 1;
	}
}

Class of VisBase is VisChild{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', as Output()]
	];

	replace Function is init(){
	}

	## Contained members are visible here, including through references.
	Function of Int is viaHelper(){
		return self:helper() * 2;
	}

	Function of Int is viaHelperRef(VisBase is ref){
		return ref:helper();
	}

	replace Function of Int is openValue(){
		return 99;
	}
}

Class is VisibilityTest{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', Output],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Regression: Visibility ===');

		local VisBase is base: VisBase:init();
		local VisChild is child: VisChild:init();

		# Case 1: public members are callable externally and dispatch virtually.
		Conditional:branch(check: { base:openValue() == 10 && child:openValue() == 99 }, then: {
			Output:line('[PASS] public: external call + virtual override');
		}, otherwise: {
			Output:line('[FAIL] public: ' . base:openValue() . ', ' . child:openValue());
		});

		# Case 2: local members work inside the declaring class.
		Conditional:branch(check: { base:publicViaSecret() == 21 }, then: {
			Output:line('[PASS] local: internal use = 21');
		}, otherwise: {
			Output:line('[FAIL] local: ' . base:publicViaSecret());
		});

		# Case 3: contained members are visible to subclasses.
		Conditional:branch(check: { child:viaHelper() == 60 }, then: {
			Output:line('[PASS] contained: subclass access = 60');
		}, otherwise: {
			Output:line('[FAIL] contained: ' . child:viaHelper());
		});

		# Case 4: contained access through a reference, from within a subclass.
		Conditional:branch(check: { child:viaHelperRef(ref: child as VisBase) == 30 }, then: {
			Output:line('[PASS] contained: reference access from subclass = 30');
		}, otherwise: {
			Output:line('[FAIL] contained: ' . child:viaHelperRef(ref: child as VisBase));
		});

		Output:line('=== End Visibility ===');
	}

}
