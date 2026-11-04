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

	replace Array of String is using: [
		base:io:Output
	];

	replace Function is init(Map of String to String is args){
		output:line("=== Regression: Visibility ===");

		local VisBase is base: VisBase:init();
		local VisChild is child: VisChild:init();

		# Case 1: public members are callable externally and dispatch virtually.
		if (base:openValue() == 10 && child:openValue() == 99) {
			output:line("[PASS] public: external call + virtual override");
		} else {
			output:line("[FAIL] public: " . base:openValue() . ", " . child:openValue());
		}

		# Case 2: local members work inside the declaring class.
		if (base:publicViaSecret() == 21) {
			output:line("[PASS] local: internal use = 21");
		} else {
			output:line("[FAIL] local: " . base:publicViaSecret());
		}

		# Case 3: contained members are visible to subclasses.
		if (child:viaHelper() == 60) {
			output:line("[PASS] contained: subclass access = 60");
		} else {
			output:line("[FAIL] contained: " . child:viaHelper());
		}

		# Case 4: contained access through a reference, from within a subclass.
		if (child:viaHelperRef(ref: child as VisBase) == 30) {
			output:line("[PASS] contained: reference access from subclass = 30");
		} else {
			output:line("[FAIL] contained: " . child:viaHelperRef(ref: child as VisBase));
		}

		output:line("=== End Visibility ===");
	}

}
