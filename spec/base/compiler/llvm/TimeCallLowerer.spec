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
		if({ !self:isFloorTarget(call: call, domain: 'Time') }, { return false; });
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			'init': { ok: true; },
			['time_monotonic_ns', 'time_monotonic_us', 'time_monotonic_ms', 'time_epoch_ms', 'time_epoch_ns']: { ok: true; },
			['time_sleep_ms', 'time_sleep_us', 'time_sleep_ns', 'time_local_offset_sec', 'time_cancel_timer']: { ok: argc >= 1; },
			'time_set_timeout': { ok: argc >= 2; },
			'time_set_interval': { ok: argc >= 3; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is res: '0';
		match(on: call:name, when: [
			'init': { res: 'null'; },
			'time_monotonic_ns': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_time_monotonic_ns', argTypes: [], args: []); },
			'time_monotonic_us': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_time_monotonic_us', argTypes: [], args: []); },
			'time_monotonic_ms': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_time_monotonic_ms', argTypes: [], args: []); },
			'time_epoch_ms': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_time_epoch_ms', argTypes: [], args: []); },
			'time_epoch_ns': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_time_epoch_ns', argTypes: [], args: []); },
			'time_sleep_ms': {
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'ms', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_time_sleep_ms', argTypes: [IrType:I64], args: [v]);
			},
			'time_sleep_us': {
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'us', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_time_sleep_us', argTypes: [IrType:I64], args: [v]);
			},
			'time_sleep_ns': {
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'ns', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_time_sleep_ns', argTypes: [IrType:I64], args: [v]);
			},
			'time_local_offset_sec': {
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'epoch_sec', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_time_local_offset_sec', argTypes: [IrType:I64], args: [v]);
			},
			'time_set_timeout': {
				local String is ms: self:lowerNamedArg(b: b, call: call, argName: 'ms', posIdx: 0, defVal: '0');
				local String is cb: self:lowerNamedArg(b: b, call: call, argName: 'callback', posIdx: 1, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_time_set_timeout', argTypes: [IrType:I64, IrType:Ptr], args: [ms, cb]);
			},
			'time_set_interval': {
				local String is ms: self:lowerNamedArg(b: b, call: call, argName: 'ms', posIdx: 0, defVal: '0');
				local String is cnt: self:lowerNamedArg(b: b, call: call, argName: 'count', posIdx: 1, defVal: '0');
				local String is cb: self:lowerNamedArg(b: b, call: call, argName: 'callback', posIdx: 2, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_time_set_interval', argTypes: [IrType:I64, IrType:I64, IrType:Ptr], args: [ms, cnt, cb]);
			},
			'time_cancel_timer': {
				local String is tid: self:lowerNamedArg(b: b, call: call, argName: 'timer_id', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_time_cancel_timer', argTypes: [IrType:I64], args: [tid]);
			}
		]);
		return res;
	}
}
