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
		if({ r != '' && r != 'Process' && r != 'Parallel' }, { return false; });
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			'init': { ok: r == 'Process'; },
			['exit', 'process_exit', 'sleep', 'process_sleep', 'atomicGet', 'atomic_get', 'map_freeze', 'array_freeze', 'sync']: { ok: argc >= 1; },
			['getEnv', 'process_getenv', 'atomicAdd', 'atomic_add', 'atomicPut', 'atomic_put', 'execute', 'process_execute', 'measure', 'process_measure', 'syncWith']: { ok: argc >= 2; },
			'run': { ok: r == 'Parallel' && argc >= 3; },
			['osName', 'process_os_name', 'getPid', 'process_get_pid', 'clockMs', 'clock_ms', 'rawArgs', 'process_raw_args', 'mem_peak_kb', 'thread_count', 'monitor_start', 'monitor_stop', 'monitor_avg_mem_kb', 'monitor_peak_mem_kb', 'monitor_avg_cpu_pct', 'monitor_peak_cpu_pct']: { ok: true; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is res: '0';
		match(on: call:name, when: [
			'init': { res: 'null'; },
			['exit', 'process_exit']: {
				local String is stV: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_process_exit', argTypes: [IrType:I64], args: [stV]);
			},
			['osName', 'process_os_name']: { res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_process_os_name', argTypes: [], args: []); },
			['getPid', 'process_get_pid']: { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_process_get_pid', argTypes: [], args: []); },
			['clockMs', 'clock_ms']: { res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_clock_ms', argTypes: [], args: []); },
			['rawArgs', 'process_raw_args']: { res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_process_raw_args', argTypes: [], args: []); },
			['getEnv', 'process_getenv']: {
				local String is k: self:lowerArg(b: b, call: call, idx: 0);
				local String is d: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_process_getenv', argTypes: [IrType:Ptr, IrType:Ptr], args: [k, d]);
			},
			['sleep', 'process_sleep']: {
				local String is ms: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_process_sleep', argTypes: [IrType:I64], args: [ms]);
			},
			['execute', 'process_execute']: {
				local String is cmd: self:lowerArg(b: b, call: call, idx: 0);
				local String is a: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_process_execute', argTypes: [IrType:Ptr, IrType:Ptr], args: [cmd, a]);
			},
			['measure', 'process_measure']: {
				local String is cmd: self:lowerArg(b: b, call: call, idx: 0);
				local String is a: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_process_measure', argTypes: [IrType:Ptr, IrType:Ptr], args: [cmd, a]);
			},
			['atomicAdd', 'atomic_add']: {
				local String is sl: self:lowerArg(b: b, call: call, idx: 0);
				local String is v: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_atomic_add', argTypes: [IrType:I64, IrType:I64], args: [sl, v]);
			},
			['atomicPut', 'atomic_put']: {
				local String is sl: self:lowerArg(b: b, call: call, idx: 0);
				local String is v: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_atomic_put', argTypes: [IrType:I64, IrType:I64], args: [sl, v]);
			},
			['atomicGet', 'atomic_get']: {
				local String is sl: self:lowerArg(b: b, call: call, idx: 0);
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
				local String is m: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_map_freeze', argTypes: [IrType:Ptr], args: [m]);
			},
			'array_freeze': {
				local String is a: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_array_freeze', argTypes: [IrType:Ptr], args: [a]);
			},
			'run': {
				local String is thr: self:lowerArg(b: b, call: call, idx: 0);
				local String is iters: self:lowerArg(b: b, call: call, idx: 1);
				local String is wrk: self:lowerArg(b: b, call: call, idx: 2);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_parallel_run', argTypes: [IrType:I64, IrType:I64, IrType:Ptr], args: [thr, iters, wrk]);
			},
			'sync': {
				local String is act: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_parallel_sync', argTypes: [IrType:Ptr], args: [act]);
			},
			'syncWith': {
				local String is lk: self:lowerArg(b: b, call: call, idx: 0);
				local String is act: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_parallel_sync_with', argTypes: [IrType:I64, IrType:Ptr], args: [lk, act]);
			}
		]);
		return res;
	}
}
