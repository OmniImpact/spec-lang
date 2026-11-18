#! SpecUnit sweep (from held_resolver_test.spec): the resolution hook —
#! a class declaring 'held Function of <T> is resolveHeld' admits any
#! undeclared name through the class-name prefix: typed as the resolver
#! return, cached with pointer identity, distinct per name, inherited
#! through the subclass prefix, and never consulted for declared helds.

Class of SpecUnitTest is TestHeldResolver{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Introspection()]
	];

	Function is testDeclaredHeldWinsOverHook(){
		Assert:areEqualString('declared', HeldRegistry:known);
	}

	Function is testHookResolutionTypedAsReturn(){
		local HeldEntry is e: HeldRegistry:alpha;
		Assert:areEqualString('alpha', e:name);
	}

	Function is testHookCachePointerIdentity(){
		# Pointer identity: two reads, one cached value.
		Assert:isTrue(Introspection:objectHash(obj: HeldRegistry:alpha) == Introspection:objectHash(obj: HeldRegistry:alpha));
	}

	Function is testDistinctNamesResolveDistinctly(){
		local HeldEntry is e: HeldRegistry:alpha;
		local HeldEntry is b: HeldRegistry:beta;
		Assert:isTrue(b:name == 'beta' && Introspection:objectHash(obj: e) != Introspection:objectHash(obj: b));
	}

	Function is testInheritedHookThroughSubclassPrefix(){
		local HeldEntry is s: HeldSubRegistry:gamma;
		Assert:areEqualString('gamma', s:name);
	}
}

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

	held Function of HeldEntry is resolveHeld(String is name, Function of HeldEntry is missing){
		# The runtime always provides the missing branch; the resolver
		# decides when to give up.
		Conditional:if(check: { name == 'phantom' }, then: {
			return missing();
		});
		return HeldEntry:init(n: name);
	}

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];
}

Class of HeldRegistry is HeldSubRegistry{
	namespace: ['test'];

	# The hook inherits: an undeclared name through the subclass prefix
	# resolves on the ancestor's registry.
}
