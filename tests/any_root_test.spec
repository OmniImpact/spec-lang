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

	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];
	local Int is id: 5;

	replace Function is init(Int is id){
		self:id: id;
	}
}

Class is AnyRootTest{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', Output],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Regression: Any Root Class ===');

		local RootProbe is probe: RootProbe:init(id: 5);

		# Case 1: default toString via Any's Stringable composition.
		local String is label: 'probe: ' . probe;
		Conditional:if(check: { label == 'probe: RootProbe' }, then: {
			Output:line('[PASS] default toString: renders class name');
		}, else: {
			Output:line('[FAIL] default toString: \'' . label . '\'');
		});

		# Case 2: typeName builtin reports the runtime class.
		local String is tn: probe:typeName();
		Conditional:if(check: { tn == 'RootProbe' }, then: {
			Output:line('[PASS] typeName: RootProbe');
		}, else: {
			Output:line('[FAIL] typeName: \'' . tn . '\'');
		});

		# Case 3: typeName through an Any-typed reference still resolves.
		local Any is asAny: probe;
		local String is tnAny: asAny:typeName();
		Conditional:if(check: { tnAny == 'RootProbe' }, then: {
			Output:line('[PASS] typeName via Any: RootProbe');
		}, else: {
			Output:line('[FAIL] typeName via Any: \'' . tnAny . '\'');
		});

		# Case 4: rendering through an Any-typed reference via cast.
		local String is strAny: asAny as String;
		Conditional:if(check: { strAny == 'RootProbe' }, then: {
			Output:line('[PASS] toString via Any: RootProbe');
		}, else: {
			Output:line('[FAIL] toString via Any: \'' . strAny . '\'');
		});

		# Case 5: root upcast and implicit downcast round trip.
		local Any is up: probe as Any;
		local RootProbe is down: up as RootProbe;
		Conditional:if(check: { down:id == 5 }, then: {
			Output:line('[PASS] as Any round trip: id = 5');
		}, else: {
			Output:line('[FAIL] as Any round trip: ' . down:id);
		});

		Output:line('=== End Any Root Class ===');
	}

}
