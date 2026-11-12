#! SpecUnit sweep (from held_metadata_test.spec): held-member metadata —
#! the Introspection floor exposes the held surface over the emitted
#! per-class name tables: declaration order, out-of-range behavior,
#! hasHeld, the strict instance-member rule, and the empty surface of a
#! plain class.

Class of SpecUnitTest is TestHeldMetadata{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Introspection()]
	];

	Function is testHeldCount(){
		local HeldMetaMixed is m: HeldMetaMixed:init();
		Assert:areEqualInt(2, Introspection:heldCount(obj: m));
	}

	Function is testHeldNamesDeclarationOrder(){
		local HeldMetaMixed is m: HeldMetaMixed:init();
		Assert:areEqualString('tag', Introspection:heldName(obj: m, index: 0));
		Assert:areEqualString('double', Introspection:heldName(obj: m, index: 1));
	}

	Function is testOutOfRangeNameEmpty(){
		local HeldMetaMixed is m: HeldMetaMixed:init();
		Assert:areEqualString('', Introspection:heldName(obj: m, index: 5));
	}

	Function is testHasHeldTrueForHeldMembers(){
		local HeldMetaMixed is m: HeldMetaMixed:init();
		Assert:isTrue(Introspection:hasHeld(obj: m, name: 'tag') && Introspection:hasHeld(obj: m, name: 'double'));
	}

	Function is testInstanceMemberIsNotHeld(){
		# The strict rule, reflectively: an instance member is not held.
		local HeldMetaMixed is m: HeldMetaMixed:init();
		Assert:isFalse(Introspection:hasHeld(obj: m, name: 'instanceField'));
	}

	Function is testPlainClassEmptySurface(){
		# A class with no held members reports an empty surface.
		local HeldMetaPlain is p: HeldMetaPlain:init();
		Assert:isTrue(Introspection:heldCount(obj: p) == 0 && !Introspection:hasHeld(obj: p, name: 'nothing'));
	}
}

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
