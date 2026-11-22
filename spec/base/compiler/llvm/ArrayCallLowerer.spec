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
				if({ call:name == 'init' && tn == 'Array' }, { isArrInit: true; });
			}
		], default: {});
		if({ isArrInit }, { return true; });
		local String is recvType: call:target:resolvedType;
		local Boolean is isArrRecv: recvType == 'Array' || b:specBaseMap:get(key: recvType, default: '') == 'Array';
		if({ call:name == 'add' && call:args:length() == 1 && isArrRecv }, {
			local Array of Type is rArgs: b:specClassArgsMap:get(key: recvType, default: []);
			local String is elemName: if({ rArgs:length() >= 1 }, { rArgs:get(index: 0, default: Type:init(name: '')):name }, { '' });
			local Expression is a0Val: call:args:get(index: 0):value;
			local Boolean is isLitArg: match(on: a0Val, when: [
				Expression:ArrayLit: local Function of Boolean(Array of Expression is items){ return true; },
				else: { false }
			]);
			if({ isLitArg && elemName != 'Array' && b:specBaseMap:get(key: elemName, default: '') != 'Array' }, {
				return true;
			});
		});
		return false;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		if({ call:name == 'init' }, {
			local String is dst: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'Vector_newVec', argTypes: [IrType:Ptr], args: ['null']));
			b:emitClaimPool(val: dst);
			return dst;
		});
		local String is aRecv: b:lowerExpr(expr: call:target);
		local NamedArg is na0: call:args:get(index: 0);
		local String is iv: b:lowerExpr(expr: na0:value);
		b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_vecAddArray', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', aRecv, iv]));
		return '0';
	}
}
