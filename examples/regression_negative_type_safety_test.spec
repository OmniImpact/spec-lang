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
## with a file:line diagnostic for each of the five violations below, and the
## backend C compiler must never be invoked.
##
## Required diagnostics (one per class):
## - NarrowFloatField:        Int field cannot be initialized with a Float (3.7).
## - ArrayElementMismatch:    Array of String is not assignable to Array of Int.
## - MapValueMismatch:        Map of String to String is not assignable to Map of String to Int.
## - UndefinedIdentifier:     'untrackedTotal' is not a declared variable or field.
## - NonBooleanConditionControl: if condition must be a Boolean.
## - UnassignedFieldRead:     field 'label' is read before being definitely assigned.
##
## The fifth class is a positive control: its diagnostic ALREADY fires today.
## Today's known status: ONLY the control error is reported; violations 1-4
## compile silently. A check run is green only when all six errors appear.
##
## NOTE FOR RUNNERS: assert that this file fails to compile AND that the
## compiler output contains all six diagnostics above.

class NarrowFloatField{
	## Violation 1: Float literal silently narrowed into an Int field.
	local Int is samples: 3.7;
}

class ArrayElementMismatch{
	## Violation 2: String elements silently accepted by an Array of Int field.
	local Array of Int is flags: ["on", "off"];
}

class MapValueMismatch{
	## Violation 3: String values silently accepted by a Map of String to Int field.
	local Map of String to Int is ages: ["ana": "ten"];
}

class UndefinedIdentifier{
	## Violation 4: typoed identifier silently inferred as Any.
	replace local Function is init(Map of String to String is args){
		local Int is total: untrackedTotal + 1;
	}
}

class NonBooleanConditionControl{
	## Control (already caught today): condition must be a Boolean.
	replace local Function is init(Map of String to String is args){
		if (1) {
			local Int is unused: 0;
		}
	}
}

class UnassignedFieldRead{
	replace local Array of String is using: [
		base:io:Output
	];

	## Violation 6: the Never Null standard guarantees this does not compile,
	## yet today the field is emitted as a C NULL pointer and the read
	## silently produces "(null)" (or a crash) at runtime.
	local String is label;

	replace local Function is init(Map of String to String is args){
		output:line(self:label);
	}
}
