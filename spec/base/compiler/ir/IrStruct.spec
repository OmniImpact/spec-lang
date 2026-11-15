#! Package base:compiler:ir
#! Struct layout descriptor in an IR module.

Class is IrStruct{
	namespace: ['base', 'compiler', 'ir'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ir', IrType],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	String is name: '';
	Array of String is fieldNames: [];
	Array of IrType is fieldTypes: [];

	replace Function is init(){
	}

	Function is init(String is name){
		self:name: name;
	}

	Function of Int is addField(String is name, IrType is ty){
		local Int is idx: self:fieldNames:length();
		self:fieldNames:add(item: name);
		self:fieldTypes:add(item: ty);
		return idx;
	}

	Function of Int is fieldIndex(String is name){
		local Int is i: 0;
		while({ i < self:fieldNames:length() }, {
			if({ self:fieldNames:get(index: i, default: '') == name }, {
				return i;
			});
			i++;
		});
		return -1;
	}
}
