#! SpecUnit sweep (from visibility_test.spec): member visibility —
#! unmarked members are public (callable externally, overridable),
#! `local` members work only inside the declaring class, and
#! `contained` members are visible to subclasses, including through
#! references.

Class of SpecUnitTest is TestVisibility{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	Function is testPublicExternalCallAndVirtualOverride(){
		local VisBase is base: VisBase:init();
		local VisChild is child: VisChild:init();
		Assert:areEqualInt(10, base:openValue());
		Assert:areEqualInt(99, child:openValue());
	}

	Function is testLocalMemberInternalUse(){
		# `local` members work inside the declaring class.
		local VisBase is base: VisBase:init();
		Assert:areEqualInt(21, base:publicViaSecret());
	}

	Function is testContainedSubclassAccess(){
		# `contained` members are visible to subclasses.
		local VisChild is child: VisChild:init();
		Assert:areEqualInt(60, child:viaHelper());
	}

	Function is testContainedReferenceAccessFromSubclass(){
		# Contained access through a reference, from within a subclass.
		local VisChild is child: VisChild:init();
		Assert:areEqualInt(30, child:viaHelperRef(ref: child as VisBase));
	}
}

Class is VisBase{

	## Public by default: overridable and externally callable.
	Function of Int is openValue(){
		return 10;
	}

	## Private: only VisBase internals may touch this.
	local Function of Int is secret(){
		return 20;
	}

	## Protected, final: subclasses may use it, never override it.
	contained Function of Int is helper(){
		return 30;
	}

	## Uses the private member internally.
	Function of Int is publicViaSecret(){
		return self:secret() + 1;
	}
}

Class of VisBase is VisChild{

	replace Function is init(){
	}

	## Contained members are visible here, including through references.
	Function of Int is viaHelper(){
		return self:helper() * 2;
	}

	Function of Int is viaHelperRef(VisBase is ref){
		return ref:helper();
	}

	replace Function of Int is openValue(){
		return 99;
	}
}
