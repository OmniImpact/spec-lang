#! Package examples:regression
#! SpecUnit sweep (from regression_enum_value_test.spec): tracks compiler
#! regressions for explicitly backed Enum values.

## Regression: Enum of Int must honor explicit variant values.
##
## Compiler issue being guarded:
## DeclarationGenerator emitted sequential ordinal indices for every non-
## string-backed enum (`HttpStatus_OK = 0, HttpStatus_NOT_FOUND = 1, ...`)
## even when the parser recorded an explicit initializer (`OK: 200`).
## For Enum of Int, value() returns the raw C enum constant, so
## HttpStatus:OK:value() yielded 0 instead of the declared 200. Only the
## string-backed path honored initializers before the fix.
##
## Status: PASSING (regression resolved; guarded by this file).

Class of SpecUnitTest is TestRegressionEnumValue{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', Output],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	## The regression: explicit Int backing values must survive codegen.
	Function is testBackedIntEnumValues(){
		local Int is okCode: HttpStatus:OK:value();
		Assert:areEqualInt(200, okCode);

		local Int is nfCode: HttpStatus:NOT_FOUND:value();
		Assert:areEqualInt(404, nfCode);
	}

	## Controls: variant name reflection, declaration-order ordinal
	## independent of the backing value, and unbacked enum ordinal.
	Function is testNameAndOrdinalControls(){
		local String is okName: HttpStatus:OK:name();
		Assert:areEqualString('OK', okName);

		local Int is nfOrdinal: HttpStatus:NOT_FOUND:ordinal();
		Assert:areEqualInt(1, nfOrdinal);

		local Int is highOrdinal: Priority:HIGH:ordinal();
		Assert:areEqualInt(1, highOrdinal);
	}

	## Control: string-backed enums already honor initializers.
	Function is testStringBackedEnumValue(){
		local LogLevel is lvl: LogLevel:INFO;
		local String is lvlValue: lvl:value();
		Assert:areEqualString('INF', lvlValue);
	}
}

Enum of Int is HttpStatus {
	OK: 200,
	NOT_FOUND: 404
}

Enum of String is LogLevel {
	DEBUG: 'DBG',
	INFO: 'INF'
}

Enum is Priority {
	LOW,
	HIGH
}
