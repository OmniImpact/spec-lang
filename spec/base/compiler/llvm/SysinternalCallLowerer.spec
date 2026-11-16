#! Package base:compiler:llvm
#! Base plugin class for lowering base:sys / sysinternal calls to Spec IR.
##
## Subclasses register automatically via CallLowerer introspection discovery.
## Each subclass owns one sysinternal domain (Console, Process, File, etc.).

Class of CallLowerer is SysinternalCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', CallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'SysinternalCallLowerer';
	}

	replace Function of Int is order(){
		return 50;
	}

	Function of String is receiverName(CallData is call){
		if({ call:bareProvider != '' }, {
			local String is bp: call:bareProvider;
			if({ bp:contains(needle: ':') }, {
				local Array of String is parts: bp:split(separator: ':');
				if({ parts:length() > 0 }, { return parts:get(index: parts:length() - 1); });
			});
			return bp;
		});
		local String is rt: call:target:resolvedType;
		if({ rt != '' && rt != 'Class' && rt != 'Any' && rt != 'Unknown' && rt != 'Void' }, {
			if({ rt:contains(needle: ':') }, {
				local Array of String is parts: rt:split(separator: ':');
				if({ parts:length() > 0 }, { return parts:get(index: parts:length() - 1); });
			});
			return rt;
		});
		local String is res: '';
		match(on: call:target, when: [
			Expression:Ident: local Function(String is n){ res: n; },
			Expression:Path: local Function(Array of String is segs){
				if({ segs:length() > 0 }, {
					res: segs:get(index: segs:length() - 1);
				});
			},
			Expression:FieldAccess: local Function(Expression is t, String is fn){ res: fn; }
		], default: {});
		return res;
	}

	Function of Boolean is matchesSys(CallData is call, String is recvName, String is methodName, Int is minArgs){
		if({ call:name != methodName || call:args:length() < minArgs }, { return false; });
		local String is r: self:receiverName(call: call);
		return r == '' || r == recvName;
	}

	Function of String is lowerArg(IrBuilder is b, CallData is call, Int is idx){
		local NamedArg is na: call:args:get(index: idx);
		return b:lowerExpr(expr: na:value);
	}

	Function of String is emitSysCall(IrBuilder is b, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args){
		if({ retType == IrType:Void }, {
			b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: callee, argTypes: argTypes, args: args));
			return '0';
		});
		local String is dst: b:nextTmp();
		b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: retType, callee: callee, argTypes: argTypes, args: args));
		return dst;
	}
}
