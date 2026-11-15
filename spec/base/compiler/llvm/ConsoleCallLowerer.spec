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
		if({ nm != 'line' && nm != 'print' }, { return false; });
		if({ call:args:length() < 1 }, { return false; });
		local String is r: self:receiverName(call: call);
		return r == '' || r == 'Output' || r == 'Console';
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is txt: self:lowerArg(b: b, call: call, idx: 0);
		if({ call:name == 'line' }, {
			return self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_print_line', argTypes: [IrType:Ptr], args: [txt]);
		});
		return self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_print', argTypes: [IrType:Ptr], args: [txt]);
	}
}
