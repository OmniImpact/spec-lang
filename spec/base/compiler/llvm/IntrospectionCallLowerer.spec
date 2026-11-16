#! Package base:compiler:llvm
#! Lowers Introspection sysinternal calls to Spec IR.

Class of SysinternalCallLowerer is IntrospectionCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', SysinternalCallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'compiler', 'ir', IrBlock],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'IntrospectionCallLowerer';
	}

	replace Function of Int is order(){
		return 47;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		local String is rt: call:target:resolvedType;
		if({ call:name == 'typeName' && call:args:length() == 0 && rt != '' && rt != 'Class' && rt != 'String' && !rt:startsWith(prefix: 'Array') && !rt:startsWith(prefix: 'Map') && !rt:startsWith(prefix: 'List') }, {
			return true;
		});
		local Int is argc: call:args:length();
		if({ self:isFloorTarget(call: call, domain: 'Reflection') }, {
			if({ call:name == 'init' || call:name == 'class' || call:name == 'method' }, { return true; });
			return false;
		});
		if({ !self:isFloorTarget(call: call, domain: 'Introspection') }, { return false; });
		local Boolean is ok: false;
		match(on: call:name, when: [
			'init': { ok: true; },
			'classNames': { ok: true; },
			['objectHash', 'heldCount', 'heldIndexOf', 'classSourceFile', 'methodNames', 'instantiate', 'typeIdentity']: { ok: argc >= 1; },
			['sameRef', 'heldName', 'hasHeld', 'hasMethod', 'classExtends', 'invokeVoidByName']: { ok: argc >= 2; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is res: '0';
		if({ self:isFloorTarget(call: call, domain: 'Reflection') }, {
			if({ call:name == 'init' }, { return 'null'; });
			if({ call:name == 'class' }, {
				local String is dst: b:nextTmp();
				local Int is sid: b:mod:internStringLiteral(value: b:currentClass);
				b:emit(inst: IrInst:ConstString(dst: dst, strId: sid));
				return dst;
			});
			if({ call:name == 'method' }, {
				local String is dst: b:nextTmp();
				local Int is sid: b:mod:internStringLiteral(value: b:currentMethod);
				b:emit(inst: IrInst:ConstString(dst: dst, strId: sid));
				return dst;
			});
		});
		match(on: call:name, when: [
			'init': { res: 'null'; },
			'classNames': {
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_class_names', argTypes: [], args: []);
				b:emitClaimPool(val: res);
			},
			'objectHash': {
				local String is o: self:lowerNamedArg(b: b, call: call, argName: 'obj', posIdx: 0, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_object_hash', argTypes: [IrType:Ptr], args: [o]);
			},
			'sameRef': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'a', posIdx: 0, defVal: 'null');
				local String is bArg: self:lowerNamedArg(b: b, call: call, argName: 'b', posIdx: 1, defVal: 'null');
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:Cmp(dst: dst, op: '==', lhs: a, rhs: bArg, ty: IrType:Ptr));
				res: dst;
			},
			'heldCount': {
				local String is o: self:lowerNamedArg(b: b, call: call, argName: 'obj', posIdx: 0, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_held_count', argTypes: [IrType:Ptr], args: [o]);
			},
			'heldIndexOf': {
				local String is o: self:lowerNamedArg(b: b, call: call, argName: 'obj', posIdx: 0, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_held_index_of', argTypes: [IrType:Ptr], args: [o]);
			},
			'heldName': {
				local String is o: self:lowerNamedArg(b: b, call: call, argName: 'obj', posIdx: 0, defVal: 'null');
				local String is idx: self:lowerNamedArg(b: b, call: call, argName: 'index', posIdx: 1, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_held_name', argTypes: [IrType:Ptr, IrType:I64], args: [o, idx]);
			},
			'hasHeld': {
				local String is o: self:lowerNamedArg(b: b, call: call, argName: 'obj', posIdx: 0, defVal: 'null');
				local String is nm: self:lowerNamedArg(b: b, call: call, argName: 'name', posIdx: 1, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_has_held', argTypes: [IrType:Ptr, IrType:Ptr], args: [o, nm]);
			},
			'classSourceFile': {
				local String is cn: self:lowerNamedArg(b: b, call: call, argName: 'className', posIdx: 0, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_class_source_file', argTypes: [IrType:Ptr], args: [cn]);
			},
			'methodNames': {
				local String is cn: self:lowerNamedArg(b: b, call: call, argName: 'className', posIdx: 0, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_method_names', argTypes: [IrType:Ptr], args: [cn]);
				b:emitClaimPool(val: res);
			},
			'hasMethod': {
				local String is cn: self:lowerNamedArg(b: b, call: call, argName: 'className', posIdx: 0, defVal: 'null');
				local String is mn: self:lowerNamedArg(b: b, call: call, argName: 'methodName', posIdx: 1, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_has_method', argTypes: [IrType:Ptr, IrType:Ptr], args: [cn, mn]);
			},
			'classExtends': {
				local String is cn: self:lowerNamedArg(b: b, call: call, argName: 'className', posIdx: 0, defVal: 'null');
				local String is bn: self:lowerNamedArg(b: b, call: call, argName: 'baseName', posIdx: 1, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_class_extends', argTypes: [IrType:Ptr, IrType:Ptr], args: [cn, bn]);
			},
			'instantiate': {
				local String is cn: self:lowerNamedArg(b: b, call: call, argName: 'className', posIdx: 0, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_instantiate', argTypes: [IrType:Ptr], args: [cn]);
			},
			'invokeVoidByName': {
				local String is inst: self:lowerNamedArg(b: b, call: call, argName: 'instance', posIdx: 0, defVal: 'null');
				local String is mn: self:lowerNamedArg(b: b, call: call, argName: 'methodName', posIdx: 1, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_invoke_void_by_name', argTypes: [IrType:Ptr, IrType:Ptr], args: [inst, mn]);
			},
			'typeIdentity': {
				local String is o: self:lowerNamedArg(b: b, call: call, argName: 'obj', posIdx: 0, defVal: 'null');
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_type_identity', argTypes: [IrType:Ptr], args: [o]);
			},
			'typeName': {
				local String is o: b:lowerExpr(expr: call:target);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_type_name', argTypes: [IrType:Ptr], args: [o]);
			}
		]);
		return res;
	}
}
