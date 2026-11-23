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
	String is qualifiedName: '';
	String is sourceFileBase: '';
	Array of String is fieldNames: Array();
	[IrType] is fieldTypes: [];
	[Boolean] is fieldIsArc: [];
	Array of String is vtableMethodNames: Array();
	Array of String is vtableFns: Array();
	Array of String is baseNames: Array();
	String is constructFn: 'null';
	String is destroyFn: 'null';
	Array of String is metaMethodNames: Array();
	Array of String is metaMethodFns: Array();
	[Int] is metaMethodFlags: [];
	[Int] is metaMethodLines: [];
	Array of String is metaFieldNames: Array();
	Array of String is metaFieldTypes: Array();
	[Int] is metaFieldIndices: [];
	[Int] is metaFieldFlags: [];
	Array of String is heldNames: Array();
	Array of String is heldGetters: Array();

	replace Function is init(){
	}

	replace Function is init(String is name){
		:name: name;
	}

	Function of Int is addField(String is name, IrType is ty){
		local Int is idx: :fieldNames:length();
		:fieldNames:add(item: name);
		:fieldTypes:push(item: ty);
		local Boolean is isPtr: ty == IrType:Ptr;
		:fieldIsArc:push(item: isPtr);
		return idx;
	}

	Function of Int is addFieldArc(String is name, IrType is ty, Boolean is isArc){
		local Int is idx: :fieldNames:length();
		:fieldNames:add(item: name);
		:fieldTypes:push(item: ty);
		:fieldIsArc:push(item: isArc);
		return idx;
	}

	Function of Int is fieldIndex(String is name){
		local Int is i: 0;
		local Int is res: -1;
		local Boolean is found: false;
		while({ i < :fieldNames:length() && !found }, {
			if({ :fieldNames:get(index: i, default: '') == name }, {
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
		while({ i < :vtableMethodNames:length() && !found }, {
			if({ :vtableMethodNames:get(index: i, default: '') == mname }, {
				res: i;
				found: true;
			});
			i++;
		});
		return res;
	}

	Function is setVtableMethod(String is mname, String is fnName){
		local Int is idx: :vtableSlot(mname: mname);
		if({ idx >= 0 }, {
			if({ fnName != 'null' }, {
				:vtableFns:set(index: idx, item: fnName);
			});
		}, {
			:vtableMethodNames:add(item: mname);
			:vtableFns:add(item: fnName);
		});
	}
}
