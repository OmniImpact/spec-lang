#! Package base:compiler:llvm
#! Lowers Time sysinternal calls (monotonic*, nowMs/Ns, sleep*, localOffsetSec) to Spec IR.

Class of SysinternalCallLowerer is TimeCallLowerer{
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
		return 'TimeCallLowerer';
	}

	replace Function of Int is order(){
		return 44;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		local String is r: self:receiverName(call: call);
		if({ r != '' && r != 'Time' }, { return false; });
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			['monotonicNs', 'monotonicUs', 'monotonicMs', 'nowMs', 'nowNs']: { ok: true; },
			['sleepMs', 'sleepUs', 'sleepNs', 'localOffsetSec']: { ok: argc >= 1; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is res: '0';
		match(on: call:name, when: [
			'monotonicNs': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_time_monotonic_ns', argTypes: [], args: []); },
			'monotonicUs': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_time_monotonic_us', argTypes: [], args: []); },
			'monotonicMs': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_time_monotonic_ms', argTypes: [], args: []); },
			'nowMs': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_time_epoch_ms', argTypes: [], args: []); },
			'nowNs': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_time_epoch_ns', argTypes: [], args: []); },
			'sleepMs': {
				local String is v: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_time_sleep_ms', argTypes: [IrType:I64], args: [v]);
			},
			'sleepUs': {
				local String is v: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_time_sleep_us', argTypes: [IrType:I64], args: [v]);
			},
			'sleepNs': {
				local String is v: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_time_sleep_ns', argTypes: [IrType:I64], args: [v]);
			},
			'localOffsetSec': {
				local String is v: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_time_local_offset_sec', argTypes: [IrType:I64], args: [v]);
			}
		]);
		return res;
	}
}
