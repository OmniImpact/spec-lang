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
	DEBUG: "DBG",
	INFO: "INF"
}

Enum is Priority {
	LOW,
	HIGH
}

Class is RegressionEnumValueTest{

	replace Array of String is using: [
		base:io:Output
	];

	replace Function is init(Map of String to String is args){
		output:line("=== Regression: Backed Enum Values ===");

		# Case 1 (the regression): explicit Int backing value must survive codegen.
		local Int is okCode: HttpStatus:OK:value();
		if (okCode == 200) {
			output:line("[PASS] HttpStatus:OK:value() = 200");
		} else {
			output:line("[FAIL] HttpStatus:OK:value(): expected 200, got " . okCode . " (ordinal leaked instead of backing value)");
		}

		# Case 2 (the regression): second variant, non-zero declared value.
		local Int is nfCode: HttpStatus:NOT_FOUND:value();
		if (nfCode == 404) {
			output:line("[PASS] HttpStatus:NOT_FOUND:value() = 404");
		} else {
			output:line("[FAIL] HttpStatus:NOT_FOUND:value(): expected 404, got " . nfCode);
		}

		# Case 3 (control): variant name reflection.
		local String is okName: HttpStatus:OK:name();
		if (okName == "OK") {
			output:line("[PASS] HttpStatus:OK:name() = OK");
		} else {
			output:line("[FAIL] HttpStatus:OK:name(): expected OK, got " . okName);
		}

		# Case 4 (control): declaration-order ordinal is independent of backing value.
		local Int is nfOrdinal: HttpStatus:NOT_FOUND:ordinal();
		if (nfOrdinal == 1) {
			output:line("[PASS] HttpStatus:NOT_FOUND:ordinal() = 1");
		} else {
			output:line("[FAIL] HttpStatus:NOT_FOUND:ordinal(): expected 1, got " . nfOrdinal);
		}

		# Case 5 (control): string-backed enums already honor initializers.
		local LogLevel is lvl: LogLevel:INFO;
		local String is lvlValue: lvl:value();
		if (lvlValue == "INF") {
			output:line("[PASS] LogLevel:INFO:value() = INF (string-backed control)");
		} else {
			output:line("[FAIL] LogLevel:INFO:value(): expected INF, got " . lvlValue);
		}

		# Case 6 (control): unbacked enum ordinal.
		local Int is highOrdinal: Priority:HIGH:ordinal();
		if (highOrdinal == 1) {
			output:line("[PASS] Priority:HIGH:ordinal() = 1 (unbacked control)");
		} else {
			output:line("[FAIL] Priority:HIGH:ordinal(): expected 1, got " . highOrdinal);
		}

		output:line("=== End Backed Enum Value Regression ===");
	}

}
