#! SpecUnit sweep (from held_methods_test.spec): held functions —
#! receiver-free class-scoped dispatch through the class-name prefix:
#! sibling held calls, construction inside a held function, parameter
#! defaults, cross-class calls from instance code, and repeat dispatch.

Class of SpecUnitTest is TestHeldMethods{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	Function is testHeldDispatch(){
		Assert:areEqualInt(21, HeldMath:triple(n: 7));
	}

	Function is testHeldSiblingCall(){
		# The held function read the class-held field through the class
		# name (scale=3) and chained a sibling held call.
		Assert:areEqualString('n=6', HeldMath:describe(n: 2));
	}

	Function is testHeldFunctionConstructsInstances(){
		local HeldCounter is c: HeldMath:freshCounter();
		c:bump();
		c:bump();
		Assert:areEqualInt(2, c:get());
	}

	Function is testHeldParameterDefaults(){
		Assert:areEqualInt(6, HeldMath:withDefault());
		Assert:areEqualInt(2, HeldMath:withDefault(n: 1));
	}

	Function is testCrossClassHeldCall(){
		# A public held function called through the class-name prefix
		# from another class's instance method.
		local HeldMathUser is u: HeldMathUser:init();
		Assert:isTrue(u:crossClassCall());
	}

	Function is testHeldRepeatCall(){
		# The strict resolution rule: an instance receiver never reaches
		# a held function — dispatch stays through the class name.
		Assert:areEqualInt(3, HeldMath:triple(n: 1));
	}
}

Class is HeldMath{
	namespace: ['test'];

	held Int is scale: 3;

	held Function of Int is triple(Int is n){
		return n * HeldMath:scale;
	}

	held Function of String is describe(Int is n){
		# A held function calling a sibling held function.
		return 'n=' . (HeldMath:triple(n: n) as String);
	}

	held Function of HeldCounter is freshCounter(){
		# Construction inside a held function: the declaring class's
		# import rules gate it (same-file grant here).
		return HeldCounter:init();
	}

	held Function of Int is withDefault(Int is n : 5){
		return n + 1;
	}
}

Class is HeldCounter{
	namespace: ['test'];

	local Int is value: 0;

	Function is bump(){
		self:value: self:value + 1;
	}

	Function of Int is get(){
		return self:value;
	}
}

Class is HeldMathUser{
	namespace: ['test'];

	Function of Boolean is crossClassCall(){
		# A public held function called through the class-name prefix
		# from another class's instance method.
		return HeldMath:triple(n: 14) == 42;
	}
}
