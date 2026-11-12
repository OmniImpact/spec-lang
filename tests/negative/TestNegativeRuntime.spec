Class of SpecUnitTest is TestNegativeRuntime{
	replace Array of Array of String is using: [
		['specunit', Assert],
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner]
	];

	Function is testByteRangePanic(){
		Assert:runFails(
			source: '''
Class is ByteRangePanicTest{
	replace Function is init(Map of String to String is args){
		local Byte is b: 300 as Byte;
	}
}
''',
			expect: 'Byte cast out of range: 300'
		);
	}

	Function is testByteHeldResolverPanic(){
		Assert:runFails(
			source: '''
Class is HeldEntry2{
	local String is name;

	Function is init(String is n){
		self:name: n;
	}
}

Class is HeldPanicRegistry{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];

	held Function of HeldEntry2 is resolveHeld(String is name, Function of HeldEntry2 is missing){
		Conditional:if(check: { name == 'phantom' }, then: {
			return missing();
		});
		return HeldEntry2:init(n: name);
	}
}

Class is HeldResolverPanicTest{
	replace Function is init(Map of String to String is args){
		local HeldEntry2 is boom: HeldPanicRegistry:phantom;
	}
}
''',
			expect: "No held member 'phantom' on HeldPanicRegistry"
		);
	}

	Function is testSpecUnitBadSignature(){
		Assert:runFails(
			source: '''
Class of SpecUnitTest is TestBadSignature{
	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner]
	];

	Function is testWithParams(Int is n){
	}
}
''',
			expect: 'Introspection:invoke supports void zero-parameter methods only'
		);
	}

	Function is testSpecUnitEmptySuite(){
		Assert:runFails(
			source: '''
Class of SpecUnitTest is TestEmptySuite{
	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner]
	];

	Function is helperNotATest(){
	}
}
''',
			expect: 'No test classes found in'
		);
	}
}
