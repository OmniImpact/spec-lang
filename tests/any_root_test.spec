#! Package examples:regression
#! Tracks the root class `Any`: implicit inheritance, Stringable composition,
#! default rendering, and the typeName builtin.

## Root class lattice semantics.
##
## Guarded behavior:
## - Every class without parents implicitly extends `Any` (via Stringable).
## - `Any.toString()` renders the declaring class name via `typeName`.
## - `typeName` builtin reports the runtime class of any instance.
## - `as Any` accepts any instance (upcast to the root).
## - All checks print "[PASS]"; any "[FAIL]" is a regression.

Class is RootProbe{
	local Int is id: 5;

	replace Function is init(Int is id){
		self:id: id;
	}
}

Class is AnyRootTest{

	replace Array of String is using: [
		base:io:Output
	];

	replace Function is init(Map of String to String is args){
		output:line('=== Regression: Any Root Class ===');

		local RootProbe is probe: RootProbe:init(id: 5);

		# Case 1: default toString via Any's Stringable composition.
		local String is label: 'probe: ' . probe;
		if (label == 'probe: RootProbe') {
			output:line('[PASS] default toString: renders class name');
		} else {
			output:line('[FAIL] default toString: \'' . label . '\'');
		}

		# Case 2: typeName builtin reports the runtime class.
		local String is tn: probe:typeName();
		if (tn == 'RootProbe') {
			output:line('[PASS] typeName: RootProbe');
		} else {
			output:line('[FAIL] typeName: \'' . tn . '\'');
		}

		# Case 3: typeName through an Any-typed reference still resolves.
		local Any is asAny: probe;
		local String is tnAny: asAny:typeName();
		if (tnAny == 'RootProbe') {
			output:line('[PASS] typeName via Any: RootProbe');
		} else {
			output:line('[FAIL] typeName via Any: \'' . tnAny . '\'');
		}

		# Case 4: rendering through an Any-typed reference via cast.
		local String is strAny: asAny as String;
		if (strAny == 'RootProbe') {
			output:line('[PASS] toString via Any: RootProbe');
		} else {
			output:line('[FAIL] toString via Any: \'' . strAny . '\'');
		}

		# Case 5: root upcast and implicit downcast round trip.
		local Any is up: probe as Any;
		local RootProbe is down: up as RootProbe;
		if (down:id == 5) {
			output:line('[PASS] as Any round trip: id = 5');
		} else {
			output:line('[FAIL] as Any round trip: ' . down:id);
		}

		output:line('=== End Any Root Class ===');
	}

}
