#! Package base:compiler:ast
#! A type reference in the source: a base name plus optional generic arguments.
##
## AST nodes are transparent data records: fields are public because the
## compiler passes (parser, checker, generator) read and write them
## directly; behavior lives in the passes, except where noted.

Class is Type{
	namespace: ['base', 'compiler', 'ast'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'lexer', Keyword]
	];

	## Base type identifier (e.g. Int, String, Array).
	String is name: '';

	## Generic type arguments (e.g. String in Array of String).
	Array of Type is params: [];

	## Initializes a simple type descriptor.
	##
	## @param name: Base type name.
	replace Function is init(String is name){
		self:name: name;
		self:params: [];
	}

	## Initializes a parameterized generic type descriptor.
	##
	## @param name: Base type name.
	## @param params: Generic type arguments.
	Function is withParams(String is name, Array of Type is params){
		self:name: name;
		self:params: params;
	}

	## True when this type carries generic arguments.
	##
	## @return: true when [params] is non-empty.
	Function of Boolean is isGeneric(){
		return self:params:length() > 0;
	}

	## Formats the type into canonical Spec syntax
	## (e.g. Array of String, Map of String to Int). The joining keywords
	## resolve from the Keyword enum so formatting cannot drift from the
	## lexer's keyword set.
	##
	## @return: Canonical type string.
	replace Function of String is toString(){
		if (self:params:length() == 0) {
			return self:name;
		}
		if (self:params:length() == 1) {
			local Type is p0: self:params:get(index: 0);
			return self:name . ' ' . Keyword:OF:value() . ' ' . p0:toString();
		}
		local Type is first: self:params:get(index: 0);
		local Type is second: self:params:get(index: 1);
		return self:name . ' ' . Keyword:OF:value() . ' ' . first:toString() . ' ' . Keyword:TO:value() . ' ' . second:toString();
	}
}
