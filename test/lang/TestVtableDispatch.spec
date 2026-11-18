#! SpecUnit sweep (from vtable_dispatch_test.spec): vtable dispatch and
#! struct layout across hierarchies — bases-first field layout at depth,
#! base/mid-typed references dispatching to the most-derived override,
#! and MI first-wins resolution (child override, undeclared-to-first).

Class of SpecUnitTest is TestVtableDispatch{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	Function is testLayoutAllLevelsIntact(){
		# Struct fields are laid out bases-first: every level round-trips.
		local LayoutLeaf is leaf: LayoutLeaf:init();
		Assert:areEqualInt(11, leaf:baseField);
		Assert:areEqualInt(22, leaf:midField);
		Assert:areEqualInt(33, leaf:leafField);
	}

	Function is testInheritedMethodReadsBaseField(){
		# Base-declared method reading the base field via a leaf object.
		local LayoutLeaf is leaf: LayoutLeaf:init();
		Assert:areEqualInt(11, leaf:describeBase());
	}

	Function is testBaseTypedVirtualDispatch(){
		# Base-typed reference dispatches to the most-derived override.
		local LayoutLeaf is leaf: LayoutLeaf:init();
		local LayoutBase is asBase: leaf;
		Assert:areEqualInt(3, asBase:poly());
	}

	Function is testMidTypedVirtualDispatch(){
		# Mid-typed reference also reaches the leaf override.
		local LayoutLeaf is leaf: LayoutLeaf:init();
		local LayoutMid is asMid: leaf;
		Assert:areEqualInt(3, asMid:poly());
	}

	Function is testMIOverrideWinsOverBothParents(){
		local MiChild is mi: MiChild:init();
		Assert:areEqualString('child-mia', mi:label());
	}

	Function is testMIFirstWinsUndeclaredMethod(){
		# Undeclared on the child: resolves to the declaring parent.
		local MiChild is mi: MiChild:init();
		Assert:areEqualString('mib', mi:tag());
	}

	Function is testMIBaseTypedDispatch(){
		local MiChild is mi: MiChild:init();
		local MiaFeature is miAsBase: mi;
		Assert:areEqualString('child-mia', miAsBase:label());
	}
}

Class is LayoutBase{
	local Int is baseField: 11;

	Function of Int is describeBase(){
		return self:baseField;
	}

	Function of Int is poly(){
		return 1;
	}
}

Class of LayoutBase is LayoutMid{
	local Int is midField: 22;

	replace Function of Int is poly(){
		return 2;
	}
}

Class of LayoutMid is LayoutLeaf{
	local Int is leafField: 33;

	replace Function of Int is poly(){
		return 3;
	}
}

Class is MiaFeature{
	Function of String is label(){
		return 'mia';
	}
}

Class is MibFeature{
	Function of String is tag(){
		return 'mib';
	}
}

Class of MiaFeature, MibFeature is MiChild{
	replace Function of String is label(){
		return 'child-mia';
	}
}
