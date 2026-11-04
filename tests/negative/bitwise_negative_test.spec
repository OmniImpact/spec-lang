#! Package examples:regression
#! Tracks type diagnostics for bitwise operators.

## NEGATIVE test: this file MUST FAIL TO COMPILE. That is its correct behavior.
##
## Guarded behavior:
## - Bitwise binary operators require Int operands.
## - Bitwise complement requires an Int operand.
##
## Required diagnostics:
## - Bitwise operator '&' requires Int operands (got 'String' and 'Int').
## - Bitwise complement '~' requires an Int operand (got 'Float').
##
## NOTE FOR RUNNERS: assert that this file fails to compile AND that the
## compiler output contains both diagnostics.

Class is BitwiseTypeMismatch{
	replace Function is init(Map of String to String is args){
		local Int is bad: 'oops' & 1;
		local Int is badComplement: ~2.5;
	}
}
