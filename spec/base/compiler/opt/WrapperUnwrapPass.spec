#! Package base:compiler:opt
#! Forwarding-wrapper unwrapping pass over IrModule.
##
## Structurally detects single-block forwarding functions (parameter/constant
## setup + one direct IrCall + Ret) and unwraps direct call sites across the
## module to call the underlying target directly.

Class of SpecOptimizer is WrapperUnwrapPass{
	namespace: ['base', 'compiler', 'opt'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'opt', SpecOptimizer],
		['base', 'compiler', 'ir', IrModule],
		['base', 'compiler', 'ir', IrFunction],
		['base', 'compiler', 'ir', IrBlock],
		['base', 'compiler', 'ir', IrInst],
		['base', 'compiler', 'ir', IrParam],
		['base', 'compiler', 'ir', IrType],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'wrapper-unwrap';
	}

	replace Function of Int is order(){
		return 30;
	}

	replace Function is runOnFunction(IrFunction is fn){
		return;
	}

	replace Function is runOnModule(IrModule is mod){
		local Map of String to String is wrapCallee: Map:init();
		local Map of String to IrType is wrapRetType: Map:init();
		local Map of String to Boolean is wrapHasDst: Map:init();
		local Map of String to Array of IrType is wrapArgTypes: Map:init();
		local Map of String to Array of Int is wrapParamIdx: Map:init();
		local Map of String to Array of String is wrapConstArg: Map:init();

		local Int is fi: 0;
		while({ fi < mod:functions:length() }, {
			local IrFunction is fn: mod:functions:get(index: fi);
			if({ !fn:isExternal && fn:name != mod:entryFunction }, {
				:tryAnalyzeWrapper(
					fn: fn,
					wrapCallee: wrapCallee,
					wrapRetType: wrapRetType,
					wrapHasDst: wrapHasDst,
					wrapArgTypes: wrapArgTypes,
					wrapParamIdx: wrapParamIdx,
					wrapConstArg: wrapConstArg
				);
			});
			fi++;
		});

		if({ wrapCallee:length() == 0 }, { return; });

		# Rewrite direct IrCall sites across all functions (fixed-point for chains).
		local Boolean is changed: true;
		local Int is round: 0;
		while({ changed && round < 8 }, {
			changed: false;
			fi: 0;
			while({ fi < mod:functions:length() }, {
				local IrFunction is fn: mod:functions:get(index: fi);
				if({ !fn:isExternal }, {
					if({ :rewriteCallsInFunction(
						fn: fn,
						wrapCallee: wrapCallee,
						wrapRetType: wrapRetType,
						wrapHasDst: wrapHasDst,
						wrapArgTypes: wrapArgTypes,
						wrapParamIdx: wrapParamIdx,
						wrapConstArg: wrapConstArg
					) }, {
						changed: true;
					});
				});
				fi++;
			});
			round++;
		});
	}

	local Function of Boolean is sameIrType(IrType is a, IrType is b){
		return (a as String) == (b as String);
	}

	local Function is tryAnalyzeWrapper(
		IrFunction is fn,
		Map of String to String is wrapCallee,
		Map of String to IrType is wrapRetType,
		Map of String to Boolean is wrapHasDst,
		Map of String to Array of IrType is wrapArgTypes,
		Map of String to Array of Int is wrapParamIdx,
		Map of String to Array of String is wrapConstArg
	){
		if({ fn:blocks:length() != 1 }, { return; });
		local IrBlock is blk: fn:blocks:get(index: 0);
		if({ blk:insts:length() < 2 }, { return; });

		# Track which registers hold parameter index i or a constant literal.
		local Map of String to Int is regParam: Map:init();
		local Map of String to String is regConst: Map:init();
		local Map of String to Int is slotParam: Map:init();
		local Map of String to String is slotConst: Map:init();
		local Map of String to Boolean is allocas: Map:init();

		local Int is pi: 0;
		while({ pi < fn:params:length() }, {
			regParam:set(key: fn:params:get(index: pi):name, value: pi);
			pi++;
		});

		local Boolean is ok: true;
		local Boolean is sawCall: false;
		local Boolean is sawRet: false;
		local String is callDst: '';
		local Boolean is callHasDst: false;
		local IrType is callRetType: IrType:Void;
		local String is callCallee: '';
		local Array of IrType is callArgTypes: Array();
		local Array of String is callArgs: Array();

		local Int is ii: 0;
		while({ ii < blk:insts:length() && ok }, {
			local IrInst is inst: blk:insts:get(index: ii);
			if({ sawRet }, { ok: false; }, {
				match(on: inst, when: [
					IrInst:Alloca: local Function(String is slot, IrType is ty){
						if({ sawCall }, { ok: false; }, { allocas:set(key: slot, value: true); });
					},
					IrInst:ConstInt: local Function(String is dst, Int is value){
						if({ sawCall }, { ok: false; }, { regConst:set(key: dst, value: (value as String)); });
					},
					IrInst:ConstFloat: local Function(String is dst, String is text){
						if({ sawCall }, { ok: false; }, { regConst:set(key: dst, value: text); });
					},
					IrInst:ConstBool: local Function(String is dst, Boolean is value){
						if({ sawCall }, { ok: false; }, {
							if({ value }, { regConst:set(key: dst, value: '1'); }, { regConst:set(key: dst, value: '0'); });
						});
					},
					IrInst:Store: local Function(String is slot, String is val, IrType is ty){
						if({ sawCall || !allocas:has(key: slot) }, { ok: false; }, {
							if({ regParam:has(key: val) }, {
								slotParam:set(key: slot, value: regParam:get(key: val, default: 0));
							}, {
								if({ regConst:has(key: val) }, {
									slotConst:set(key: slot, value: regConst:get(key: val, default: ''));
								}, {
									ok: false;
								});
							});
						});
					},
					IrInst:Load: local Function(String is dst, String is slot, IrType is ty){
						if({ sawCall }, { ok: false; }, {
							if({ slotParam:has(key: slot) }, {
								regParam:set(key: dst, value: slotParam:get(key: slot, default: 0));
							}, {
								if({ slotConst:has(key: slot) }, {
									regConst:set(key: dst, value: slotConst:get(key: slot, default: ''));
								}, {
									ok: false;
								});
							});
						});
					},
					IrInst:IrCall: local Function(String is dst, Boolean is hasDst, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args){
						if({ sawCall || callee == fn:name || callee == 'spec_pool_frame' || callee == 'spec_pool_release_to' }, {
							ok: false;
						}, {
							sawCall: true;
							callDst: dst;
							callHasDst: hasDst;
							callRetType: retType;
							callCallee: callee;
							callArgTypes: argTypes;
							callArgs: args;
						});
					},
					IrInst:Ret: local Function(Boolean is hasVal, String is val, IrType is ty){
						if({ !sawCall }, { ok: false; }, {
							if({ !:sameIrType(a: ty, b: fn:retType) || !:sameIrType(a: callRetType, b: fn:retType) }, {
								ok: false;
							}, {
								if({ hasVal }, {
									if({ !callHasDst || val != callDst }, { ok: false; });
								}, {
									if({ callHasDst }, { ok: false; });
								});
							});
							sawRet: true;
						});
					},
					else: {
						ok: false;
					}
				]);
			});
			ii++;
		});

		if({ !ok || !sawCall || !sawRet }, { return; });

		# Map each argument of the inner IrCall to a caller param index or constant literal.
		local Array of Int is paramIndices: Array();
		local Array of String is constArgs: Array();
		local Int is ai: 0;
		while({ ai < callArgs:length() }, {
			local String is arg: callArgs:get(index: ai);
			if({ regParam:has(key: arg) }, {
				paramIndices:add(item: regParam:get(key: arg, default: 0));
				constArgs:add(item: '');
			}, {
				if({ regConst:has(key: arg) }, {
					paramIndices:add(item: -1);
					constArgs:add(item: regConst:get(key: arg, default: ''));
				}, {
					if({ !arg:startsWith(prefix: '%') && !arg:startsWith(prefix: '@') }, {
						paramIndices:add(item: -1);
						constArgs:add(item: arg);
					}, {
						return;
					});
				});
			});
			ai++;
		});

		wrapCallee:set(key: fn:name, value: callCallee);
		wrapRetType:set(key: fn:name, value: callRetType);
		wrapHasDst:set(key: fn:name, value: callHasDst);
		wrapArgTypes:set(key: fn:name, value: callArgTypes);
		wrapParamIdx:set(key: fn:name, value: paramIndices);
		wrapConstArg:set(key: fn:name, value: constArgs);
	}

	local Function of Boolean is rewriteCallsInFunction(
		IrFunction is fn,
		Map of String to String is wrapCallee,
		Map of String to IrType is wrapRetType,
		Map of String to Boolean is wrapHasDst,
		Map of String to Array of IrType is wrapArgTypes,
		Map of String to Array of Int is wrapParamIdx,
		Map of String to Array of String is wrapConstArg
	){
		local Boolean is anyChanged: false;
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				local IrInst is inst: blk:insts:get(index: ii);
				local IrInst is nextInst: match(on: inst, when: [
					IrInst:IrCall: local Function of IrInst(String is dst, Boolean is hasDst, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args){
						if({ !wrapCallee:has(key: callee) }, { return inst; });
						local String is target: wrapCallee:get(key: callee, default: '');
						if({ target == fn:name }, { return inst; });
						local Array of Int is pIdx: wrapParamIdx:get(key: callee, default: Array());
						local Array of String is cArg: wrapConstArg:get(key: callee, default: Array());
						local Array of IrType is tTypes: wrapArgTypes:get(key: callee, default: Array());
						local Array of String is newArgs: Array();
						local Int is ai: 0;
						while({ ai < pIdx:length() }, {
							local Int is idx: pIdx:get(index: ai);
							if({ idx >= 0 }, {
								if({ idx >= args:length() }, { return inst; });
								newArgs:add(item: args:get(index: idx));
							}, {
								newArgs:add(item: cArg:get(index: ai));
							});
							ai++;
						});
						anyChanged: true;
						return IrInst:IrCall(
							dst: dst,
							hasDst: hasDst,
							retType: retType,
							callee: target,
							argTypes: tTypes,
							args: newArgs
						);
					},
					else: { return inst; }
				]);
				blk:insts:set(index: ii, item: nextInst);
				ii++;
			});
			bi++;
		});
		return anyChanged;
	}
}
