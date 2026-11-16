#! Package base:compiler:llvm
#! Canonical field layouts for C-ABI runtime structs emitted by LlvmEmitter.
##
## Centralizes field order, LLVM types, constant aggregate formatting, and
## named field indices so LlvmEmitter and IrBuilder do not duplicate raw
## '{ ptr, ptr, i32 }' literals or magic GEP offsets.

Class is LlvmStructLayout{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	String is structName: '';
	Array of String is fieldNames: [];
	Array of String is fieldTypes: [];

	replace Function is init(String is structName: ''){
		self:structName: structName;
	}

	Function of LlvmStructLayout is addField(String is name, String is llvmType){
		self:fieldNames:add(item: name);
		self:fieldTypes:add(item: llvmType);
		return self;
	}

	Function of Int is fieldCount(){
		return self:fieldNames:length();
	}

	Function of Int is fieldIndex(String is name){
		local Int is found: -1;
		local Int is i: 0;
		while({ i < self:fieldNames:length() }, {
			if({ found < 0 && self:fieldNames:get(index: i, default: '') == name }, {
				found: i;
			});
			i++;
		});
		return found;
	}

	Function of String is llvmType(){
		local String is body: '';
		local Int is i: 0;
		while({ i < self:fieldTypes:length() }, {
			if({ i > 0 }, { body: body . ', '; });
			body: body . self:fieldTypes:get(index: i, default: 'ptr');
			i++;
		});
		return '{ ' . body . ' }';
	}

	Function of String is formatConst(Array of String is values){
		local String is body: '';
		local Int is i: 0;
		while({ i < self:fieldTypes:length() }, {
			if({ i > 0 }, { body: body . ', '; });
			local String is ty: self:fieldTypes:get(index: i, default: 'ptr');
			local String is val: values:get(index: i, default: 'null');
			body: body . ty . ' ' . val;
			i++;
		});
		return self:llvmType() . ' { ' . body . ' }';
	}

	held Function of LlvmStructLayout is objHeader(){
		local LlvmStructLayout is s: LlvmStructLayout:init(structName: 'ObjHeader');
		s:addField(name: 'type_name', llvmType: 'ptr');
		s:addField(name: 'vtable', llvmType: 'ptr');
		return s;
	}

	held Function of LlvmStructLayout is methodMeta(){
		local LlvmStructLayout is s: LlvmStructLayout:init(structName: 'SpecMethodMeta');
		s:addField(name: 'name', llvmType: 'ptr');
		s:addField(name: 'fn', llvmType: 'ptr');
		s:addField(name: 'flags', llvmType: 'i32');
		s:addField(name: 'line', llvmType: 'i32');
		return s;
	}

	held Function of LlvmStructLayout is classMeta(){
		local LlvmStructLayout is s: LlvmStructLayout:init(structName: 'SpecClassMeta');
		s:addField(name: 'name', llvmType: 'ptr');
		s:addField(name: 'source_file', llvmType: 'ptr');
		s:addField(name: 'base_names', llvmType: 'ptr');
		s:addField(name: 'base_count', llvmType: 'i32');
		s:addField(name: 'construct', llvmType: 'ptr');
		s:addField(name: 'methods', llvmType: 'ptr');
		s:addField(name: 'method_count', llvmType: 'i32');
		return s;
	}

	held Function of LlvmStructLayout is heldEntry(){
		local LlvmStructLayout is s: LlvmStructLayout:init(structName: 'SpecHeldEntry');
		s:addField(name: 'type_name', llvmType: 'ptr');
		s:addField(name: 'names', llvmType: 'ptr');
		s:addField(name: 'count', llvmType: 'i32');
		s:addField(name: 'getters', llvmType: 'ptr');
		return s;
	}
}
