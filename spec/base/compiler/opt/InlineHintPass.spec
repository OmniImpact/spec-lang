#! Package base:compiler:opt
#! Marks acyclic non-recursive single-block functions and model-class methods
#! (userFields > 0 && userFields >= userMethods) for inlining on IrFunction.

Class of SpecOptimizer is InlineHintPass{
	namespace: ['base', 'compiler', 'opt'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'opt', SpecOptimizer],
		['base', 'compiler', 'ir', IrModule],
		['base', 'compiler', 'ir', IrStruct],
		['base', 'compiler', 'ir', IrFunction],
		['base', 'compiler', 'ir', IrBlock],
		['base', 'compiler', 'ir', IrInst],
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
		return 'inline-hint';
	}

	replace Function of Int is order(){
		return 35;
	}

	replace Function is runOnFunction(IrFunction is fn){
		return;
	}

	local Function of Boolean is blockCallsFn(IrBlock is blk, String is fnName){
		local Int is ii: 0;
		while({ ii < blk:insts:length() }, {
			local Boolean is hit: match(on: blk:insts:get(index: ii), when: [
				IrInst:IrCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
					return callee == fnName;
				},
				else: { return false; }
			]);
			if({ hit }, { return true; });
			ii++;
		});
		return false;
	}

	local Function of Boolean is isAcyclicNonRecursive(IrFunction is fn){
		local Map of String to Int is blkIdx: Map:init();
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			blkIdx:set(key: blk:label, value: bi);
			if({ :blockCallsFn(blk: blk, fnName: fn:name) }, { return false; });
			bi++;
		});
		bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Int is n: blk:insts:length();
			if({ n > 0 }, {
				local Boolean is backedge: match(on: blk:insts:get(index: n - 1), when: [
					IrInst:Br: local Function of Boolean(String is target){
						return blkIdx:get(key: target, default: 0) <= bi;
					},
					IrInst:CondBr: local Function of Boolean(String is cond, String is thenLabel, String is elseLabel){
						return blkIdx:get(key: thenLabel, default: 0) <= bi || blkIdx:get(key: elseLabel, default: 0) <= bi;
					},
					else: { return false; }
				]);
				if({ backedge }, { return false; });
			});
			bi++;
		});
		return true;
	}

	local Function of Boolean is isIntrinsicLeaf(IrFunction is fn){
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				local Boolean is ok: match(on: blk:insts:get(index: ii), when: [
					IrInst:AllocObj: local Function of Boolean(String is dst, String is structName, String is destroyFn){
						return false;
					},
					IrInst:IndirectCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is fnPtr, [IrType] is argTypes, [String] is args){
						return false;
					},
					IrInst:IrCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
						return callee:startsWith(prefix: '__spec_') || callee:startsWith(prefix: 'spec_');
					},
					else: { return true; }
				]);
				if({ !ok }, { return false; });
				ii++;
			});
			bi++;
		});
		return true;
	}

	replace Function is runOnModule(IrModule is mod){
		local Map of String to Boolean is modelFnSet: Map:init();
		local Int is si: 0;
		while({ si < mod:structs:length() }, {
			local IrStruct is st: mod:structs:get(index: si);
			local Int is userFields: st:fieldNames:length() - 2;
			if({ userFields < 0 }, { userFields: 0; });
			local Int is userMethods: 0;
			each(list: st:metaMethodNames, action: local Function(String is umName){
				if({ umName != 'init' && umName != 'toString' && umName != 'className' && umName != 'equals' && umName != 'hashCode' }, {
					userMethods++;
				});
			});
			if({ userFields > 0 && userFields >= userMethods }, {
				each(list: st:metaMethodFns, action: local Function(String is mf){
					if({ mf != '' && mf != 'null' }, { modelFnSet:set(key: mf, value: true); });
				});
				each(list: st:vtableFns, action: local Function(String is vf){
					if({ vf != '' && vf != 'null' }, { modelFnSet:set(key: vf, value: true); });
				});
			});
			si++;
		});

		local Int is fi: 0;
		while({ fi < mod:functions:length() }, {
			local IrFunction is fn: mod:functions:get(index: fi);
			if({ !fn:isExternal && fn:blocks:length() > 0 && fn:name != 'main' && fn:name != 'Arc_destroyObj' && fn:name != 'Arc_release' }, {
				local Boolean is isSingleBlock: fn:blocks:length() == 1;
				local Boolean is isModelFn: modelFnSet:has(key: fn:name);
				local Boolean is isSlabFast: fn:name == 'Slab_allocSlot' || fn:name == 'Slab_classForSize' || fn:name == 'Slab_slotSizeForClass';
				if({ isSlabFast || (:isAcyclicNonRecursive(fn: fn) && (isSingleBlock || isModelFn || :isIntrinsicLeaf(fn: fn))) }, {
					fn:alwaysInline: true;
				});
			});
			fi++;
		});
	}
}
