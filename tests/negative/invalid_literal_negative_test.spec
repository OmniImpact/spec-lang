#! Package examples:regression
#! Tracks lexical diagnostics for numeric base literals.

## NEGATIVE test: this file MUST FAIL TO COMPILE. That is its correct behavior.
##
## Guarded behavior: invalid digits in base literals are lexical errors
## reported with file and line coordinates at load time.
##
## Required diagnostic:
## - Invalid digit in base-16 number literal.
##
## NOTE FOR RUNNERS: assert that this file fails to compile AND that the
## compiler output contains the diagnostic.

Class is InvalidHexLiteral{
	## 'g' is not a valid hex digit.
	local Int is mask: 0xGG;
}
