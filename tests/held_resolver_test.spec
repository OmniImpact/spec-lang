#! The resolution hook (PLAN-ENUM Stage 2): a class declaring
#! 'held Function of <T> is resolveHeld(String is name, Function of <T>
#! is missing)' admits ANY undeclared name through the class-name
#! prefix — the runtime resolves on first access, caches (pointer
#! identity forever), and hands the missing branch as the safe failure
#! path. Declared held members always win; the default without a hook
#! stays a compile error.

Class is HeldEntry{
	namespace: ['test'];

	local String is name;

	Function is init(String is n){
		self:name: n;
	}

	replace Function of String is toString(){
		return 'Entry(' . self:name . ')';
	}
}

Class is HeldRegistry{
	namespace: ['test'];

	# Declared held members win over the hook — resolution is compile-time
	# wherever it can be.
	held String is known: 'declared';

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];

	held Function of HeldEntry is resolveHeld(String is name, Function of HeldEntry is missing){
		# The runtime always provides the missing branch; the resolver
		# decides when to give up.
		Conditional:if(check: { name == 'phantom' }, then: {
			return missing();
		});
		return HeldEntry:init(n: name);
	}
}

Class of HeldRegistry is HeldSubRegistry{
	namespace: ['test'];

	# The hook inherits: an undeclared name through the subclass prefix
	# resolves on the ancestor's registry.
}

Class is HeldResolverTest{
	namespace: ['test'];

	replace Function is init(Map of String to String is args){
		local Int is failures: 0;

		# Declared held wins — the hook is never consulted.
		Conditional:if(check: { HeldRegistry:known == 'declared' }, then: {
		}, else: {
			Output:line('[FAIL] declared held member must win over the hook');
			failures: failures + 1;
		});

		# A hook-resolved reference types as the resolver's return type.
		local HeldEntry is e: HeldRegistry:alpha;
		Conditional:if(check: { e:name == 'alpha' }, then: {
		}, else: {
			Output:line('[FAIL] hook resolution typed as the resolver return: ' . e:toString());
			failures: failures + 1;
		});

		# Pointer identity: two reads, one cached value.
		Conditional:if(check: { Introspection:objectHash(obj: HeldRegistry:alpha) == Introspection:objectHash(obj: HeldRegistry:alpha) }, then: {
		}, else: {
			Output:line('[FAIL] hook cache must hold pointer identity');
			failures: failures + 1;
		});

		# Distinct names resolve to distinct values.
		local HeldEntry is b: HeldRegistry:beta;
		Conditional:if(check: { b:name == 'beta' && Introspection:objectHash(obj: e) != Introspection:objectHash(obj: b) }, then: {
		}, else: {
			Output:line('[FAIL] distinct hook names must resolve distinctly');
			failures: failures + 1;
		});

		# The hook inherits through the subclass prefix.
		local HeldEntry is s: HeldSubRegistry:gamma;
		Conditional:if(check: { s:name == 'gamma' }, then: {
		}, else: {
			Output:line('[FAIL] inherited hook resolution: ' . s:toString());
			failures: failures + 1;
		});

		Conditional:if(check: { failures == 0 }, then: {
			Output:line('[PASS] held resolver test complete');
		}, else: {
			Output:line('[FAIL] held resolver test: ' . (failures as String) . ' failures');
		});
	}

	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Introspection()]
	];
}
