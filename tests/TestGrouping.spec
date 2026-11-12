#! SpecUnit sweep (from grouping_test.spec): class assembly regression —
#! the `group:` partial mechanism is retired and multi-parent assembly is
#! MI: the child sees both parents' members, the second parent's members
#! stay reachable, and shared state lives in the class with its method.

Class of SpecUnitTest is TestGrouping{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	Function is testMIAssemblyExposesBothParents(){
		local Calc is calc: Calc:init();
		Assert:areEqualInt(42, calc:add(a: 2, b: 40));
	}

	Function is testSecondParentMembersReachable(){
		local Calc is calc: Calc:init();
		Assert:areEqualString('grouped!', calc:shout(msg: 'grouped'));
	}

	Function is testSharedStateInClass(){
		# Shared state: the field and the method that touches it in one class.
		local Accumulator is acc: Accumulator:init(start: 100);
		acc:bump(by: 1);
		Assert:areEqualInt(101, acc:total);
	}
}

Class is CalcArithmetic{
	Function of Int is add(Int is a, Int is b){
		return a + b;
	}
}

Class is CalcText{
	Function of String is shout(String is msg){
		return msg . '!';
	}
}

## The assembled class: both parents' members through normal MI.
Class of CalcArithmetic, CalcText is Calc{
}

## Shared state lives IN the class (the field + the method that touches it).
Class is Accumulator{
	local Int is total: 0;

	replace Function is init(Int is start){
		self:total: start;
	}

	Function is bump(Int is by){
		self:total: self:total + by;
	}
}
