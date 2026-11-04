#! Package examples:regression
#! Tracks cast validation diagnostics for the `as` operator.

## NEGATIVE test: this file MUST FAIL TO COMPILE. That is its correct behavior.
##
## Guarded behavior:
## - Casting between unrelated classes is rejected.
## - Casting to an enum is rejected (construct a variant instead).
## - Base casts on non-Int/String operands are rejected.
## - Unknown cast targets are rejected.
##
## Required diagnostics:
## - Cannot cast 'Cat' to unrelated class 'Dog'.
## - Cannot cast to enum 'Color'; construct a variant instead.
## - Cast 'as Hex' requires an Int or String operand (got 'Boolean').
## - Unknown cast target 'Hexadecimal'.
##
## NOTE FOR RUNNERS: assert that this file fails to compile AND that the
## compiler output contains all five diagnostics.

Enum is Color {
	RED
}

Class is Dog{
}

Class is Cat{
}

Class is AsNegativeTest{

	replace Function is init(Map of String to String is args){
		local Cat is cat: Cat:init();
		local Dog is dog: cat as Dog;
		local Color is c: dog as Color;
		local Int is fromBool: true as Hex;
		local Int is unknown: 5 as Hexadecimal;
	}
}
