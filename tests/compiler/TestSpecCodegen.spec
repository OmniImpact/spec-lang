#! CodeGenerator port check (step 1): program registries, virtual-slot
#! assignment, type/ownership policy, symbol lookups, target-type
#! inference, and the claim/ARC helpers — no emission yet.

Class of SpecUnitTest is TestSpecCodegen{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'compiler', 'gen', CodeGenerator],
		['base', 'compiler', 'gen', BuiltinCallGenerator],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', StatementKind],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'struct', Map],
		['base', 'math', as Math()],
		['base', 'sys', as Conditional()]
	];

	## Parses a source snippet into a program.
	Function of ProgramNode is parseOf(String is src){
		local Lexer is lx: Lexer:init(source: src);
		local Parser is p: Parser:init(tokens: lx:tokenize());
		return p:parseProgram();
	}

	## Parses a single expression from a snippet.
	Function of Expression is exprOf(String is src){
		local ProgramNode is prog: self:parseOf(src: "Class is P{ replace Function is init(Map of String to String is args){ " . src . "; } }");
		local ClassInfo is cls: prog:classes:get(index: 0) as ClassInfo;
		local Member is m: cls:members:get(index: 0) as Member;
		local Statement is stmt: m:body:get(index: 0) as Statement;
		return stmt:exprStmt;
	}

	## Parses a single statement from a snippet.
	Function of Statement is stmtOf(String is src){
		local ProgramNode is prog: self:parseOf(src: "Class is P{ replace Function is init(Map of String to String is args){ " . src . "; } }");
		local ClassInfo is cls: prog:classes:get(index: 0) as ClassInfo;
		local Member is m: cls:members:get(index: 0) as Member;
		return m:body:get(index: 0) as Statement;
	}

	Function of ProgramNode is sampleAnimalDogProgram(){
		return self:parseOf(src: "Class is Animal{

	replace Array of Array of String is using: [
		['base', 'math', as Math()],
		['base', 'sys', as Output()]
	];
	local Int is weight: 0;
	replace Function of String is describe(){
		return 'animal';
	}
}
Class of Animal is Dog{

	replace Array of Array of String is using: [
		['base', 'math', as Math()],
		['base', 'sys', as Output()]
	];
	local String is name;
	replace Function of Dog is init(Map of String to String is args){
	}
	replace Function of Int is grow(Int is by){
		return self:weight + by;
	}
	replace Function of String is describe(){
		return 'dog';
	}
}
Enum of String is Level {
	NONE: '',
	ERR: 'E'
}");
	}

	Function of CodeGenerator is sampleCodeGen(){
		local ProgramNode is prog: self:sampleAnimalDogProgram();
		local CodeGenerator is cg: CodeGenerator:init();
		cg:registerProgram(classes: prog:classes);
		cg:assignVirtualSlots(classes: prog:classes);
		return cg;
	}

	Function is testVirtualSlotsFirstSeenOrder(){
		local CodeGenerator is cg: self:sampleCodeGen();

		Assert:areEqualString('0', cg:methodSlots:getString(key: 'describe', default: '?'));
		Assert:areEqualString('1', cg:methodSlots:getString(key: 'init', default: '?'));
		Assert:areEqualString('2', cg:methodSlots:getString(key: 'grow', default: '?'));
		Assert:areEqualString('3', cg:methodSlots:getString(key: 'value', default: '?'));
		Assert:areEqualString('4', cg:methodSlots:getString(key: 'toString', default: '?'));
		Assert:areEqualInt(5, cg:methodSlotCount);
		Assert:isFalse(cg:methodSlots:has(key: 'name'));
		Assert:isFalse(cg:methodSlots:has(key: 'ordinal'));
		Assert:isTrue(cg:overriddenMethods:has(key: 'describe'));
		Assert:isFalse(cg:overriddenMethods:has(key: 'grow'));
		Assert:areEqualString('describe', cg:slotNames:get(index: 0));
	}

	Function is testProgramRegistries(){
		local CodeGenerator is cg: self:sampleCodeGen();

		Assert:isTrue(cg:allClassNames:has(key: 'Dog'));
		Assert:isTrue(cg:allClassNames:has(key: 'Level'));
		Assert:isFalse(cg:allEnumNames:has(key: 'Level'));
		Assert:isTrue(cg:heldFields:has(key: 'Level:ERR'));
		Assert:areEqualString('Level', cg:heldFieldTypes:getString(key: 'Level:ERR', default: '?'));
	}

	Function is testIsArcType(){
		local CodeGenerator is cg: self:sampleCodeGen();
		Assert:isTrue(cg:isArcType(typeName: 'String'));
		Assert:isFalse(cg:isArcType(typeName: 'Int'));
		Assert:isTrue(cg:isArcType(typeName: 'Level'));
		Assert:isTrue(cg:isArcType(typeName: 'Animal'));
		Assert:isTrue(cg:isArcType(typeName: 'Array of Int'));
		Assert:isTrue(cg:isArcType(typeName: 'Map of String to Int'));
		Assert:isFalse(cg:isArcType(typeName: ''));
	}

	Function is testContainerElementExtraction(){
		local CodeGenerator is cg: self:sampleCodeGen();
		Assert:areEqualString('String', cg:elemOfType(t: 'Array of String'));
		Assert:areEqualString('String', cg:elemOfType(t: 'Array:String'));
		Assert:areEqualString('Int', cg:elemOfType(t: 'Map of String to Int'));
		Assert:areEqualString('Int', cg:elemOfType(t: 'Map:String:Int'));
		Assert:areEqualString('Byte', cg:elemOfType(t: 'List of Byte'));
		Assert:areEqualString('', cg:elemOfType(t: 'Int'));

		Assert:areEqualString('none', cg:containerElemKind(containerType: 'Array of Int'));
		Assert:areEqualString('byte', cg:containerElemKind(containerType: 'Array of Byte'));
		Assert:areEqualString('object', cg:containerElemKind(containerType: 'Array of String'));
		Assert:areEqualString('object', cg:containerElemKind(containerType: 'Array of Animal'));
		Assert:isTrue(cg:containerElemIsArc(containerType: 'Map of String to Animal'));
		Assert:isFalse(cg:containerElemIsArc(containerType: 'Map of String to Int'));
	}

	Function is testSymbolLookupsThroughInheritance(){
		local CodeGenerator is cg: self:sampleCodeGen();

		local ClassInfo is dogCls: cg:findClass(name: 'Dog');
		Assert:areEqualString('Dog', dogCls:name);
		Assert:areEqualString('String', cg:lookupFieldType(className: 'Dog', fieldName: 'name'));
		Assert:areEqualString('Int', cg:lookupFieldType(className: 'Dog', fieldName: 'weight'));
		Assert:areEqualString('Int', cg:lookupMethodReturnType(className: 'Dog', methodName: 'grow'));
		Assert:isTrue(cg:isSubclassOf(subName: 'Dog', baseName: 'Animal'));
		Assert:isFalse(cg:isSubclassOf(subName: 'Animal', baseName: 'Dog'));
	}

	Function is testTargetTypeInference(){
		local CodeGenerator is cg: self:sampleCodeGen();
		cg:currentClassName: 'Dog';
		cg:fieldTypes:set(key: 'weight', value: 'Int');
		cg:localVars:set(key: 'x', value: 'Int');

		Assert:areEqualString('String', cg:inferTargetType(expr: self:exprOf(src: "'hi'")));
		Assert:areEqualString('Int', cg:inferTargetType(expr: self:exprOf(src: '42')));
		Assert:areEqualString('Float', cg:inferTargetType(expr: self:exprOf(src: '3.5')));
		Assert:areEqualString('Boolean', cg:inferTargetType(expr: self:exprOf(src: 'true')));
		Assert:areEqualString('Int', cg:inferTargetType(expr: self:exprOf(src: 'x')));
		Assert:areEqualString('Int', cg:inferTargetType(expr: self:exprOf(src: 'self:weight')));
		Assert:areEqualString('Int', cg:inferTargetType(expr: self:exprOf(src: 'self:grow(by: 2)')));
	}

	Function is testClaimsAndFreshConstructors(){
		local CodeGenerator is cg: self:sampleCodeGen();
		Assert:isTrue(cg:isFreshConstructorCall(expr: self:exprOf(src: 'Dog:init()')));
		Assert:isTrue(cg:yieldsClaim(expr: self:exprOf(src: 'Dog:init()')));
		Assert:isTrue(cg:yieldsClaim(expr: self:exprOf(src: "'a' . 'b'")));
		Assert:isFalse(cg:yieldsClaim(expr: self:exprOf(src: 'x')));
		Assert:isFalse(cg:yieldsClaim(expr: self:exprOf(src: '42')));
	}

	Function is testGenerateTypedConstructor(){
		local CodeGenerator is cg: self:sampleCodeGen();
		Assert:areEqualString('spec_construct_string(lit)', cg:generateTypedConstructor(typeName: 'String', valueC: 'lit', cType: 'SpecBuf*', claims: false));
		Assert:areEqualString('lit', cg:generateTypedConstructor(typeName: 'String', valueC: 'lit', cType: 'SpecBuf*', claims: true));
		Assert:areEqualString('spec_construct_byte((long long)(b))', cg:generateTypedConstructor(typeName: 'Byte', valueC: 'b', cType: 'unsigned char', claims: false));
		Assert:areEqualString('(Animal*)spec_retain((void*)(a))', cg:generateTypedConstructor(typeName: 'Animal', valueC: 'a', cType: 'Animal*', claims: false));
		Assert:areEqualString('(Animal*)((a))', cg:generateTypedConstructor(typeName: 'Animal', valueC: 'a', cType: 'Animal*', claims: true));
		Assert:areEqualString('5', cg:generateTypedConstructor(typeName: 'Int', valueC: '5', cType: 'long long', claims: false));
	}

	Function is testVocabularyChecks(){
		local CodeGenerator is cg: self:sampleCodeGen();
		Assert:isTrue(cg:isVoidType(t: 'Void'));
		Assert:isFalse(cg:isVoidType(t: 'void'));
		Assert:isFalse(cg:isVoidType(t: 'Int'));
		Assert:isTrue(cg:isPrimitiveName(t: 'Int'));
		Assert:isTrue(cg:isPrimitiveName(t: 'String'));
		Assert:isFalse(cg:isPrimitiveName(t: 'Animal'));
	}

	Function is testWrapToString(){
		local CodeGenerator is cg: self:sampleCodeGen();
		Assert:areEqualString('spec_to_string_int(42)', cg:wrapToString(expr: self:exprOf(src: '42'), exprC: '42'));
		Assert:areEqualString('spec_to_string_bool(1)', cg:wrapToString(expr: self:exprOf(src: 'true'), exprC: '1'));
		Assert:areEqualString('spec_string_intern("hi")', cg:wrapToString(expr: self:exprOf(src: "'hi'"), exprC: 'x'));
	}

	Function is testExpressionEmission(){
		local ProgramNode is eprog: self:parseOf(src: "Class is Animal{
	local Int is weight: 0;
	replace Function of String is describe(){
		return 'animal';
	}
	replace Function of Int is grow(Int is by){
		return self:weight + by;
	}
}");
		local CodeGenerator is eg: CodeGenerator:init();
		eg:registerProgram(classes: eprog:classes);
		eg:currentClassName: 'Animal';
		eg:fieldTypes:set(key: 'weight', value: 'Int');
		eg:localVars:set(key: 'n', value: 'Int');
		eg:localVars:set(key: 'xs', value: 'Array of Int');

		Assert:areEqualString('((1) + (((2) * (3))))', eg:generateExpression(expr: self:exprOf(src: '1 + 2 * 3')));
		Assert:areEqualString('n', eg:generateExpression(expr: self:exprOf(src: 'n')));
		Assert:areEqualString('self->weight', eg:generateExpression(expr: self:exprOf(src: 'self:weight')));
		Assert:areEqualString('Animal_grow(self, 2) /* inst:Animal:grow */', eg:generateExpression(expr: self:exprOf(src: 'self:grow(by: 2)')));
		Assert:areEqualString('((double)(n))', eg:generateExpression(expr: self:exprOf(src: 'n as Float')));
		Assert:isTrue(eg:generateExpression(expr: self:exprOf(src: '[1, 2]')):contains(needle: 'spec_array_new()'));
		Assert:isTrue(eg:generateExpression(expr: self:exprOf(src: 'xs:get(index: 0)')):contains(needle: 'spec_array_get(xs, 0)'));
	}

	Function is testStatementEmission(){
		local ProgramNode is eprog: self:parseOf(src: "Class is Animal{
	local Int is weight: 0;
	replace Function of String is describe(){
		return 'animal';
	}
	replace Function of Int is grow(Int is by){
		return self:weight + by;
	}
}");
		local CodeGenerator is eg: CodeGenerator:init();
		eg:registerProgram(classes: eprog:classes);
		eg:currentClassName: 'Animal';
		eg:fieldTypes:set(key: 'weight', value: 'Int');
		eg:localVars:set(key: 'n', value: 'Int');

		Assert:areEqualString("    long long m = ((n) + (1));\n", eg:generateStatement(stmt: self:stmtOf(src: 'local Int is m: n + 1')));
		Assert:areEqualString("    n = 5;\n", eg:generateStatement(stmt: self:stmtOf(src: 'n: 5')));
		Assert:areEqualString("    return ((self->weight) + (1));\n", eg:generateStatement(stmt: self:stmtOf(src: 'return self:weight + 1')));
	}

	Function is testBuiltinCallBindings(){
		local ProgramNode is eprog: self:parseOf(src: "Class is Animal{
	local Int is weight: 0;
	replace Function of String is describe(){
		return 'animal';
	}
	replace Function of Int is grow(Int is by){
		return self:weight + by;
	}
}");
		local CodeGenerator is eg: CodeGenerator:init();
		eg:registerProgram(classes: eprog:classes);
		eg:currentClassName: 'Animal';
		eg:fieldTypes:set(key: 'weight', value: 'Int');
		eg:localVars:set(key: 'n', value: 'Int');
		eg:localVars:set(key: 'xs', value: 'Array of Int');

		local BuiltinCallGenerator is bcg: BuiltinCallGenerator:init();
		Assert:areEqualString('', bcg:generateBuiltinCall(expr: self:exprOf(src: 'Output:line(text: \'hi\')'), targetC: 'Output', targetType: '', cg: eg));
		Assert:areEqualString('spec_string_length(s)', bcg:generateBuiltinCall(expr: self:exprOf(src: 's:length()'), targetC: 's', targetType: 'String', cg: eg));
		Assert:areEqualString('spec_math_sqrt(n)', bcg:generateBuiltinCall(expr: self:exprOf(src: 'Math:sqrt(value: n)'), targetC: 'Math', targetType: '', cg: eg));
		Assert:areEqualString('spec_array_length(xs)', bcg:generateBuiltinCall(expr: self:exprOf(src: 'xs:length()'), targetC: 'xs', targetType: 'Array of Int', cg: eg));
	}

	Function is testProgramAssemblyFullCGeneration(){
		local ProgramNode is assembler: self:parseOf(src: "Class is Counter{
	local Int is count: 0;
	replace Function is init(Map of String to String is args){
	}
	replace Function of Counter is bump(Int is by){
		self:count: self:count + by;
		return self;
	}
	replace Function of String is toString(){
		return 'Counter';
	}
}
Class is CodegenE2E{

	replace Array of Array of String is using: [
		['base', 'math', as Math()],
		['base', 'sys', as Output()]
	];
	replace Function is init(Map of String to String is args){
		local Counter is c: Counter:init();
		c:bump(by: 5);
	}
}");
		local CodeGenerator is pg: CodeGenerator:init();
		pg:registerProgram(classes: assembler:classes);
		local String is cSrc: pg:generateProgram(program: assembler, entryClass: 'CodegenE2E');

		Assert:isTrue(cSrc:contains(needle: 'spec_alloc'));
		Assert:isTrue(cSrc:contains(needle: 'typedef struct Counter Counter;'));
		Assert:isTrue(cSrc:contains(needle: 'struct Counter {'));
		Assert:isTrue(cSrc:contains(needle: 'Counter_bump'));
		Assert:isTrue(cSrc:contains(needle: 'Counter* Counter_new(void)'));
		Assert:isTrue(cSrc:contains(needle: 'Counter_toString'));
		Assert:isTrue(cSrc:contains(needle: 'int main('));
		Assert:isTrue(cSrc:contains(needle: 'Counter* _inst = Counter_new(); Counter_init(_inst, 0);'));
	}
}
