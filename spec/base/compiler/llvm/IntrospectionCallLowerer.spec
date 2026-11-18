#! Package base:compiler:llvm
#! Lowers Reflection and Any:typeName calls to Spec IR.

Class of SysinternalCallLowerer is IntrospectionCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', SysinternalCallLowerer],
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
		if({ :isFloorTarget(call: call, domain: 'Reflection') }, {
			if({ call:name == 'init' || call:name == 'class' || call:name == 'method' || call:name == 'file' || call:name == 'line' || call:name == 'isArcTypeParam' || call:name == 'closureReturnKind' }, { return true; });
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
			if({ call:name == 'isArcTypeParam' }, {
				local String is cType: b:currentCallExpr:resolvedType;
				local String is elemSpec: '';
				local Int is ofIdx: cType:indexOf(search: ' of ', default: -1);
				if({ ofIdx > 0 }, {
					elemSpec: cType:substring(start: ofIdx + 4, end: cType:length());
				}, {
					local Int is colIdx: cType:indexOf(search: ':', default: -1);
					if({ colIdx > 0 }, {
						elemSpec: cType:substring(start: colIdx + 1, end: cType:length());
					});
				});
				local Boolean is isArc: elemSpec != '' && b:isArcSpecType(specType: elemSpec);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:ConstBool(dst: dst, value: isArc));
				return dst;
			});
			if({ call:name == 'closureReturnKind' }, {
				local String is retSpec: '';
				match(on: b:currentCallExpr, when: [
					Expression:Call: local Function(CallData is outerCall){
						if({ outerCall:args:length() > 0 }, {
							local NamedArg is a0: outerCall:args:get(index: 0);
							local String is fnT: a0:value:resolvedType;
							if({ fnT:startsWith(prefix: 'Function:') && fnT:length() > 9 }, {
								retSpec: fnT:substring(start: 9, end: fnT:length());
							});
						});
					}
				], default: {});
				if({ retSpec == '' }, {
					local String is cType: b:currentCallExpr:resolvedType;
					local Int is ofIdx: cType:indexOf(search: ' of ', default: -1);
					if({ ofIdx > 0 }, {
						retSpec: cType:substring(start: ofIdx + 4, end: cType:length());
					}, {
						local Int is colIdx: cType:indexOf(search: ':', default: -1);
						if({ colIdx > 0 }, {
							retSpec: cType:substring(start: colIdx + 1, end: cType:length());
						});
					});
				});
				local Int is kind: 3;
				if({ retSpec != '' && retSpec != 'Void' && retSpec != 'void' }, {
					if({ retSpec == 'Float' }, {
						kind: 2;
					}, {
						if({ b:isArcSpecType(specType: retSpec) }, {
							kind: 1;
						}, {
							kind: 0;
						});
					});
				});
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: dst, value: kind));
				return dst;
			});
		});
		local String is o: b:lowerExpr(expr: call:target);
		return :emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_type_name', argTypes: [IrType:Ptr], args: [o]);
	}
}
