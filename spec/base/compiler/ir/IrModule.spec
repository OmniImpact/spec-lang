#! Package base:compiler:ir
#! Top-level IR module containing structs, string literals, and functions.

Class is IrModule{
	namespace: ['base', 'compiler', 'ir'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ir', IrStruct],
		['base', 'compiler', 'ir', IrFunction],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Array of IrStruct is structs: [];
	Array of IrFunction is functions: [];
	Array of String is stringLiterals: [];
	Map of String to Int is stringIds: Map:init();
	String is entryFunction: '';

	replace Function is init(){
	}

	Function of Int is internStringLiteral(String is value){
		if({ self:stringIds:has(key: value) }, {
			return self:stringIds:get(key: value, default: 0);
		});
		local Int is id: self:stringLiterals:length();
		self:stringLiterals:add(item: value);
		self:stringIds:set(key: value, value: id);
		return id;
	}

	Function is addStruct(IrStruct is s){
		self:structs:add(item: s);
	}

	Function is addFunction(IrFunction is fn){
		self:functions:add(item: fn);
	}

	Function of IrStruct is findStruct(String is name){
		local Int is i: 0;
		while({ i < self:structs:length() }, {
			local IrStruct is s: self:structs:get(index: i);
			if({ s:name == name }, {
				return s;
			});
			i++;
		});
		return IrStruct:init(name: '');
	}
}
