#! Package examples:regression
#! Tracks compiler regressions for lambda (anonymous Function) capture lowering.

## Regression: closures must compile and capture correctly inside init scopes.
##
## Compiler issue being guarded:
## The ANON_FN capture machinery captures *every* local visible in the
## enclosing scope, including locals the lambda never references, and emits
## the captured variable's formatted type verbatim into C. For the Map-typed
## `args` parameter of init this produces `static Map:String:String* _cap_N_args;`
## which is not valid C, so any lambda stored as a Function value inside
## init(...) fails to compile with 4+ gcc errors.
##
## Expected outcome (once fixed):
## - This file compiles cleanly with the Spec compiler.
## - Lambdas capture the variables they reference (locals and self).
## - Lambdas do not reference-capture unused locals such as args.
## - All five checks print "[PASS]"; any "[FAIL]" or compile error is a regression.
##
## Status: PASSING (regression resolved; guarded by this file).
Class is RegressionClosureCaptureTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'io', as Output()]
	];

	## Field read by a closure through self capture.
	local Int is multiplier: 3;

	## Case 1: closure stored in a Function-typed local, capturing an Int local.
	##
	## This is the primary regression: init always has a Map-typed parameter
	## (args) in scope, which today poisons the capture set.
	replace Function is init(Map of String to String is args){
		Output:line('=== Regression: Closure Capture ===');

		# Case 1: capture of an Int local inside init.
		local Int is offset: 10;
		local Function of Int to Int is addOffset: local Function of Int(Int is x){
			return x + offset;
		};
		local Int is sum: addOffset(5);
		if (sum == 15) {
			Output:line('[PASS] init-scope Int capture: addOffset(5) = 15');
		} else {
			Output:line('[FAIL] init-scope Int capture: expected 15, got ' . sum);
		}

		# Case 2: capture of self (field access through the closure).
		local Function of Int to Int is timesThree: local Function of Int(Int is x){
			return x * self:multiplier;
		};
		local Int is product: timesThree(7);
		if (product == 21) {
			Output:line('[PASS] self capture: timesThree(7) = 21');
		} else {
			Output:line('[FAIL] self capture: expected 21, got ' . product);
		}

		# Case 3: capture of a String local.
		local String is prefix: 'v';
		local Function of String is tag: local Function of String(String is code){
			return prefix . code;
		};
		local String is tagged: tag('9');
		if (tagged == 'v9') {
			Output:line('[PASS] String capture: tag(9) = v9');
		} else {
			Output:line('[FAIL] String capture: expected v9, got ' . tagged);
		}

		# Case 4: higher-order use - Function value passed as a parameter.
		local Function of Int to Int is doubler: local Function of Int(Int is x){
			return x * 2;
		};
		local Int is applied: self:apply(fn: doubler, v: 5);
		if (applied == 10) {
			Output:line('[PASS] higher-order call: apply(doubler, 5) = 10');
		} else {
			Output:line('[FAIL] higher-order call: expected 10, got ' . applied);
		}

		# Case 5 (control): closure inside a helper method with no Map in scope.
		# This path already works today and must keep working.
		local Int is control: self:computeWithLocal();
		if (control == 124) {
			Output:line('[PASS] control helper-method capture: computeWithLocal() = 124');
		} else {
			Output:line('[FAIL] control helper-method capture: expected 124, got ' . control);
		}

		Output:line('=== End Closure Capture Regression ===');
	}

	## Higher-order helper: invokes a Function value with an argument.
	##
	## @param fn: Single-argument Int transform.
	## @param v: Value to transform.
	## @return: Result of invoking fn with v.
	local Function of Int is apply(Function of Int to Int is fn, Int is v){
		return fn(v);
	}

	## Control case: closure in a scope containing only primitive locals.
	##
	## @return: (6 * 4) + 100.
	local Function of Int is computeWithLocal(){
		local Int is factor: 4;
		local Int is base: 100;
		local Function of Int to Int is step: local Function of Int(Int is x){
			return x * factor + base;
		};
		return step(6);
	}

}
