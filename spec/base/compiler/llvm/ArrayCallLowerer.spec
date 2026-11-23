#! Package base:compiler:llvm
#! Lowers Array:init() and batch ArrayLit add (arr:add([a, b])) to Spec IR.
#! All regular Array and List methods lower directly through their monomorphized
#! or bare Spec declarations in base:struct:Array and base:struct:List.

Class of CallLowerer is ArrayCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', CallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'ArrayCallLowerer';
	}

	replace Function of Int is order(){
		return 30;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		local Boolean is isArrInit: false;
		match(on: call:target, when: [
			Expression:Ident: local Function(String is tn){
				if({ call:name == 'init' && call:args:length() <= 1 && (tn == 'Array' || b:specBaseMap:get(key: tn, default: '') == 'Array') }, { isArrInit: true; });
			}
		], default: {});
		if({ isArrInit }, { return true; });
		local String is recvType: call:target:resolvedType;
		local Boolean is isArrRecv: recvType == 'Array' || b:specBaseMap:get(key: recvType, default: '') == 'Array';
		if({ call:name == 'add' && call:args:length() == 1 && isArrRecv }, {
			local Array of Type is rArgs: b:specClassArgsMap:get(key: recvType, default: Array());
			local String is elemName: if({ rArgs:length() >= 1 }, { rArgs:get(index: 0, default: Type:init(name: '')):name }, { '' });
			local Expression is a0Val: call:args:get(index: 0):value;
			local Boolean is isLitArg: match(on: a0Val, when: [
				Expression:ArrayLit: local Function of Boolean(Array of Expression is items){ return true; },
				else: { false }
			]);
			if({ isLitArg && elemName != 'Array' && elemName != 'List' && b:specBaseMap:get(key: elemName, default: '') != 'Array' && b:specBaseMap:get(key: elemName, default: '') != 'List' }, {
				return true;
			});
		});
		return false;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		if({ call:name == 'init' }, {
			local Type is resNode: expr:getResolvedTypeNode();
			local String is resName: resNode:name;
			local String is arrStruct: b:cStructName(qname: resName);
			if({ !((b:specBaseMap:get(key: resName, default: '') == 'Array' || resNode:isArray()) && b:mod:findStruct(name: arrStruct):name != '') }, {
				arrStruct: 'Array';
			});
			local Type is elemNode: Type:init(name: '');
			if({ b:specBaseMap:get(key: resName, default: '') == 'Array' && b:specClassArgsMap:has(key: resName) }, {
				local Array of Type is mArgs: b:specClassArgsMap:get(key: resName, default: Array());
				if({ mArgs:length() >= 1 }, {
					elemNode: mArgs:get(index: 0, default: Type:init(name: ''));
				});
			});
			if({ elemNode:name == '' && resNode:isArray() && resNode:isGeneric() }, {
				elemNode: resNode:elemType();
			});
			if({ elemNode:name == '' && call:args:length() == 1 }, {
				local Type is a0Node: call:args:get(index: 0):value:getResolvedTypeNode();
				if({ a0Node:isGeneric() }, {
					elemNode: a0Node:elemType();
				}, {
					if({ b:specClassArgsMap:has(key: a0Node:name) }, {
						local Array of Type is a0Args: b:specClassArgsMap:get(key: a0Node:name, default: Array());
						if({ a0Args:length() >= 1 }, {
							elemNode: a0Args:get(index: 0, default: Type:init(name: ''));
						});
					});
				});
			});
			local Int is ekInt: if({ elemNode:name != '' && (b:isArcTypeNode(t: elemNode) || elemNode:isAny()) }, { 1 }, { 0 });
			if({ elemNode:name == '' && call:args:length() == 1 }, {
				match(on: call:args:get(index: 0):value, when: [
					Expression:ArrayLit: local Function(Array of Expression is litItems){
						if({ litItems:length() > 0 }, {
							local Boolean is allPtr: true;
							local Int is oi: 0;
							while({ oi < litItems:length() && allPtr }, {
								local Type is itNode: litItems:get(index: oi):getResolvedTypeNode();
								if({ b:irTypeForNode(t: itNode) != IrType:Ptr || itNode:isRawPtr() }, {
									allPtr: false;
								});
								oi++;
							});
							if({ allPtr }, { ekInt: 1; });
						});
					}
				], default: {});
			});
			local String is dst: b:nextTmp();
			b:emit(inst: IrInst:AllocObj(dst: dst, structName: arrStruct, destroyFn: b:destroyFnFor(structName: arrStruct)));
			local String is ekV: b:nextTmp();
			b:emit(inst: IrInst:ConstInt(dst: ekV, value: ekInt));
			b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: arrStruct . '_init', argTypes: [IrType:Ptr, IrType:I64], args: [dst, ekV]));
			if({ call:args:length() == 1 }, {
				local Expression is srcExpr: call:args:get(index: 0):value;
				local String is srcVal: b:lowerExpr(expr: srcExpr);
				local Type is srcNode: srcExpr:getResolvedTypeNode();
				local Boolean is srcIsList: srcNode:isList() || b:specBaseMap:get(key: srcNode:name, default: '') == 'List';
				if({ srcIsList }, {
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: arrStruct . '_addList', argTypes: [IrType:Ptr, IrType:Ptr], args: [dst, srcVal]));
				}, {
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: arrStruct . '_addArray', argTypes: [IrType:Ptr, IrType:Ptr], args: [dst, srcVal]));
				});
			});
			b:emitClaimPool(val: dst);
			return dst;
		});
		local String is aRecv: b:lowerExpr(expr: call:target);
		local NamedArg is na0: call:args:get(index: 0);
		local String is iv: b:lowerExpr(expr: na0:value);
		local Type is rNode: call:target:getResolvedTypeNode();
		local String is recvStruct: b:cStructName(qname: rNode:name);
		if({ !((b:specBaseMap:get(key: rNode:name, default: '') == 'Array' || rNode:isArray()) && b:mod:findStruct(name: recvStruct):name != '') }, {
			recvStruct: 'Array';
		});
		local Type is vNode: na0:value:getResolvedTypeNode();
		local Boolean is vIsList: vNode:isList() || b:specBaseMap:get(key: vNode:name, default: '') == 'List';
		if({ vIsList }, {
			b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: recvStruct . '_addList', argTypes: [IrType:Ptr, IrType:Ptr], args: [aRecv, iv]));
		}, {
			b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: recvStruct . '_addArray', argTypes: [IrType:Ptr, IrType:Ptr], args: [aRecv, iv]));
		});
		return '0';
	}
}
