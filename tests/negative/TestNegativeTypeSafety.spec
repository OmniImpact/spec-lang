Class of SpecUnitTest is TestNegativeTypeSafety{
	replace Array of Array of String is using: [
		['specunit', Assert],
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner]
	];

	Function is testNarrowFloatField(){
		Assert:compilerRejects(
			source: '''
Class is NarrowFloatField{
	local Int is samples: 3.7;
}
''',
			expect: "cannot assign 'Float' to 'Int'"
		);
	}

	Function is testArrayElementMismatch(){
		Assert:compilerRejects(
			source: '''
Class is ArrayElementMismatch{
	local Array of Int is flags: ['on', 'off'];
}
''',
			expect: "Cannot assign 'Array:String' to 'Array:Int'"
		);
	}

	Function is testMapValueMismatch(){
		Assert:compilerRejects(
			source: '''
Class is MapValueMismatch{
	local Map of String to Int is ages: ['ana': 'ten'];
}
''',
			expect: "Cannot assign 'Map:String:String' to 'Map:String:Int'"
		);
	}

	Function is testUndefinedIdentifier(){
		Assert:compilerRejects(
			source: '''
Class is UndefinedIdentifier{
	replace Function is init(Map of String to String is args){
		local Int is total: untrackedTotal + 1;
	}
}
''',
			expect: "Undefined identifier 'untrackedTotal'"
		);
	}

	Function is testNonBooleanConditionControl(){
		Assert:compilerRejects(
			source: '''
Class is NonBooleanConditionControl{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Conditional:if(check: { 1 }, then: {
			local Int is unused: 0;
		});
	}
}
''',
			expect: "Method declared return type 'Boolean', but returned 'Int'"
		);
	}

	Function is testUnassignedFieldRead(){
		Assert:compilerRejects(
			source: '''
Class is UnassignedFieldRead{
	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	local String is label;

	replace Function is init(Map of String to String is args){
		Output:line(self:label);
	}
}
''',
			expect: "is read before being initialized"
		);
	}

	Function is testCallArgumentMismatch(){
		Assert:compilerRejects(
			source: '''
Class is CallArgumentMismatch{
	Function of Int is double(Int is n){
		return n * 2;
	}

	replace Function is init(Map of String to String is args){
		local Int is result: self:double(n: 'not-a-number');
	}
}
''',
			expect: "Argument 'n' for 'CallArgumentMismatch.double': cannot assign 'String' to 'Int'"
		);
	}

	Function is testIncompleteWhenBranches(){
		Assert:compilerRejects(
			source: '''
Enum is TransportMode{
	CAR,
	BIKE
}

Class is IncompleteWhenBranches{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];

	Function of String is describe(TransportMode is mode){
		return Conditional:match(on: mode, when: [
			TransportMode:CAR: { 'drives' }
		]);
	}
}
''',
			expect: "Non-exhaustive match: missing arm(s) TransportMode:BIKE"
		);
	}

	Function is testIncompatibleArrayElements(){
		Assert:compilerRejects(
			source: '''
Class is IncompatibleArrayElements{
	replace Function is init(Map of String to String is args){
		local Int is n: [1, 'mixed']:length();
	}
}
''',
			expect: "Incompatible array element types"
		);
	}

	Function is testByteAssignmentAndCast(){
		Assert:compilerRejects(
			source: '''
Class is ByteAssignmentMismatch{
	replace Function is init(Map of String to String is args){
		local Byte is direct: 5;
	}
}
''',
			expect: "cannot assign 'Int' to 'Byte'"
		);

		Assert:compilerRejects(
			source: '''
Class is ByteStringCastMismatch{
	replace Function is init(Map of String to String is args){
		local Byte is fromString: 'hello' as Byte;
	}
}
''',
			expect: "Cannot cast 'String' to 'Byte'"
		);
	}

	Function is testBitwiseOperands(){
		Assert:compilerRejects(
			source: '''
Class is BitwiseOperandMismatch{
	replace Function is init(Map of String to String is args){
		local Int is bad: 'oops' & 1;
	}
}
''',
			expect: "Bitwise operator '&' requires Int operands"
		);

		Assert:compilerRejects(
			source: '''
Class is BitwiseComplementMismatch{
	replace Function is init(Map of String to String is args){
		local Int is badComplement: ~2.5;
	}
}
''',
			expect: "Bitwise complement '~' requires an Int operand"
		);
	}

	Function is testInvalidHexLiteral(){
		Assert:compilerRejects(
			source: '''
Class is InvalidHexLiteral{
	local Int is mask: 0xGG;
}
''',
			expect: "Invalid digit in base-16 number literal"
		);
	}

	Function is testListGuard(){
		Assert:compilerRejects(
			source: '''
Class is BareListGuard{
	replace Function is init(Map of String to String is args){
		local List is bare;
	}
}
''',
			expect: "Bare List type requires"
		);

		Assert:compilerRejects(
			source: '''
Class is ListGetGuard{
	replace Function is init(Map of String to String is args){
		local [Byte] is buf;
		local Byte is b: buf:get(index: 0);
	}
}
''',
			expect: "requires a 'default:' argument"
		);
	}

	Function is testAnyContractRootOnly(){
		Assert:compilerRejects(
			source: '''
Class is StrictAnimal{
	Function of String is speak(){
		return '...';
	}
}

Class of StrictAnimal is StrictDog{
	Function of String is fetch(){
		return 'ball';
	}
}

Class is StrictNegativeTest{
	replace Function is init(Map of String to String is args){
		local Any is anyRef: StrictDog:init();
		anyRef:fetch();
	}
}
''',
			expect: "Member 'fetch' is not part of the root contract"
		);
	}

	Function is testStringRelationalMixed(){
		Assert:compilerRejects(
			source: '''
Class is N17StringRelationalMixed{
	replace Function is init(Map of String to String is args){
		local String is s: 'm';
		local Int is n: 5;
		local Boolean is b: s >= n;
	}
}
''',
			expect: "requires two String operands"
		);
	}

	Function is testFunctionTypedParam(){
		Assert:compilerRejects(
			source: '''
Class is N22FunctionTypedParam{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		local Function is voidClosure: { Output:line('side effect'); };
		Conditional:if(check: voidClosure, then: {
			Output:line('branched');
		});
	}
}
''',
			expect: "Argument 'check' for 'Conditional.if': cannot assign 'Function' to 'Function of Boolean'"
		);
	}

	Function is testVoidInValueContext(){
		Assert:compilerRejects(
			source: '''
Class is N23VoidInValueContext{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		local String is a: Conditional:if(check: { true }, then: { 'x' });
	}
}
''',
			expect: "'Conditional.if' declares no return value"
		);
	}
}
