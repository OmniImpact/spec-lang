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
		local String is r: self:receiverName(call: call);
		if({ nm == 'init' }, { return r == 'Output' || r == 'Console' || r == 'Stderr' || r == 'Terminal'; });
		if({ nm == 'console_binary_mode' && (r == '' || r == 'Console') }, { return true; });
		if({ (nm == 'read_bytes' || nm == 'read_line') && (r == '' || r == 'Console') && call:args:length() >= 1 }, { return true; });
		if({ (nm == 'term_width' || nm == 'term_height') && (r == '' || r == 'Terminal') }, { return true; });
		if({ nm != 'line' && nm != 'print' && nm != 'print_line' && nm != 'error_line' && nm != 'consOut' }, { return false; });
		if({ call:args:length() < 1 }, { return false; });
		return r == '' || r == 'Output' || r == 'Console' || r == 'Stderr';
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
		if({ call:name == 'line' || call:name == 'print_line' }, {
			return self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_print_line', argTypes: [IrType:Ptr], args: [txt]);
		});
		if({ call:name == 'error_line' }, {
			return self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_error_line', argTypes: [IrType:Ptr], args: [txt]);
		});
		return self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_print', argTypes: [IrType:Ptr], args: [txt]);
	}
}
