#! SpecUnit sweep (from regression_closure_capture_test.spec).
#! Package examples:regression — tracks compiler regressions for lambda
#! (anonymous Function) capture lowering.
#!
## Regression guarded: the ANON_FN capture machinery captures *every*
## local visible in the enclosing scope, including locals the lambda
## never references, and emits the captured variable's formatted type
## verbatim into C. For a Map-typed variable this produces
## `static Map:String:String* _cap_N_args;` — not valid C — so a lambda
## stored as a Function value in a scope with a Map-typed `args` visible
## fails to compile. The first test recreates that scope shape (an
## unused Map-typed local named args) around a stored lambda.
#!
## Expected outcome: the file compiles cleanly; lambdas capture the
## variables they reference (locals and self); lambdas do not
## reference-capture unused locals such as args. Status: PASSING.

Class of SpecUnitTest is TestRegressionClosureCapture{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', Output],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()],
		['base', 'struct', Map]
	];

	## Field read by a closure through self capture.
	local Int is multiplier: 3;

	## Case 1: closure stored in a Function-typed local, capturing an
	## Int local — with the original hazard shape in scope: an unused
	## Map-typed local named args that the lambda never references.
	Function is testInitScopeIntCapture(){
		local Map of String to String is args;
		local Int is offset: 10;
		local Function of Int to Int is addOffset: local Function of Int(Int is x){
			return x + offset;
		};
		local Int is sum: addOffset(5);
		Assert:areEqualInt(15, sum);
	}

	## Case 2: capture of self (field access through the closure).
	Function is testSelfCapture(){
		local Function of Int to Int is timesThree: local Function of Int(Int is x){
			return x * self:multiplier;
		};
		local Int is product: timesThree(7);
		Assert:areEqualInt(21, product);
	}

	## Case 3: capture of a String local.
	Function is testStringCapture(){
		local String is prefix: 'v';
		local Function of String is tag: local Function of String(String is code){
			return prefix . code;
		};
		local String is tagged: tag('9');
		Assert:areEqualString('v9', tagged);
	}

	## Case 4: higher-order use - Function value passed as a parameter.
	Function is testHigherOrderCall(){
		local Function of Int to Int is doubler: local Function of Int(Int is x){
			return x * 2;
		};
		local Int is applied: self:apply(fn: doubler, v: 5);
		Assert:areEqualInt(10, applied);
	}

	## Case 5 (control): closure inside a helper method with no Map in
	## scope. This path already works and must keep working.
	Function is testControlHelperCapture(){
		local Int is control: self:computeWithLocal();
		Assert:areEqualInt(124, control);
	}

	## Higher-order helper: invokes a Function value with an argument.
	local Function of Int is apply(Function of Int to Int is fn, Int is v){
		return fn(v);
	}

	## Control case: closure in a scope containing only primitive locals.
	## Returns (6 * 4) + 100.
	local Function of Int is computeWithLocal(){
		local Int is factor: 4;
		local Int is base: 100;
		local Function of Int to Int is step: local Function of Int(Int is x){
			return x * factor + base;
		};
		return step(6);
	}
}
