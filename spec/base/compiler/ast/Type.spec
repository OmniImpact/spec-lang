#! Package base:compiler:ast
#! A type reference in the source: a base name plus optional generic arguments.
##
## AST nodes are transparent data records: fields are public because the
## compiler passes (parser, checker, generator) read and write them
## directly; behavior lives in the passes, except where noted.

Class is Type{
	namespace: ['base', 'compiler', 'ast'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'lexer', Keyword],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## Base type identifier (e.g. Int, String, Array).
	String is name: '';

	## Generic type arguments (e.g. String in Array of String).
	Array of Type is params: [];

	## Initializes a simple type descriptor.
	##
	## @param name: Base type name.
	replace Function is init(String is name){
		:name: name;
		:params: [];
	}

	## Produces a parameterized generic type descriptor. Self-free
	## factory: Type is field-ful, so this call never goes through the
	## elided instance path (E2 v1); it constructs explicitly.
	##
	## @param name: Base type name.
	## @param params: Generic type arguments.
	## @return: The new [Type].
	held Function of Type is withParams(String is name, Array of Type is params){
		local Type is t: Type:init(name: name);
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
		local Array of Type is cp: [];
		local Int is i: 0;
		while({ i < :params:length() }, {
			local Type is p: :params:get(index: i);
			cp:add(item: p:clone());
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
