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

	[IrStruct] is structs: [];
	[IrFunction] is functions: [];
	[String] is stringLiterals: [];
	Map of String to Int is stringIds: Map();
	[String] is globalNames: [];
	[IrType] is globalTypes: [];
	[String] is globalInits: [];
	String is entryFunction: '';

	replace Function is init(){
	}

	Function is addGlobal(String is name, IrType is ty, String is initVal){
		:globalNames:push(item: name);
		:globalTypes:push(item: ty);
		:globalInits:push(item: initVal);
	}

	Function of Int is internStringLiteral(String is value){
		if({ :stringIds:has(key: value) }, {
			return :stringIds:get(key: value, default: 0);
		});
		local Int is id: :stringLiterals:length();
		:stringLiterals:push(item: value);
		:stringIds:set(key: value, value: id);
		return id;
	}

	Function is addStruct(IrStruct is s){
		:structs:push(item: s);
	}

	Function is addFunction(IrFunction is fn){
		:functions:push(item: fn);
	}

	Function of IrStruct is findStruct(String is name){
		local Int is i: 0;
		local Boolean is found: false;
		local IrStruct is res: IrStruct:init(name: '');
		while({ i < :structs:length() && !found }, {
			local IrStruct is s: :structs:get(index: i);
			if({ s:name == name }, {
				res: s;
				found: true;
			});
			i++;
		});
		return res;
	}
}
