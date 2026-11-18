#! SpecUnit test suite for base:sys:Box.

Class of SpecUnitTest is TestBox{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', Box],
		['base', 'sys', as Loops()]
	];

	Function is incrementBox(Box of Int is b){
		local Int is current: b:get();
		b:set(value: current + 1);
	}

	## Case 1: Primitive Int box operations.
	Function is testPrimitiveIntBox(){
		local Box of Int is b: Box:init(value: 42, isArc: false);
		Assert:isFalse(b:isArc());
		Assert:areEqualInt(42, b:get());

		b:set(value: 100);
		Assert:areEqualInt(100, b:get());
		Assert:areEqualString('Box(100)', b:toString());
	}

	## Case 2: Primitive Boolean box operations.
	Function is testPrimitiveBooleanBox(){
		local Box of Boolean is b: Box:init(value: true, isArc: false);
		Assert:isFalse(b:isArc());
		Assert:isTrue(b:get());

		b:set(value: false);
		Assert:isFalse(b:get());
	}

	## Case 3: ARC-managed String box operations.
	Function is testArcStringBox(){
		local Box of String is b: Box:init(value: 'hello');
		Assert:isTrue(b:isArc());
		Assert:areEqualString('hello', b:get());

		b:set(value: 'world');
		Assert:areEqualString('world', b:get());
		Assert:areEqualString('Box(world)', b:toString());
	}

	## Case 4: Multiple references sharing the same box mutate jointly.
	Function is testSharedReferenceMutation(){
		local Box of Int is b1: Box:init(value: 10, isArc: false);
		local Box of Int is b2: b1;

		b2:set(value: 99);
		Assert:areEqualInt(99, b1:get());
		Assert:areEqualInt(99, b2:get());
	}

	## Case 5: Pass-by-reference out-parameter simulation via Box.
	Function is testPassByReferenceHelper(){
		local Box of Int is counter: Box:init(value: 0, isArc: false);
		self:incrementBox(b: counter);
		self:incrementBox(b: counter);
		self:incrementBox(b: counter);
		Assert:areEqualInt(3, counter:get());
	}

	## Case 6: Box mutations inside loops and closures.
	Function is testBoxInLoopClosure(){
		local Box of Int is total: Box:init(value: 0, isArc: false);
		repeat(times: 5, action: local Function(Int is i){
			total:set(value: total:get() + 10);
		});
		Assert:areEqualInt(50, total:get());
	}
}
