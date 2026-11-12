#! Package examples:regression
#! SpecUnit sweep (from regression_method_resolution_test.spec): tracks
#! compiler regressions for instance-method resolution versus builtin
#! dispatch.

## Regression: user-defined methods must not be hijacked by runtime
## builtins.
##
## Compiler issue being guarded:
## BuiltinCallGenerator intercepted calls by METHOD NAME before instance
## dispatch. A user class declaring its own get(), length(), add(), set(),
## trim(), has(), or keys() method, invoked on a *statically typed*
## receiver, was compiled to the corresponding spec_* array/map builtin
## instead of the user method. For get() this was a hard gcc error
## (incompatible pointer types); for length() pre-GCC-14 toolchains it
## silently returned garbage.
##
## Status: PASSING (regression resolved; guarded by this file).

Class of SpecUnitTest is TestRegressionMethodResolution{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', Output],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	## Case 1 (the regression): a user class with its own get() method
	## must dispatch to the user method, not spec_array_get.
	Function is testUserGetDispatch(){
		local UserRecord is rec: UserRecord:init();
		local Int is got: rec:get();
		Assert:areEqualInt(42, got);
	}

	## Case 2 (the regression): a user length() with custom semantics
	## must dispatch to the user method, not spec_array_length.
	Function is testUserLengthDispatch(){
		local LogStore is store: LogStore:init();
		local Int is len: store:length();
		Assert:areEqualInt(7, len);
	}

	## Case 3 (control): identical shape with non-colliding method names
	## must keep working.
	Function is testNonCollidingMethodControl(){
		local UserRecord is rec2: UserRecord:init();
		local Int is safe: rec2:fetchIdentifier();
		Assert:areEqualInt(42, safe);
	}
}

## User class intentionally declaring a method named like an Array builtin.
Class is UserRecord{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];
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

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];
	local Int is maxEntries: 7;

	## Returns the configured capacity. Must NOT be lowered to spec_array_length.
	Function of Int is length(){
		return self:maxEntries;
	}
}
