#! Package base:compiler:llvm
#! Lowers Audio and Socket sysinternal calls to Spec IR.

Class of SysinternalCallLowerer is NetAudioCallLowerer{
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
		return 'NetAudioCallLowerer';
	}

	replace Function of Int is order(){
		return 47;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		local String is r: self:receiverName(call: call);
		if({ r != '' && r != 'Audio' && r != 'Socket' }, { return false; });
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			['audio_drain', 'audio_close', 'socket_accept', 'socket_close']: { ok: argc >= 1; },
			['audio_write', 'socket_accept_cb', 'socket_send', 'socket_send_str', 'socket_recv', 'socket_recv_str', 'socket_set_timeout']: { ok: argc >= 2; },
			['audio_open', 'audio_write_cb', 'tcp_connect', 'tcp_listen', 'socket_send_cb', 'socket_send_str_cb', 'socket_recv_cb', 'socket_recv_str_cb', 'socket_poll']: { ok: argc >= 3; },
			['audio_open_cb', 'tcp_connect_cb', 'tcp_listen_cb']: { ok: argc >= 4; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is res: '0';
		match(on: call:name, when: [
			'init': { res: 'null'; },
			'audio_open': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				local String is a2: self:lowerArg(b: b, call: call, idx: 2);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_audio_open', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [a0, a1, a2]);
			},
			'audio_open_cb': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				local String is a2: self:lowerArg(b: b, call: call, idx: 2);
				local String is a3: self:lowerArg(b: b, call: call, idx: 3);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_audio_open_cb', argTypes: [IrType:I64, IrType:I64, IrType:I64, IrType:Ptr], args: [a0, a1, a2, a3]);
			},
			'audio_write': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_audio_write', argTypes: [IrType:I64, IrType:Ptr], args: [a0, a1]);
			},
			'audio_write_cb': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				local String is a2: self:lowerArg(b: b, call: call, idx: 2);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_audio_write_cb', argTypes: [IrType:I64, IrType:Ptr, IrType:Ptr], args: [a0, a1, a2]);
			},
			'audio_drain': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_audio_drain', argTypes: [IrType:I64], args: [a0]);
			},
			'audio_close': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_audio_close', argTypes: [IrType:I64], args: [a0]);
			},
			'tcp_connect': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				local String is a2: self:lowerArg(b: b, call: call, idx: 2);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_tcp_connect', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [a0, a1, a2]);
			},
			'tcp_connect_cb': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				local String is a2: self:lowerArg(b: b, call: call, idx: 2);
				local String is a3: self:lowerArg(b: b, call: call, idx: 3);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_tcp_connect_cb', argTypes: [IrType:Ptr, IrType:I64, IrType:I64, IrType:Ptr], args: [a0, a1, a2, a3]);
			},
			'tcp_listen': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				local String is a2: self:lowerArg(b: b, call: call, idx: 2);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_tcp_listen', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [a0, a1, a2]);
			},
			'tcp_listen_cb': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				local String is a2: self:lowerArg(b: b, call: call, idx: 2);
				local String is a3: self:lowerArg(b: b, call: call, idx: 3);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_tcp_listen_cb', argTypes: [IrType:Ptr, IrType:I64, IrType:I64, IrType:Ptr], args: [a0, a1, a2, a3]);
			},
			'socket_accept': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_socket_accept', argTypes: [IrType:I64], args: [a0]);
			},
			'socket_accept_cb': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_socket_accept_cb', argTypes: [IrType:I64, IrType:Ptr], args: [a0, a1]);
			},
			'socket_send': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_socket_send', argTypes: [IrType:I64, IrType:Ptr], args: [a0, a1]);
			},
			'socket_send_cb': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				local String is a2: self:lowerArg(b: b, call: call, idx: 2);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_socket_send_cb', argTypes: [IrType:I64, IrType:Ptr, IrType:Ptr], args: [a0, a1, a2]);
			},
			'socket_send_str': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_socket_send_str', argTypes: [IrType:I64, IrType:Ptr], args: [a0, a1]);
			},
			'socket_send_str_cb': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				local String is a2: self:lowerArg(b: b, call: call, idx: 2);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_socket_send_str_cb', argTypes: [IrType:I64, IrType:Ptr, IrType:Ptr], args: [a0, a1, a2]);
			},
			'socket_recv': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_socket_recv', argTypes: [IrType:I64, IrType:I64], args: [a0, a1]);
				b:emitClaimPool(val: res);
			},
			'socket_recv_cb': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				local String is a2: self:lowerArg(b: b, call: call, idx: 2);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_socket_recv_cb', argTypes: [IrType:I64, IrType:I64, IrType:Ptr], args: [a0, a1, a2]);
				b:emitClaimPool(val: res);
			},
			'socket_recv_str': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_socket_recv_str', argTypes: [IrType:I64, IrType:I64], args: [a0, a1]);
				b:emitClaimPool(val: res);
			},
			'socket_recv_str_cb': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				local String is a2: self:lowerArg(b: b, call: call, idx: 2);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_socket_recv_str_cb', argTypes: [IrType:I64, IrType:I64, IrType:Ptr], args: [a0, a1, a2]);
				b:emitClaimPool(val: res);
			},
			'socket_close': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_socket_close', argTypes: [IrType:I64], args: [a0]);
			},
			'socket_poll': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				local String is a2: self:lowerArg(b: b, call: call, idx: 2);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_socket_poll', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [a0, a1, a2]);
			},
			'socket_set_timeout': {
				local String is a0: self:lowerArg(b: b, call: call, idx: 0);
				local String is a1: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_socket_set_timeout', argTypes: [IrType:I64, IrType:I64], args: [a0, a1]);
			}
		]);
		return res;
	}
}
