#! Package base:compiler:llvm
#! Lowers Reflection and Any:typeName calls to Spec IR.

Class of SysinternalCallLowerer is IntrospectionCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', SysinternalCallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
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
		if({ self:isFloorTarget(call: call, domain: 'Reflection') }, {
			if({ call:name == 'init' || call:name == 'class' || call:name == 'method' }, { return true; });
			return false;
		});
		return false;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
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
		local String is o: b:lowerExpr(expr: call:target);
		return self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_type_name', argTypes: [IrType:Ptr], args: [o]);
	}
}
