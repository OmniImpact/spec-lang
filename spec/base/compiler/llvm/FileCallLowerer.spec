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
		if({ self:matchesSys(call: call, recvName: 'File', methodName: 'fileExists', minArgs: 1) }, { return true; });
		if({ self:matchesSys(call: call, recvName: 'File', methodName: 'fileRemove', minArgs: 1) }, { return true; });
		if({ self:matchesSys(call: call, recvName: 'File', methodName: 'fileRead', minArgs: 1) }, { return true; });
		if({ self:matchesSys(call: call, recvName: 'File', methodName: 'fileWrite', minArgs: 2) }, { return true; });
		return false;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		if({ nm == 'fileExists' }, {
			local String is p: self:lowerArg(b: b, call: call, idx: 0);
			return self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_file_exists', argTypes: [IrType:Ptr], args: [p]);
		});
		if({ nm == 'fileRemove' }, {
			local String is p: self:lowerArg(b: b, call: call, idx: 0);
			return self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_file_remove', argTypes: [IrType:Ptr], args: [p]);
		});
		if({ nm == 'fileRead' }, {
			local String is p: self:lowerArg(b: b, call: call, idx: 0);
			local String is defV: self:namedOrNull(b: b, call: call, argName: 'default');
			local String is okCb: self:namedOrNull(b: b, call: call, argName: 'onSuccess');
			local String is errCb: self:namedOrNull(b: b, call: call, argName: 'onError');
			return self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_file_read', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr, IrType:Ptr], args: [p, defV, okCb, errCb]);
		});
		if({ nm == 'fileWrite' }, {
			local String is p: self:lowerArg(b: b, call: call, idx: 0);
			local String is c: self:lowerArg(b: b, call: call, idx: 1);
			local String is okCb: self:namedOrNull(b: b, call: call, argName: 'onSuccess');
			local String is errCb: self:namedOrNull(b: b, call: call, argName: 'onError');
			return self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_file_write', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr, IrType:Ptr], args: [p, c, okCb, errCb]);
		});
		return '0';
	}
}
