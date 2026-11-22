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
		if({ call:name != 'init' }, { return false; });
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
		local String is resTy: expr:resolvedType;
		local Int is kk: 0;
		local Int is vk: 0;
		# A mangled instantiation's kinds are its own type arguments.
		local Boolean is argsDone: false;
		if({ b:specBaseMap:get(key: resTy, default: '') == 'Map' && b:specClassArgsMap:has(key: resTy) }, {
			local Array of Type is mArgs: b:specClassArgsMap:get(key: resTy, default: []);
			if({ mArgs:length() >= 1 }, {
				local String is kArg: mArgs:get(index: 0, default: Type:init(name: '')):name;
				b:checkConcreteMapKindType(specType: kArg, role: 'key');
				kk: b:mapKeyKindFor(specType: kArg);
			});
			if({ mArgs:length() >= 2 }, {
				local String is vArg: mArgs:get(index: 1, default: Type:init(name: '')):name;
				b:checkConcreteMapKindType(specType: vArg, role: 'value');
				if({ b:isArcSpecType(specType: vArg) || vArg == 'Any' }, { vk: 1; });
			});
			argsDone: true;
		});
		if({ !argsDone }, {
			local String is kSpec: b:extractMapKeySpec(mapType: resTy);
			if({ kSpec != '' }, {
				b:checkConcreteMapKindType(specType: kSpec, role: 'key');
			});
			if({ resTy:startsWith(prefix: 'Map of Int to ') || resTy:startsWith(prefix: 'Map:Int:') || resTy:startsWith(prefix: 'Map of Boolean to ') || resTy:startsWith(prefix: 'Map:Boolean:') }, { kk: 1; });
			if({ resTy:startsWith(prefix: 'Map of Float to ') || resTy:startsWith(prefix: 'Map:Float:') }, { kk: 2; });
			if({ kk == 0 && resTy != 'Map' && resTy != '' && !resTy:startsWith(prefix: 'Map of String to ') && !resTy:startsWith(prefix: 'Map:String:') && !resTy:startsWith(prefix: 'Map of Any to ') && !resTy:startsWith(prefix: 'Map:Any:') }, { kk: 3; });
			if({ kk == 0 && (resTy == 'Map' || resTy == '') && b:expectedMapKeyType != '' }, {
				local String is ek: b:expectedMapKeyType;
				b:checkConcreteMapKindType(specType: ek, role: 'key');
				if({ ek == 'Int' || ek == 'Boolean' }, { kk: 1; });
				if({ ek == 'Float' }, { kk: 2; });
				if({ kk == 0 && ek != 'String' && ek != 'Any' }, { kk: 3; });
			});
		});
		if({ !argsDone }, {
			local Int is toIdx: resTy:indexOf(search: ' to ', default: -1);
			if({ toIdx >= 0 }, {
				local String is vSpec: resTy:substring(start: toIdx + 4, end: resTy:length());
				b:checkConcreteMapKindType(specType: vSpec, role: 'value');
				if({ b:isArcSpecType(specType: vSpec) || vSpec == 'Any' }, { vk: 1; });
			}, {
				if({ resTy:startsWith(prefix: 'Map:') }, {
					local String is afterMap: resTy:substring(start: 4, end: resTy:length());
					local Int is cIdx: afterMap:indexOf(search: ':', default: -1);
					if({ cIdx >= 0 }, {
						local String is vSpec2: afterMap:substring(start: cIdx + 1, end: afterMap:length());
						b:checkConcreteMapKindType(specType: vSpec2, role: 'value');
						if({ b:isArcSpecType(specType: vSpec2) || vSpec2 == 'Any' }, { vk: 1; });
					});
				}, {
					if({ (resTy == 'Map' || resTy == '') && b:expectedMapValType != '' }, {
						b:checkConcreteMapKindType(specType: b:expectedMapValType, role: 'value');
						if({ b:isArcSpecType(specType: b:expectedMapValType) || b:expectedMapValType == 'Any' }, { vk: 1; });
					});
				});
			});
		});
		if({ kk != 0 || vk != 0 }, {
			if({ kk == 0 && vk == 1 }, {
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapNewObject', argTypes: [IrType:Ptr], args: ['null']));
			}, {
				local String is kkV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: kkV, value: kk));
				local String is vkV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: vkV, value: vk));
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapNewTyped', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: ['null', kkV, vkV]));
			});
		}, {
			local String is kkV0: b:nextTmp();
			b:emit(inst: IrInst:ConstInt(dst: kkV0, value: 0));
			local String is vkV0: b:nextTmp();
			b:emit(inst: IrInst:ConstInt(dst: vkV0, value: 0));
			b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapNewTyped', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: ['null', kkV0, vkV0]));
		});
		b:emitClaimPool(val: dst);
		return dst;
	}
}
