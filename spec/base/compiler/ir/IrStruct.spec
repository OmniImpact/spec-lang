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
	Array of String is vtableMethodNames: [];
	Array of String is vtableFns: [];

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
		local Int is res: -1;
		local Boolean is found: false;
		while({ i < self:fieldNames:length() && !found }, {
			if({ self:fieldNames:get(index: i, default: '') == name }, {
				res: i;
				found: true;
			});
			i++;
		});
		return res;
	}

	Function of Int is vtableSlot(String is mname){
		local Int is i: 0;
		local Int is res: -1;
		local Boolean is found: false;
		while({ i < self:vtableMethodNames:length() && !found }, {
			if({ self:vtableMethodNames:get(index: i, default: '') == mname }, {
				res: i;
				found: true;
			});
			i++;
		});
		return res;
	}

	Function is setVtableMethod(String is mname, String is fnName){
		local Int is idx: self:vtableSlot(mname: mname);
		if({ idx >= 0 }, {
			if({ fnName != 'null' }, {
				self:vtableFns:set(index: idx, value: fnName);
			});
		}, {
			self:vtableMethodNames:add(item: mname);
			self:vtableFns:add(item: fnName);
		});
	}
}
