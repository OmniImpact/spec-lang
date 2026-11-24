#! Package base:compiler:ast
#! A type reference in the source: a base name plus optional generic arguments.
##
## AST nodes are transparent data records: fields are public because the
## compiler passes (parser, checker, generator) read and write them
## directly; behavior lives in the passes, except where noted.

Class is Type{
	replace [String] is namespace: ['base', 'compiler', 'ast'];

	replace [[String]] is using: [
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## Shared empty sentinel for read-only default/fallback returns.
	held Type is EMPTY: Type:init(name: '');

	## Base type identifier (e.g. Int, String, Array).
	String is name: '';

	## Generic type arguments (e.g. String in Array of String).
	[Type] is params: [];

	## Initializes a simple type descriptor.
	##
	## @param name: Base type name.
	replace Function is init(String is name){
		:name: name;
	}

	## Produces a parameterized generic type descriptor. Self-free
	## factory: Type is field-ful, so this call never goes through the
	## elided instance path (E2 v1); it constructs explicitly.
	##
	## @param name: Base type name.
	## @param params: Generic type arguments.
	## @return: The new [Type].
	held Function of Type is withParams(String is name, [Type] is params){
		local Type is t: Type(name: name);
		t:params: params;
		return t;
	}

	## Structural equality over the [Type] tree (`:name` and `:params`).
	Function of Boolean is equals(Type is other){
		if({ :name != other:name || :params:length() != other:params:length() }, {
			return false;
		});
		local Int is i: 0;
		while({ i < :params:length() }, {
			local Type is pA: :params:get(index: i);
			local Type is pB: other:params:get(index: i);
			if({ !pA:equals(other: pB) }, {
				return false;
			});
			i++;
		});
		return true;
	}

	## Deep clone of this [Type] tree.
	Function of Type is clone(){
		if({ :params:length() == 0 }, {
			return Type:init(name: :name);
		});
		local [Type] is cp: [];
		local Int is i: 0;
		while({ i < :params:length() }, {
			local Type is p: :params:get(index: i);
			cp:push(item: p:clone());
			i++;
		});
		return Type:withParams(name: :name, params: cp);
	}

	## True when this type carries generic arguments.
	##
	## @return: true when [params] is non-empty.
	Function of Boolean is isGeneric(){
		return :params:length() > 0;
	}

	## True when this type descriptor is unset/empty.
	Function of Boolean is isEmpty(){
		return :name == '';
	}

	## Resolves the base name against the authoritative [Primitive] enum.
	Function of Primitive is primitive(){
		return Primitive:of(:name);
	}

	## True when this type is a builtin primitive (not a class).
	Function of Boolean is isPrimitive(){
		return Primitive:of(:name) != Primitive:NONE;
	}

	## True when this type is Void.
	Function of Boolean is isVoid(){
		return Primitive:of(:name) == Primitive:VOID;
	}

	## True when this type is Any.
	Function of Boolean is isAny(){
		return Primitive:of(:name) == Primitive:ANY;
	}

	## True when this type is a signed integer primitive (Int8/16/32/Int/Int128/ISize).
	Function of Boolean is isSignedInt(){
		local Primitive is p: Primitive:of(:name);
		return p == Primitive:INT || p == Primitive:INT8 || p == Primitive:INT16 || p == Primitive:INT32 || p == Primitive:INT128 || p == Primitive:ISIZE;
	}

	## True when this type is an unsigned integer primitive (Byte/UInt8/16/32/64/128/USize/Rune).
	Function of Boolean is isUnsigned(){
		local Primitive is p: Primitive:of(:name);
		return p == Primitive:BYTE || p == Primitive:UINT8 || p == Primitive:UINT16 || p == Primitive:UINT32 || p == Primitive:UINT64 || p == Primitive:UINT128 || p == Primitive:USIZE || p == Primitive:RUNE;
	}

	## True when this type is a floating-point primitive (Float32/Float).
	Function of Boolean is isFloat(){
		local Primitive is p: Primitive:of(:name);
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
		return Primitive:of(:name) == Primitive:RAWPTR;
	}

	## True when this type is String or Str.
	Function of Boolean is isStringLike(){
		return Primitive:of(:name) == Primitive:STRING || :name == 'Str';
	}

	## True when this type is Array (bare or parameterized).
	Function of Boolean is isArray(){
		return :name == 'Array';
	}

	## True when this type is List (bare or parameterized).
	Function of Boolean is isList(){
		return :name == 'List';
	}

	## True when this type is Map (bare or parameterized).
	Function of Boolean is isMap(){
		return :name == 'Map';
	}

	## True when this type is Function (bare or with return type).
	Function of Boolean is isFunction(){
		return Primitive:of(:name) == Primitive:FUNCTION;
	}

	## True when this type is a builtin container (Array, List, or Map).
	Function of Boolean is isContainer(){
		return :name == 'Array' || :name == 'List' || :name == 'Map';
	}

	## Returns the single element type of a 1-arg generic, or an empty [Type].
	Function of Type is elemType(){
		if({ :params:length() >= 1 }, {
			return :params:get(index: 0);
		});
		return Type:EMPTY;
	}

	## Returns the key type of a parameterized Map, or an empty [Type].
	Function of Type is mapKeyType(){
		if({ :name == 'Map' && :params:length() >= 1 }, {
			return :params:get(index: 0);
		});
		return Type:EMPTY;
	}

	## Returns the value type of a parameterized Map, or an empty [Type].
	Function of Type is mapValType(){
		if({ :name == 'Map' && :params:length() >= 2 }, {
			return :params:get(index: 1);
		});
		return Type:EMPTY;
	}

	## Returns the return type of a Function type, or an empty [Type].
	Function of Type is functionReturn(){
		if({ Primitive:of(:name) == Primitive:FUNCTION && :params:length() >= 1 }, {
			return :params:get(index: 0);
		});
		return Type:EMPTY;
	}

	## Formats the type into canonical Spec syntax
	## (e.g. Array of String, Map of String to Int). The joining keywords
	## resolve from the Keyword enum so formatting cannot drift from the
	## lexer's keyword set.
	##
	## @return: Canonical type string.
	replace Function of String is toString(){
		if({ :params:length() == 0 }, {
			return :name;
		});
		if({ :params:length() == 1 }, {
			local Type is p0: :params:get(index: 0);
			return :name . ' ' . Keyword:OF:value() . ' ' . p0:toString();
		});
		local Type is first: :params:get(index: 0);
		local Type is second: :params:get(index: 1);
		return :name . ' ' . Keyword:OF:value() . ' ' . first:toString() . ' ' . Keyword:TO:value() . ' ' . second:toString();
	}
}
