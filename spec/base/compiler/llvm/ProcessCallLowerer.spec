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
		local String is r: self:receiverName(call: call);
		if({ r != '' && r != 'Process' }, { return false; });
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			'exit': { ok: argc >= 1; },
			['osName', 'getPid', 'clockMs']: { ok: true; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is res: '0';
		match(on: call:name, when: [
			'exit': {
				local String is stV: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_process_exit', argTypes: [IrType:I64], args: [stV]);
			},
			'osName': { res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_process_os_name', argTypes: [], args: []); },
			'getPid': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_process_get_pid', argTypes: [], args: []); },
			'clockMs': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_clock_ms', argTypes: [], args: []); }
		]);
		return res;
	}
}
