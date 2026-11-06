#! CodeGenerator port check (step 1): program registries, virtual-slot
#! assignment, type/ownership policy, symbol lookups, target-type
#! inference, and the claim/ARC helpers — no emission yet.

Class is SpecCodegenTest{
	namespace: ['spec', 'test'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'gen', CodeGenerator],
		['spec', 'base', 'compiler', 'ast', ProgramNode],
		['spec', 'base', 'compiler', 'ast', ClassInfo],
		['spec', 'base', 'compiler', 'ast', Member],
		['spec', 'base', 'compiler', 'ast', Statement],
		['spec', 'base', 'compiler', 'ast', StatementKind],
		['spec', 'base', 'compiler', 'ast', Expression],
		['spec', 'base', 'compiler', 'parser', Parser],
		['spec', 'base', 'compiler', 'lexer', Lexer],
		['lib', 'base', 'io', Output]
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

	replace Function is init(Map of String to String is args){
		output:line('=== Spec Codegen Test (step 1) ===');
		local Int is failures: 0;

		local ProgramNode is prog: self:parseOf(src: "Enum of String is Level {
	NONE: '',
	ERR: 'E'
}
Class is Animal{
	local Int is weight: 0;
	replace Function of String is describe(){
		return 'animal';
	}
}
Class of Animal is Dog{
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
		if (cg:methodSlots:getString(key: 'describe', default: '?') == '0'
			&& cg:methodSlots:getString(key: 'init', default: '?') == '1'
			&& cg:methodSlots:getString(key: 'grow', default: '?') == '2'
			&& cg:methodSlotCount == 3
			&& cg:overriddenMethods:has(key: 'describe')
			&& !cg:overriddenMethods:has(key: 'grow')
			&& cg:slotNames:get(index: 0) == 'describe') {
			output:line('[PASS] virtual slots in first-seen order');
		} else {
			output:line('[FAIL] virtual slots');
			failures: failures + 1;
		}

		# --- registries: classes, enums, variants ---
		if (cg:allClassNames:has(key: 'Dog')
			&& cg:allEnumNames:has(key: 'Level')
			&& cg:allEnumVariants:getString(key: 'ERR', default: '?') == 'Level'
			&& cg:allStringBackedEnums:has(key: 'Level')) {
			output:line('[PASS] program registries');
		} else {
			output:line('[FAIL] program registries');
			failures: failures + 1;
		}

		# --- ownership policy: isArcType ---
		if (cg:isArcType(typeName: 'String')
			&& !cg:isArcType(typeName: 'Int')
			&& !cg:isArcType(typeName: 'Level')
			&& cg:isArcType(typeName: 'Animal')
			&& cg:isArcType(typeName: 'Array of Int')
			&& cg:isArcType(typeName: 'Map of String to Int')
			&& !cg:isArcType(typeName: '')) {
			output:line('[PASS] isArcType');
		} else {
			output:line('[FAIL] isArcType');
			failures: failures + 1;
		}

		# --- container element extraction, both spellings ---
		if (cg:elemOfType(t: 'Array of String') == 'String'
			&& cg:elemOfType(t: 'Array:String') == 'String'
			&& cg:elemOfType(t: 'Map of String to Int') == 'Int'
			&& cg:elemOfType(t: 'Map:String:Int') == 'Int'
			&& cg:elemOfType(t: 'List of Byte') == 'Byte'
			&& cg:elemOfType(t: 'Int') == '') {
			output:line('[PASS] elemOfType both spellings');
		} else {
			output:line('[FAIL] elemOfType');
			failures: failures + 1;
		}

		if (cg:containerElemKind(containerType: 'Array of Int') == 'none'
			&& cg:containerElemKind(containerType: 'Array of Byte') == 'byte'
			&& cg:containerElemKind(containerType: 'Array of String') == 'object'
			&& cg:containerElemKind(containerType: 'Array of Animal') == 'object'
			&& cg:containerElemIsArc(containerType: 'Map of String to Animal')
			&& !cg:containerElemIsArc(containerType: 'Map of String to Int')) {
			output:line('[PASS] containerElemKind');
		} else {
			output:line('[FAIL] containerElemKind');
			failures: failures + 1;
		}

		# --- symbol lookups through the inheritance chain ---
		local ClassInfo is dogCls: cg:findClass(name: 'Dog');
		if (dogCls:name == 'Dog'
			&& cg:lookupFieldType(className: 'Dog', fieldName: 'name') == 'String'
			&& cg:lookupFieldType(className: 'Dog', fieldName: 'weight') == 'Int'
			&& cg:lookupMethodReturnType(className: 'Dog', methodName: 'grow') == 'Int'
			&& cg:isSubclassOf(subName: 'Dog', baseName: 'Animal')
			&& !cg:isSubclassOf(subName: 'Animal', baseName: 'Dog')) {
			output:line('[PASS] lookups through inheritance');
		} else {
			output:line('[FAIL] lookups');
			failures: failures + 1;
		}

		# --- target-type inference: literals and identifiers ---
		cg:currentClassName: 'Dog';
		cg:fieldTypes:set(key: 'weight', value: 'Int');
		cg:localVars:set(key: 'x', value: 'Int');
		if (cg:inferTargetType(expr: self:exprOf(src: "'hi'")) == 'String'
			&& cg:inferTargetType(expr: self:exprOf(src: '42')) == 'Int'
			&& cg:inferTargetType(expr: self:exprOf(src: '3.5')) == 'Float'
			&& cg:inferTargetType(expr: self:exprOf(src: 'true')) == 'Boolean'
			&& cg:inferTargetType(expr: self:exprOf(src: 'x')) == 'Int'
			&& cg:inferTargetType(expr: self:exprOf(src: 'self:weight')) == 'Int'
			&& cg:inferTargetType(expr: self:exprOf(src: 'self:grow(by: 2)')) == 'Int') {
			output:line('[PASS] inferTargetType');
		} else {
			output:line('[FAIL] inferTargetType');
			failures: failures + 1;
		}

		# --- claims: constructors yes, borrows no, concat yes ---
		if (cg:isFreshConstructorCall(expr: self:exprOf(src: 'Dog:init()'))
			&& cg:yieldsClaim(expr: self:exprOf(src: 'Dog:init()'))
			&& cg:yieldsClaim(expr: self:exprOf(src: "'a' . 'b'"))
			&& !cg:yieldsClaim(expr: self:exprOf(src: 'x'))
			&& !cg:yieldsClaim(expr: self:exprOf(src: '42'))) {
			output:line('[PASS] yieldsClaim / isFreshConstructorCall');
		} else {
			output:line('[FAIL] yieldsClaim');
			failures: failures + 1;
		}

		# --- typed constructors: cast, wrap, retain, claim passthrough ---
		if (cg:generateTypedConstructor(typeName: 'String', valueC: 'lit', cType: 'SpecBuf*', claims: false) == 'spec_construct_string(lit)'
			&& cg:generateTypedConstructor(typeName: 'String', valueC: 'lit', cType: 'SpecBuf*', claims: true) == 'lit'
			&& cg:generateTypedConstructor(typeName: 'Byte', valueC: 'b', cType: 'unsigned char', claims: false) == 'spec_construct_byte((long long)(b))'
			&& cg:generateTypedConstructor(typeName: 'Animal', valueC: 'a', cType: 'Animal*', claims: false) == '(Animal*)spec_retain((void*)(a))'
			&& cg:generateTypedConstructor(typeName: 'Animal', valueC: 'a', cType: 'Animal*', claims: true) == '(Animal*)((a))'
			&& cg:generateTypedConstructor(typeName: 'Int', valueC: '5', cType: 'long long', claims: false) == '5') {
			output:line('[PASS] generateTypedConstructor');
		} else {
			output:line('[FAIL] generateTypedConstructor');
			failures: failures + 1;
		}

		# --- vocabulary: void spellings and primitive names ---
		if (cg:isVoidType(t: 'void') && cg:isVoidType(t: 'Void') && !cg:isVoidType(t: 'Int')
			&& cg:isPrimitiveName(t: 'Int') && cg:isPrimitiveName(t: 'String')
			&& !cg:isPrimitiveName(t: 'Animal')) {
			output:line('[PASS] isVoidType / isPrimitiveName');
		} else {
			output:line('[FAIL] vocabulary checks');
			failures: failures + 1;
		}

		# --- string wrapping policy ---
		if (cg:wrapToString(expr: self:exprOf(src: '42'), exprC: '42') == 'spec_to_string_int(42)'
			&& cg:wrapToString(expr: self:exprOf(src: 'true'), exprC: '1') == 'spec_to_string_bool(1)'
			&& cg:wrapToString(expr: self:exprOf(src: "'hi'"), exprC: 'x') == 'spec_string_intern("hi")') {
			output:line('[PASS] wrapToString');
		} else {
			output:line('[FAIL] wrapToString');
			failures: failures + 1;
		}

		if (failures == 0) {
			output:line('[PASS] spec codegen test complete');
		} else {
			output:line('[FAIL] spec codegen test: ' . (failures as String) . ' failures');
		}
	}
}
