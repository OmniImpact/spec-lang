#! Package base:compiler:opt
#! Block-local ARC Retain/Release peephole pass over IrModule.
##
## 1. Tracks known-null registers and Alloca slots within each basic block and
##    eliminates Retain/Release on known-null values.
## 2. Cancels redundant Retain(x) / Release(x) pairs on the same register within
##    a basic block when no intervening instruction can observe or drop x.

Class of SpecOptimizer is ArcPeepholePass{
	namespace: ['base', 'compiler', 'opt'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'opt', SpecOptimizer],
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
		return 'arc-peephole';
	}

	replace Function of Int is order(){
		return 18;
	}

	replace Function is runOnFunction(IrFunction is fn){
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			:peepholeBlock(blk: blk);
			bi++;
		});
	}

	local Function of Boolean is isPureForArc(IrInst is inst){
		return match(on: inst, when: [
			IrInst:ConstInt: { return true; },
			IrInst:ConstFloat: { return true; },
			IrInst:ConstBool: { return true; },
			IrInst:ConstString: { return true; },
			IrInst:Alloca: { return true; },
			IrInst:Load: { return true; },
			IrInst:BinOp: { return true; },
			IrInst:UnaryOp: { return true; },
			IrInst:Cmp: { return true; },
			IrInst:GlobalAddr: { return true; },
			IrInst:FieldPtr: { return true; },
			IrInst:PtrElem: { return true; },
			IrInst:IrCast: { return true; },
			else: { return false; }
		]);
	}

	local Function is peepholeBlock(IrBlock is blk){
		local Int is n: blk:insts:length();
		if({ n == 0 }, { return; });

		local Map of String to Boolean is nullRegs: Map:init();
		local Map of String to Boolean is nullSlots: Map:init();
		nullRegs:set(key: 'null', value: true);

		local [Boolean] is drop: [];
		while([Int is di: 0], { di < n }, {
			drop:push(item: false);
			di++;
		});
		local Int is i: 0;

		# Pass 1: Eliminate Retain/Release on known-null registers.
		i: 0;
		while({ i < n }, {
			local IrInst is inst: blk:insts:get(index: i);
			match(on: inst, when: [
				IrInst:Store: local Function(String is slot, String is val, IrType is ty){
					if({ nullRegs:has(key: val) }, {
						nullSlots:set(key: slot, value: true);
					}, {
						nullSlots:set(key: slot, value: false);
					});
				},
				IrInst:Load: local Function(String is dst, String is slot, IrType is ty){
					if({ nullSlots:get(key: slot, default: false) }, {
						nullRegs:set(key: dst, value: true);
					});
				},
				IrInst:Retain: local Function(String is val){
					if({ nullRegs:has(key: val) }, {
						drop:set(index: i, item: true);
					});
				},
				IrInst:Release: local Function(String is val){
					if({ nullRegs:has(key: val) }, {
						drop:set(index: i, item: true);
					});
				},
				else: { }
			]);
			i++;
		});

		# Pass 2: Cancel local Retain(x) ... Release(x) separated only by pure ops.
		i: 0;
		while({ i < n }, {
			if({ !drop:get(index: i) }, {
				local String is retVal: match(on: blk:insts:get(index: i), when: [
					IrInst:Retain: local Function of String(String is val){ return val; },
					else: { return ''; }
				]);
				if({ retVal != '' }, {
					local Int is j: i + 1;
					local Boolean is scanning: true;
					while({ j < n && scanning }, {
						if({ !drop:get(index: j) }, {
							local IrInst is jInst: blk:insts:get(index: j);
							local String is relVal: match(on: jInst, when: [
								IrInst:Release: local Function of String(String is val){ return val; },
								else: { return ''; }
							]);
							if({ relVal == retVal }, {
								drop:set(index: i, item: true);
								drop:set(index: j, item: true);
								scanning: false;
							}, {
								if({ !:isPureForArc(inst: jInst) }, {
									scanning: false;
								});
							});
						});
						j++;
					});
				});
			});
			i++;
		});

		# Pass 3: Elide claim_pool(x); Retain(x); pool_release_to(f); claim_pool(x) -> pool_release_to(f); claim_pool(x).
		i: 0;
		while({ i + 3 < n }, {
			if({ !drop:get(index: i) && !drop:get(index: i + 1) && !drop:get(index: i + 2) && !drop:get(index: i + 3) }, {
				local String is c1: match(on: blk:insts:get(index: i), when: [
					IrInst:IrCall: local Function of String(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
						if({ callee == 'spec_claim_pool' && args:length() == 1 }, { return args:get(index: 0, default: ''); });
						return '';
					},
					else: { return ''; }
				]);
				if({ c1 != '' }, {
					local String is r1: match(on: blk:insts:get(index: i + 1), when: [
						IrInst:Retain: local Function of String(String is val){ return val; },
						else: { return ''; }
					]);
					if({ r1 == c1 }, {
						local Boolean is isRel: match(on: blk:insts:get(index: i + 2), when: [
							IrInst:IrCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
								return callee == 'spec_pool_release_to';
							},
							else: { return false; }
						]);
						if({ isRel }, {
							local String is c2: match(on: blk:insts:get(index: i + 3), when: [
								IrInst:IrCall: local Function of String(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
									if({ callee == 'spec_claim_pool' && args:length() == 1 }, { return args:get(index: 0, default: ''); });
									return '';
								},
								else: { return ''; }
							]);
							if({ c2 == c1 }, {
								drop:set(index: i, item: true);
								drop:set(index: i + 1, item: true);
							});
						});
					});
				});
			});
			i++;
		});

		local [IrInst] is newInsts: [];
		local [Int] is newLines: [];
		i: 0;
		while({ i < n }, {
			if({ !drop:get(index: i) }, {
				newInsts:push(item: blk:insts:get(index: i));
				newLines:push(item: blk:instLines:get(index: i));
			});
			i++;
		});
		blk:insts: newInsts;
		blk:instLines: newLines;
	}
}
