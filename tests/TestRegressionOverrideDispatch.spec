#! Package examples:regression
#! SpecUnit sweep (from regression_override_dispatch_test.spec): tracks
#! compiler regressions for multi-level polymorphic dispatch.

## Regression: an inherited override must survive further subclassing.
##
## Compiler issue being guarded:
## Virtual dispatch is emulated by prepending strcmp(self->_type_name, "Sub")
## trampolines to every base-class method body. Only subclasses that declare
## the override themselves get a trampoline. With the chain
## Animal -> Dog (overrides speak) -> Puppy (does not), a call through an
## Animal-typed reference holding a Puppy checked "Puppy" (not an
## implementer), failed the "Dog" name comparison, and silently fell
## through to Animal's body. Dog's override was lost for all more-derived
## instances.
##
## Status: PASSING (regression resolved; guarded by this file).

Class of SpecUnitTest is TestRegressionOverrideDispatch{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'sys', Output],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	## Case 1 (control): one-level override through a base-typed reference.
	Function is testOneLevelOverride(){
		local Animal is dogAsAnimal: Dog:init();
		local String is dogSound: dogAsAnimal:speak();
		Assert:areEqualString('woof', dogSound);
	}

	## Case 2 (the regression): two-level override, no re-override in Puppy.
	Function is testTwoLevelOverride(){
		local Animal is puppyAsAnimal: Puppy:init();
		local String is puppySound: puppyAsAnimal:speak();
		Assert:areEqualString('woof', puppySound);
	}

	## Case 3 (the regression): three-level chain, override declared two
	## levels up.
	Function is testThreeLevelOverride(){
		local Animal is labAsAnimal: Lab:init();
		local String is labSound: labAsAnimal:speak();
		Assert:areEqualString('woof', labSound);
	}

	## Case 4: heterogeneous collection mixing all levels of the chain —
	## every resident must dispatch to Dog's override via Animal's
	## trampoline.
	Function is testHeterogeneousCollectionDispatch(){
		local Array of Animal is kennel: [Dog:init(), Puppy:init(), Lab:init()];
		local Int is woofCount: kennel:count(predicate: local Function of Boolean(Animal is resident){
			return resident:speak() == 'woof';
		});
		Assert:areEqualInt(3, woofCount);
	}
}

## Base class declaring the polymorphic contract.
Class is Animal{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];
	Function of String is speak(){
		return '...';
	}
}

## Mid-chain class whose override must remain visible to subclasses.
Class of Animal is Dog{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];
	replace Function of String is speak(){
		return 'woof';
	}
}

## Leaf class that does NOT re-declare speak; must inherit Dog's override.
Class of Dog is Puppy{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];
	local Boolean is isYoung: true;
}

## Deeper leaf class that does NOT re-declare speak.
Class of Dog is Lab{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];
	local String is breed: 'labrador';
}
