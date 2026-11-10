#! Held-member metadata (PLAN-ENUM Stage 1): the Introspection floor
#! exposes the held surface over the emitted per-class name tables —
#! declaration order (the ordinal index), fields and functions alike.
#! The count is the DECLARING class's own held surface; inherited held
#! members live on their declaring ancestor's table.

Class is HeldMetaMixed{
	namespace: ['test'];

	held String is tag: 'meta';
	local Int is instanceField: 9;
	held Function of Int is double(Int is n){
		return n * 2;
	}
}

Class is HeldMetaPlain{
	namespace: ['test'];

	local String is nothing: 'held';
}

Class is HeldMetadataTest{
	namespace: ['test'];

	replace Function is init(Map of String to String is args){
		local Int is failures: 0;
		local HeldMetaMixed is m: HeldMetaMixed:init();

		Conditional:if(check: { Introspection:heldCount(obj: m) == 2 }, then: {
		}, else: {
			Output:line('[FAIL] held count: ' . (Introspection:heldCount(obj: m) as String));
			failures: failures + 1;
		});

		Conditional:if(check: { Introspection:heldName(obj: m, index: 0) == 'tag' && Introspection:heldName(obj: m, index: 1) == 'double' }, then: {
		}, else: {
			Output:line('[FAIL] held names in declaration order: ' . Introspection:heldName(obj: m, index: 0) . ',' . Introspection:heldName(obj: m, index: 1));
			failures: failures + 1;
		});

		Conditional:if(check: { Introspection:heldName(obj: m, index: 5) == '' }, then: {
		}, else: {
			Output:line('[FAIL] out-of-range held name should be empty');
			failures: failures + 1;
		});

		Conditional:if(check: { Introspection:hasHeld(obj: m, name: 'tag') && Introspection:hasHeld(obj: m, name: 'double') }, then: {
		}, else: {
			Output:line('[FAIL] hasHeld true for held members');
			failures: failures + 1;
		});

		# The strict rule, reflectively: an instance member is not held.
		Conditional:if(check: { !Introspection:hasHeld(obj: m, name: 'instanceField') }, then: {
		}, else: {
			Output:line('[FAIL] hasHeld must be false for instance members');
			failures: failures + 1;
		});

		# A class with no held members reports an empty surface.
		local HeldMetaPlain is p: HeldMetaPlain:init();
		Conditional:if(check: { Introspection:heldCount(obj: p) == 0 && !Introspection:hasHeld(obj: p, name: 'nothing') }, then: {
		}, else: {
			Output:line('[FAIL] plain class held surface must be empty');
			failures: failures + 1;
		});

		Conditional:if(check: { failures == 0 }, then: {
			Output:line('[PASS] held metadata test complete');
		}, else: {
			Output:line('[FAIL] held metadata test: ' . (failures as String) . ' failures');
		});
	}

	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Introspection()]
	];
}
