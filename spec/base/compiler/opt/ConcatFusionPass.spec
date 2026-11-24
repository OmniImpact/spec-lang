#! Package base:compiler:opt
#! Structural multi-buffer concatenation fusion pass.
#! Recognizes pure-Spec 2-buffer concat functions by IR shape (2 Ptr params ->
#! Ptr return, >= 2 Mem_loadI64, >= 2 Mem_copy, >= 1 Mem_strFromBytes, non-recursive)
#! and fuses chains of >= 2 calls into a single pre-sized buffer write.

Class of SpecOptimizer is ConcatFusionPass{
	replace [String] is namespace: ['base', 'compiler', 'opt'];

	replace [[String]] is using: [
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
		return 'concat-fusion';
	}

	replace Function of Int is order(){
		return 32;
	}

	replace Function is runOnFunction(IrFunction is fn){
		return;
	}

	local Function of Boolean is isBufferConcatFn(IrFunction is fn){
		if({ fn:isExternal || fn:retType != IrType:Ptr || fn:params:length() != 2 }, {
			return false;
		});
		if({ fn:params:get(index: 0):ty != IrType:Ptr || fn:params:get(index: 1):ty != IrType:Ptr }, {
			return false;
		});
		local Int is loadCount: 0;
		local Int is copyCount: 0;
		local Int is strFromCount: 0;
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			local Int is ii: 0;
			while({ ii < blk:insts:length() }, {
				local Boolean is rec: match(on: blk:insts:get(index: ii), when: [
					IrInst:IrCall: local Function of Boolean(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
						if({ callee == fn:name }, { return true; });
						if({ callee == '__spec_mem_load_i64' }, { loadCount++; });
						if({ callee == '__spec_mem_copy' || callee == 'memcpy' }, { copyCount++; });
						if({ callee == '__spec_mem_str_from_bytes' || callee == 'spec_string_from_bytes' }, { strFromCount++; });
						return false;
					},
					else: { return false; }
				]);
				if({ rec }, { return false; });
				ii++;
			});
			bi++;
		});
		return loadCount >= 2 && copyCount >= 2 && strFromCount >= 1;
	}

	local Function is bumpUse(Map of String to Int is uses, String is v){
		if({ v == '' || v == 'null' || !v:startsWith(prefix: '%') }, { return; });
		uses:set(key: v, value: uses:get(key: v, default: 0) + 1);
	}

	local Function of Map of String to Int is countUses(IrFunction is fn){
		local Map of String to Int is uses: Map:init();
		times(count: fn:blocks:length(), worker: local Function(Int is bi){
			local IrBlock is blk: fn:blocks:get(index: bi);
			times(count: blk:insts:length(), worker: local Function(Int is ii){
				match(on: blk:insts:get(index: ii), when: [
					IrInst:Load: local Function(String is dst, String is slot, IrType is ty){
						:bumpUse(uses: uses, v: slot);
					},
					IrInst:Store: local Function(String is slot, String is val, IrType is ty){
						:bumpUse(uses: uses, v: val);
					},
					IrInst:BinOp: local Function(String is dst, String is op, String is lhs, String is rhs, IrType is ty){
						:bumpUse(uses: uses, v: lhs);
						:bumpUse(uses: uses, v: rhs);
					},
					IrInst:UnaryOp: local Function(String is dst, String is op, String is operand, IrType is ty){
						:bumpUse(uses: uses, v: operand);
					},
					IrInst:Cmp: local Function(String is dst, String is op, String is lhs, String is rhs, IrType is ty){
						:bumpUse(uses: uses, v: lhs);
						:bumpUse(uses: uses, v: rhs);
					},
					IrInst:IrCall: local Function(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
						times(count: args:length(), worker: local Function(Int is ai){
							:bumpUse(uses: uses, v: args:get(index: ai, default: ''));
						});
					},
					IrInst:IndirectCall: local Function(String is dst, Boolean is hasDst, IrType is retType, String is fnPtr, [IrType] is argTypes, [String] is args){
						:bumpUse(uses: uses, v: fnPtr);
						times(count: args:length(), worker: local Function(Int is ai){
							:bumpUse(uses: uses, v: args:get(index: ai, default: ''));
						});
					},
					IrInst:FieldPtr: local Function(String is dst, String is objPtr, String is structName, Int is fieldIndex){
						:bumpUse(uses: uses, v: objPtr);
					},
					IrInst:PtrElem: local Function(String is dst, String is basePtr, Int is index){
						:bumpUse(uses: uses, v: basePtr);
					},
					IrInst:IrCast: local Function(String is dst, String is val, IrType is fromType, IrType is toType){
						:bumpUse(uses: uses, v: val);
					},
					IrInst:Retain: local Function(String is val){
						:bumpUse(uses: uses, v: val);
					},
					IrInst:Release: local Function(String is val){
						:bumpUse(uses: uses, v: val);
					},
					IrInst:Ret: local Function(Boolean is hasVal, String is val, IrType is ty){
						if({ hasVal }, { :bumpUse(uses: uses, v: val); });
					},
					IrInst:CondBr: local Function(String is cond, String is thenLabel, String is elseLabel){
						:bumpUse(uses: uses, v: cond);
					},
					else: {}
				]);
			});
		});
		return uses;
	}

	local Function of IrFunction is buildConcatHelper(Int is k){
		local String is kStr: k as String;
		local IrFunction is fn: IrFunction:init(name: '__spec_concat_' . kStr, retType: IrType:Ptr);
		local Int is i: 0;
		while({ i < k }, {
			fn:addParam(name: '%p' . (i as String), ty: IrType:Ptr);
			i++;
		});

		local IrBlock is entry: fn:addBlock(label: 'entry');
		local [String] is lenSlots: [];
		local [String] is dataSlots: [];
		times(count: k, worker: local Function(Int is ti){
			local String is iStr: ti as String;
			local String is ls: '%len_slot_' . iStr;
			local String is ds: '%data_slot_' . iStr;
			entry:append(inst: IrInst:Alloca(slot: ls, ty: IrType:I64));
			entry:append(inst: IrInst:Alloca(slot: ds, ty: IrType:Ptr));
			lenSlots:push(item: ls);
			dataSlots:push(item: ds);
		});
		local String is zeroI64: '%zero_i64';
		entry:append(inst: IrInst:ConstInt(dst: zeroI64, value: 0));
		entry:append(inst: IrInst:Br(target: 'chk_0'));

		times(count: k, worker: local Function(Int is ti){
			local String is iStr: ti as String;
			local String is nextLbl: if({ ti + 1 < k }, { 'chk_' . ((ti + 1) as String) }, { 'alloc_buf' });
			local IrBlock is chkBlk: fn:addBlock(label: 'chk_' . iStr);
			local String is p: '%p' . iStr;
			local String is pAddr: '%p_addr_' . iStr;
			local String is isNull: '%is_null_' . iStr;
			chkBlk:append(inst: IrInst:IrCast(dst: pAddr, val: p, fromType: IrType:Ptr, toType: IrType:I64));
			chkBlk:append(inst: IrInst:Cmp(dst: isNull, op: '==', lhs: pAddr, rhs: zeroI64, ty: IrType:I64));
			chkBlk:append(inst: IrInst:CondBr(cond: isNull, thenLabel: 'null_' . iStr, elseLabel: 'ok_' . iStr));

			local IrBlock is nullBlk: fn:addBlock(label: 'null_' . iStr);
			nullBlk:append(inst: IrInst:Store(slot: lenSlots:get(index: ti), val: zeroI64, ty: IrType:I64));
			nullBlk:append(inst: IrInst:Store(slot: dataSlots:get(index: ti), val: 'null', ty: IrType:Ptr));
			nullBlk:append(inst: IrInst:Br(target: nextLbl));

			local IrBlock is okBlk: fn:addBlock(label: 'ok_' . iStr);
			local String is lp: '%lp_' . iStr;
			local String is lv: '%lv_' . iStr;
			local String is dp: '%dp_' . iStr;
			local String is dv: '%dv_' . iStr;
			okBlk:append(inst: IrInst:PtrElem(dst: lp, basePtr: p, index: 1));
			okBlk:append(inst: IrInst:Load(dst: lv, slot: lp, ty: IrType:I64));
			okBlk:append(inst: IrInst:Store(slot: lenSlots:get(index: ti), val: lv, ty: IrType:I64));
			okBlk:append(inst: IrInst:PtrElem(dst: dp, basePtr: p, index: 0));
			okBlk:append(inst: IrInst:Load(dst: dv, slot: dp, ty: IrType:Ptr));
			okBlk:append(inst: IrInst:Store(slot: dataSlots:get(index: ti), val: dv, ty: IrType:Ptr));
			okBlk:append(inst: IrInst:Br(target: nextLbl));
		});

		local IrBlock is allocBlk: fn:addBlock(label: 'alloc_buf');
		local [String] is lens: [];
		local [String] is datas: [];
		local String is totalVal: '';
		times(count: k, worker: local Function(Int is ti){
			local String is iStr: ti as String;
			local String is lv: '%l_' . iStr;
			local String is dv: '%d_' . iStr;
			allocBlk:append(inst: IrInst:Load(dst: lv, slot: lenSlots:get(index: ti), ty: IrType:I64));
			allocBlk:append(inst: IrInst:Load(dst: dv, slot: dataSlots:get(index: ti), ty: IrType:Ptr));
			lens:push(item: lv);
			datas:push(item: dv);
			if({ ti == 0 }, {
				totalVal: lv;
			}, {
				local String is sumTmp: '%sum_' . iStr;
				allocBlk:append(inst: IrInst:BinOp(dst: sumTmp, op: '+', lhs: totalVal, rhs: lv, ty: IrType:I64));
				totalVal: sumTmp;
			});
		});

		local String is c256: '%c256';
		local String is isSmall: '%is_small';
		local String is bufSlot: '%buf_addr_slot';
		allocBlk:append(inst: IrInst:Alloca(slot: bufSlot, ty: IrType:I64));
		allocBlk:append(inst: IrInst:ConstInt(dst: c256, value: 256));
		allocBlk:append(inst: IrInst:Cmp(dst: isSmall, op: '<=', lhs: totalVal, rhs: c256, ty: IrType:I64));
		allocBlk:append(inst: IrInst:CondBr(cond: isSmall, thenLabel: 'small_buf', elseLabel: 'large_buf'));

		local IrBlock is smallBlk: fn:addBlock(label: 'small_buf');
		local String is cSlot2: '%c_slot2';
		local String is scratch0: '%scratch0';
		local String is needAlloc: '%need_tls_alloc';
		smallBlk:append(inst: IrInst:ConstInt(dst: cSlot2, value: 2));
		smallBlk:append(inst: IrInst:IrCall(dst: scratch0, hasDst: true, retType: IrType:I64, callee: '__spec_mem_tls_get_i64', argTypes: [IrType:I64], args: [cSlot2]));
		smallBlk:append(inst: IrInst:Cmp(dst: needAlloc, op: '==', lhs: scratch0, rhs: zeroI64, ty: IrType:I64));
		smallBlk:append(inst: IrInst:CondBr(cond: needAlloc, thenLabel: 'init_tls', elseLabel: 'use_tls'));

		local IrBlock is initTlsBlk: fn:addBlock(label: 'init_tls');
		local String is scratchNew: '%scratch_new';
		initTlsBlk:append(inst: IrInst:IrCall(dst: scratchNew, hasDst: true, retType: IrType:I64, callee: '__spec_mem_alloc', argTypes: [IrType:I64], args: [c256]));
		initTlsBlk:append(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: '__spec_mem_tls_set_i64', argTypes: [IrType:I64, IrType:I64], args: [cSlot2, scratchNew]));
		initTlsBlk:append(inst: IrInst:Store(slot: bufSlot, val: scratchNew, ty: IrType:I64));
		initTlsBlk:append(inst: IrInst:Br(target: 'copy_0'));

		local IrBlock is useTlsBlk: fn:addBlock(label: 'use_tls');
		useTlsBlk:append(inst: IrInst:Store(slot: bufSlot, val: scratch0, ty: IrType:I64));
		useTlsBlk:append(inst: IrInst:Br(target: 'copy_0'));

		local IrBlock is largeBlk: fn:addBlock(label: 'large_buf');
		local String is largeAddr: '%large_addr';
		largeBlk:append(inst: IrInst:IrCall(dst: largeAddr, hasDst: true, retType: IrType:I64, callee: '__spec_mem_alloc', argTypes: [IrType:I64], args: [totalVal]));
		largeBlk:append(inst: IrInst:Store(slot: bufSlot, val: largeAddr, ty: IrType:I64));
		largeBlk:append(inst: IrInst:Br(target: 'copy_0'));

		local String is curOff: zeroI64;
		i: 0;
		while({ i < k }, {
			local String is iStr: i as String;
			local String is nextCopyLbl: if({ i + 1 < k }, { 'copy_' . ((i + 1) as String) }, { 'finish' });
			local IrBlock is copyChk: fn:addBlock(label: 'copy_' . iStr);
			if({ i > 0 }, {
				local String is nextOff: '%off_' . iStr;
				copyChk:append(inst: IrInst:BinOp(dst: nextOff, op: '+', lhs: curOff, rhs: lens:get(index: i - 1), ty: IrType:I64));
				curOff: nextOff;
			});
			local String is hasBytes: '%has_bytes_' . iStr;
			copyChk:append(inst: IrInst:Cmp(dst: hasBytes, op: '>', lhs: lens:get(index: i), rhs: zeroI64, ty: IrType:I64));
			copyChk:append(inst: IrInst:CondBr(cond: hasBytes, thenLabel: 'do_copy_' . iStr, elseLabel: nextCopyLbl));

			local IrBlock is doCopy: fn:addBlock(label: 'do_copy_' . iStr);
			local String is baseAddr: '%base_addr_' . iStr;
			local String is dstAddr: '%dst_addr_' . iStr;
			local String is dstPtr: '%dst_ptr_' . iStr;
			local String is cpTmp: '%cp_tmp_' . iStr;
			doCopy:append(inst: IrInst:Load(dst: baseAddr, slot: bufSlot, ty: IrType:I64));
			doCopy:append(inst: IrInst:BinOp(dst: dstAddr, op: '+', lhs: baseAddr, rhs: curOff, ty: IrType:I64));
			doCopy:append(inst: IrInst:IrCast(dst: dstPtr, val: dstAddr, fromType: IrType:I64, toType: IrType:Ptr));
			doCopy:append(inst: IrInst:IrCall(dst: cpTmp, hasDst: true, retType: IrType:Ptr, callee: 'memcpy', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64], args: [dstPtr, datas:get(index: i), lens:get(index: i)]));
			doCopy:append(inst: IrInst:Br(target: nextCopyLbl));
			i++;
		});

		local IrBlock is finBlk: fn:addBlock(label: 'finish');
		local String is finAddr: '%fin_addr';
		local String is res: '%res';
		finBlk:append(inst: IrInst:Load(dst: finAddr, slot: bufSlot, ty: IrType:I64));
		finBlk:append(inst: IrInst:IrCall(dst: res, hasDst: true, retType: IrType:Ptr, callee: '__spec_mem_str_from_bytes', argTypes: [IrType:I64, IrType:I64], args: [finAddr, totalVal]));
		finBlk:append(inst: IrInst:CondBr(cond: isSmall, thenLabel: 'ret_blk', elseLabel: 'free_large'));

		local IrBlock is freeBlk: fn:addBlock(label: 'free_large');
		freeBlk:append(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: '__spec_mem_free', argTypes: [IrType:I64], args: [finAddr]));
		freeBlk:append(inst: IrInst:Br(target: 'ret_blk'));

		local IrBlock is retBlk: fn:addBlock(label: 'ret_blk');
		retBlk:append(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_claim_pool', argTypes: [IrType:Ptr], args: [res]));
		retBlk:append(inst: IrInst:Ret(hasVal: true, val: res, ty: IrType:Ptr));
		return fn;
	}

	local Function of Boolean is blkHasConcatPair(IrBlock is blk, Map of String to Boolean is concatFns){
		local Int is hits: 0;
		local Int is ii: 0;
		while({ ii < blk:insts:length() }, {
			match(on: blk:insts:get(index: ii), when: [
				IrInst:IrCall: local Function(String is _dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is _argTypes, [String] is args){
					if({ hasDst && retType == IrType:Ptr && concatFns:has(key: callee) && args:length() == 2 }, {
						hits++;
					});
				}
			], default: {});
			if({ hits >= 2 }, { return true; });
			ii++;
		});
		return false;
	}

	local Function of Boolean is fnHasConcatPair(IrFunction is fn, Map of String to Boolean is concatFns){
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			if({ :blkHasConcatPair(blk: fn:blocks:get(index: bi), concatFns: concatFns) }, {
				return true;
			});
			bi++;
		});
		return false;
	}

	local Function is fuseBlock(IrBlock is blk, Map of String to Int is uses, Map of String to Boolean is concatFns, Map of Int to Boolean is createdArities, [Int] is neededArities){
		local Map of String to [String] is partsMap: Map();
		local Map of String to [Int] is callsMap: Map();
		local Map of String to String is calleeMap: Map();
		local Map of String to Boolean is isRoot: Map();
		local [String] is rootOrder: [];

		times(count: blk:insts:length(), worker: local Function(Int is ii){
			local Int is curIdx: ii;
			match(on: blk:insts:get(index: ii), when: [
				IrInst:IrCall: local Function(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args){
					if({ hasDst && retType == IrType:Ptr && concatFns:has(key: callee) && args:length() == 2 }, {
						local String is a0: args:get(index: 0, default: '');
						local String is a1: args:get(index: 1, default: '');
						local [String] is parts: [];
						local [Int] is cIdxs: [];

						local Boolean is fuseLeft: isRoot:get(key: a0, default: false) && uses:get(key: a0, default: 0) == 1 && calleeMap:get(key: a0, default: '') == callee;
						local Boolean is fuseRight: a1 != a0 && isRoot:get(key: a1, default: false) && uses:get(key: a1, default: 0) == 1 && calleeMap:get(key: a1, default: '') == callee;

						if({ fuseLeft }, {
							local [String] is lp: partsMap:get(key: a0, default: []);
							local [Int] is lc: callsMap:get(key: a0, default: []);
							each(list: lp, action: local Function(String is p){ parts:push(item: p); });
							range(start: 0, end: lc:length(), worker: local Function(Int is li){ cIdxs:push(item: lc:get(index: li)); });
							isRoot:set(key: a0, value: false);
						}, {
							parts:push(item: a0);
						});

						if({ fuseRight }, {
							local [String] is rp: partsMap:get(key: a1, default: []);
							local [Int] is rc: callsMap:get(key: a1, default: []);
							each(list: rp, action: local Function(String is p){ parts:push(item: p); });
							range(start: 0, end: rc:length(), worker: local Function(Int is ri){ cIdxs:push(item: rc:get(index: ri)); });
							isRoot:set(key: a1, value: false);
						}, {
							parts:push(item: a1);
						});

						cIdxs:push(item: curIdx);
						partsMap:set(key: dst, value: parts);
						callsMap:set(key: dst, value: cIdxs);
						calleeMap:set(key: dst, value: callee);
						isRoot:set(key: dst, value: true);
						rootOrder:push(item: dst);
					});
				},
				else: {}
			]);
		});

		local Map of Int to Boolean is deleteSet: Map();
		local Map of Int to [String] is replaceMap: Map();
		local Map of Int to String is replaceDstMap: Map();
		each(list: rootOrder, action: local Function(String is rDst){
			if({ isRoot:get(key: rDst, default: false) }, {
				local [Int] is cIdxs: callsMap:get(key: rDst, default: []);
				if({ cIdxs:length() >= 2 }, {
					range(start: 0, end: cIdxs:length() - 1, worker: local Function(Int is ci){
						deleteSet:set(key: cIdxs:get(index: ci), value: true);
					});
					local Int is lastIdx: cIdxs:get(index: cIdxs:length() - 1);
					local [String] is rParts: partsMap:get(key: rDst, default: []);
					replaceMap:set(key: lastIdx, value: rParts);
					replaceDstMap:set(key: lastIdx, value: rDst);
					local Int is k: rParts:length();
					if({ !createdArities:has(key: k) }, {
						createdArities:set(key: k, value: true);
						neededArities:push(item: k);
					});
				});
			});
		});

		if({ deleteSet:length() > 0 || replaceMap:length() > 0 }, {
			local [IrInst] is newInsts: [];
			range(start: 0, end: blk:insts:length(), worker: local Function(Int is i2){
				if({ !deleteSet:get(key: i2, default: false) }, {
					if({ replaceMap:has(key: i2) }, {
						local [String] is rParts: replaceMap:get(key: i2, default: []);
						local String is rDst: replaceDstMap:get(key: i2, default: '');
						local [IrType] is rTys: [];
						local [String] is rArgs: [];
						each(list: rParts, action: local Function(String is rp){
							rTys:push(item: IrType:Ptr);
							rArgs:push(item: rp);
						});
						newInsts:push(item: IrInst:IrCall(
							dst: rDst,
							hasDst: true,
							retType: IrType:Ptr,
							callee: '__spec_concat_' . (rParts:length() as String),
							argTypes: rTys,
							args: rArgs
						));
					}, {
						newInsts:push(item: blk:insts:get(index: i2));
					});
				});
			});
			blk:insts: newInsts;
		});
	}

	local Function is fuseFunction(IrFunction is fn, Map of String to Boolean is concatFns, Map of Int to Boolean is createdArities, [Int] is neededArities){
		if({ !:fnHasConcatPair(fn: fn, concatFns: concatFns) }, {
			return;
		});
		local Map of String to Int is uses: :countUses(fn: fn);
		times(count: fn:blocks:length(), worker: local Function(Int is bi){
			local IrBlock is blk: fn:blocks:get(index: bi);
			if({ :blkHasConcatPair(blk: blk, concatFns: concatFns) }, {
				:fuseBlock(blk: blk, uses: uses, concatFns: concatFns, createdArities: createdArities, neededArities: neededArities);
			});
		});
	}

	replace Function is runOnModule(IrModule is mod){
		local Map of String to Boolean is concatFns: Map:init();
		local Int is fi: 0;
		while({ fi < mod:functions:length() }, {
			local IrFunction is fn: mod:functions:get(index: fi);
			if({ :isBufferConcatFn(fn: fn) }, {
				concatFns:set(key: fn:name, value: true);
			});
			fi++;
		});
		if({ concatFns:length() == 0 }, { return; });

		local [Int] is neededArities: [];
		local Map of Int to Boolean is createdArities: Map();

		fi: 0;
		while({ fi < mod:functions:length() }, {
			local IrFunction is fn: mod:functions:get(index: fi);
			if({ !fn:isExternal && !fn:name:startsWith(prefix: '__spec_concat_') }, {
				:fuseFunction(fn: fn, concatFns: concatFns, createdArities: createdArities, neededArities: neededArities);
			});
			fi++;
		});

		times(count: neededArities:length(), worker: local Function(Int is ai){
			local Int is k: neededArities:get(index: ai);
			mod:functions:push(item: :buildConcatHelper(k: k));
		});
	}
}