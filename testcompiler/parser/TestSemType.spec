#! specunit: suite
#! Unit tests for SemType (sum-type semantic type tree) and SemTypes (singleton/factory cache).

Class of SpecUnitTest is TestSemType{

	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', 'ast', SemType],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'checker', as SemTypes()],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()]
	];

	Function is testPrimitivesAndStrView(){
		local SemType is tInt: SemTypes:prim(kind: Primitive:INT);
		Assert:isTrue(tInt:isPrimitive());
		Assert:isTrue(tInt:isSignedInt());
		Assert:isTrue(tInt:isIntLike());
		Assert:isTrue(tInt:isNumeric());
		Assert:isFalse(tInt:isUnsigned());
		Assert:isFalse(tInt:isFloat());
		Assert:areEqualString('Int', tInt:baseName());
		Assert:areEqualString('Int', tInt:toKey());
		Assert:areEqualString('Int', tInt:toDisplayString());

		local SemType is tStr: SemTypes:STR;
		Assert:isTrue(tStr:isStringLike());
		Assert:isFalse(tStr:isPrimitive());
		Assert:areEqualString('Str', tStr:baseName());
		Assert:areEqualString('Str', tStr:toKey());
		Assert:isFalse(tStr:equals(other: SemTypes:STRING));
		Assert:isTrue(SemTypes:STRING:isStringLike());

		local SemType is tEmpty: SemTypes:EMPTY;
		Assert:isTrue(tEmpty:isEmpty());
		Assert:areEqualString('', tEmpty:toKey());
		Assert:areEqualString('', tEmpty:toDisplayString());
	}

	Function is testContainersAndNestedGenerics(){
		local SemType is arrInt: SemTypes:arrayOf(elem: SemTypes:INT);
		Assert:isTrue(arrInt:isArray());
		Assert:isTrue(arrInt:isContainer());
		Assert:isTrue(arrInt:isGeneric());
		Assert:isTrue(arrInt:elemType():equals(other: SemTypes:INT));
		Assert:areEqualString('Array', arrInt:baseName());
		Assert:areEqualString('Array:Int', arrInt:toKey());
		Assert:areEqualString('Array of Int', arrInt:toDisplayString());

		local SemType is mapNested: SemTypes:mapOf(key: SemTypes:STRING, val: arrInt);
		Assert:isTrue(mapNested:isMap());
		Assert:isTrue(mapNested:isContainer());
		Assert:isTrue(mapNested:mapKeyType():equals(other: SemTypes:STRING));
		Assert:isTrue(mapNested:mapValType():equals(other: arrInt));
		Assert:areEqualString('Map:String:Array:Int', mapNested:toKey());
		Assert:areEqualString('Map of String to Array of Int', mapNested:toDisplayString());

		local SemType is bareMap: SemTypes:mapOf(key: SemTypes:EMPTY, val: SemTypes:EMPTY);
		Assert:isTrue(bareMap:isMap());
		Assert:isFalse(bareMap:isGeneric());
		Assert:areEqualString('Map', bareMap:toKey());
		Assert:areEqualString('Map', bareMap:toDisplayString());
	}

	Function is testFunctionVariants(){
		local SemType is bareFn: SemTypes:fnOf(ret: SemTypes:VOID);
		Assert:isTrue(bareFn:isFunction());
		Assert:isFalse(bareFn:hasFunctionReturn());
		Assert:areEqualString('Function', bareFn:toKey());
		Assert:areEqualString('Function', bareFn:toDisplayString());
		Assert:isTrue(bareFn:equals(other: SemTypes:BARE_FN));

		local SemType is fnInt: SemTypes:fnOf(ret: SemTypes:INT);
		Assert:isTrue(fnInt:isFunction());
		Assert:isTrue(fnInt:hasFunctionReturn());
		Assert:isTrue(fnInt:functionReturn():equals(other: SemTypes:INT));
		Assert:areEqualString('Function:Int', fnInt:toKey());
		Assert:areEqualString('Function of Int', fnInt:toDisplayString());
	}

	Function is testQualifiedNestedClassVsGeneric(){
		# Outer:Inner (nested class) must preserve path segments separately from generic params.
		local Type is astNested: Type:withParams(name: 'Outer:Inner', params: [Type:init(name: 'Int')]);
		local SemType is nested: SemTypes:fromAstType(t: astNested);
		Assert:isTrue(nested:isNamed());
		Assert:isTrue(nested:isGeneric());
		Assert:areEqualString('Outer:Inner', nested:baseName());
		Assert:areEqualString('Outer', nested:rootName());
		Assert:areEqualString('Inner', nested:leafName());
		Assert:areEqualInt(2, nested:pathSegments():length());
		Assert:areEqualInt(1, nested:typeParams():length());
		Assert:isTrue(nested:elemType():equals(other: SemTypes:INT));
		Assert:areEqualString('Outer:Inner:Int', nested:toKey());
		Assert:areEqualString('Outer:Inner of Int', nested:toDisplayString());

		# Round-trip to AST Type preserves name and params.
		local Type is rt: nested:toAstType();
		Assert:isTrue(rt:equals(other: astNested));
	}

	Function is testSubstituteAndUnify(){
		local SemType is tVarK: SemTypes:named(name: 'K');
		local SemType is tVarV: SemTypes:named(name: 'V');
		local SemType is pattern: SemTypes:mapOf(key: tVarK, val: SemTypes:arrayOf(elem: tVarV));
		local SemType is concrete: SemTypes:mapOf(key: SemTypes:STRING, val: SemTypes:arrayOf(elem: SemTypes:INT));

		local Map of String to Boolean is typeParams: Map:init();
		typeParams:set(key: 'K', value: true);
		typeParams:set(key: 'V', value: true);

		local Map of String to SemType is bindings: Map:init();
		Assert:isTrue(pattern:unify(concrete: concrete, typeParams: typeParams, bindings: bindings));
		Assert:isTrue(bindings:get(key: 'K', default: SemTypes:EMPTY):equals(other: SemTypes:STRING));
		Assert:isTrue(bindings:get(key: 'V', default: SemTypes:EMPTY):equals(other: SemTypes:INT));

		local SemType is substituted: pattern:substitute(subst: bindings);
		Assert:isTrue(substituted:equals(other: concrete));

		# Conflicting binding: Pair of T to T unified with Pair of Int to String must fail.
		local SemType is tVar: SemTypes:named(name: 'T');
		local SemType is pairPat: SemTypes:namedWithParams(name: 'Pair', params: [tVar, tVar]);
		local SemType is pairBad: SemTypes:namedWithParams(name: 'Pair', params: [SemTypes:INT, SemTypes:STRING]);
		local Map of String to Boolean is tpT: Map:init();
		tpT:set(key: 'T', value: true);
		local Map of String to SemType is badBindings: Map:init();
		Assert:isFalse(pairPat:unify(concrete: pairBad, typeParams: tpT, bindings: badBindings));
	}

	Function is testExpressionSemTypeBridge(){
		local Expression is e: Expression:NumberLit(value: 42, text: '42');
		Assert:isTrue(e:getSemType():isEmpty());
		e:setSemType(st: SemTypes:INT);
		Assert:isTrue(e:getSemType():equals(other: SemTypes:INT));
	}
}
