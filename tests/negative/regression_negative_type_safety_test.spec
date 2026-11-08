#! Package examples:regression
#! Tracks compiler regressions for strict type-checking diagnostics.

## NEGATIVE test: this file MUST FAIL TO COMPILE. That is its correct behavior.
##
## Compiler issues being guarded:
## The TypeChecker currently accepts several programs it should reject:
## 1. Int <- Float implicit narrowing: isAssignable allows Int and Float in
##    BOTH directions, so 3.7 silently truncates into a long long.
## 2. Cross-element container assignability: any "Array:X" is assignable to
##    any "Array:Y" (and Map likewise), so String elements sneak into an
##    Array of Int and corrupt memory at runtime via (void*)(intptr_t) casts.
## 3. Undefined identifiers: an unknown name infers type "Any", which is
##    assignable to everything, so a typoed variable reaches gcc as an
##    undeclared C identifier with no Spec-level file:line diagnostic.
##
## Required outcome (once fixed): compilation must abort during type checking
## with a file:line diagnostic for each of the eight violations below, and the
## backend C compiler must never be invoked.
##
## Required diagnostics (one per class):
## - NarrowFloatField:        Int field cannot be initialized with a Float (3.7).
## - ArrayElementMismatch:    Array of String is not assignable to Array of Int.
## - MapValueMismatch:        Map of String to String is not assignable to Map of String to Int.
## - UndefinedIdentifier:     'untrackedTotal' is not a declared variable or field.
## - NonBooleanConditionControl: a check closure must yield a Boolean
##   (the Function-of-Boolean enforcement).
## - UnassignedFieldRead:     field 'label' is read before being definitely assigned.
## - CallArgumentMismatch:    String argument passed to an Int parameter.
## - IncompleteWhenBranches:  'when' over an enum missing a variant with no else arm.
##
## The fifth class is a positive control: its diagnostic ALREADY fires today.
## A check run is green only when all eight errors appear.
##
## NOTE FOR RUNNERS: assert that this file fails to compile AND that the
## compiler output contains all eight diagnostics above.

Enum is TransportMode {
	CAR,
	BIKE
}

Class is NarrowFloatField{

	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];
	## Violation 1: Float literal silently narrowed into an Int field.
	local Int is samples: 3.7;
}

Class is ArrayElementMismatch{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', as Output()]
	];
	## Violation 2: String elements silently accepted by an Array of Int field.
	local Array of Int is flags: ['on', 'off'];
}

Class is MapValueMismatch{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', as Output()]
	];
	## Violation 3: String values silently accepted by a Map of String to Int field.
	local Map of String to Int is ages: ['ana': 'ten'];
}

Class is UndefinedIdentifier{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', as Output()]
	];
	## Violation 4: typoed identifier silently inferred as Any.
	replace Function is init(Map of String to String is args){
		local Int is total: untrackedTotal + 1;
	}
}

Class is NonBooleanConditionControl{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', as Output()]
	];
	## Control (already caught today): condition must be a Boolean.
	replace Function is init(Map of String to String is args){
		Conditional:if(check: { 1 }, then: {
			local Int is unused: 0;
		});
	}
}

Class is UnassignedFieldRead{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', Output],
		['base', 'io', as Output()]
	];

	## Violation 6: the Never Null standard guarantees this does not compile,
	## yet today the field is emitted as a C NULL pointer and the read
	## silently produces "(null)" (or a crash) at runtime.
	local String is label;

	replace Function is init(Map of String to String is args){
		Output:line(self:label);
	}
}

Class is CallArgumentMismatch{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', as Output()]
	];
	## Violation 7: call-site argument types were not checked, so a String
	## argument silently reached an Int parameter and was truncated at the
	## C level with no diagnostic.
	replace Function of Int is double(Int is n){
		return n * 2;
	}

	replace Function is init(Map of String to String is args){
		local Int is result: self:double(n: 'not-a-number');
	}
}

Class is IncompleteWhenBranches{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', as Output()]
	];
	## Violation 8: 'when' over enum TransportMode covers only CAR and omits
	## BIKE with no else arm. Exhaustiveness must be enforced at compile time.
	replace Function of String is describe(TransportMode is mode){
		return when (mode) {
			is CAR: 'drives';
		};
	}
}
