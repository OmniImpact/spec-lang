#! Package base:compiler:opt
#! Known-type devirtualization and dead-receiver elision pass over IrModule.
##
## 1. Tracks concrete struct types from AllocObj through local SSA registers
##    and devirtualizes vtable IndirectCalls to direct IrCalls.
## 2. Structurally identifies functions that never read %self (and no-op
##    constructors), rewrites unused receiver args to null, and elides
##    non-escaping AllocObj + no-op init + spec_claim_pool sequences.

Class of SpecOptimizer is DevirtPass{
	namespace: ['base', 'compiler', 'opt'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'opt', SpecOptimizer],
		['base', 'compiler', 'ir', IrModule],
		['base', 'compiler', 'ir', IrStruct],
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
		return 'devirt';
	}

	replace Function of Int is order(){
		return 15;
	}

	replace Function is runOnFunction(IrFunction is fn){
		return;
	}

	replace Function is runOnModule(IrModule is mod){
		local Map of String to IrStruct is structMap: Map:init();
		local Int is si: 0;
		while({ si < mod:structs:length() }, {
			local IrStruct is st: mod:structs:get(index: si);
			structMap:set(key: st:name, value: st);
			si++;
		});

		local Map of String to Boolean is noOpInit: Map:init();
		local Map of String to Boolean is unusedSelf: Map:init();
		local Int is fi: 0;
		while({ fi < mod:functions:length() }, {
			local IrFunction is fn: mod:functions:get(index: fi);
			if({ !fn:isExternal }, {
				if({ :isNoOpInit(fn: fn) }, {
					noOpInit:set(key: fn:name, value: true);
				});
				if({ :fnNeverReadsSelf(fn: fn) }, {
					unusedSelf:set(key: fn:name, value: true);
				});
			});
			fi++;
		});

		fi: 0;
		while({ fi < mod:functions:length() }, {
			local IrFunction is fn: mod:functions:get(index: fi);
			if({ !fn:isExternal }, {
				:processFunction(fn: fn, structMap: structMap, noOpInit: noOpInit, unusedSelf: unusedSelf);
			});
			fi++;
		});
	}

	## True if fn has 1 block, >=1 param (%self), and only stores params into
	## allocas and returns void (no calls, no field writes, no side effects).
	local Function of Boolean is isNoOpInit(IrFunction is fn){
		if({ fn:blocks:length() != 1 || fn:params:length() == 0 }, { return false; });
		if({ (fn:retType as String) != (IrType:Void as String) }, { return false; });
		local IrBlock is blk: fn:blocks:get(index: 0);
		local Map of String to Boolean is allocas: Map:init();
		local Int is ii: 0;
		while({ ii < blk:insts:length() }, {
			local IrInst is inst: blk:insts:get(index: ii);
			local Boolean is ok: match(on: inst, when: [
				IrInst:Alloca: local Function of Boolean(String is slot, IrType is ty){
					allocas:set(key: slot, value: true);
					return true;
				},
				IrInst:Store: local Function of Boolean(String is slot, String is val, IrType is ty){
					return allocas:has(key: slot);
				},
				IrInst:IrCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args){
					return callee == 'spec_pool_frame' || callee == 'spec_pool_release_to';
				},
				IrInst:Ret: local Function of Boolean(Boolean is hasVal, String is val, IrType is ty){
					return !hasVal;
				},
				else: { return false; }
			]);
			if({ !ok }, { return false; });
			ii++;
		});
		return true;
	}

	## True if fn has >=1 param (%self) and %self is only ever stored into its
	## entry alloca slot (never loaded or passed anywhere else).
	local Function of Boolean is fnNeverReadsSelf(IrFunction is fn){
		if({ fn:params:length() == 0 }, { return false; });
		local String is selfName: fn:params:get(index: 0):name;
		local Map of String to Boolean is selfSlots: Map:init();

		# Find alloca slots that only receive selfName.
		if({ fn:blocks:length() > 0 }, {
			local IrBlock is entry: fn:blocks:get(index: 0);
			local Int is ii: 0;
			while({ ii < entry:insts:length() }, {
				match(on: entry:insts:get(index: ii), when: [
					IrInst:Store: local Function(String is slot, String is val, IrType is ty){
						if({ val == selfName }, { selfSlots:set(key: slot, value: true); });
					},
					else: { }
				]);
				ii++;
			});
		});

		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				local IrInst is inst: blk:insts:get(index: ii);
				local Boolean is bad: match(on: inst, when: [
					IrInst:Store: local Function of Boolean(String is slot, String is val, IrType is ty){
						if({ val == selfName && selfSlots:has(key: slot) }, { return false; });
						return val == selfName || slot == selfName || selfSlots:has(key: slot);
					},
					IrInst:Load: local Function of Boolean(String is dst, String is slot, IrType is ty){
						return slot == selfName || selfSlots:has(key: slot);
					},
					IrInst:FieldPtr: local Function of Boolean(String is dst, String is objPtr, String is structName, Int is fieldIndex){
						return objPtr == selfName;
					},
					IrInst:PtrElem: local Function of Boolean(String is dst, String is basePtr, Int is index){
						return basePtr == selfName;
					},
					IrInst:IrCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args){
						local Int is ai: 0;
						while({ ai < args:length() }, {
							if({ args:get(index: ai) == selfName }, { return true; });
							ai++;
						});
						return false;
					},
					IrInst:IndirectCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is fnPtr, Array of IrType is argTypes, Array of String is args){
						if({ fnPtr == selfName }, { return true; });
						local Int is ai: 0;
						while({ ai < args:length() }, {
							if({ args:get(index: ai) == selfName }, { return true; });
							ai++;
						});
						return false;
					},
					IrInst:Retain: local Function of Boolean(String is val){ return val == selfName; },
					IrInst:Release: local Function of Boolean(String is val){ return val == selfName; },
					IrInst:Ret: local Function of Boolean(Boolean is hasVal, String is val, IrType is ty){ return hasVal && val == selfName; },
					IrInst:IrCast: local Function of Boolean(String is dst, String is val, IrType is fromType, IrType is toType){ return val == selfName; },
					IrInst:Cmp: local Function of Boolean(String is dst, String is op, String is lhs, String is rhs, IrType is ty){ return lhs == selfName || rhs == selfName; },
					else: { return false; }
				]);
				if({ bad }, { return false; });
				ii++;
			});
			bi++;
		});
		return true;
	}

	local Function is processFunction(
		IrFunction is fn,
		Map of String to IrStruct is structMap,
		Map of String to Boolean is noOpInit,
		Map of String to Boolean is unusedSelf
	){
		# Pass 1: Track known struct types from AllocObj and devirtualize IndirectCalls.
		local Map of String to String is knownType: Map:init();
		local Map of String to String is vtPtrType: Map:init();
		local Map of String to String is vtLoadedType: Map:init();
		local Map of String to String is fnSlotTarget: Map:init();
		local Map of String to String is fnPtrTarget: Map:init();

		local Boolean is anyDevirt: false;
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				local IrInst is inst: blk:insts:get(index: ii);
				local IrInst is nextInst: match(on: inst, when: [
					IrInst:AllocObj: local Function of IrInst(String is dst, String is structName, String is destroyFn){
						knownType:set(key: dst, value: structName);
						return inst;
					},
					IrInst:FieldPtr: local Function of IrInst(String is dst, String is objPtr, String is structName, Int is fieldIndex){
						if({ fieldIndex == 1 && knownType:has(key: objPtr) }, {
							vtPtrType:set(key: dst, value: knownType:get(key: objPtr, default: ''));
						});
						return inst;
					},
					IrInst:Load: local Function of IrInst(String is dst, String is slot, IrType is ty){
						if({ vtPtrType:has(key: slot) }, {
							vtLoadedType:set(key: dst, value: vtPtrType:get(key: slot, default: ''));
						}, {
							if({ fnSlotTarget:has(key: slot) }, {
								fnPtrTarget:set(key: dst, value: fnSlotTarget:get(key: slot, default: ''));
							});
						});
						return inst;
					},
					IrInst:PtrElem: local Function of IrInst(String is dst, String is basePtr, Int is index){
						if({ vtLoadedType:has(key: basePtr) }, {
							local String is sname: vtLoadedType:get(key: basePtr, default: '');
							if({ structMap:has(key: sname) }, {
								local IrStruct is st: structMap:get(key: sname, default: IrStruct:init(name: ''));
								if({ index >= 0 && index < st:vtableFns:length() }, {
									local String is target: st:vtableFns:get(index: index);
									if({ target != '' && target != 'null' }, {
										fnSlotTarget:set(key: dst, value: target);
									});
								});
							});
						});
						return inst;
					},
					IrInst:IndirectCall: local Function of IrInst(String is dst, Boolean is hasDst, IrType is retType, String is fnPtr, Array of IrType is argTypes, Array of String is args){
						if({ fnPtrTarget:has(key: fnPtr) }, {
							local String is target: fnPtrTarget:get(key: fnPtr, default: '');
							anyDevirt: true;
							local Array of String is newArgs: args;
							if({ unusedSelf:has(key: target) && newArgs:length() > 0 && argTypes:length() > 0 && (argTypes:get(index: 0) as String) == (IrType:Ptr as String) }, {
								local Array of String is nulled: ['null'];
								local Int is ai: 1;
								while({ ai < newArgs:length() }, {
									nulled:add(item: newArgs:get(index: ai));
									ai++;
								});
								newArgs: nulled;
							});
							return IrInst:IrCall(
								dst: dst,
								hasDst: hasDst,
								retType: retType,
								callee: target,
								argTypes: argTypes,
								args: newArgs
							);
						});
						return inst;
					},
					IrInst:IrCall: local Function of IrInst(String is dst, Boolean is hasDst, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args){
						if({ unusedSelf:has(key: callee) && args:length() > 0 && argTypes:length() > 0 && (argTypes:get(index: 0) as String) == (IrType:Ptr as String) && args:get(index: 0, default: '') != 'null' }, {
							local Array of String is nulled: ['null'];
							local Int is ai: 1;
							while({ ai < args:length() }, {
								nulled:add(item: args:get(index: ai));
								ai++;
							});
							return IrInst:IrCall(
								dst: dst,
								hasDst: hasDst,
								retType: retType,
								callee: callee,
								argTypes: argTypes,
								args: nulled
							);
						});
						return inst;
					},
					else: { return inst; }
				]);
				blk:insts:set(index: ii, item: nextInst);
				ii++;
			});
			bi++;
		});

		if({ knownType:length() == 0 }, { return; });

		# Pass 2: Fold Cmp(!=, allocReg, null) -> ConstBool(true) and drop dead
		# FieldPtr/PtrElem/Load chains left behind by devirtualization, then elide
		# AllocObj + noOpInit + spec_claim_pool when allocReg has no other uses.
		bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				local IrInst is inst: blk:insts:get(index: ii);
				local IrInst is nextInst: match(on: inst, when: [
					IrInst:Cmp: local Function of IrInst(String is dst, String is op, String is lhs, String is rhs, IrType is ty){
						if({ op == '!=' && rhs == 'null' && knownType:has(key: lhs) }, {
							return IrInst:ConstBool(dst: dst, value: true);
						});
						return inst;
					},
					else: { return inst; }
				]);
				blk:insts:set(index: ii, item: nextInst);
				ii++;
			});
			bi++;
		});

		# Remove dead vtable lookup instructions (FieldPtr/Load/PtrElem/Load whose
		# dst is never referenced anywhere in fn).
		:removeDeadVtableLoads(fn: fn, vtPtrType: vtPtrType, vtLoadedType: vtLoadedType, fnSlotTarget: fnSlotTarget, fnPtrTarget: fnPtrTarget);

		# Check which AllocObj registers now have ONLY no-op init and spec_claim_pool uses.
		local Map of String to Boolean is deadAllocs: Map:init();
		local Map of String to Boolean is badAllocs: Map:init();
		bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				local IrInst is inst: blk:insts:get(index: ii);
				:scanUsesForAlloc(inst: inst, knownType: knownType, noOpInit: noOpInit, badAllocs: badAllocs);
				ii++;
			});
			bi++;
		});

		bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				match(on: blk:insts:get(index: ii), when: [
					IrInst:AllocObj: local Function(String is dst, String is structName, String is destroyFn){
						if({ !badAllocs:has(key: dst) }, {
							deadAllocs:set(key: dst, value: true);
						});
					},
					else: { }
				]);
				ii++;
			});
			bi++;
		});

		if({ deadAllocs:length() == 0 }, { return; });

		bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Array of IrInst is newInsts: [];
			local Array of Int is newLines: [];
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				local IrInst is inst: blk:insts:get(index: ii);
				local Boolean is drop: match(on: inst, when: [
					IrInst:AllocObj: local Function of Boolean(String is dst, String is structName, String is destroyFn){
						return deadAllocs:has(key: dst);
					},
					IrInst:IrCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args){
						if({ args:length() == 1 }, {
							local String is a0: args:get(index: 0, default: '');
							if({ deadAllocs:has(key: a0) }, {
								if({ callee == 'spec_claim_pool' || noOpInit:has(key: callee) }, {
									return true;
								});
							});
						});
						return false;
					},
					else: { return false; }
				]);
				if({ !drop }, {
					newInsts:add(item: inst);
					newLines:add(item: blk:instLines:get(index: ii));
				});
				ii++;
			});
			blk:insts: newInsts;
			blk:instLines: newLines;
			bi++;
		});
	}

	local Function is removeDeadVtableLoads(
		IrFunction is fn,
		Map of String to String is vtPtrType,
		Map of String to String is vtLoadedType,
		Map of String to String is fnSlotTarget,
		Map of String to String is fnPtrTarget
	){
		# Iterate to drop unused fnPtr -> fnSlot -> vtLoaded -> vtPtr chain.
		local Boolean is changed: true;
		while({ changed }, {
			changed: false;
			local Map of String to Boolean is usedRegs: Map:init();
			local Int is bi: 0;
			while({ bi < fn:blocks:length() }, {
				local IrBlock is blk: fn:blocks:get(index: bi);
				local Int is ii: 0;
				while({ ii < blk:insts:length() }, {
					:collectUsedRegs(inst: blk:insts:get(index: ii), usedRegs: usedRegs);
					ii++;
				});
				bi++;
			});

			bi: 0;
			while({ bi < fn:blocks:length() }, {
				local IrBlock is blk: fn:blocks:get(index: bi);
				local Array of IrInst is newInsts: [];
				local Array of Int is newLines: [];
				local Int is ii: 0;
				while({ ii < blk:insts:length() }, {
					local IrInst is inst: blk:insts:get(index: ii);
					local Boolean is drop: match(on: inst, when: [
						IrInst:FieldPtr: local Function of Boolean(String is dst, String is objPtr, String is structName, Int is fieldIndex){
							return vtPtrType:has(key: dst) && !usedRegs:has(key: dst);
						},
						IrInst:PtrElem: local Function of Boolean(String is dst, String is basePtr, Int is index){
							return fnSlotTarget:has(key: dst) && !usedRegs:has(key: dst);
						},
						IrInst:Load: local Function of Boolean(String is dst, String is slot, IrType is ty){
							return (vtLoadedType:has(key: dst) || fnPtrTarget:has(key: dst)) && !usedRegs:has(key: dst);
						},
						else: { return false; }
					]);
					if({ drop }, {
						changed: true;
					}, {
						newInsts:add(item: inst);
						newLines:add(item: blk:instLines:get(index: ii));
					});
					ii++;
				});
				blk:insts: newInsts;
				blk:instLines: newLines;
				bi++;
			});
		});
	}

	local Function is collectUsedRegs(IrInst is inst, Map of String to Boolean is usedRegs){
		match(on: inst, when: [
			IrInst:Load: local Function(String is dst, String is slot, IrType is ty){ usedRegs:set(key: slot, value: true); },
			IrInst:Store: local Function(String is slot, String is val, IrType is ty){ usedRegs:set(key: slot, value: true); usedRegs:set(key: val, value: true); },
			IrInst:BinOp: local Function(String is dst, String is op, String is lhs, String is rhs, IrType is ty){ usedRegs:set(key: lhs, value: true); usedRegs:set(key: rhs, value: true); },
			IrInst:UnaryOp: local Function(String is dst, String is op, String is operand, IrType is ty){ usedRegs:set(key: operand, value: true); },
			IrInst:Cmp: local Function(String is dst, String is op, String is lhs, String is rhs, IrType is ty){ usedRegs:set(key: lhs, value: true); usedRegs:set(key: rhs, value: true); },
			IrInst:IrCall: local Function(String is dst, Boolean is hasDst, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args){
				local Int is i: 0;
				while({ i < args:length() }, { usedRegs:set(key: args:get(index: i), value: true); i++; });
			},
			IrInst:IndirectCall: local Function(String is dst, Boolean is hasDst, IrType is retType, String is fnPtr, Array of IrType is argTypes, Array of String is args){
				usedRegs:set(key: fnPtr, value: true);
				local Int is i: 0;
				while({ i < args:length() }, { usedRegs:set(key: args:get(index: i), value: true); i++; });
			},
			IrInst:FieldPtr: local Function(String is dst, String is objPtr, String is structName, Int is fieldIndex){ usedRegs:set(key: objPtr, value: true); },
			IrInst:PtrElem: local Function(String is dst, String is basePtr, Int is index){ usedRegs:set(key: basePtr, value: true); },
			IrInst:IrCast: local Function(String is dst, String is val, IrType is fromType, IrType is toType){ usedRegs:set(key: val, value: true); },
			IrInst:Retain: local Function(String is val){ usedRegs:set(key: val, value: true); },
			IrInst:Release: local Function(String is val){ usedRegs:set(key: val, value: true); },
			IrInst:Ret: local Function(Boolean is hasVal, String is val, IrType is ty){ if({ hasVal }, { usedRegs:set(key: val, value: true); }); },
			IrInst:CondBr: local Function(String is cond, String is thenLabel, String is elseLabel){ usedRegs:set(key: cond, value: true); },
			else: { }
		]);
	}

	local Function is scanUsesForAlloc(
		IrInst is inst,
		Map of String to String is knownType,
		Map of String to Boolean is noOpInit,
		Map of String to Boolean is badAllocs
	){
		match(on: inst, when: [
			IrInst:IrCall: local Function(String is dst, Boolean is hasDst, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args){
				local Boolean is safeCall: args:length() == 1 && (callee == 'spec_claim_pool' || noOpInit:has(key: callee));
				local Int is i: 0;
				while({ i < args:length() }, {
					local String is a: args:get(index: i);
					if({ knownType:has(key: a) && !(safeCall && i == 0) }, {
						badAllocs:set(key: a, value: true);
					});
					i++;
				});
			},
			IrInst:IndirectCall: local Function(String is dst, Boolean is hasDst, IrType is retType, String is fnPtr, Array of IrType is argTypes, Array of String is args){
				if({ knownType:has(key: fnPtr) }, { badAllocs:set(key: fnPtr, value: true); });
				local Int is i: 0;
				while({ i < args:length() }, {
					local String is a: args:get(index: i);
					if({ knownType:has(key: a) }, { badAllocs:set(key: a, value: true); });
					i++;
				});
			},
			IrInst:Store: local Function(String is slot, String is val, IrType is ty){
				if({ knownType:has(key: val) }, { badAllocs:set(key: val, value: true); });
				if({ knownType:has(key: slot) }, { badAllocs:set(key: slot, value: true); });
			},
			IrInst:FieldPtr: local Function(String is dst, String is objPtr, String is structName, Int is fieldIndex){
				if({ knownType:has(key: objPtr) }, { badAllocs:set(key: objPtr, value: true); });
			},
			IrInst:PtrElem: local Function(String is dst, String is basePtr, Int is index){
				if({ knownType:has(key: basePtr) }, { badAllocs:set(key: basePtr, value: true); });
			},
			IrInst:IrCast: local Function(String is dst, String is val, IrType is fromType, IrType is toType){
				if({ knownType:has(key: val) }, { badAllocs:set(key: val, value: true); });
			},
			IrInst:Retain: local Function(String is val){
				if({ knownType:has(key: val) }, { badAllocs:set(key: val, value: true); });
			},
			IrInst:Release: local Function(String is val){
				if({ knownType:has(key: val) }, { badAllocs:set(key: val, value: true); });
			},
			IrInst:Ret: local Function(Boolean is hasVal, String is val, IrType is ty){
				if({ hasVal && knownType:has(key: val) }, { badAllocs:set(key: val, value: true); });
			},
			IrInst:Cmp: local Function(String is dst, String is op, String is lhs, String is rhs, IrType is ty){
				if({ knownType:has(key: lhs) }, { badAllocs:set(key: lhs, value: true); });
				if({ knownType:has(key: rhs) }, { badAllocs:set(key: rhs, value: true); });
			},
			else: { }
		]);
	}
}
