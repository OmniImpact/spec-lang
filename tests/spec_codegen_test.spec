#! CodeGenerator port check (step 1): program registries, virtual-slot
#! assignment, type/ownership policy, symbol lookups, target-type
#! inference, and the claim/ARC helpers — no emission yet.

Class is SpecCodegenTest{
	namespace: ['test'];

	replace Array of Array of String is using: [
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
		['base', 'io', Output],
		['base', 'struct', Map],
		['base', 'math', as Math()],
		['base', 'io', as Output()],
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

	replace Function is init(Map of String to String is args){
		Output:line('=== Spec Codegen Test (step 1) ===');
		local Int is failures: 0;

		local ProgramNode is prog: self:parseOf(src: "Enum of String is Level {
	NONE: '',
	ERR: 'E'
}
Class is Animal{

	replace Array of Array of String is using: [
		['base', 'math', as Math()],
		['base', 'io', as Output()]
	];
	local Int is weight: 0;
	replace Function of String is describe(){
		return 'animal';
	}
}
Class of Animal is Dog{

	replace Array of Array of String is using: [
		['base', 'math', as Math()],
		['base', 'io', as Output()]
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
}");
		local CodeGenerator is cg: CodeGenerator:init();
		cg:registerProgram(classes: prog:classes);
		cg:assignVirtualSlots(classes: prog:classes);

		# --- virtual slots: first-seen order, overrides flagged ---
		Conditional:if(check: { cg:methodSlots:getString(key: 'describe', default: '?') == '0'
			&& cg:methodSlots:getString(key: 'init', default: '?') == '1'
			&& cg:methodSlots:getString(key: 'grow', default: '?') == '2'
			&& cg:methodSlotCount == 3
			&& cg:overriddenMethods:has(key: 'describe')
			&& !cg:overriddenMethods:has(key: 'grow')
			&& cg:slotNames:get(index: 0) == 'describe' }, then: {
			Output:line('[PASS] virtual slots in first-seen order');
		}, else: {
			Output:line('[FAIL] virtual slots');
			failures: failures + 1;
		});

		# --- registries: classes, enums, variants ---
		Conditional:if(check: { cg:allClassNames:has(key: 'Dog')
			&& cg:allEnumNames:has(key: 'Level')
			&& cg:allEnumVariants:getString(key: 'ERR', default: '?') == 'Level'
			&& cg:allStringBackedEnums:has(key: 'Level') }, then: {
			Output:line('[PASS] program registries');
		}, else: {
			Output:line('[FAIL] program registries');
			failures: failures + 1;
		});

		# --- ownership policy: isArcType ---
		Conditional:if(check: { cg:isArcType(typeName: 'String')
			&& !cg:isArcType(typeName: 'Int')
			&& !cg:isArcType(typeName: 'Level')
			&& cg:isArcType(typeName: 'Animal')
			&& cg:isArcType(typeName: 'Array of Int')
			&& cg:isArcType(typeName: 'Map of String to Int')
			&& !cg:isArcType(typeName: '') }, then: {
			Output:line('[PASS] isArcType');
		}, else: {
			Output:line('[FAIL] isArcType');
			failures: failures + 1;
		});

		# --- container element extraction, both spellings ---
		Conditional:if(check: { cg:elemOfType(t: 'Array of String') == 'String'
			&& cg:elemOfType(t: 'Array:String') == 'String'
			&& cg:elemOfType(t: 'Map of String to Int') == 'Int'
			&& cg:elemOfType(t: 'Map:String:Int') == 'Int'
			&& cg:elemOfType(t: 'List of Byte') == 'Byte'
			&& cg:elemOfType(t: 'Int') == '' }, then: {
			Output:line('[PASS] elemOfType both spellings');
		}, else: {
			Output:line('[FAIL] elemOfType');
			failures: failures + 1;
		});

		Conditional:if(check: { cg:containerElemKind(containerType: 'Array of Int') == 'none'
			&& cg:containerElemKind(containerType: 'Array of Byte') == 'byte'
			&& cg:containerElemKind(containerType: 'Array of String') == 'object'
			&& cg:containerElemKind(containerType: 'Array of Animal') == 'object'
			&& cg:containerElemIsArc(containerType: 'Map of String to Animal')
			&& !cg:containerElemIsArc(containerType: 'Map of String to Int') }, then: {
			Output:line('[PASS] containerElemKind');
		}, else: {
			Output:line('[FAIL] containerElemKind');
			failures: failures + 1;
		});

		# --- symbol lookups through the inheritance chain ---
		local ClassInfo is dogCls: cg:findClass(name: 'Dog');
		Conditional:if(check: { dogCls:name == 'Dog'
			&& cg:lookupFieldType(className: 'Dog', fieldName: 'name') == 'String'
			&& cg:lookupFieldType(className: 'Dog', fieldName: 'weight') == 'Int'
			&& cg:lookupMethodReturnType(className: 'Dog', methodName: 'grow') == 'Int'
			&& cg:isSubclassOf(subName: 'Dog', baseName: 'Animal')
			&& !cg:isSubclassOf(subName: 'Animal', baseName: 'Dog') }, then: {
			Output:line('[PASS] lookups through inheritance');
		}, else: {
			Output:line('[FAIL] lookups');
			failures: failures + 1;
		});

		# --- target-type inference: literals and identifiers ---
		cg:currentClassName: 'Dog';
		cg:fieldTypes:set(key: 'weight', value: 'Int');
		cg:localVars:set(key: 'x', value: 'Int');
		Conditional:if(check: { cg:inferTargetType(expr: self:exprOf(src: "'hi'")) == 'String'
			&& cg:inferTargetType(expr: self:exprOf(src: '42')) == 'Int'
			&& cg:inferTargetType(expr: self:exprOf(src: '3.5')) == 'Float'
			&& cg:inferTargetType(expr: self:exprOf(src: 'true')) == 'Boolean'
			&& cg:inferTargetType(expr: self:exprOf(src: 'x')) == 'Int'
			&& cg:inferTargetType(expr: self:exprOf(src: 'self:weight')) == 'Int'
			&& cg:inferTargetType(expr: self:exprOf(src: 'self:grow(by: 2)')) == 'Int' }, then: {
			Output:line('[PASS] inferTargetType');
		}, else: {
			Output:line('[FAIL] inferTargetType');
			failures: failures + 1;
		});

		# --- claims: constructors yes, borrows no, concat yes ---
		Conditional:if(check: { cg:isFreshConstructorCall(expr: self:exprOf(src: 'Dog:init()'))
			&& cg:yieldsClaim(expr: self:exprOf(src: 'Dog:init()'))
			&& cg:yieldsClaim(expr: self:exprOf(src: "'a' . 'b'"))
			&& !cg:yieldsClaim(expr: self:exprOf(src: 'x'))
			&& !cg:yieldsClaim(expr: self:exprOf(src: '42')) }, then: {
			Output:line('[PASS] yieldsClaim / isFreshConstructorCall');
		}, else: {
			Output:line('[FAIL] yieldsClaim');
			failures: failures + 1;
		});

		# --- typed constructors: cast, wrap, retain, claim passthrough ---
		Conditional:if(check: { cg:generateTypedConstructor(typeName: 'String', valueC: 'lit', cType: 'SpecBuf*', claims: false) == 'spec_construct_string(lit)'
			&& cg:generateTypedConstructor(typeName: 'String', valueC: 'lit', cType: 'SpecBuf*', claims: true) == 'lit'
			&& cg:generateTypedConstructor(typeName: 'Byte', valueC: 'b', cType: 'unsigned char', claims: false) == 'spec_construct_byte((long long)(b))'
			&& cg:generateTypedConstructor(typeName: 'Animal', valueC: 'a', cType: 'Animal*', claims: false) == '(Animal*)spec_retain((void*)(a))'
			&& cg:generateTypedConstructor(typeName: 'Animal', valueC: 'a', cType: 'Animal*', claims: true) == '(Animal*)((a))'
			&& cg:generateTypedConstructor(typeName: 'Int', valueC: '5', cType: 'long long', claims: false) == '5' }, then: {
			Output:line('[PASS] generateTypedConstructor');
		}, else: {
			Output:line('[FAIL] generateTypedConstructor');
			failures: failures + 1;
		});

		# --- vocabulary: void spellings and primitive names ---
		Conditional:if(check: { cg:isVoidType(t: 'void') && cg:isVoidType(t: 'Void') && !cg:isVoidType(t: 'Int')
			&& cg:isPrimitiveName(t: 'Int') && cg:isPrimitiveName(t: 'String')
			&& !cg:isPrimitiveName(t: 'Animal') }, then: {
			Output:line('[PASS] isVoidType / isPrimitiveName');
		}, else: {
			Output:line('[FAIL] vocabulary checks');
			failures: failures + 1;
		});

		# --- string wrapping policy ---
		Conditional:if(check: { cg:wrapToString(expr: self:exprOf(src: '42'), exprC: '42') == 'spec_to_string_int(42)'
			&& cg:wrapToString(expr: self:exprOf(src: 'true'), exprC: '1') == 'spec_to_string_bool(1)'
			&& cg:wrapToString(expr: self:exprOf(src: "'hi'"), exprC: 'x') == 'spec_string_intern("hi")' }, then: {
			Output:line('[PASS] wrapToString');
		}, else: {
			Output:line('[FAIL] wrapToString');
			failures: failures + 1;
		});

		# --- expression emission shapes ---
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

		Conditional:if(check: { eg:generateExpression(expr: self:exprOf(src: '1 + 2 * 3')) == '((1) + (((2) * (3))))'
			&& eg:generateExpression(expr: self:exprOf(src: 'n')) == 'n'
			&& eg:generateExpression(expr: self:exprOf(src: 'self:weight')) == 'self->weight'
			&& eg:generateExpression(expr: self:exprOf(src: 'self:grow(by: 2)')) == 'Animal_grow(self, 2) /* inst:Animal:grow */'
			&& eg:generateExpression(expr: self:exprOf(src: 'n as Float')) == '((double)(n))'
			&& eg:generateExpression(expr: self:exprOf(src: '[1, 2]')):contains(needle: 'spec_array_new()')
			&& eg:generateExpression(expr: self:exprOf(src: 'xs:get(index: 0)')):contains(needle: 'spec_array_get(xs, 0)') }, then: {
			Output:line('[PASS] expression emission');
		}, else: {
			Output:line('[FAIL] expression emission');
			failures: failures + 1;
		});

		# --- statement emission shapes ---
		Conditional:if(check: { eg:generateStatement(stmt: self:stmtOf(src: 'local Int is m: n + 1')) == "    long long m = ((n) + (1));\n"
			&& eg:generateStatement(stmt: self:stmtOf(src: 'n: 5')) == "    n = 5;\n"
			&& eg:generateStatement(stmt: self:stmtOf(src: 'return self:weight + 1')) == "    return ((self->weight) + (1));\n" }, then: {
			Output:line('[PASS] statement emission');
		}, else: {
			Output:line('[FAIL] statement emission');
			failures: failures + 1;
		});

		# --- builtin call bindings ---
		local BuiltinCallGenerator is bcg: BuiltinCallGenerator:init();
		local Map of String to String is enumNames: Map:init();
		enumNames:set(key: 'Level', value: 'true');
		bcg:setEnumNames(names: enumNames);
		Conditional:if(check: { bcg:generateBuiltinCall(expr: self:exprOf(src: 'Output:line(text: \'hi\')'), targetC: 'Output', targetType: '', cg: eg):contains(needle: 'printf("%s\\n", spec_buf_to_cstring((SpecBuf*)(')
			&& bcg:generateBuiltinCall(expr: self:exprOf(src: 's:length()'), targetC: 's', targetType: 'String', cg: eg) == 'spec_string_length(s)'
			&& bcg:generateBuiltinCall(expr: self:exprOf(src: 'Math:sqrt(value: n)'), targetC: 'Math', targetType: '', cg: eg) == 'spec_math_sqrt(n)'
			&& bcg:generateBuiltinCall(expr: self:exprOf(src: 'Level:of(name: \'E\')'), targetC: 'Level', targetType: '', cg: eg) == 'Level_of(spec_string_intern("E"))'
			&& bcg:generateBuiltinCall(expr: self:exprOf(src: 'xs:length()'), targetC: 'xs', targetType: 'Array of Int', cg: eg) == 'spec_array_length(xs)' }, then: {
			Output:line('[PASS] builtin call bindings');
		}, else: {
			Output:line('[FAIL] builtin call bindings');
			failures: failures + 1;
		});

		# --- program assembly: full C generation ---
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
		['base', 'io', as Output()]
	];
	replace Function is init(Map of String to String is args){
		local Counter is c: Counter:init();
		c:bump(by: 5);
	}
}");
		local CodeGenerator is pg: CodeGenerator:init();
		pg:registerProgram(classes: assembler:classes);
		local String is cSrc: pg:generateProgram(program: assembler, entryClass: 'CodegenE2E');
		Conditional:if(check: { cSrc:contains(needle: 'spec_alloc')
			&& cSrc:contains(needle: 'typedef struct Counter Counter;')
			&& cSrc:contains(needle: 'struct Counter {')
			&& cSrc:contains(needle: 'Counter_bump')
			&& cSrc:contains(needle: 'Counter* Counter_new(void)')
			&& cSrc:contains(needle: 'Counter_toString')
			&& cSrc:contains(needle: 'int main(')
			&& cSrc:contains(needle: 'Counter* _inst = Counter_new(); Counter_init(_inst, 0);') }, then: {
			Output:line('[PASS] program assembly');
		}, else: {
			Output:line('[FAIL] program assembly');
			failures: failures + 1;
		});

		Conditional:if(check: { failures == 0 }, then: {
			Output:line('[PASS] spec codegen test complete');
		}, else: {
			Output:line('[FAIL] spec codegen test: ' . (failures as String) . ' failures');
		});
	}
}
