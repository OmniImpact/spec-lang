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
	[String] is fieldNames: [];
	[IrType] is fieldTypes: [];
	[Boolean] is fieldIsArc: [];
	[String] is vtableMethodNames: [];
	[String] is vtableFns: [];
	[String] is baseNames: [];
	String is constructFn: 'null';
	String is destroyFn: 'null';
	[String] is metaMethodNames: [];
	[String] is metaMethodFns: [];
	[Int] is metaMethodFlags: [];
	[Int] is metaMethodLines: [];
	[String] is metaFieldNames: [];
	[String] is metaFieldTypes: [];
	[Int] is metaFieldIndices: [];
	[Int] is metaFieldFlags: [];
	[String] is heldNames: [];
	[String] is heldGetters: [];

	replace Function is init(){
	}

	replace Function is init(String is name){
		:name: name;
	}

	Function of Int is addField(String is name, IrType is ty){
		local Int is idx: :fieldNames:length();
		:fieldNames:push(item: name);
		:fieldTypes:push(item: ty);
		local Boolean is isPtr: ty == IrType:Ptr;
		:fieldIsArc:push(item: isPtr);
		return idx;
	}

	Function of Int is addFieldArc(String is name, IrType is ty, Boolean is isArc){
		local Int is idx: :fieldNames:length();
		:fieldNames:push(item: name);
		:fieldTypes:push(item: ty);
		:fieldIsArc:push(item: isArc);
		return idx;
	}

	Function of Int is fieldIndex(String is name){
		local Int is res: -1;
		while([Int is i: 0], { i < :fieldNames:length() && res < 0 }, {
			if({ :fieldNames:get(index: i) == name }, {
				res: i;
			});
			i++;
		});
		return res;
	}

	Function of Int is vtableSlot(String is mname){
		local Int is res: -1;
		while([Int is i: 0], { i < :vtableMethodNames:length() && res < 0 }, {
			if({ :vtableMethodNames:get(index: i) == mname }, {
				res: i;
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
			:vtableMethodNames:push(item: mname);
			:vtableFns:push(item: fnName);
		});
	}
}
