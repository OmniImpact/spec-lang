#! Package base:compiler:llvm
#! Lowers Process sysinternal calls (exit, osName, getPid, clockMs) to Spec IR.

Class of SysinternalCallLowerer is ProcessCallLowerer{
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
		return 'ProcessCallLowerer';
	}

	replace Function of Int is order(){
		return 45;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		if({ self:matchesSys(call: call, recvName: 'Process', methodName: 'exit', minArgs: 1) }, { return true; });
		if({ self:matchesSys(call: call, recvName: 'Process', methodName: 'osName', minArgs: 0) }, { return true; });
		if({ self:matchesSys(call: call, recvName: 'Process', methodName: 'getPid', minArgs: 0) }, { return true; });
		if({ self:matchesSys(call: call, recvName: 'Process', methodName: 'clockMs', minArgs: 0) }, { return true; });
		return false;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		if({ nm == 'exit' }, {
			local String is stV: self:lowerArg(b: b, call: call, idx: 0);
			return self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_process_exit', argTypes: [IrType:I64], args: [stV]);
		});
		if({ nm == 'osName' }, {
			return self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_process_os_name', argTypes: [], args: []);
		});
		if({ nm == 'getPid' }, {
			return self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_process_get_pid', argTypes: [], args: []);
		});
		if({ nm == 'clockMs' }, {
			return self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_clock_ms', argTypes: [], args: []);
		});
		return '0';
	}
}
