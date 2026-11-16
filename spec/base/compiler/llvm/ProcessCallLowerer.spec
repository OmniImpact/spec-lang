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
		local Int is argc: call:args:length();
		if({ self:isTargetClass(call: call, clsName: 'Parallel') }, {
			if({ call:name == 'init' }, { return true; });
			if({ call:name == 'sync' && argc >= 1 }, { return true; });
			if({ call:name == 'syncWith' && argc >= 2 }, { return true; });
			if({ call:name == 'run' && argc >= 3 }, { return true; });
			return false;
		});
		if({ !self:isFloorTarget(call: call, domain: 'Process') }, { return false; });
		local Boolean is ok: false;
		match(on: call:name, when: [
			'init': { ok: true; },
			['process_exit', 'process_sleep', 'atomic_get', 'map_freeze', 'array_freeze']: { ok: argc >= 1; },
			['process_getenv', 'atomic_add', 'atomic_put', 'process_execute', 'process_measure']: { ok: argc >= 2; },
			['process_os_name', 'process_get_pid', 'clock_ms', 'process_raw_args', 'mem_peak_kb', 'thread_count', 'monitor_start', 'monitor_stop', 'monitor_avg_mem_kb', 'monitor_peak_mem_kb', 'monitor_avg_cpu_pct', 'monitor_peak_cpu_pct']: { ok: true; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is res: '0';
		match(on: call:name, when: [
			'init': { res: 'null'; },
			'process_exit': {
				local String is stV: self:lowerNamedArg(b: b, call: call, argName: 'status', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_process_exit', argTypes: [IrType:I64], args: [stV]);
			},
			'process_os_name': { res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_process_os_name', argTypes: [], args: []); },
			'process_get_pid': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_process_get_pid', argTypes: [], args: []); },
			'clock_ms': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_clock_ms', argTypes: [], args: []); },
			'process_raw_args': {
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_process_raw_args', argTypes: [], args: []);
				b:emitClaimPool(val: res);
			},
			'process_getenv': {
				local String is k: self:lowerNamedArg(b: b, call: call, argName: 'key', posIdx: 0, defVal: 'null');
				local String is d: self:lowerNamedArg(b: b, call: call, argName: 'default', posIdx: 1, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_process_getenv', argTypes: [IrType:Ptr, IrType:Ptr], args: [k, d]);
				b:emitClaimPool(val: res);
			},
			'process_sleep': {
				local String is ms: self:lowerNamedArg(b: b, call: call, argName: 'milliseconds', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_process_sleep', argTypes: [IrType:I64], args: [ms]);
			},
			'process_execute': {
				local String is cmd: self:lowerNamedArg(b: b, call: call, argName: 'command', posIdx: 0, defVal: 'null');
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'args', posIdx: 1, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_process_execute', argTypes: [IrType:Ptr, IrType:Ptr], args: [cmd, a]);
			},
			'process_measure': {
				local String is cmd: self:lowerNamedArg(b: b, call: call, argName: 'command', posIdx: 0, defVal: 'null');
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'args', posIdx: 1, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_process_measure', argTypes: [IrType:Ptr, IrType:Ptr], args: [cmd, a]);
				b:emitClaimPool(val: res);
			},
			'atomic_add': {
				local String is sl: self:lowerNamedArg(b: b, call: call, argName: 'slot', posIdx: 0, defVal: '0');
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'value', posIdx: 1, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_atomic_add', argTypes: [IrType:I64, IrType:I64], args: [sl, v]);
			},
			'atomic_put': {
				local String is sl: self:lowerNamedArg(b: b, call: call, argName: 'slot', posIdx: 0, defVal: '0');
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'value', posIdx: 1, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_atomic_put', argTypes: [IrType:I64, IrType:I64], args: [sl, v]);
			},
			'atomic_get': {
				local String is sl: self:lowerNamedArg(b: b, call: call, argName: 'slot', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_atomic_get', argTypes: [IrType:I64], args: [sl]);
			},
			'mem_peak_kb': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_mem_peak_kb', argTypes: [], args: []); },
			'thread_count': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_thread_count', argTypes: [], args: []); },
			'monitor_start': { res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_monitor_start', argTypes: [], args: []); },
			'monitor_stop': { res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_monitor_stop', argTypes: [], args: []); },
			'monitor_avg_mem_kb': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_monitor_avg_mem_kb', argTypes: [], args: []); },
			'monitor_peak_mem_kb': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_monitor_peak_mem_kb', argTypes: [], args: []); },
			'monitor_avg_cpu_pct': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_monitor_avg_cpu_pct', argTypes: [], args: []); },
			'monitor_peak_cpu_pct': { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_monitor_peak_cpu_pct', argTypes: [], args: []); },
			'map_freeze': {
				local String is m: self:lowerNamedArg(b: b, call: call, argName: 'm', posIdx: 0, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'HashTable_mapFreeze', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', m]);
			},
			'array_freeze': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'a', posIdx: 0, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'Vector_vecFreeze', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', a]);
			},
			'run': {
				local String is thr: self:lowerNamedArg(b: b, call: call, argName: 'threads', posIdx: 0, defVal: '1');
				local String is iters: self:lowerNamedArg(b: b, call: call, argName: 'iterations', posIdx: 1, defVal: '0');
				local String is wrk: self:lowerNamedArg(b: b, call: call, argName: 'worker', posIdx: 2, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_parallel_run', argTypes: [IrType:I64, IrType:I64, IrType:Ptr], args: [thr, iters, wrk]);
			},
			'sync': {
				local String is act: self:lowerNamedArg(b: b, call: call, argName: 'action', posIdx: 0, defVal: 'null');
				local String is raw: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_parallel_sync', argTypes: [IrType:Ptr], args: [act]);
				local IrType is retTy: b:irTypeFor(specType: expr:resolvedType);
				res: b:castIfNeeded(val: raw, fromTy: IrType:Ptr, toTy: retTy);
			},
			'syncWith': {
				local String is lk: self:lowerNamedArg(b: b, call: call, argName: 'lock', posIdx: 0, defVal: '0');
				local String is act: self:lowerNamedArg(b: b, call: call, argName: 'action', posIdx: 1, defVal: 'null');
				local String is raw: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_parallel_sync_with', argTypes: [IrType:I64, IrType:Ptr], args: [lk, act]);
				local IrType is retTy: b:irTypeFor(specType: expr:resolvedType);
				res: b:castIfNeeded(val: raw, fromTy: IrType:Ptr, toTy: retTy);
			}
		]);
		return res;
	}
}
