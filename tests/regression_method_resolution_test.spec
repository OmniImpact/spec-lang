#! Package examples:regression
#! Tracks compiler regressions for instance-method resolution versus builtin dispatch.

## Regression: user-defined methods must not be hijacked by runtime builtins.
##
## Compiler issue being guarded:
## BuiltinCallGenerator intercepts calls by METHOD NAME before instance
## dispatch. A user class declaring its own get(), length(), add(), set(),
## trim(), has(), or keys() method, invoked on a *statically typed* receiver,
## is compiled to the corresponding spec_* array/map builtin instead of the
## user method. For get() this is a hard gcc error (incompatible pointer
## types); for length() pre-GCC-14 toolchains it silently returns garbage.
##
## Expected outcome (once fixed):
## - This file compiles cleanly; the user methods are invoked.
## - All three checks print "[PASS]"; any "[FAIL]" or compile error is a regression.
##
## Status: PASSING (regression resolved; guarded by this file).
Class is RegressionMethodResolutionTest{

	replace Array of String is using: [
		base:io:Output
	];

	replace Function is init(Map of String to String is args){
		output:line("=== Regression: Method Resolution vs Builtins ===");

		# Case 1: user class with its own get() method (hard compile error today).
		local UserRecord is rec: UserRecord:init();
		local Int is got: rec:get();
		if (got == 42) {
			output:line("[PASS] user get() dispatch: rec:get() = 42");
		} else {
			output:line("[FAIL] user get() dispatch: expected 42, got " . got);
		}

		# Case 2: user class whose length() has custom semantics.
		# The builtin hijack silently returns the wrong number on some toolchains.
		local LogStore is store: LogStore:init();
		local Int is len: store:length();
		if (len == 7) {
			output:line("[PASS] user length() dispatch: store:length() = 7");
		} else {
			output:line("[FAIL] user length() dispatch: expected 7, got " . len);
		}

		# Case 3 (control): identical shape with non-colliding method names.
		# This path already works today and must keep working.
		local UserRecord is rec2: UserRecord:init();
		local Int is safe: rec2:fetchIdentifier();
		if (safe == 42) {
			output:line("[PASS] control non-colliding method: fetchIdentifier() = 42");
		} else {
			output:line("[FAIL] control non-colliding method: expected 42, got " . safe);
		}

		output:line("=== End Method Resolution Regression ===");
	}

}

## User class intentionally declaring a method named like an Array builtin.
Class is UserRecord{
	local Int is identifier: 42;

	## Returns the record identifier. Must NOT be lowered to spec_array_get.
	Function of Int is get(){
		return self:identifier;
	}

	## Control accessor with a non-colliding name.
	Function of Int is fetchIdentifier(){
		return self:identifier;
	}
}

## User class intentionally declaring a method named like an Array builtin.
Class is LogStore{
	local Int is maxEntries: 7;

	## Returns the configured capacity. Must NOT be lowered to spec_array_length.
	Function of Int is length(){
		return self:maxEntries;
	}
}
