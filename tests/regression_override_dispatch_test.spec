#! Package examples:regression
#! Tracks compiler regressions for multi-level polymorphic dispatch.

## Regression: an inherited override must survive further subclassing.
##
## Compiler issue being guarded:
## Virtual dispatch is emulated by prepending strcmp(self->_type_name, "Sub")
## trampolines to every base-class method body. Only subclasses that declare
## the override themselves get a trampoline. With the chain
## Animal -> Dog (overrides speak) -> Puppy (does not), a call through an
## Animal-typed reference holding a Puppy checks "Puppy" (not an implementer),
## fails the "Dog" name comparison, and silently falls through to Animal's
## body. Dog's override is lost for all more-derived instances.
##
## Expected outcome (once fixed):
## - Every check prints "[PASS]".
## - speak() through a base-typed reference resolves to the most-derived
##   implementation in the chain (Puppy answers "woof", not Animal's "...").
##
## Status: PASSING (regression resolved; guarded by this file).
Class is RegressionOverrideDispatchTest{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'io', Output],
	];

	replace Function is init(Map of String to String is args){
		output:line('=== Regression: Multi-Level Override Dispatch ===');

		# Case 1 (control): one-level override through a base-typed reference.
		# This path already works today and must keep working.
		local Animal is dogAsAnimal: Dog:init();
		local String is dogSound: dogAsAnimal:speak();
		if (dogSound == 'woof') {
			output:line('[PASS] one-level override: Dog speaks woof');
		} else {
			output:line('[FAIL] one-level override: expected woof, got ' . dogSound);
		}

		# Case 2 (the regression): two-level override, no re-override in Puppy.
		local Animal is puppyAsAnimal: Puppy:init();
		local String is puppySound: puppyAsAnimal:speak();
		if (puppySound == 'woof') {
			output:line('[PASS] two-level override: Puppy inherits Dog\'s woof');
		} else {
			output:line('[FAIL] two-level override: expected woof, got \'' . puppySound . '\' (Base body leaked through)');
		}

		# Case 3 (the regression): three-level chain, override declared two levels up.
		local Animal is labAsAnimal: Lab:init();
		local String is labSound: labAsAnimal:speak();
		if (labSound == 'woof') {
			output:line('[PASS] three-level override: Lab inherits Dog\'s woof');
		} else {
			output:line('[FAIL] three-level override: expected woof, got \'' . labSound . '\'');
		}

		# Case 4: heterogeneous collection mixing all levels of the chain.
		# Every resident must dispatch to Dog's override via Animal's trampoline.
		local Array of Animal is kennel: [Dog:init(), Puppy:init(), Lab:init()];
		local Int is woofCount: kennel:count(predicate: local Function of Boolean(Animal is resident){
			return resident:speak() == 'woof';
		});
		if (woofCount == 3) {
			output:line('[PASS] heterogeneous dispatch: 3 of 3 kennel residents speak woof');
		} else {
			output:line('[FAIL] heterogeneous dispatch: expected 3 woofs, got ' . woofCount);
		}

		output:line('=== End Override Dispatch Regression ===');
	}

}

## Base class declaring the polymorphic contract.
Class is Animal{
	Function of String is speak(){
		return '...';
	}
}

## Mid-chain class whose override must remain visible to subclasses.
Class of Animal is Dog{
	replace Function of String is speak(){
		return 'woof';
	}
}

## Leaf class that does NOT re-declare speak; must inherit Dog's override.
Class of Dog is Puppy{
	local Boolean is isYoung: true;
}

## Deeper leaf class that does NOT re-declare speak.
Class of Dog is Lab{
	local String is breed: 'labrador';
}
