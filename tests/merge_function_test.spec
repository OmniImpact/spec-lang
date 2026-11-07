#! Package examples:regression
#! Tracks merge-on-Function: delegation to the parent implementation.

## Function merge: `(args...)` forwards to the nearest parent implementation.
##
## Guarded behavior:
## - Forward with adapted arguments (constants and derived expressions).
## - Value-returning parents: the forward's value is returned implicitly.
## - Partial forwards pass named arguments; unnamed parent params fall back
##   to their declared defaults.
## - Statements may precede the forward in the merge method body.
## - Delegation chains compose (Child2 -> Child1 -> Base).
## - merge init chains parent constructors.
## - Merge overrides dispatch virtually: base-typed and subclass-typed calls
##   both reach the forward (unified semantics under vtable dispatch).
## - All checks print "[PASS]"; any "[FAIL]" is a regression.

Class is LoggerBase{
	local String is tag;

	replace Function is init(String is tag){
		self:tag: tag;
	}

	Function of Int is add(Int is a, Int is b){
		return a + b;
	}

	Function of Int is scale(Int is n, Int is factor: 2){
		return n * factor;
	}
}

Class of LoggerBase is ChildLogger{

	# Adapted forward: derive arguments before delegating.
	merge Function of Int is add(Int is a, Int is b){
		local Int is bumped: a + 100;
		(bumped, b);
	}

	# Partial named forward: parent default supplies factor.
	merge Function of Int is scale(Int is n, Int is factor: 2){
		(n: n);
	}
}

Class of ChildLogger is GrandLogger{

	# Chained forward: delegates to ChildLogger, which delegates to LoggerBase.
	merge Function of Int is add(Int is a, Int is b){
		(a, b);
	}

	# merge init: chains the parent constructor.
	merge Function is init(String is tag){
		(tag);
	}
}

Class is MergeFunctionTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
	];

	replace Function is init(Map of String to String is args){
		output:line('=== Regression: Function Merge ===');

		local GrandLogger is gl: GrandLogger:init(tag: 'grand');

		# Case 1: chained forward with adaptation (1+100)+2 = 103.
		local Int is added: gl:add(a: 1, b: 2);
		if (added == 103) {
			output:line('[PASS] chained forward: add(1, 2) = 103');
		} else {
			output:line('[FAIL] chained forward: expected 103, got ' . added);
		}

		# Case 2: partial named forward with parent default (7 * 2 = 14).
		local Int is scaled: gl:scale(n: 7);
		if (scaled == 14) {
			output:line('[PASS] partial named forward: scale(7) = 14');
		} else {
			output:line('[FAIL] partial named forward: expected 14, got ' . scaled);
		}

		# Case 3: merge init chained the parent constructor.
		if (gl:tag == 'grand') {
			output:line('[PASS] merge init chain: tag = grand');
		} else {
			output:line('[FAIL] merge init chain: expected grand, got ' . gl:tag);
		}

		# Case 4: merge init can also adapt arguments.
		local ChildLogger is cl: ChildLogger:init(tag: 'x');
		# ChildLogger inherits LoggerBase:init unchanged; tag round-trips.
		if (cl:tag == 'x') {
			output:line('[PASS] inherited init: tag = x');
		} else {
			output:line('[FAIL] inherited init: expected x, got ' . cl:tag);
		}

		# Case 5: merge overrides are virtual - base-typed call applies the
		# forward identically to the subclass-typed call (no recursion).
		local LoggerBase is asBase: gl;
		local Int is baseResult: asBase:add(a: 1, b: 2);
		if (baseResult == 103) {
			output:line('[PASS] base-typed call: add(1, 2) = 103 (virtual forward)');
		} else {
			output:line('[FAIL] base-typed call: expected 103, got ' . baseResult);
		}

		# Case 6: subclass-typed call goes through the merge forward.
		local ChildLogger is asChild: GrandLogger:init(tag: 'c');
		local Int is childResult: asChild:add(a: 1, b: 2);
		if (childResult == 103) {
			output:line('[PASS] subclass-typed call: add(1, 2) = 103 (forward applied)');
		} else {
			output:line('[FAIL] subclass-typed call: expected 103, got ' . childResult);
		}

		output:line('=== End Function Merge Regression ===');
	}

}
