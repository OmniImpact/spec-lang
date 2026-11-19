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

	Function is storeTempStringInBox(Box of String is b, String is prefix){
		local String is dynamicStr: prefix . '-allocated-inside-helper-frame';
		b:set(value: dynamicStr);
	}

	## Case 1: Primitive Int box operations.
	Function is testPrimitiveIntBox(){
		local Box of Int is b: Box:init(value: 42);
		Assert:areEqualInt(42, b:get());

		b:set(value: 100);
		Assert:areEqualInt(100, b:get());
		Assert:areEqualString('Box(100)', b:toString());
	}

	## Case 2: Primitive Boolean and Float box operations.
	Function is testPrimitiveBooleanAndFloatBox(){
		local Box of Boolean is b: Box:init(value: true);
		Assert:isTrue(b:get());

		b:set(value: false);
		Assert:isFalse(b:get());

		local Box of Float is fb: Box:init(value: 3.5);
		Assert:isTrue(fb:get() > 3.4 && fb:get() < 3.6);
		fb:set(value: 7.25);
		Assert:isTrue(fb:get() > 7.2 && fb:get() < 7.3);
	}

	## Case 3: ARC-managed String box operations and cross-frame lifetime retention.
	Function is testArcStringBox(){
		local Box of String is b: Box:init(value: 'hello');
		Assert:areEqualString('hello', b:get());

		b:set(value: 'world');
		Assert:areEqualString('world', b:get());
		Assert:areEqualString('Box(world)', b:toString());

		:storeTempStringInBox(b: b, prefix: 'monomorph');
		Assert:areEqualString('monomorph-allocated-inside-helper-frame', b:get());
	}

	## Case 4: Multiple references sharing the same box mutate jointly.
	Function is testSharedReferenceMutation(){
		local Box of Int is b1: Box:init(value: 10);
		local Box of Int is b2: b1;

		b2:set(value: 99);
		Assert:areEqualInt(99, b1:get());
		Assert:areEqualInt(99, b2:get());
	}

	## Case 5: Pass-by-reference out-parameter simulation via Box.
	Function is testPassByReferenceHelper(){
		local Box of Int is counter: Box:init(value: 0);
		:incrementBox(b: counter);
		:incrementBox(b: counter);
		:incrementBox(b: counter);
		Assert:areEqualInt(3, counter:get());
	}

	## Case 6: Box mutations inside loops and closures.
	Function is testBoxInLoopClosure(){
		local Box of Int is total: Box:init(value: 0);
		repeat(times: 5, action: local Function(Int is i){
			total:set(value: total:get() + 10);
		});
		Assert:areEqualInt(50, total:get());
	}

	## Case 7: Compile-time rejection of mismatched generic arguments and defaults.
	Function is testCompileTimeGenericTypeEnforcement(){
		Assert:compilerRejects(
			source: '''
Class is BadBox of T{
	T is val: 0;
}
Class is App{
	replace Function is init(){
	}
}
''',
			expect: "Type mismatch in field 'BadBox:val': cannot assign 'Int' to 'T'"
		);

		Assert:compilerRejects(
			source: '''
Class is BadParamDefault of T{
	Function is set(T is v: 'invalid'){}
}
Class is App{
	replace Function is init(){
	}
}
''',
			expect: "Default value for parameter 'v' in 'BadParamDefault:set' has type 'String', expected 'T'"
		);

		Assert:compilerRejects(
			source: '''
Class is App{
	replace Array of Array of String is using: [
		['base', 'sys', Box]
	];
	replace Function is init(){
		local Box of Int is b: Box:init(value: 'not-an-int');
	}
}
''',
			expect: "cannot assign 'String' to 'Int'"
		);

		Assert:compilerRejects(
			source: '''
Class is App{
	replace Array of Array of String is using: [
		['base', 'sys', Box]
	];
	replace Function is init(){
		local Box of Int is b: Box:init(value: 10);
		b:set(value: 'not-an-int');
	}
}
''',
			expect: "cannot assign 'String' to 'Int'"
		);
	}
}
