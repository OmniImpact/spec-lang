#! Package base:compiler:llvm
#! Lowers Reflection and Any:typeName calls to Spec IR.

Class of SysinternalCallLowerer is IntrospectionCallLowerer{
	replace [String] is namespace: ['base', 'compiler', 'llvm'];

	replace [[String]] is using: [
		['base', 'compiler', 'llvm', SysinternalCallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', SemType],
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
		return 'IntrospectionCallLowerer';
	}

	replace Function of Int is order(){
		return 47;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		local SemType is rtSem: call:target:getSemType();
		if({ call:name == 'typeName' && call:args:length() == 0 && !rtSem:isEmpty() && rtSem:baseName() != 'Class' }, {
			return true;
		});
		if({ :isFloorTarget(call: call, domain: 'Reflection') }, {
			if({ call:name == 'init' || call:name == 'class' || call:name == 'method' || call:name == 'file' || call:name == 'line' }, { return true; });
			return false;
		});
		return false;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		if({ :isFloorTarget(call: call, domain: 'Reflection') }, {
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
			if({ call:name == 'file' }, {
				local String is dst: b:nextTmp();
				local Int is sid: b:mod:internStringLiteral(value: b:curFn:sourceFile);
				b:emit(inst: IrInst:ConstString(dst: dst, strId: sid));
				return dst;
			});
			if({ call:name == 'line' }, {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: dst, value: b:currentLine));
				return dst;
			});
		});
		local String is o: b:lowerExpr(expr: call:target);
		return :emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_type_name', argTypes: [IrType:Ptr], args: [o]);
	}
}
