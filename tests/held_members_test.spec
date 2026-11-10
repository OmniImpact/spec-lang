#! Held members (PLAN-ENUM Stage 1): class-scoped storage reached
#! through the class-name prefix. Lazy once-guard construction, full
#! expression initializers, lattice inheritance, strict resolution
#! (an instance reference reaches exactly the instance members), and
#! pointer identity of the cached value.

Class is HeldShared{
	namespace: ['test'];

	held String is root: 'shared-root';
	held Int is depth: 7;
	held contained Int is family: 5;
}

Class of HeldShared is HeldChild{
	namespace: ['test'];

	# Reaches the inherited held members through its own class name:
	# HeldChild:root and HeldChild:family resolve up the lattice, and
	# `held contained` admits the subclass.
	Function of Boolean is checkInherited(){
		return HeldChild:root == 'shared-root' && HeldChild:family == 5;
	}

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];
}

Class is HeldConfig{
	namespace: ['test'];

	held String is appName: 'HeldApp';
	held Int is maxDepth: 2 + 3 * 2;
	# A cross-class held reference inside a held initializer — the two
	# once-guards are independent, so the chain resolves (same-class
	# references are rejected: the guards would deadlock).
	held String is banner: HeldShared:root . ' :: HeldApp';
	held Array of String is tags: ['alpha', 'beta'];
	held local Int is secret: 42;

	replace Function is init(Map of String to String is args){
		local Int is failures: 0;

		Conditional:if(check: { HeldConfig:appName == 'HeldApp' }, then: {
		}, else: {
			Output:line('[FAIL] held string constant: ' . HeldConfig:appName);
			failures: failures + 1;
		});

		Conditional:if(check: { HeldConfig:maxDepth == 8 }, then: {
		}, else: {
			Output:line('[FAIL] held expression initializer: ' . (HeldConfig:maxDepth as String));
			failures: failures + 1;
		});

		Conditional:if(check: { HeldConfig:banner == 'shared-root :: HeldApp' }, then: {
		}, else: {
			Output:line('[FAIL] cross-class held initializer: ' . HeldConfig:banner);
			failures: failures + 1;
		});

		Conditional:if(check: { HeldConfig:tags:length() == 2 && HeldConfig:tags:get(index: 1) == 'beta' }, then: {
		}, else: {
			Output:line('[FAIL] held container initializer');
			failures: failures + 1;
		});

		# held local: visible inside the declaring class.
		Conditional:if(check: { HeldConfig:secret == 42 }, then: {
		}, else: {
			Output:line('[FAIL] held local read from declaring class');
			failures: failures + 1;
		});

		# Inherited held members through the subclass name (public root),
		# and the subclass reads its ancestor's `held contained`.
		local HeldChild is child: HeldChild:init();
		Conditional:if(check: { HeldChild:root == 'shared-root' && child:checkInherited() }, then: {
		}, else: {
			Output:line('[FAIL] inherited held via subclass prefix');
			failures: failures + 1;
		});

		# Pointer identity: two reads of the held member hand back the
		# same cached value (argument passing does not construct).
		Conditional:if(check: { Introspection:objectHash(obj: HeldConfig:banner) == Introspection:objectHash(obj: HeldConfig:banner) }, then: {
		}, else: {
			Output:line('[FAIL] held identity: the once-guard must cache one instance');
			failures: failures + 1;
		});

		# A public held member reads from another class through the
		# class-name prefix (cross-class access in instance code).
		local HeldProbe is probe: HeldProbe:init();
		Conditional:if(check: { probe:checkApp(name: 'HeldApp') }, then: {
		}, else: {
			Output:line('[FAIL] cross-class held read');
			failures: failures + 1;
		});

		Conditional:if(check: { failures == 0 }, then: {
			Output:line('[PASS] held members test complete');
		}, else: {
			Output:line('[FAIL] held members test: ' . (failures as String) . ' failures');
		});
	}

	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Introspection()]
	];
}

## Reads another class's public held member through the class-name
## prefix — the general constant-registry use case.
Class is HeldProbe{
	namespace: ['test'];

	Function of Boolean is checkApp(String is name){
		return HeldConfig:appName == name;
	}

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];
}
