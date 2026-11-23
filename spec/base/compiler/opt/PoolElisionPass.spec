#! Package base:compiler:opt
#! Structural claim-pool elision pass over IrModule.
##
## Removes (spec_pool_frame, spec_pool_release_to) pairs whose reachable
## dynamic region cannot push onto the caller's or current claim pool.

Class of SpecOptimizer is PoolElisionPass{
	namespace: ['base', 'compiler', 'opt'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'opt', SpecOptimizer],
		['base', 'compiler', 'ir', IrModule],
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
		return 'pool-elision';
	}

	replace Function of Int is order(){
		return 20;
	}

	replace Function is runOnFunction(IrFunction is fn){
		return;
	}

	replace Function is runOnModule(IrModule is mod){
		local Map of String to IrFunction is fnMap: Map:init();
		local Map of String to Boolean is mayClaimToCaller: Map:init();
		local Map of String to Boolean is balancedFrame: Map:init();

		local Int is fi: 0;
		while({ fi < mod:functions:length() }, {
			local IrFunction is fn: mod:functions:get(index: fi);
			if({ !fn:isExternal }, {
				fnMap:set(key: fn:name, value: fn);
				balancedFrame:set(key: fn:name, value: :hasBalancedEntryFrame(fn: fn));
				mayClaimToCaller:set(key: fn:name, value: false);
			});
			fi++;
		});

		# Fixed-point: a defined function may leave items on the caller's pool if
		# it lacks a balanced entry/exit pool frame AND can execute a claim/alloc.
		local Boolean is changed: true;
		while({ changed }, {
			changed: false;
			fi: 0;
			while({ fi < mod:functions:length() }, {
				local IrFunction is fn: mod:functions:get(index: fi);
				if({ !fn:isExternal && !mayClaimToCaller:get(key: fn:name, default: false) }, {
					if({ !balancedFrame:get(key: fn:name, default: false) }, {
						if({ :fnBodyMayClaim(fn: fn, fnMap: fnMap, mayClaimToCaller: mayClaimToCaller) }, {
							mayClaimToCaller:set(key: fn:name, value: true);
							changed: true;
						});
					});
				});
				fi++;
			});
		});

		fi: 0;
		while({ fi < mod:functions:length() }, {
			local IrFunction is fn: mod:functions:get(index: fi);
			if({ !fn:isExternal }, {
				:elideInFunction(fn: fn, fnMap: fnMap, mayClaimToCaller: mayClaimToCaller);
			});
			fi++;
		});
	}

	local Function of Boolean is hasBalancedEntryFrame(IrFunction is fn){
		if({ fn:blocks:length() == 0 }, { return false; });
		local IrBlock is entry: fn:blocks:get(index: 0);
		local String is entryMark: '';
		local Int is ii: 0;
		while({ ii < entry:insts:length() && entryMark == '' }, {
			local IrInst is inst: entry:insts:get(index: ii);
			local String is found: match(on: inst, when: [
				IrInst:IrCall: local Function of String(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
					if({ hasDst && callee == 'spec_pool_frame' }, { return dst; });
					return '';
				},
				else: { return ''; }
			]);
			if({ found != '' }, { entryMark: found; });
			ii++;
		});
		if({ entryMark == '' }, { return false; });

		# Every Ret in fn must be preceded by spec_pool_release_to(entryMark).
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Int is n: blk:insts:length();
			if({ n > 0 }, {
				local Boolean is isRet: match(on: blk:insts:get(index: n - 1), when: [
					IrInst:Ret: { return true; },
					else: { return false; }
				]);
				if({ isRet }, {
					if({ n < 2 }, { return false; });
					local Boolean is hasRel: match(on: blk:insts:get(index: n - 2), when: [
						IrInst:IrCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
							return callee == 'spec_pool_release_to' && args:length() == 1 && args:get(index: 0, default: '') == entryMark;
						},
						else: { return false; }
					]);
					if({ !hasRel }, { return false; });
				});
			});
			bi++;
		});
		return true;
	}

	local Function of Boolean is fnBodyMayClaim(IrFunction is fn, Map of String to IrFunction is fnMap, Map of String to Boolean is mayClaimToCaller){
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				if({ :instMayClaim(inst: blk:insts:get(index: ii), fnMap: fnMap, mayClaimToCaller: mayClaimToCaller) }, {
					return true;
				});
				ii++;
			});
			bi++;
		});
		return false;
	}

	local Function of Boolean is instMayClaim(IrInst is inst, Map of String to IrFunction is fnMap, Map of String to Boolean is mayClaimToCaller){
		return match(on: inst, when: [
			IrInst:AllocObj: { return true; },
			IrInst:IndirectCall: { return true; },
			IrInst:IrCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
				if({ callee == 'spec_claim_pool' || callee == '__spec_mem_claim_pool_addr' }, { return true; });
				if({ callee == 'spec_pool_frame' || callee == 'spec_pool_release_to' }, { return false; });
				if({ fnMap:has(key: callee) }, {
					return mayClaimToCaller:get(key: callee, default: true);
				});
				return false;
			},
			else: { return false; }
		]);
	}

	local Function of Boolean is instUsesReg(IrInst is inst, String is reg){
		return match(on: inst, when: [
			IrInst:Load: local Function of Boolean(String is dst, String is slot, IrType is ty){ return slot == reg; },
			IrInst:Store: local Function of Boolean(String is slot, String is val, IrType is ty){ return slot == reg || val == reg; },
			IrInst:BinOp: local Function of Boolean(String is dst, String is op, String is lhs, String is rhs, IrType is ty){ return lhs == reg || rhs == reg; },
			IrInst:UnaryOp: local Function of Boolean(String is dst, String is op, String is operand, IrType is ty){ return operand == reg; },
			IrInst:Cmp: local Function of Boolean(String is dst, String is op, String is lhs, String is rhs, IrType is ty){ return lhs == reg || rhs == reg; },
			IrInst:IrCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
				local Int is i: 0;
				while({ i < args:length() }, {
					if({ args:get(index: i, default: '') == reg }, { return true; });
					i++;
				});
				return false;
			},
			IrInst:IndirectCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is fnPtr, [IrType] is argTypes, [String] is args){
				if({ fnPtr == reg }, { return true; });
				local Int is i: 0;
				while({ i < args:length() }, {
					if({ args:get(index: i, default: '') == reg }, { return true; });
					i++;
				});
				return false;
			},
			IrInst:FieldPtr: local Function of Boolean(String is dst, String is objPtr, String is structName, Int is fieldIndex){ return objPtr == reg; },
			IrInst:PtrElem: local Function of Boolean(String is dst, String is basePtr, Int is index){ return basePtr == reg; },
			IrInst:IrCast: local Function of Boolean(String is dst, String is val, IrType is fromType, IrType is toType){ return val == reg; },
			IrInst:Retain: local Function of Boolean(String is val){ return val == reg; },
			IrInst:Release: local Function of Boolean(String is val){ return val == reg; },
			IrInst:Ret: local Function of Boolean(Boolean is hasVal, String is val, IrType is ty){ return hasVal && val == reg; },
			IrInst:CondBr: local Function of Boolean(String is cond, String is thenLabel, String is elseLabel){ return cond == reg; },
			else: { return false; }
		]);
	}

	local Function of Boolean is markOnlyUsedInRelease(IrFunction is fn, String is mark){
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				local IrInst is inst: blk:insts:get(index: ii);
				if({ :instUsesReg(inst: inst, reg: mark) }, {
					local Boolean is isRel: match(on: inst, when: [
						IrInst:IrCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
							return callee == 'spec_pool_release_to' && args:length() == 1 && args:get(index: 0, default: '') == mark;
						},
						else: { return false; }
					]);
					if({ !isRel }, { return false; });
				});
				ii++;
			});
			bi++;
		});
		return true;
	}

	local Function is elideInFunction(IrFunction is fn, Map of String to IrFunction is fnMap, Map of String to Boolean is mayClaimToCaller){
		local Map of String to Int is labelToIdx: Map:init();
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			labelToIdx:set(key: fn:blocks:get(index: bi):label, value: bi);
			bi++;
		});

		local Map of String to Boolean is elideMarks: Map:init();
		bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				local IrInst is inst: blk:insts:get(index: ii);
				local String is mark: match(on: inst, when: [
					IrInst:IrCall: local Function of String(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
						if({ hasDst && callee == 'spec_pool_frame' }, { return dst; });
						return '';
					},
					else: { return ''; }
				]);
				if({ mark != '' }, {
					if({ :markOnlyUsedInRelease(fn: fn, mark: mark) }, {
						if({ :regionIsPoolFree(fn: fn, startBlk: bi, startInst: ii + 1, mark: mark, labelToIdx: labelToIdx, fnMap: fnMap, mayClaimToCaller: mayClaimToCaller) }, {
							elideMarks:set(key: mark, value: true);
						});
					});
				});
				ii++;
			});
			bi++;
		});

		if({ elideMarks:length() == 0 }, { return; });

		bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local [IrInst] is newInsts: [];
			local [Int] is newLines: [];
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				local IrInst is inst: blk:insts:get(index: ii);
				local Boolean is drop: match(on: inst, when: [
					IrInst:IrCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
						if({ hasDst && callee == 'spec_pool_frame' && elideMarks:has(key: dst) }, { return true; });
						if({ callee == 'spec_pool_release_to' && args:length() == 1 && elideMarks:has(key: args:get(index: 0)) }, { return true; });
						return false;
					},
					else: { return false; }
				]);
				if({ !drop }, {
					newInsts:push(item: inst);
					newLines:push(item: blk:instLines:get(index: ii));
				});
				ii++;
			});
			blk:insts: newInsts;
			blk:instLines: newLines;
			bi++;
		});
	}

	local Function of Boolean is regionIsPoolFree(IrFunction is fn, Int is startBlk, Int is startInst, String is mark, Map of String to Int is labelToIdx, Map of String to IrFunction is fnMap, Map of String to Boolean is mayClaimToCaller){
		local [Int] is workBlk: [startBlk];
		local [Int] is workIdx: [startInst];
		local Map of String to Boolean is visited: Map:init();
		local Int is wi: 0;

		while({ wi < workBlk:length() }, {
			local Int is bi: workBlk:get(index: wi);
			local Int is ii: workIdx:get(index: wi);
			wi++;

			local IrBlock is blk: fn:blocks:get(index: bi);
			local Boolean is closed: false;
			while({ ii < blk:insts:length() && !closed }, {
				local IrInst is inst: blk:insts:get(index: ii);
				local Boolean is isRel: match(on: inst, when: [
					IrInst:IrCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
						return callee == 'spec_pool_release_to' && args:length() == 1 && args:get(index: 0, default: '') == mark;
					},
					else: { return false; }
				]);
				if({ isRel }, {
					closed: true;
				}, {
					if({ :instMayClaim(inst: inst, fnMap: fnMap, mayClaimToCaller: mayClaimToCaller) }, {
						return false;
					});
				});
				ii++;
			});

			if({ !closed && blk:insts:length() > 0 }, {
				local IrInst is term: blk:insts:get(index: blk:insts:length() - 1);
				match(on: term, when: [
					IrInst:Br: local Function(String is target){
						if({ labelToIdx:has(key: target) && !visited:has(key: target) }, {
							visited:set(key: target, value: true);
							workBlk:push(item: labelToIdx:get(key: target, default: 0));
							workIdx:push(item: 0);
						});
					},
					IrInst:CondBr: local Function(String is cond, String is thenLabel, String is elseLabel){
						if({ labelToIdx:has(key: thenLabel) && !visited:has(key: thenLabel) }, {
							visited:set(key: thenLabel, value: true);
							workBlk:push(item: labelToIdx:get(key: thenLabel, default: 0));
							workIdx:push(item: 0);
						});
						if({ labelToIdx:has(key: elseLabel) && !visited:has(key: elseLabel) }, {
							visited:set(key: elseLabel, value: true);
							workBlk:push(item: labelToIdx:get(key: elseLabel, default: 0));
							workIdx:push(item: 0);
						});
					},
					else: { }
				]);
			});
		});
		return true;
	}
}
