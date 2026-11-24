#! Package base:compiler:ast
#! Semantic type representation modeled as a recursive tagged-union enum.
##
## Replaces string-encoded types ('Array:Int', 'Map of K to V', 'Function:R',
## 'Outer:Inner') with an explicit sum type:
##   - Primitives carry the [Primitive] enum directly.
##   - Builtin containers (Array, List, Map) and Function types have dedicated
##     variants with recursive [SemType] payloads.
##   - Named types separate qualified class paths ([String]) from generic type
##     arguments ([SemType]), eliminating ':' ambiguity between nested classes
##     ('Outer:Inner') and generic parameters ('Box:Int').
##
## Formatting to strings (toKey / toDisplayString) is one-way at boundaries
## (map keys, symbol mangling, diagnostics).

Enum is SemType {
	replace [String] is namespace: ['base', 'compiler', 'ast'];

	replace [[String]] is using: [
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Empty,
	Prim(Primitive is kind),
	StrView,
	ArrayOf(SemType is elem),
	ListOf(SemType is elem),
	MapOf(SemType is key, SemType is val),
	FnOf(SemType is ret),
	Named([String] is path, [SemType] is params),

	## True when this type is unset/empty.
	Function of Boolean is isEmpty(){
		return match(on: :, when: [
			SemType:Empty: { true },
			else: { false }
		]);
	}

	## Returns the [Primitive] enum value if this is a [Prim] variant, else [Primitive:NONE].
	Function of Primitive is primitive(){
		return match(on: :, when: [
			SemType:Prim: local Function of Primitive(Primitive is kind){ return kind; },
			SemType:FnOf: local Function of Primitive(SemType is ret){ return Primitive:FUNCTION; },
			else: { Primitive:NONE }
		]);
	}

	## True when this type is a builtin primitive (including Function).
	Function of Boolean is isPrimitive(){
		return :primitive() != Primitive:NONE;
	}

	## True when this type is Void.
	Function of Boolean is isVoid(){
		return :primitive() == Primitive:VOID;
	}

	## True when this type is Any.
	Function of Boolean is isAny(){
		return :primitive() == Primitive:ANY;
	}

	## True when this type is a signed integer primitive (Int8/16/32/Int/Int128/ISize).
	Function of Boolean is isSignedInt(){
		local Primitive is p: :primitive();
		return p == Primitive:INT || p == Primitive:INT8 || p == Primitive:INT16 || p == Primitive:INT32 || p == Primitive:INT128 || p == Primitive:ISIZE;
	}

	## True when this type is an unsigned integer primitive (Byte/UInt8/16/32/64/128/USize/Rune).
	Function of Boolean is isUnsigned(){
		local Primitive is p: :primitive();
		return p == Primitive:BYTE || p == Primitive:UINT8 || p == Primitive:UINT16 || p == Primitive:UINT32 || p == Primitive:UINT64 || p == Primitive:UINT128 || p == Primitive:USIZE || p == Primitive:RUNE;
	}

	## True when this type is a floating-point primitive (Float32/Float).
	Function of Boolean is isFloat(){
		local Primitive is p: :primitive();
		return p == Primitive:FLOAT || p == Primitive:FLOAT32;
	}

	## True when this type is any integer primitive (signed or unsigned).
	Function of Boolean is isIntLike(){
		return :isSignedInt() || :isUnsigned();
	}

	## True when this type is any numeric primitive (integer or floating-point).
	Function of Boolean is isNumeric(){
		return :isIntLike() || :isFloat();
	}

	## True when this type is RawPtr.
	Function of Boolean is isRawPtr(){
		return :primitive() == Primitive:RAWPTR;
	}

	## True when this type is String or Str.
	Function of Boolean is isStringLike(){
		return match(on: :, when: [
			SemType:Prim: local Function of Boolean(Primitive is kind){ return kind == Primitive:STRING; },
			SemType:StrView: { true },
			else: { false }
		]);
	}

	## True when this type is Array (bare or parameterized).
	Function of Boolean is isArray(){
		return match(on: :, when: [
			SemType:ArrayOf: local Function of Boolean(SemType is elem){ return true; },
			else: { false }
		]);
	}

	## True when this type is List (bare or parameterized).
	Function of Boolean is isList(){
		return match(on: :, when: [
			SemType:ListOf: local Function of Boolean(SemType is elem){ return true; },
			else: { false }
		]);
	}

	## True when this type is Map (bare or parameterized).
	Function of Boolean is isMap(){
		return match(on: :, when: [
			SemType:MapOf: local Function of Boolean(SemType is key, SemType is val){ return true; },
			else: { false }
		]);
	}

	## True when this type is a builtin container (Array, List, or Map).
	Function of Boolean is isContainer(){
		return :isArray() || :isList() || :isMap();
	}

	## True when this type is a Function type (bare or with return type).
	Function of Boolean is isFunction(){
		return match(on: :, when: [
			SemType:FnOf: local Function of Boolean(SemType is ret){ return true; },
			else: { false }
		]);
	}

	## True when this type is a Function type carrying a non-empty, non-Void return type.
	Function of Boolean is hasFunctionReturn(){
		return match(on: :, when: [
			SemType:FnOf: local Function of Boolean(SemType is ret){ return !ret:isEmpty() && !ret:isVoid(); },
			else: { false }
		]);
	}

	## True when this type is a Named class/enum/type-parameter reference.
	Function of Boolean is isNamed(){
		return match(on: :, when: [
			SemType:Named: local Function of Boolean([String] is path, [SemType] is params){ return true; },
			else: { false }
		]);
	}

	## True when this type carries generic arguments.
	Function of Boolean is isGeneric(){
		return match(on: :, when: [
			SemType:ArrayOf: local Function of Boolean(SemType is elem){ return !elem:isEmpty(); },
			SemType:ListOf: local Function of Boolean(SemType is elem){ return !elem:isEmpty(); },
			SemType:MapOf: local Function of Boolean(SemType is key, SemType is val){ return !key:isEmpty() && !val:isEmpty(); },
			SemType:FnOf: local Function of Boolean(SemType is ret){ return !ret:isEmpty() && !ret:isVoid(); },
			SemType:Named: local Function of Boolean([String] is path, [SemType] is params){ return params:length() > 0; },
			else: { false }
		]);
	}

	## Returns the qualified base name (e.g. 'Int', 'Str', 'Array', 'Map', 'Function', 'Outer:Inner').
	Function of String is baseName(){
		return match(on: :, when: [
			SemType:Empty: { '' },
			SemType:Prim: local Function of String(Primitive is kind){ return kind:value(); },
			SemType:StrView: { 'Str' },
			SemType:ArrayOf: local Function of String(SemType is elem){ return 'Array'; },
			SemType:ListOf: local Function of String(SemType is elem){ return 'List'; },
			SemType:MapOf: local Function of String(SemType is key, SemType is val){ return 'Map'; },
			SemType:FnOf: local Function of String(SemType is ret){ return 'Function'; },
			SemType:Named: local Function of String([String] is path, [SemType] is params){
				if({ path:length() == 0 }, { return ''; });
				if({ path:length() == 1 }, { return path:get(index: 0); });
				local String is out: path:get(index: 0);
				range(start: 1, end: path:length(), worker: local Function(Int is i){
					out: out . ':' . path:get(index: i);
				});
				return out;
			}
		]);
	}

	## Returns the root segment of a qualified path (e.g. 'Outer' for 'Outer:Inner'), or baseName().
	Function of String is rootName(){
		return match(on: :, when: [
			SemType:Named: local Function of String([String] is path, [SemType] is params){
				if({ path:length() > 0 }, { return path:get(index: 0); });
				return '';
			},
			else: { :baseName() }
		]);
	}

	## Returns the leaf segment of a qualified path (e.g. 'Inner' for 'Outer:Inner'), or baseName().
	Function of String is leafName(){
		return match(on: :, when: [
			SemType:Named: local Function of String([String] is path, [SemType] is params){
				if({ path:length() > 0 }, { return path:get(index: path:length() - 1); });
				return '';
			},
			else: { :baseName() }
		]);
	}

	## Returns the path segments for a Named type, or an empty list for other variants.
	Function of [String] is pathSegments(){
		return match(on: :, when: [
			SemType:Named: local Function of [String]([String] is path, [SemType] is params){ return path; },
			else: { [] }
		]);
	}

	## Returns the generic parameter list for a Named type, or an empty list for other variants.
	Function of [SemType] is typeParams(){
		return match(on: :, when: [
			SemType:Named: local Function of [SemType]([String] is path, [SemType] is params){ return params; },
			else: { [] }
		]);
	}

	## Returns all generic type arguments uniformly across ArrayOf, ListOf, MapOf, FnOf, and Named.
	Function of [SemType] is allArgs(){
		return match(on: :, when: [
			SemType:ArrayOf: local Function of [SemType](SemType is elem){
				return if({ elem:isEmpty() }, { [] }, { [elem] });
			},
			SemType:ListOf: local Function of [SemType](SemType is elem){
				return if({ elem:isEmpty() }, { [] }, { [elem] });
			},
			SemType:MapOf: local Function of [SemType](SemType is key, SemType is val){
				return if({ key:isEmpty() || val:isEmpty() }, { [] }, { [key, val] });
			},
			SemType:FnOf: local Function of [SemType](SemType is ret){
				return if({ ret:isEmpty() || ret:isVoid() }, { [] }, { [ret] });
			},
			SemType:Named: local Function of [SemType]([String] is path, [SemType] is params){ return params; },
			else: { [] }
		]);
	}

	## Returns the element type of Array, List, or a 1-arg Named generic (e.g. Flow/Task/Channel), else Empty.
	Function of SemType is elemType(){
		return match(on: :, when: [
			SemType:ArrayOf: local Function of SemType(SemType is elem){ return elem; },
			SemType:ListOf: local Function of SemType(SemType is elem){ return elem; },
			SemType:Named: local Function of SemType([String] is path, [SemType] is params){
				if({ params:length() >= 1 }, { return params:get(index: 0); });
				return SemType:Empty;
			},
			else: { SemType:Empty }
		]);
	}

	## Returns the key type of a Map, else Empty.
	Function of SemType is mapKeyType(){
		return match(on: :, when: [
			SemType:MapOf: local Function of SemType(SemType is key, SemType is val){ return key; },
			else: { SemType:Empty }
		]);
	}

	## Returns the value type of a Map, else Empty.
	Function of SemType is mapValType(){
		return match(on: :, when: [
			SemType:MapOf: local Function of SemType(SemType is key, SemType is val){ return val; },
			else: { SemType:Empty }
		]);
	}

	## Returns the return type of a Function type, else Empty.
	Function of SemType is functionReturn(){
		return match(on: :, when: [
			SemType:FnOf: local Function of SemType(SemType is ret){ return ret; },
			else: { SemType:Empty }
		]);
	}

	## Deep structural equality over two [SemType] trees.
	Function of Boolean is equals(SemType is other){
		return match(on: :, when: [
			SemType:Empty: { other:isEmpty() },
			SemType:Prim: local Function of Boolean(Primitive is kind){
				return match(on: other, when: [
					SemType:Prim: local Function of Boolean(Primitive is okind){ return kind == okind; },
					else: { false }
				]);
			},
			SemType:StrView: {
				match(on: other, when: [
					SemType:StrView: { true },
					else: { false }
				])
			},
			SemType:ArrayOf: local Function of Boolean(SemType is elem){
				return match(on: other, when: [
					SemType:ArrayOf: local Function of Boolean(SemType is oelem){ return elem:equals(other: oelem); },
					else: { false }
				]);
			},
			SemType:ListOf: local Function of Boolean(SemType is elem){
				return match(on: other, when: [
					SemType:ListOf: local Function of Boolean(SemType is oelem){ return elem:equals(other: oelem); },
					else: { false }
				]);
			},
			SemType:MapOf: local Function of Boolean(SemType is key, SemType is val){
				return match(on: other, when: [
					SemType:MapOf: local Function of Boolean(SemType is okey, SemType is oval){
						return key:equals(other: okey) && val:equals(other: oval);
					},
					else: { false }
				]);
			},
			SemType:FnOf: local Function of Boolean(SemType is ret){
				return match(on: other, when: [
					SemType:FnOf: local Function of Boolean(SemType is oret){
						local Boolean is aEmpty: ret:isEmpty() || ret:isVoid();
						local Boolean is bEmpty: oret:isEmpty() || oret:isVoid();
						if({ aEmpty && bEmpty }, { return true; });
						if({ aEmpty || bEmpty }, { return false; });
						return ret:equals(other: oret);
					},
					else: { false }
				]);
			},
			SemType:Named: local Function of Boolean([String] is path, [SemType] is params){
				return match(on: other, when: [
					SemType:Named: local Function of Boolean([String] is opath, [SemType] is oparams){
						if({ path:length() != opath:length() || params:length() != oparams:length() }, {
							return false;
						});
						local Int is i: 0;
						while({ i < path:length() }, {
							if({ path:get(index: i) != opath:get(index: i) }, { return false; });
							i++;
						});
						i: 0;
						while({ i < params:length() }, {
							local SemType is pA: params:get(index: i);
							local SemType is pB: oparams:get(index: i);
							if({ !pA:equals(other: pB) }, { return false; });
							i++;
						});
						return true;
					},
					else: { false }
				]);
			}
		]);
	}

	## Recursively substitutes unbound type-parameter names found in [subst].
	Function of SemType is substitute(Map of String to SemType is subst){
		return match(on: :, when: [
			SemType:Empty: { : },
			SemType:Prim: local Function of SemType(Primitive is kind){ return :; },
			SemType:StrView: { : },
			SemType:ArrayOf: local Function of SemType(SemType is elem){
				if({ elem:isEmpty() }, { return :; });
				local SemType is ne: elem:substitute(subst: subst);
				if({ ne:equals(other: elem) }, { return :; });
				return SemType:ArrayOf(elem: ne);
			},
			SemType:ListOf: local Function of SemType(SemType is elem){
				if({ elem:isEmpty() }, { return :; });
				local SemType is ne: elem:substitute(subst: subst);
				if({ ne:equals(other: elem) }, { return :; });
				return SemType:ListOf(elem: ne);
			},
			SemType:MapOf: local Function of SemType(SemType is key, SemType is val){
				if({ key:isEmpty() && val:isEmpty() }, { return :; });
				local SemType is nk: key:substitute(subst: subst);
				local SemType is nv: val:substitute(subst: subst);
				if({ nk:equals(other: key) && nv:equals(other: val) }, { return :; });
				return SemType:MapOf(key: nk, val: nv);
			},
			SemType:FnOf: local Function of SemType(SemType is ret){
				if({ ret:isEmpty() }, { return :; });
				local SemType is nr: ret:substitute(subst: subst);
				if({ nr:equals(other: ret) }, { return :; });
				return SemType:FnOf(ret: nr);
			},
			SemType:Named: local Function of SemType([String] is path, [SemType] is params){
				if({ path:length() == 1 && params:length() == 0 }, {
					local String is nm: path:get(index: 0);
					if({ subst:has(key: nm) }, {
						return subst:get(key: nm, default: :);
					});
					return :;
				});
				if({ params:length() == 0 }, { return :; });
				local [SemType] is newParams: [];
				local Boolean is changed: false;
				times(count: params:length(), worker: local Function(Int is i){
					local SemType is p: params:get(index: i);
					local SemType is np: p:substitute(subst: subst);
					if({ !np:equals(other: p) }, { changed: true; });
					newParams:push(item: np);
				});
				if({ !changed }, { return :; });
				return SemType:Named(path: path, params: newParams);
			}
		]);
	}

	## Recursively unifies this pattern type against [concrete], recording any
	## inferred bindings for names present in [typeParams] into [bindings].
	## Returns false if a structural mismatch or conflicting binding occurs.
	Function of Boolean is unify(SemType is concrete, Map of String to Boolean is typeParams, Map of String to SemType is bindings){
		if({ :isEmpty() || concrete:isEmpty() }, { return true; });
		return match(on: :, when: [
			SemType:Named: local Function of Boolean([String] is path, [SemType] is params){
				if({ path:length() == 1 && params:length() == 0 && typeParams:has(key: path:get(index: 0)) }, {
					local String is tp: path:get(index: 0);
					if({ concrete:isVoid() }, { return false; });
					if({ bindings:has(key: tp) }, {
						local SemType is prev: bindings:get(key: tp, default: SemType:Empty);
						return prev:equals(other: concrete);
					});
					bindings:set(key: tp, value: concrete);
					return true;
				});
				return match(on: concrete, when: [
					SemType:Named: local Function of Boolean([String] is cpath, [SemType] is cparams){
						if({ path:length() != cpath:length() || params:length() != cparams:length() }, {
							return false;
						});
						local Int is i: 0;
						while({ i < path:length() }, {
							if({ path:get(index: i) != cpath:get(index: i) }, { return false; });
							i++;
						});
						i: 0;
						while({ i < params:length() }, {
							local SemType is pA: params:get(index: i);
							local SemType is pB: cparams:get(index: i);
							if({ !pA:unify(concrete: pB, typeParams: typeParams, bindings: bindings) }, { return false; });
							i++;
						});
						return true;
					},
					else: { false }
				]);
			},
			SemType:ArrayOf: local Function of Boolean(SemType is elem){
				return match(on: concrete, when: [
					SemType:ArrayOf: local Function of Boolean(SemType is celem){
						return elem:unify(concrete: celem, typeParams: typeParams, bindings: bindings);
					},
					else: { false }
				]);
			},
			SemType:ListOf: local Function of Boolean(SemType is elem){
				return match(on: concrete, when: [
					SemType:ListOf: local Function of Boolean(SemType is celem){
						return elem:unify(concrete: celem, typeParams: typeParams, bindings: bindings);
					},
					else: { false }
				]);
			},
			SemType:MapOf: local Function of Boolean(SemType is key, SemType is val){
				return match(on: concrete, when: [
					SemType:MapOf: local Function of Boolean(SemType is ckey, SemType is cval){
						return key:unify(concrete: ckey, typeParams: typeParams, bindings: bindings) && val:unify(concrete: cval, typeParams: typeParams, bindings: bindings);
					},
					else: { false }
				]);
			},
			SemType:FnOf: local Function of Boolean(SemType is ret){
				return match(on: concrete, when: [
					SemType:FnOf: local Function of Boolean(SemType is cret){
						return ret:unify(concrete: cret, typeParams: typeParams, bindings: bindings);
					},
					else: { false }
				]);
			},
			else: { :equals(other: concrete) }
		]);
	}

	## One-way canonical interned key for map lookups and symbol mangling
	## (e.g. 'Int', 'Array:String', 'Map:String:Int', 'Function:Int', 'Outer:Inner').
	Function of String is toKey(){
		return match(on: :, when: [
			SemType:Empty: { '' },
			SemType:Prim: local Function of String(Primitive is kind){ return kind:value(); },
			SemType:StrView: { 'Str' },
			SemType:ArrayOf: local Function of String(SemType is elem){
				if({ elem:isEmpty() }, { return 'Array'; });
				return ('Array:' . elem:toKey()):intern();
			},
			SemType:ListOf: local Function of String(SemType is elem){
				if({ elem:isEmpty() }, { return 'List'; });
				return ('List:' . elem:toKey()):intern();
			},
			SemType:MapOf: local Function of String(SemType is key, SemType is val){
				if({ key:isEmpty() || val:isEmpty() }, { return 'Map'; });
				return ('Map:' . key:toKey() . ':' . val:toKey()):intern();
			},
			SemType:FnOf: local Function of String(SemType is ret){
				if({ ret:isEmpty() || ret:isVoid() }, { return 'Function'; });
				return ('Function:' . ret:toKey()):intern();
			},
			SemType:Named: local Function of String([String] is path, [SemType] is params){
				if({ path:length() == 1 && params:length() == 0 }, { return path:get(index: 0); });
				local String is base: :baseName();
				if({ params:length() == 0 }, { return base; });
				local String is out: base;
				times(count: params:length(), worker: local Function(Int is i){
					local SemType is p: params:get(index: i);
					out: out . ':' . p:toKey();
				});
				return out:intern();
			}
		]);
	}

	## One-way human-readable Spec syntax for diagnostics
	## (e.g. 'Array of String', 'Map of String to Int', 'Function of Int').
	Function of String is toDisplayString(){
		return match(on: :, when: [
			SemType:Empty: { '' },
			SemType:Prim: local Function of String(Primitive is kind){ return kind:value(); },
			SemType:StrView: { 'Str' },
			SemType:ArrayOf: local Function of String(SemType is elem){
				if({ elem:isEmpty() }, { return 'Array'; });
				return 'Array ' . Keyword:OF:value() . ' ' . elem:toDisplayString();
			},
			SemType:ListOf: local Function of String(SemType is elem){
				if({ elem:isEmpty() }, { return 'List'; });
				return 'List ' . Keyword:OF:value() . ' ' . elem:toDisplayString();
			},
			SemType:MapOf: local Function of String(SemType is key, SemType is val){
				if({ key:isEmpty() || val:isEmpty() }, { return 'Map'; });
				return 'Map ' . Keyword:OF:value() . ' ' . key:toDisplayString() . ' ' . Keyword:TO:value() . ' ' . val:toDisplayString();
			},
			SemType:FnOf: local Function of String(SemType is ret){
				if({ ret:isEmpty() || ret:isVoid() }, { return 'Function'; });
				return 'Function ' . Keyword:OF:value() . ' ' . ret:toDisplayString();
			},
			SemType:Named: local Function of String([String] is path, [SemType] is params){
				if({ path:length() == 1 && params:length() == 0 }, { return path:get(index: 0); });
				local String is base: :baseName();
				if({ params:length() == 0 }, { return base; });
				local String is out: base . ' ' . Keyword:OF:value() . ' ' . params:get(index: 0):toDisplayString();
				range(start: 1, end: params:length(), worker: local Function(Int is i){
					out: out . ' ' . Keyword:TO:value() . ' ' . params:get(index: i):toDisplayString();
				});
				return out;
			}
		]);
	}

	## Converts this [SemType] back to an AST [Type] node for legacy bridges.
	Function of Type is toAstType(){
		return match(on: :, when: [
			SemType:Empty: { Type:EMPTY },
			SemType:Prim: local Function of Type(Primitive is kind){ return Type:init(name: kind:value()); },
			SemType:StrView: { Type:init(name: 'Str') },
			SemType:ArrayOf: local Function of Type(SemType is elem){
				if({ elem:isEmpty() }, { return Type:init(name: 'Array'); });
				return Type:withParams(name: 'Array', params: [elem:toAstType()]);
			},
			SemType:ListOf: local Function of Type(SemType is elem){
				if({ elem:isEmpty() }, { return Type:init(name: 'List'); });
				return Type:withParams(name: 'List', params: [elem:toAstType()]);
			},
			SemType:MapOf: local Function of Type(SemType is key, SemType is val){
				if({ key:isEmpty() || val:isEmpty() }, { return Type:init(name: 'Map'); });
				return Type:withParams(name: 'Map', params: [key:toAstType(), val:toAstType()]);
			},
			SemType:FnOf: local Function of Type(SemType is ret){
				if({ ret:isEmpty() || ret:isVoid() }, { return Type:init(name: 'Function'); });
				return Type:withParams(name: 'Function', params: [ret:toAstType()]);
			},
			SemType:Named: local Function of Type([String] is path, [SemType] is params){
				local String is base: :baseName();
				if({ params:length() == 0 }, { return Type:init(name: base); });
				local [Type] is ps: [];
				times(count: params:length(), worker: local Function(Int is i){
					ps:push(item: params:get(index: i):toAstType());
				});
				return Type:withParams(name: base, params: ps);
			}
		]);
	}
}
