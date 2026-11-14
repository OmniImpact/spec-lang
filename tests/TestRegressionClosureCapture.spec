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
		['base', 'struct', Map],
		['base', 'sys', as Loops()]
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

	## Case 6: Multiple runtime closures sharing a mutable counter in Loops:while.
	Function is testSharedMutableCounter(){
		local Int is count: 0;
		local Function of Boolean is cond: local Function of Boolean(){
			return count < 5;
		};
		local Function is step: local Function(){
			count: count + 1;
		};
		Loops:while(evaluate: cond, iteration: step);
		Assert:areEqualInt(5, count);
	}

	## Case 7: Closure mutation observed by caller.
	Function is testClosureMutationObservedByCaller(){
		local Int is x: 10;
		local Function is mutate: local Function(){
			x: 42;
		};
		mutate();
		Assert:areEqualInt(42, x);
	}

	## Case 8: Caller mutation observed by closure.
	Function is testCallerMutationObservedByClosure(){
		local Int is x: 10;
		local Function of Int is readX: local Function of Int(){
			return x;
		};
		Assert:areEqualInt(10, readX());
		x: 99;
		Assert:areEqualInt(99, readX());
	}

	## Case 9: Escaping closure accumulator state retention.
	local Function of Function:Int is makeAccumulator(Int is start){
		local Int is total: start;
		return local Function of Int(Int is delta){
			total: total + delta;
			return total;
		};
	}

	Function is testEscapingClosure(){
		local Function of Int to Int is acc: self:makeAccumulator(start: 100);
		Assert:areEqualInt(110, acc(10));
		Assert:areEqualInt(135, acc(25));
		Assert:areEqualInt(130, acc(-5));
	}

	## Case 10: Multiple closures reading and modifying a shared String.
	Function is testMultipleClosuresSharedString(){
		local String is msg: 'hello';
		local Function is appendWorld: local Function(){
			msg: msg . ' world';
		};
		local Function is appendExclamation: local Function(){
			msg: msg . '!';
		};
		appendWorld();
		appendExclamation();
		Assert:areEqualString('hello world!', msg);
	}

	## Case 11: Loops:repeat with a plain local counter.
	Function is testRepeatWithPlainLocal(){
		local Int is tally: 0;
		Loops:repeat(count: 7, worker: local Function(){
			tally: tally + 3;
		});
		Assert:areEqualInt(21, tally);
	}
	## Case 12: Local mutated inside an inlined closure in a VarDecl initializer
	## and captured by a runtime closure.
	Function is testMutationInVarDeclInitializerCapturedByClosure(){
		local Int is count: 0;
		local Int is initial: if({ true }, {
			count: count + 10;
			100
		}, {
			0
		});
		local Function of Int is getCount: local Function of Int(){
			return count;
		};
		Assert:areEqualInt(100, initial);
		Assert:areEqualInt(10, getCount());
		count: count + 5;
		Assert:areEqualInt(15, getCount());
	}

	## Case 13: Local mutated inside an inlined closure on an Assign RHS
	## and captured by a runtime closure.
	Function is testMutationInAssignValueCapturedByClosure(){
		local Int is total: 1;
		local Int is dummy: 0;
		dummy: if({ true }, {
			total: total * 5;
			50
		}, {
			0
		});
		local Function of Int is getTotal: local Function of Int(){
			return total;
		};
		Assert:areEqualInt(50, dummy);
		Assert:areEqualInt(5, getTotal());
		total: total + 3;
		Assert:areEqualInt(8, getTotal());
	}
}
