#! SpecUnit sweep (from held_members_test.spec): held members — class-scoped
#! singletons reached through the class-name prefix: constant, expression,
#! cross-class and container initializers, held local visibility inside the
#! declaring class, lattice inheritance through the subclass prefix, pointer
#! identity of the cached value, and cross-class public reads.

Class of SpecUnitTest is TestHeldMembers{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Introspection()]
	];

	Function is testHeldConstantAndExpressionInitializers(){
		Assert:areEqualString('HeldApp', HeldConfig:appName);
		Assert:areEqualInt(8, HeldConfig:maxDepth);
	}

	Function is testCrossClassHeldInitializer(){
		# A cross-class held reference inside a held initializer — the two
		# once-guards are independent, so the chain resolves.
		Assert:areEqualString('shared-root :: HeldApp', HeldConfig:banner);
	}

	Function is testHeldContainerInitializer(){
		Assert:isTrue(HeldConfig:tags:length() == 2 && HeldConfig:tags:get(index: 1) == 'beta');
	}

	Function is testHeldLocalVisibleInDeclaringClass(){
		# held local: visible inside the declaring class, read through a
		# declaring-class member.
		local HeldConfig is cfg: HeldConfig:init();
		Assert:areEqualInt(42, cfg:readSecret());
	}

	Function is testInheritedHeldViaSubclassPrefix(){
		# Inherited held members through the subclass name (public root),
		# and the subclass reads its ancestor's `held contained`.
		local HeldChild is child: HeldChild:init();
		Assert:isTrue(HeldChild:root == 'shared-root' && child:checkInherited());
	}

	Function is testHeldPointerIdentity(){
		# Two reads of the held member hand back the same cached value
		# (argument passing does not construct).
		Assert:isTrue(Introspection:objectHash(obj: HeldConfig:banner) == Introspection:objectHash(obj: HeldConfig:banner));
	}

	Function is testCrossClassHeldRead(){
		# A public held member reads from another class through the
		# class-name prefix (cross-class access in instance code).
		local HeldProbe is probe: HeldProbe:init();
		Assert:isTrue(probe:checkApp(name: 'HeldApp'));
	}
}

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

	## held local is declaring-class-visible; the suite reads it through
	## this member.
	Function of Int is readSecret(){
		return HeldConfig:secret;
	}
}

## Reads another class's public held member through the class-name
## prefix — the general constant-registry use case.
Class is HeldProbe{
	namespace: ['test'];

	Function of Boolean is checkApp(String is name){
		return HeldConfig:appName == name;
	}
}
