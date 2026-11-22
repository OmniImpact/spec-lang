#! specunit: negative-suite

#! case: testNarrowFloatField
#! expect: cannot assign 'Float' to 'Int'
Class is NarrowFloatField{
	local Int is samples: 3.7;
}

#! case: testArrayElementMismatch
#! expect: Cannot assign 'Array:String' to 'Array:Int'
Class is ArrayElementMismatch{
	local Array of Int is flags: ['on', 'off'];
}

#! case: testMapValueMismatch
#! expect: Cannot assign 'Map:String:String' to 'Map:String:Int'
Class is MapValueMismatch{
	local Map of String to Int is ages: ['ana': 'ten'];
}

#! case: testUndefinedIdentifier
#! expect: Undefined identifier 'untrackedTotal'
Class is UndefinedIdentifier{
	replace Function is init(Map of String to String is args){
		local Int is total: untrackedTotal + 1;
	}
}

#! case: testNonBooleanConditionControl
#! expect: Method declared return type 'Boolean', but returned 'Int'
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

#! case: testUnassignedFieldRead
#! expect: is read before being initialized
Class is UnassignedFieldRead{
	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	local String is label;

	replace Function is init(Map of String to String is args){
		Output:line(:label);
	}
}

#! case: testCallArgumentMismatch
#! expect: Argument 'n' for 'CallArgumentMismatch.double': cannot assign 'String' to 'Int'
Class is CallArgumentMismatch{
	Function of Int is double(Int is n){
		return n * 2;
	}

	replace Function is init(Map of String to String is args){
		local Int is result: :double(n: 'not-a-number');
	}
}

#! case: testIncompleteWhenBranches
#! expect: Non-exhaustive match: missing arm(s) TransportMode:BIKE
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

#! case: testIncompatibleArrayElements
#! expect: Incompatible array element types
Class is IncompatibleArrayElements{
	replace Function is init(Map of String to String is args){
		local Int is n: [1, 'mixed']:length();
	}
}

#! case: testByteAssignmentAndCast_1
#! expect: cannot assign 'Int' to 'Byte'
Class is ByteAssignmentMismatch{
	replace Function is init(Map of String to String is args){
		local Byte is direct: 5;
	}
}

#! case: testByteAssignmentAndCast_2
#! expect: Cannot cast 'String' to 'Byte'
Class is ByteStringCastMismatch{
	replace Function is init(Map of String to String is args){
		local Byte is fromString: 'hello' as Byte;
	}
}

#! case: testBitwiseOperands_1
#! expect: Bitwise operator '&' requires Int operands
Class is BitwiseOperandMismatch{
	replace Function is init(Map of String to String is args){
		local Int is bad: 'oops' & 1;
	}
}

#! case: testBitwiseOperands_2
#! expect: Bitwise complement '~' requires an Int operand
Class is BitwiseComplementMismatch{
	replace Function is init(Map of String to String is args){
		local Int is badComplement: ~2.5;
	}
}

#! case: testInvalidHexLiteral
#! expect: Invalid digit in base-16 number literal
Class is InvalidHexLiteral{
	local Int is mask: 0xGG;
}

#! case: testListGuard_1
#! expect: Bare List type requires
Class is BareListGuard{
	replace Function is init(Map of String to String is args){
		local List is bare;
	}
}

#! case: testListGuard_2
#! expect: requires a 'default:' argument
Class is ListGetGuard{
	replace Function is init(Map of String to String is args){
		local [Byte] is buf;
		local Byte is b: buf:get(index: 0);
	}
}

#! case: testAnyContractRootOnly
#! expect: Member 'fetch' is not part of the root contract
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

#! case: testStringRelationalMixed
#! expect: requires two String operands
Class is N17StringRelationalMixed{
	replace Function is init(Map of String to String is args){
		local String is s: 'm';
		local Int is n: 5;
		local Boolean is b: s >= n;
	}
}

#! case: testFunctionTypedParam
#! expect: Argument 'check' for 'Conditional.if': cannot assign 'Function' to 'Function of Boolean'
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

#! case: testVoidInValueContext
#! expect: 'Conditional.if' declares no return value
Class is N23VoidInValueContext{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		local String is a: Conditional:if(check: { true }, then: { 'x' });
	}
}

#! case: testFunctionColonSyntaxRejected
#! expect: Function type must use 'Function of <Ret>' or 'Function of <Arg> to <Ret>', not colon syntax.
Class is N24FunctionColonSyntax{
	replace Function is init(Map of String to String is args){
		local Function:Int is fn: { 42 };
	}
}

#! case: testMethodSignatureTypoRejected
#! expect: Unknown or unimported type 'Strng'
Class is MethodSigTypo{
	Function is greet(Strng is name){}
	replace Function is init(){}
}

#! case: testUngroundedGenericMethodRejected
#! expect: defined but never grounded by any concrete call
Class is UngroundedGenericMethod{
	Function of T is identity(T is x){
		return x;
	}
	replace Function is init(){}
}

#! case: testArrayGetDefaultTypeMismatch
#! expect: cannot assign 'String' to 'Int'
Class is ArrayDefaultMismatch{
	replace Array of Array of String is using: [
		['base', 'struct', Array]
	];
	replace Function is init(){
		local Array of Int is nums: [1, 2, 3];
		local Int is v: nums:get(index: 0, default: 'bad');
	}
}

#! case: testMapGetDefaultTypeMismatch
#! expect: cannot assign 'String' to 'Int'
Class is MapDefaultMismatch{
	replace Array of Array of String is using: [
		['base', 'struct', Map]
	];
	replace Function is init(){
		local Map of String to Int is ages: ['a': 1];
		local Int is v: ages:get(key: 'a', default: 'bad');
	}
}

#! case: testGenericVariantArmMismatch
#! expect: Match arm parameter 'v' for 'Maybe:Some' has type 'String', expected 'Int'
#! Generic variant payload types are grounded through the subject's
#! instantiation before the comparison — the diagnostic names the
#! concrete type ('Int'), not the parameter ('T').
Enum is Maybe of T {
	Some(T is value),
	None
}
Class is App{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		local Maybe of Int is m: Maybe:Some(value: 42);
		local Int is v: match(on: m, when: [
			Maybe:Some: local Function of Int(String is v){ return 1; },
			Maybe:None: { 0 }
		]);
	}
}

#! case: testUninitializedObjectLocalRejected
#! expect: must be initialized (Spec does not have null)
Class is UninitLocalApp{
	replace Function is init(Map of String to String is args){
		local String is s;
	}
}

#! case: testUninitializedLocalFieldRejected
#! expect: is not initialized by 'init' (Spec does not have null)
Class is UninitFieldHolder{
	local String is label;
	replace Function is init(){
		local Int is x: 1;
	}
}
Class is UninitFieldApp{
	replace Function is init(Map of String to String is args){
		local UninitFieldHolder is h: UninitFieldHolder:init();
	}
}
