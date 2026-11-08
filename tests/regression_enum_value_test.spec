#! Package examples:regression
#! Tracks compiler regressions for explicitly backed Enum values.

## Regression: Enum of Int must honor explicit variant values.
##
## Compiler issue being guarded:
## DeclarationGenerator emits sequential ordinal indices for every non-
## string-backed enum (`HttpStatus_OK = 0, HttpStatus_NOT_FOUND = 1, ...`)
## even when the parser recorded an explicit initializer (`OK: 200`).
## For Enum of Int, value() returns the raw C enum constant, so
## HttpStatus:OK:value() yields 0 instead of the declared 200. Only the
## string-backed path honors initializers today.
##
## Expected outcome (once fixed):
## - value() on an Enum of Int returns the declared backing value.
## - Cases 1 and 2 print "[PASS]"; control cases 3-5 must keep printing "[PASS]".
##
## Status: PASSING (regression resolved; guarded by this file).
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

Class is RegressionEnumValueTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Regression: Backed Enum Values ===');

		# Case 1 (the regression): explicit Int backing value must survive codegen.
		local Int is okCode: HttpStatus:OK:value();
		Conditional:branch(check: { okCode == 200 }, then: {
			Output:line('[PASS] HttpStatus:OK:value() = 200');
		}, otherwise: {
			Output:line('[FAIL] HttpStatus:OK:value(): expected 200, got ' . okCode . ' (ordinal leaked instead of backing value)');
		});

		# Case 2 (the regression): second variant, non-zero declared value.
		local Int is nfCode: HttpStatus:NOT_FOUND:value();
		Conditional:branch(check: { nfCode == 404 }, then: {
			Output:line('[PASS] HttpStatus:NOT_FOUND:value() = 404');
		}, otherwise: {
			Output:line('[FAIL] HttpStatus:NOT_FOUND:value(): expected 404, got ' . nfCode);
		});

		# Case 3 (control): variant name reflection.
		local String is okName: HttpStatus:OK:name();
		Conditional:branch(check: { okName == 'OK' }, then: {
			Output:line('[PASS] HttpStatus:OK:name() = OK');
		}, otherwise: {
			Output:line('[FAIL] HttpStatus:OK:name(): expected OK, got ' . okName);
		});

		# Case 4 (control): declaration-order ordinal is independent of backing value.
		local Int is nfOrdinal: HttpStatus:NOT_FOUND:ordinal();
		Conditional:branch(check: { nfOrdinal == 1 }, then: {
			Output:line('[PASS] HttpStatus:NOT_FOUND:ordinal() = 1');
		}, otherwise: {
			Output:line('[FAIL] HttpStatus:NOT_FOUND:ordinal(): expected 1, got ' . nfOrdinal);
		});

		# Case 5 (control): string-backed enums already honor initializers.
		local LogLevel is lvl: LogLevel:INFO;
		local String is lvlValue: lvl:value();
		Conditional:branch(check: { lvlValue == 'INF' }, then: {
			Output:line('[PASS] LogLevel:INFO:value() = INF (string-backed control)');
		}, otherwise: {
			Output:line('[FAIL] LogLevel:INFO:value(): expected INF, got ' . lvlValue);
		});

		# Case 6 (control): unbacked enum ordinal.
		local Int is highOrdinal: Priority:HIGH:ordinal();
		Conditional:branch(check: { highOrdinal == 1 }, then: {
			Output:line('[PASS] Priority:HIGH:ordinal() = 1 (unbacked control)');
		}, otherwise: {
			Output:line('[FAIL] Priority:HIGH:ordinal(): expected 1, got ' . highOrdinal);
		});

		Output:line('=== End Backed Enum Value Regression ===');
	}

}
