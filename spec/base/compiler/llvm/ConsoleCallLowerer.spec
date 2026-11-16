#! Package base:compiler:llvm
#! Lowers Output/Console sysinternal calls (line, print) to Spec IR.

Class of SysinternalCallLowerer is ConsoleCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', SysinternalCallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ir', IrType],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'ConsoleCallLowerer';
	}

	replace Function of Int is order(){
		return 15;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		if({ self:isFloorTarget(call: call, domain: 'Terminal') }, {
			return nm == 'init' || nm == 'term_width' || nm == 'term_height';
		});
		if({ !self:isFloorTarget(call: call, domain: 'Console') }, { return false; });
		if({ nm == 'init' || nm == 'console_binary_mode' }, { return true; });
		if({ (nm == 'read_bytes' || nm == 'read_line' || nm == 'print_line' || nm == 'print' || nm == 'error_line') && call:args:length() >= 1 }, {
			return true;
		});
		return false;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		if({ call:name == 'init' }, { return 'null'; });
		if({ call:name == 'console_binary_mode' }, {
			return self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_console_binary_mode', argTypes: [], args: []);
		});
		if({ call:name == 'read_bytes' }, {
			local String is cnt: self:lowerArg(b: b, call: call, idx: 0);
			local String is res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_read_bytes', argTypes: [IrType:I64], args: [cnt]);
			b:emitClaimPool(val: res);
			return res;
		});
		if({ call:name == 'read_line' }, {
			local String is cb: self:lowerArg(b: b, call: call, idx: 0);
			return self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_read_line', argTypes: [IrType:Ptr], args: [cb]);
		});
		if({ call:name == 'term_width' }, {
			return self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_term_width', argTypes: [], args: []);
		});
		if({ call:name == 'term_height' }, {
			return self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_term_height', argTypes: [], args: []);
		});
		local String is txt: self:lowerArg(b: b, call: call, idx: 0);
		if({ call:name == 'print_line' }, {
			return self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_print_line', argTypes: [IrType:Ptr], args: [txt]);
		});
		if({ call:name == 'error_line' }, {
			return self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_error_line', argTypes: [IrType:Ptr], args: [txt]);
		});
		return self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_print', argTypes: [IrType:Ptr], args: [txt]);
	}
}
