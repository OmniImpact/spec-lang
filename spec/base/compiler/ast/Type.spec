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
		['base', 'sys', as Conditional()]
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

	## Produces a parameterized generic type descriptor. Self-free
	## factory: Type is field-ful, so this call never goes through the
	## elided instance path (E2 v1); it constructs explicitly.
	##
	## @param name: Base type name.
	## @param params: Generic type arguments.
	## @return: The new [Type].
	Function of Type is withParams(String is name, Array of Type is params){
		local Type is t: Type:init(name: name);
		t:params: params;
		return t;
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
		Conditional:if(check: { self:params:length() == 0 }, then: {
			return self:name;
		});
		Conditional:if(check: { self:params:length() == 1 }, then: {
			local Type is p0: self:params:get(index: 0);
			return self:name . ' ' . Keyword:OF:value() . ' ' . p0:toString();
		});
		local Type is first: self:params:get(index: 0);
		local Type is second: self:params:get(index: 1);
		return self:name . ' ' . Keyword:OF:value() . ' ' . first:toString() . ' ' . Keyword:TO:value() . ' ' . second:toString();
	}
}
