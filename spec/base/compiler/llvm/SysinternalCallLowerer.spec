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
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
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

	Function of Boolean is isFloorTarget(CallData is call, String is domain){
		if({ call:bareProvider:endsWith(suffix: ':sysinternal:' . domain) }, { return true; });
		local Boolean is isPathMatch: false;
		local Boolean is isIdentMatch: false;
		match(on: call:target, when: [
			Expression:Path: local Function(Array of String is segs){
				local Int is n: segs:length();
				if({ n >= 2 && segs:get(index: n - 1, default: '') == domain && segs:get(index: n - 2, default: '') == 'sysinternal' }, {
					isPathMatch: true;
				});
			},
			Expression:Ident: local Function(String is tn){
				if({ tn == domain }, { isIdentMatch: true; });
			}
		], default: {});
		if({ isPathMatch }, { return true; });
		if({ domain == 'Console' || domain == 'Terminal' || domain == 'Reflection' || domain == 'Mem' }, {
			if({ isIdentMatch || call:bareProvider == domain }, { return true; });
		});
		return false;
	}

	Function of Boolean is isTargetClass(CallData is call, String is clsName){
		if({ call:bareProvider == clsName || call:bareProvider:endsWith(suffix: ':' . clsName) }, { return true; });
		if({ call:target:resolvedType == clsName || call:target:resolvedType:endsWith(suffix: ':' . clsName) }, { return true; });
		local Boolean is ok: false;
		match(on: call:target, when: [
			Expression:Ident: local Function(String is tn){
				if({ tn == clsName }, { ok: true; });
			},
			Expression:Path: local Function(Array of String is segs){
				if({ segs:length() > 0 && segs:get(index: segs:length() - 1, default: '') == clsName }, {
					ok: true;
				});
			}
		], default: {});
		return ok;
	}

	Function of String is receiverName(CallData is call){
		if({ call:bareProvider != '' }, {
			local String is bp: call:bareProvider;
			if({ bp:contains(needle: ':') }, {
				local Array of String is parts: bp:split(delimiter: ':');
				if({ parts:length() > 0 }, { return parts:get(index: parts:length() - 1); });
			});
			return bp;
		});
		local String is rt: call:target:resolvedType;
		if({ rt != '' && rt != 'Class' && rt != 'Any' && rt != 'Unknown' && rt != 'Void' }, {
			if({ rt:contains(needle: ':') }, {
				local Array of String is parts: rt:split(delimiter: ':');
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
		return :isFloorTarget(call: call, domain: recvName);
	}

	Function of String is lowerArg(IrBuilder is b, CallData is call, Int is idx){
		local NamedArg is na: call:args:get(index: idx);
		return b:lowerExpr(expr: na:value);
	}

	Function of String is lowerNamedArg(IrBuilder is b, CallData is call, String is argName, Int is posIdx, String is defVal){
		local Int is i: 0;
		local Boolean is found: false;
		local String is res: defVal;
		while({ i < call:args:length() && !found }, {
			local NamedArg is na: call:args:get(index: i);
			if({ na:name == argName }, {
				res: b:lowerExpr(expr: na:value);
				found: true;
			});
			i++;
		});
		if({ !found && posIdx >= 0 && posIdx < call:args:length() }, {
			local NamedArg is pna: call:args:get(index: posIdx);
			if({ pna:name == '' }, {
				res: b:lowerExpr(expr: pna:value);
			});
		});
		return res;
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

	local Function of String is toSnakeCase(Str is s){
		local Str is lowerAlpha: 'abcdefghijklmnopqrstuvwxyz';
		local String is out: '';
		local Int is i: 0;
		local Int is n: s:length();
		while({ i < n }, {
			local Int is chByte: s:byteAt(index: i, default: 0);
			if({ chByte >= 65 && chByte <= 90 }, {
				if({ i > 0 }, {
					out: out . '_';
				});
				out: out . lowerAlpha:substring(start: chByte - 65, end: chByte - 64);
			}, {
				out: out . s:substring(start: i, end: i + 1);
			});
			i++;
		});
		return out;
	}

	local Function of String is floorDomain(IrBuilder is b, CallData is call){
		local String is cand: '';
		if({ call:bareProvider:contains(needle: ':sysinternal:') }, {
			local Array of String is parts: call:bareProvider:split(delimiter: ':');
			if({ parts:length() > 0 }, {
				cand: parts:get(index: parts:length() - 1, default: '');
			});
		});
		if({ cand == '' }, {
			match(on: call:target, when: [
				Expression:Path: local Function(Array of String is segs){
					local Int is n: segs:length();
					if({ n >= 2 && segs:get(index: n - 2, default: '') == 'sysinternal' }, {
						cand: segs:get(index: n - 1, default: '');
					});
				},
				Expression:Ident: local Function(String is tn){
					if({ tn == 'Console' || tn == 'Terminal' }, {
						cand: tn;
					});
				}
			], default: {});
		});
		if({ cand == '' && (call:bareProvider == 'Console' || call:bareProvider == 'Terminal') }, {
			cand: call:bareProvider;
		});
		if({ cand == '' || cand == 'Mem' || cand == 'Math' || cand == 'Reflection' || cand == 'Conditional' || cand == 'Loops' || cand == 'Loadable' }, {
			return '';
		});
		if({ !b:sysinternalClasses:has(key: cand) || !:isFloorTarget(call: call, domain: cand) }, {
			return '';
		});
		return cand;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		local String is dom: :floorDomain(b: b, call: call);
		if({ dom == '' }, { return false; });
		if({ call:name == 'init' }, { return true; });
		local ClassInfo is cls: b:sysinternalClasses:get(key: dom, default: ClassInfo:init(name: '', baseClass: '', members: []));
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:METHOD && (m:name == call:name || :toSnakeCase(s: m:name) == call:name) }, {
				return true;
			});
			mi++;
		});
		return false;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		if({ call:name == 'init' }, { return 'null'; });
		local String is dom: :floorDomain(b: b, call: call);
		local ClassInfo is cls: b:sysinternalClasses:get(key: dom, default: ClassInfo:init(name: '', baseClass: '', members: []));
		local Int is mi: 0;
		while({ mi < cls:members:length() }, {
			local Member is m: cls:members:get(index: mi);
			if({ m:kind == MemberKind:METHOD && (m:name == call:name || :toSnakeCase(s: m:name) == call:name) }, {
				local Array of IrType is argTypes: [];
				local Array of String is args: [];
				local Int is pi: 0;
				while({ pi < m:params:length() }, {
					local Parameter is p: m:params:get(index: pi);
					local IrType is pty: b:irTypeFor(specType: p:paramType:name);
					local String is defVal: 'null';
					if({ pty == IrType:I64 || pty == IrType:I1 }, { defVal: '0'; });
					if({ pty == IrType:F64 }, { defVal: '0.0'; });
					local String is av: :lowerNamedArg(b: b, call: call, argName: p:name, posIdx: pi, defVal: defVal);
					argTypes:add(item: pty);
					args:add(item: av);
					pi++;
				});
				local String is retSpec: b:methodReturnSpecType(mt: m:memberType);
				local IrType is retTy: b:methodReturnType(mt: m:memberType);
				local String is callee: 'spec_' . :toSnakeCase(s: m:name);
				local String is res: :emitSysCall(b: b, retType: retTy, callee: callee, argTypes: argTypes, args: args);
				if({ b:isArcSpecType(specType: retSpec) }, {
					b:emitClaimPool(val: res);
				});
				return res;
			});
			mi++;
		});
		return '0';
	}
}
