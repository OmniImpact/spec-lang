#! SpecUnit sweep (from merge_function_test.spec): merge-on-Function —
#! delegation to the nearest parent implementation: adapted forwards,
#! partial named forwards falling back to parent defaults, statement-
#! then-forward bodies, delegation chains, merge init chaining parent
#! constructors, and virtual dispatch of merge overrides.

Class of SpecUnitTest is TestMergeFunction{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	Function is testChainedForwardWithAdaptation(){
		# Chained forward with adaptation: (1+100)+2 = 103.
		local GrandLogger is gl: GrandLogger:init(tag: 'grand');
		Assert:areEqualInt(103, gl:add(a: 1, b: 2));
	}

	Function is testPartialNamedForwardWithParentDefault(){
		# Partial named forward: parent default supplies factor (7 * 2 = 14).
		local GrandLogger is gl: GrandLogger:init(tag: 'grand');
		Assert:areEqualInt(14, gl:scale(n: 7));
	}

	Function is testMergeInitChainsParentConstructor(){
		local GrandLogger is gl: GrandLogger:init(tag: 'grand');
		Assert:areEqualString('grand', gl:tag);
	}

	Function is testInheritedInitRoundTrips(){
		# ChildLogger inherits LoggerBase:init unchanged; tag round-trips.
		local ChildLogger is cl: ChildLogger:init(tag: 'x');
		Assert:areEqualString('x', cl:tag);
	}

	Function is testBaseTypedVirtualForward(){
		# Merge overrides are virtual: the base-typed call applies the
		# forward identically (no recursion).
		local GrandLogger is gl: GrandLogger:init(tag: 'grand');
		local LoggerBase is asBase: gl;
		Assert:areEqualInt(103, asBase:add(a: 1, b: 2));
	}

	Function is testSubclassTypedForward(){
		# Subclass-typed call goes through the merge forward.
		local ChildLogger is asChild: GrandLogger:init(tag: 'c');
		Assert:areEqualInt(103, asChild:add(a: 1, b: 2));
	}
}

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
