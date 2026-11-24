#! Package base:compiler:checker
#! Zero-allocation singleton cache and factory helpers for [SemType].
##
## Lives in base:compiler:checker (outside the AST arena) so the held
## singletons for primitives, Str, Empty, and bare containers remain immortal
## across compilation phases without ARC churn on every expression check.

Class is SemTypes{
	replace [String] is namespace: ['base', 'compiler', 'checker'];

	replace [[String]] is using: [
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', 'ast', SemType],
		['base', 'compiler', 'ast', Type],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	held SemType is EMPTY: SemType:Empty;
	held SemType is VOID: SemType:Prim(kind: Primitive:VOID);
	held SemType is ANY: SemType:Prim(kind: Primitive:ANY);
	held SemType is INT: SemType:Prim(kind: Primitive:INT);
	held SemType is INT8: SemType:Prim(kind: Primitive:INT8);
	held SemType is INT16: SemType:Prim(kind: Primitive:INT16);
	held SemType is INT32: SemType:Prim(kind: Primitive:INT32);
	held SemType is INT128: SemType:Prim(kind: Primitive:INT128);
	held SemType is ISIZE: SemType:Prim(kind: Primitive:ISIZE);
	held SemType is FLOAT: SemType:Prim(kind: Primitive:FLOAT);
	held SemType is FLOAT32: SemType:Prim(kind: Primitive:FLOAT32);
	held SemType is BOOLEAN: SemType:Prim(kind: Primitive:BOOLEAN);
	held SemType is STRING: SemType:Prim(kind: Primitive:STRING);
	held SemType is STR: SemType:StrView;
	held SemType is BYTE: SemType:Prim(kind: Primitive:BYTE);
	held SemType is UINT8: SemType:Prim(kind: Primitive:UINT8);
	held SemType is UINT16: SemType:Prim(kind: Primitive:UINT16);
	held SemType is UINT32: SemType:Prim(kind: Primitive:UINT32);
	held SemType is UINT64: SemType:Prim(kind: Primitive:UINT64);
	held SemType is UINT128: SemType:Prim(kind: Primitive:UINT128);
	held SemType is USIZE: SemType:Prim(kind: Primitive:USIZE);
	held SemType is RUNE: SemType:Prim(kind: Primitive:RUNE);
	held SemType is RAWPTR: SemType:Prim(kind: Primitive:RAWPTR);
	held SemType is BARE_ARRAY: SemType:ArrayOf(elem: SemType:Empty);
	held SemType is BARE_LIST: SemType:ListOf(elem: SemType:Empty);
	held SemType is BARE_MAP: SemType:MapOf(key: SemType:Empty, val: SemType:Empty);
	held SemType is BARE_FN: SemType:FnOf(ret: SemType:Empty);

	## Returns the cached singleton [SemType] for [kind].
	Function of SemType is prim(Primitive is kind){
		return match(on: kind, when: [
			Primitive:NONE: { SemTypes:EMPTY },
			Primitive:INT: { SemTypes:INT },
			Primitive:INT8: { SemTypes:INT8 },
			Primitive:INT16: { SemTypes:INT16 },
			Primitive:INT32: { SemTypes:INT32 },
			Primitive:INT128: { SemTypes:INT128 },
			Primitive:ISIZE: { SemTypes:ISIZE },
			Primitive:FLOAT: { SemTypes:FLOAT },
			Primitive:FLOAT32: { SemTypes:FLOAT32 },
			Primitive:BOOLEAN: { SemTypes:BOOLEAN },
			Primitive:STRING: { SemTypes:STRING },
			Primitive:BYTE: { SemTypes:BYTE },
			Primitive:UINT8: { SemTypes:UINT8 },
			Primitive:UINT16: { SemTypes:UINT16 },
			Primitive:UINT32: { SemTypes:UINT32 },
			Primitive:UINT64: { SemTypes:UINT64 },
			Primitive:UINT128: { SemTypes:UINT128 },
			Primitive:USIZE: { SemTypes:USIZE },
			Primitive:RUNE: { SemTypes:RUNE },
			Primitive:RAWPTR: { SemTypes:RAWPTR },
			Primitive:VOID: { SemTypes:VOID },
			Primitive:ANY: { SemTypes:ANY },
			Primitive:FUNCTION: { SemTypes:BARE_FN }
		]);
	}

	## Constructs a [SemType:Array], reusing [BARE_ARRAY] when [elem] is empty.
	Function of SemType is arrayOf(SemType is elem){
		if({ elem:isEmpty() }, { return SemTypes:BARE_ARRAY; });
		return SemType:ArrayOf(elem: elem);
	}

	## Constructs a [SemType:List], reusing [BARE_LIST] when [elem] is empty.
	Function of SemType is listOf(SemType is elem){
		if({ elem:isEmpty() }, { return SemTypes:BARE_LIST; });
		return SemType:ListOf(elem: elem);
	}

	## Constructs a [SemType:Map], reusing [BARE_MAP] when [key] or [val] is empty.
	Function of SemType is mapOf(SemType is key, SemType is val){
		if({ key:isEmpty() || val:isEmpty() }, { return SemTypes:BARE_MAP; });
		return SemType:MapOf(key: key, val: val);
	}

	## Constructs a [SemType:Fn], reusing [BARE_FN] when [ret] is empty or Void.
	Function of SemType is fnOf(SemType is ret){
		if({ ret:isEmpty() || ret:isVoid() }, { return SemTypes:BARE_FN; });
		return SemType:FnOf(ret: ret);
	}

	## Splits a qualified class name ('Outer:Inner') into path segments.
	Function of [String] is splitPath(String is name){
		if({ name == '' }, { return []; });
		if({ !name:contains(needle: ':') }, { return [name]; });
		local Array of String is parts: name:split(delimiter: ':');
		local [String] is out: [];
		times(count: parts:length(), worker: local Function(Int is i){
			local String is seg: parts:get(index: i, default: '');
			if({ seg != '' }, { out:push(item: seg); });
		});
		return out;
	}

	## Constructs a [SemType:Named] from a class name (possibly qualified like 'Outer:Inner').
	Function of SemType is named(String is name){
		if({ name == '' }, { return SemTypes:EMPTY; });
		if({ name == 'Str' }, { return SemTypes:STR; });
		local Primitive is p: Primitive:of(name);
		if({ p != Primitive:NONE }, { return :prim(kind: p); });
		if({ name == 'Array' }, { return SemTypes:BARE_ARRAY; });
		if({ name == 'List' }, { return SemTypes:BARE_LIST; });
		if({ name == 'Map' }, { return SemTypes:BARE_MAP; });
		return SemType:Named(path: :splitPath(name: name), params: []);
	}

	## Constructs a parameterized [SemType:Named] (or builtin container/Fn when applicable).
	Function of SemType is namedWithParams(String is name, [SemType] is params){
		if({ name == '' }, { return SemTypes:EMPTY; });
		if({ params:length() == 0 }, { return :named(name: name); });
		return match(on: name, when: [
			'Array': { :arrayOf(elem: params:get(index: 0)) },
			'List': { :listOf(elem: params:get(index: 0)) },
			'Map': {
				if({ params:length() >= 2 }, {
					:mapOf(key: params:get(index: 0), val: params:get(index: 1))
				}, {
					SemTypes:BARE_MAP
				})
			},
			'Function': {
				local SemType is ret: if({ params:length() >= 2 }, { params:get(index: 1) }, { params:get(index: 0) });
				:fnOf(ret: ret)
			},
			else: { SemType:Named(path: :splitPath(name: name), params: params) }
		]);
	}

	## Constructs a [SemType:Named] directly from explicit path segments and params.
	Function of SemType is namedPath([String] is path, [SemType] is params){
		if({ path:length() == 0 }, { return SemTypes:EMPTY; });
		if({ path:length() == 1 }, {
			return :namedWithParams(name: path:get(index: 0), params: params);
		});
		return SemType:Named(path: path, params: params);
	}

	## Converts a parser AST [Type] tree into a canonical [SemType] tree.
	Function of SemType is fromAstType(Type is t){
		if({ t:name == '' }, { return SemTypes:EMPTY; });
		if({ t:params:length() == 0 }, {
			return :named(name: t:name);
		});
		local [SemType] is ps: [];
		times(count: t:params:length(), worker: local Function(Int is i){
			ps:push(item: :fromAstType(t: t:params:get(index: i)));
		});
		return :namedWithParams(name: t:name, params: ps);
	}
}
