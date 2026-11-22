#! Package base:compiler:llvm
#! Lowers Map:init() / Map__K__V:init() construction to Spec IR with compile-time
#! key/value storage kind tags. All regular Map methods lower directly through
#! their monomorphized or bare Spec declarations in base:struct:Map.

Class of CallLowerer is MapCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', CallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
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
		return 'MapCallLowerer';
	}

	replace Function of Int is order(){
		return 40;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		if({ call:name != 'init' || call:args:length() > 0 }, { return false; });
		local Boolean is isMapCtor: false;
		match(on: call:target, when: [
			Expression:Ident: local Function(String is tn){
				if({ tn == 'Map' || b:specBaseMap:get(key: tn, default: '') == 'Map' }, { isMapCtor: true; });
			}
		], default: {});
		return isMapCtor;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is dst: b:nextTmp();
		local Type is resNode: expr:getResolvedTypeNode();
		local Int is kk: b:resolveMapKeyKind(resNode: resNode);
		local Int is vk: b:resolveMapValKind(resNode: resNode);
		local String is mapStruct: b:cStructName(qname: resNode:name);
		if({ !((b:specBaseMap:get(key: resNode:name, default: '') == 'Map' || resNode:isMap()) && b:mod:findStruct(name: mapStruct):name != '') }, {
			mapStruct: 'Map';
		});
		b:emit(inst: IrInst:AllocObj(dst: dst, structName: mapStruct, destroyFn: b:destroyFnFor(structName: mapStruct)));
		local String is kkV: b:nextTmp();
		b:emit(inst: IrInst:ConstInt(dst: kkV, value: kk));
		local String is vkV: b:nextTmp();
		b:emit(inst: IrInst:ConstInt(dst: vkV, value: vk));
		b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: mapStruct . '_init', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [dst, kkV, vkV]));
		b:emitClaimPool(val: dst);
		return dst;
	}
}
