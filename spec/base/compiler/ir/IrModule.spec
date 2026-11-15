#! Package base:compiler:ir
#! Top-level IR module containing structs, string literals, and functions.

Class is IrModule{
	namespace: ['base', 'compiler', 'ir'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ir', IrType],
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
	Array of String is globalNames: [];
	Array of IrType is globalTypes: [];
	Array of String is globalInits: [];
	String is entryFunction: '';

	replace Function is init(){
	}

	Function is addGlobal(String is name, IrType is ty, String is initVal){
		self:globalNames:add(item: name);
		self:globalTypes:add(item: ty);
		self:globalInits:add(item: initVal);
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
		local Boolean is found: false;
		local IrStruct is res: IrStruct:init(name: '');
		while({ i < self:structs:length() && !found }, {
			local IrStruct is s: self:structs:get(index: i);
			if({ s:name == name }, {
				res: s;
				found: true;
			});
			i++;
		});
		return res;
	}
}
