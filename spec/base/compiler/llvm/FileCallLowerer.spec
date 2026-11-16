#! Package base:compiler:llvm
#! Lowers File sysinternal calls (fileExists, fileRemove, fileRead, fileWrite) to Spec IR.

Class of SysinternalCallLowerer is FileCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', SysinternalCallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ir', IrType],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'FileCallLowerer';
	}

	replace Function of Int is order(){
		return 46;
	}

	local Function of String is namedOrNull(IrBuilder is b, CallData is call, String is argName){
		local Int is i: 0;
		local String is res: 'null';
		local Boolean is found: false;
		while({ i < call:args:length() && !found }, {
			local NamedArg is na: call:args:get(index: i);
			if({ na:name == argName }, {
				res: b:lowerExpr(expr: na:value);
				found: true;
			});
			i++;
		});
		return res;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		if({ !self:isFloorTarget(call: call, domain: 'File') }, { return false; });
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			'init': { ok: true; },
			['file_exists', 'file_remove', 'file_remove_cb', 'file_read', 'file_read_async', 'file_temp', 'file_temp_cb']: { ok: argc >= 1; },
			['file_write', 'file_append', 'file_write_async']: { ok: argc >= 2; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is res: '0';
		match(on: call:name, when: [
			'init': { res: 'null'; },
			'file_exists': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'path', posIdx: 0, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_file_exists', argTypes: [IrType:Ptr], args: [p]);
			},
			'file_remove': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'path', posIdx: 0, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_file_remove', argTypes: [IrType:Ptr], args: [p]);
			},
			'file_remove_cb': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'path', posIdx: 0, defVal: 'null');
				local String is errCb: self:lowerNamedArg(b: b, call: call, argName: 'on_error', posIdx: 1, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_file_remove_cb', argTypes: [IrType:Ptr, IrType:Ptr], args: [p, errCb]);
			},
			'file_read': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'path', posIdx: 0, defVal: 'null');
				local String is defV: self:lowerNamedArg(b: b, call: call, argName: 'default', posIdx: 1, defVal: 'null');
				local String is okCb: self:lowerNamedArg(b: b, call: call, argName: 'on_success', posIdx: 2, defVal: 'null');
				local String is errCb: self:lowerNamedArg(b: b, call: call, argName: 'on_error', posIdx: 3, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_file_read', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr, IrType:Ptr], args: [p, defV, okCb, errCb]);
				b:emitClaimPool(val: res);
			},
			'file_read_async': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'path', posIdx: 0, defVal: 'null');
				local String is defV: self:lowerNamedArg(b: b, call: call, argName: 'default', posIdx: 1, defVal: 'null');
				local String is okCb: self:lowerNamedArg(b: b, call: call, argName: 'on_success', posIdx: 2, defVal: 'null');
				local String is errCb: self:lowerNamedArg(b: b, call: call, argName: 'on_error', posIdx: 3, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_file_read_async', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr, IrType:Ptr], args: [p, defV, okCb, errCb]);
			},
			'file_write': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'path', posIdx: 0, defVal: 'null');
				local String is c: self:lowerNamedArg(b: b, call: call, argName: 'content', posIdx: 1, defVal: 'null');
				local String is okCb: self:lowerNamedArg(b: b, call: call, argName: 'on_success', posIdx: 2, defVal: 'null');
				local String is errCb: self:lowerNamedArg(b: b, call: call, argName: 'on_error', posIdx: 3, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_file_write', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr, IrType:Ptr], args: [p, c, okCb, errCb]);
			},
			'file_append': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'path', posIdx: 0, defVal: 'null');
				local String is c: self:lowerNamedArg(b: b, call: call, argName: 'content', posIdx: 1, defVal: 'null');
				local String is okCb: self:lowerNamedArg(b: b, call: call, argName: 'on_success', posIdx: 2, defVal: 'null');
				local String is errCb: self:lowerNamedArg(b: b, call: call, argName: 'on_error', posIdx: 3, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_file_append', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr, IrType:Ptr], args: [p, c, okCb, errCb]);
			},
			'file_write_async': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'path', posIdx: 0, defVal: 'null');
				local String is c: self:lowerNamedArg(b: b, call: call, argName: 'content', posIdx: 1, defVal: 'null');
				local String is okCb: self:lowerNamedArg(b: b, call: call, argName: 'on_success', posIdx: 2, defVal: 'null');
				local String is errCb: self:lowerNamedArg(b: b, call: call, argName: 'on_error', posIdx: 3, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_file_write_async', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr, IrType:Ptr], args: [p, c, okCb, errCb]);
			},
			'file_temp': {
				local String is tpl: self:lowerNamedArg(b: b, call: call, argName: 'template', posIdx: 0, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_file_temp', argTypes: [IrType:Ptr], args: [tpl]);
				b:emitClaimPool(val: res);
			},
			'file_temp_cb': {
				local String is tpl: self:lowerNamedArg(b: b, call: call, argName: 'template', posIdx: 0, defVal: 'null');
				local String is errCb: self:lowerNamedArg(b: b, call: call, argName: 'on_error', posIdx: 1, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_file_temp_cb', argTypes: [IrType:Ptr, IrType:Ptr], args: [tpl, errCb]);
				b:emitClaimPool(val: res);
			}
		]);
		return res;
	}
}
