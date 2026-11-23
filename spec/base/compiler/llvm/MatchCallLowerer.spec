#! Package base:compiler:llvm
#! Lowers match(on: ..., when: [...], default: ...) expressions to Spec IR.

Class of CallLowerer is MatchCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', CallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'compiler', 'ir', IrBlock],
		['base', 'compiler', 'ir', IrStruct],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'MatchCallLowerer';
	}

	replace Function of Int is order(){
		return 15;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		if({ call:name != 'match' }, { return false; });
		local Boolean is isMapLit: false;
		local Int is i: 0;
		while({ i < call:args:length() }, {
			local NamedArg is na: call:args:get(index: i);
			if({ na:name == 'when' || (na:name == '' && i == 1) }, {
				match(on: na:value, when: [
					Expression:MapLit: local Function(Array of Expression is _ks, Array of Expression is _vs){
						isMapLit: true;
					}
				], default: {});
			});
			i++;
		});
		return isMapLit;
	}

	local Function of Boolean is isElseKey(Expression is key){
		return match(on: key, when: [
			Expression:Ident: local Function of Boolean(String is nm){ return nm == 'else'; }
		], default: { return false; });
	}

	local Function of Boolean is storeLastStmt(IrBuilder is b, Statement is st, String is resSlot, IrType is resTy){
		local Boolean is stored: false;
		match(on: st, when: [
			Statement:Return: local Function(Expression is re, Boolean is hr){
				if({ hr }, {
					local String is rv: b:lowerExpr(expr: re);
					b:emit(inst: IrInst:Store(slot: resSlot, val: rv, ty: resTy));
				});
				stored: true;
			},
			Statement:Expr: local Function(Expression is es){
				local String is ev: b:lowerExpr(expr: es);
				b:emit(inst: IrInst:Store(slot: resSlot, val: ev, ty: resTy));
				stored: true;
			}
		], default: {});
		return stored;
	}

	local Function is lowerArmBody(IrBuilder is b, Expression is armExpr, String is resSlot, IrType is resTy, Boolean is hasResult, String is endLbl){
		local String is prevRetSlot: b:inlineReturnSlot;
		local String is prevRetEnd: b:inlineReturnEndLbl;
		local IrType is prevRetTy: b:inlineReturnTy;
		if({ hasResult }, {
			b:inlineReturnSlot: resSlot;
			b:inlineReturnEndLbl: endLbl;
			b:inlineReturnTy: resTy;
		});
		local Boolean is handledAnon: false;
		match(on: armExpr, when: [
			Expression:AnonFn: local Function(Type is _rt, Array of Parameter is _ps, Array of Statement is bd){
				handledAnon: true;
				local Int is i: 0;
				while({ i < bd:length() && !b:blkTerminated }, {
					local Statement is st: bd:get(index: i);
					local Boolean is isLast: i == (bd:length() - 1);
					if({ hasResult && isLast }, {
						if({ !:storeLastStmt(b: b, st: st, resSlot: resSlot, resTy: resTy) }, {
							b:lowerStmts(stmts: Array([st]));
						});
					}, {
						b:lowerStmts(stmts: Array([st]));
					});
					i++;
				});
			}
		], default: {});
		if({ !handledAnon }, {
			local String is v: b:lowerExpr(expr: armExpr);
			if({ hasResult }, {
				b:emit(inst: IrInst:Store(slot: resSlot, val: v, ty: resTy));
			});
		});
		b:inlineReturnSlot: prevRetSlot;
		b:inlineReturnEndLbl: prevRetEnd;
		b:inlineReturnTy: prevRetTy;
		if({ !b:blkTerminated }, {
			b:terminate(inst: IrInst:Br(target: endLbl));
		});
	}

	local Function of String is emitKeyMatchCond(IrBuilder is b, Expression is onExpr, String is subjVal, IrType is subjTy, Expression is k){
		local Boolean is isArrKey: false;
		local Array of Expression is arrItems: Array();
		match(on: k, when: [
			Expression:ArrayLit: local Function(Array of Expression is items){
				isArrKey: true;
				arrItems: items;
			}
		], default: {});
		if({ isArrKey }, {
			if({ arrItems:length() == 0 }, {
				local String is fTmp: b:nextTmp();
				b:emit(inst: IrInst:ConstBool(dst: fTmp, value: false));
				return fTmp;
			});
			local String is accCond: :emitKeyMatchCond(b: b, onExpr: onExpr, subjVal: subjVal, subjTy: subjTy, k: arrItems:get(index: 0));
			local Int is ai: 1;
			while({ ai < arrItems:length() }, {
				local String is nxtCond: :emitKeyMatchCond(b: b, onExpr: onExpr, subjVal: subjVal, subjTy: subjTy, k: arrItems:get(index: ai));
				local String is orTmp: b:nextTmp();
				b:emit(inst: IrInst:BinOp(dst: orTmp, op: '||', lhs: accCond, rhs: nxtCond, ty: IrType:I1));
				accCond: orTmp;
				ai++;
			});
			return accCond;
		});

		local String is variantStruct: '';
		match(on: k, when: [
			Expression:Path: local Function(Array of String is segs){
				local String is joined: '';
				local Int is si: 0;
				while({ si < segs:length() }, {
					if({ si > 0 }, { joined: joined . '_'; });
					joined: joined . segs:get(index: si, default: '');
					si++;
				});
				if({ joined != '' && b:mod:findStruct(name: joined):name != '' }, {
					variantStruct: joined;
				});
				# Generic enums: the key names the TEMPLATE's variant
				# ('Box2:Full') while the subject is a spec instantiation
				# ('Box2__Float'). Resolve the variant struct through the
				# subject's spec class so dispatch and payload binding hit
				# the concrete layout.
				if({ segs:length() >= 2 && b:specBaseMap:has(key: onExpr:resolvedType) }, {
					local String is alt: onExpr:resolvedType . '_' . segs:get(index: segs:length() - 1, default: '');
					if({ b:mod:findStruct(name: alt):name != '' }, {
						variantStruct: alt;
					});
				});
			}
		], default: {});
		if({ variantStruct != '' }, {
			local String is vSlot: b:nextTmp();
			b:emit(inst: IrInst:Alloca(slot: vSlot, ty: IrType:I1));
			local String is falseConst: b:nextTmp();
			b:emit(inst: IrInst:ConstBool(dst: falseConst, value: false));
			b:emit(inst: IrInst:Store(slot: vSlot, val: falseConst, ty: IrType:I1));
			local String is nonNull: b:nextTmp();
			b:emit(inst: IrInst:Cmp(dst: nonNull, op: '!=', lhs: subjVal, rhs: 'null', ty: IrType:Ptr));
			local String is chkLbl: b:nextLabel(prefix: 'var_chk');
			local String is doneLbl: b:nextLabel(prefix: 'var_done');
			b:terminate(inst: IrInst:CondBr(cond: nonNull, thenLabel: chkLbl, elseLabel: doneLbl));
			local IrBlock is chkBlk: b:curFn:addBlock(label: chkLbl);
			b:switchBlock(blk: chkBlk);
			local String is tnAddr: b:nextTmp();
			b:emit(inst: IrInst:FieldPtr(dst: tnAddr, objPtr: subjVal, structName: variantStruct, fieldIndex: 0));
			local String is tnVal: b:nextTmp();
			b:emit(inst: IrInst:Load(dst: tnVal, slot: tnAddr, ty: IrType:Ptr));
			local String is expTn: b:nextTmp();
			b:emit(inst: IrInst:GlobalAddr(dst: expTn, globalName: '.typename.' . variantStruct));
			local String is vCond: b:nextTmp();
			b:emit(inst: IrInst:Cmp(dst: vCond, op: '==', lhs: tnVal, rhs: expTn, ty: IrType:Ptr));
			b:emit(inst: IrInst:Store(slot: vSlot, val: vCond, ty: IrType:I1));
			b:terminate(inst: IrInst:Br(target: doneLbl));
			local IrBlock is doneBlk: b:curFn:addBlock(label: doneLbl);
			b:switchBlock(blk: doneBlk);
			local String is resCond: b:nextTmp();
			b:emit(inst: IrInst:Load(dst: resCond, slot: vSlot, ty: IrType:I1));
			return resCond;
		});

		local String is kVal: '';
		local Boolean is resolvedEnumIdent: false;
		local String is subjStruct: b:cStructName(qname: onExpr:resolvedType);
		match(on: k, when: [
			Expression:Ident: local Function(String is kn){
				if({ !b:localSlots:has(key: kn) && subjStruct != '' && b:heldFields:has(key: subjStruct . ':' . kn) }, {
					kVal: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: kVal, hasDst: true, retType: IrType:Ptr, callee: subjStruct . '_' . kn . '__ensure', argTypes: Array(), args: Array()));
					b:emitClaimPool(val: kVal);
					resolvedEnumIdent: true;
				});
			}
		], default: {});
		if({ !resolvedEnumIdent }, {
			kVal: b:lowerExpr(expr: k);
		});
		local String is condVal: b:nextTmp();
		if({ subjTy == IrType:Ptr && (onExpr:getResolvedTypeNode():isStringLike() || k:getResolvedTypeNode():isStringLike()) }, {
			b:emit(inst: IrInst:IrCall(dst: condVal, hasDst: true, retType: IrType:I1, callee: 'Str_stringEquals', argTypes: Array([IrType:Ptr, IrType:Ptr, IrType:Ptr]), args: Array(['null', subjVal, kVal])));
		}, {
			if({ subjTy == IrType:Ptr && kVal == '0' }, {
				b:addError(msg: 'Invalid zero/void match key compared against pointer subject.');
				kVal: 'null';
			});
			b:emit(inst: IrInst:Cmp(dst: condVal, op: '==', lhs: subjVal, rhs: kVal, ty: subjTy));
		});
		return condVal;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local Boolean is hasOn: false;
		local Expression is onExpr: Expression:Unknown;
		local Boolean is hasWhen: false;
		local Expression is whenExpr: Expression:Unknown;
		local Boolean is hasElse: false;
		local Expression is elseExpr: Expression:Unknown;

		local Int is ai: 0;
		while({ ai < call:args:length() }, {
			local NamedArg is na: call:args:get(index: ai);
			if({ na:name == 'on' }, { hasOn: true; onExpr: na:value; });
			if({ na:name == 'when' }, { hasWhen: true; whenExpr: na:value; });
			if({ na:name == 'default' }, { hasElse: true; elseExpr: na:value; });
			ai++;
		});

		local IrType is resTy: b:irTypeForNode(t: expr:getResolvedTypeNode());
		local Boolean is hasResult: resTy != IrType:Void;
		local String is resSlot: '';
		if({ hasResult }, {
			resSlot: '%match_res_' . (b:nextTmp());
			resSlot: '%match_res_' . (b:tmpCounter as String);
			b:emit(inst: IrInst:Alloca(slot: resSlot, ty: resTy));
			local String is initDef: b:emitDefaultVal(ty: resTy);
			b:emit(inst: IrInst:Store(slot: resSlot, val: initDef, ty: resTy));
		});

		local String is subjVal: '0';
		local IrType is subjTy: IrType:I64;
		if({ hasOn }, {
			subjVal: b:lowerExpr(expr: onExpr);
			subjTy: b:irTypeForNode(t: onExpr:getResolvedTypeNode());
			if({ subjTy == IrType:Void }, { subjTy: IrType:I64; });
		});

		local String is endLbl: b:nextLabel(prefix: 'match_end');
		local Array of Expression is keys: Array();
		local Array of Expression is vals: Array();
		if({ hasWhen }, {
			match(on: whenExpr, when: [
				Expression:MapLit: local Function(Array of Expression is ks, Array of Expression is vs){
					keys: ks;
					vals: vs;
				}
			], default: {});
		});

		local Int is ki: 0;
		while({ ki < keys:length() }, {
			local Expression is k: keys:get(index: ki);
			local Expression is v: vals:get(index: ki);
			if({ :isElseKey(key: k) }, {
				hasElse: true;
				elseExpr: v;
			}, {
				local String is condVal: '0';
				local String is variantStruct: '';
				if({ hasOn }, {
					match(on: k, when: [
						Expression:Path: local Function(Array of String is segs){
							local String is joined: '';
							local Int is si: 0;
							while({ si < segs:length() }, {
								if({ si > 0 }, { joined: joined . '_'; });
								joined: joined . segs:get(index: si, default: '');
								si++;
							});
							if({ joined != '' && b:mod:findStruct(name: joined):name != '' }, {
								variantStruct: joined;
							});
						}
					], default: {});
					condVal: :emitKeyMatchCond(b: b, onExpr: onExpr, subjVal: subjVal, subjTy: subjTy, k: k);
				}, {
					local Boolean is unwrapped: false;
					match(on: k, when: [
						Expression:AnonFn: local Function(Type is _rt, Array of Parameter is _ps, Array of Statement is kbd){
							unwrapped: true;
							b:pushScope();
							if({ kbd:length() > 0 }, {
								local Int is kbi: 0;
								while({ kbi < (kbd:length() - 1) && !b:blkTerminated }, {
									b:lowerStmt(stmt: kbd:get(index: kbi));
									kbi++;
								});
								if({ !b:blkTerminated }, {
									local Statement is ks: kbd:get(index: kbd:length() - 1);
									match(on: ks, when: [
										Statement:Return: local Function(Expression is re, Boolean is hr){
											if({ hr }, { condVal: b:lowerExpr(expr: re); });
										},
										Statement:Expr: local Function(Expression is es){
											condVal: b:lowerExpr(expr: es);
										}
									], default: {});
								});
							});
							b:popScope();
						}
					], default: {});
					if({ !unwrapped }, {
						condVal: b:lowerExpr(expr: k);
					});
				});
				local String is armLbl: b:nextLabel(prefix: 'match_arm');
				local String is nextLbl: b:nextLabel(prefix: 'match_next');
				b:terminate(inst: IrInst:CondBr(cond: condVal, thenLabel: armLbl, elseLabel: nextLbl));

				local IrBlock is armBlk: b:curFn:addBlock(label: armLbl);
				b:switchBlock(blk: armBlk);
				b:pushScope();
				if({ variantStruct != '' }, {
					local IrStruct is vst: b:mod:findStruct(name: variantStruct);
					match(on: v, when: [
						Expression:AnonFn: local Function(Type is _rt, Array of Parameter is ps, Array of Statement is _bd){
							local Int is pi: 0;
							while({ pi < ps:length() }, {
								local Parameter is p: ps:get(index: pi);
								local IrType is pty: b:irTypeFor(specType: p:paramType:name);
								if({ pty == IrType:Void }, { pty: IrType:Ptr; });
								local Int is fidx: vst:fieldIndex(name: p:name);
								if({ fidx < 0 }, {
									fidx: vst:fieldNames:length() - ps:length() + pi;
								});
								local String is fPtr: b:nextTmp();
								b:emit(inst: IrInst:FieldPtr(dst: fPtr, objPtr: subjVal, structName: variantStruct, fieldIndex: fidx));
								local String is pVal: b:nextTmp();
								b:emit(inst: IrInst:Load(dst: pVal, slot: fPtr, ty: pty));
								local String is pSlot: '%arm_' . p:name . '_' . (b:nextTmp());
								pSlot: '%arm_' . p:name . '_' . (b:tmpCounter as String);
								local Boolean is pIsArc: b:isArcTypeNode(t: p:paramType);
								local Boolean is pBoxed: b:capturedNames:has(key: p:name);
								b:bindLocal(name: p:name, slot: pSlot, ty: pty, isArc: pIsArc, specType: p:paramType:name, isBoxed: pBoxed);
								if({ pBoxed }, {
									b:emit(inst: IrInst:Alloca(slot: pSlot, ty: IrType:Ptr));
									local String is boxPtr: b:emitNewBox(initVal: pVal, ty: pty, isArc: pIsArc);
									b:emit(inst: IrInst:Store(slot: pSlot, val: boxPtr, ty: IrType:Ptr));
								}, {
									b:emit(inst: IrInst:Alloca(slot: pSlot, ty: pty));
									b:emit(inst: IrInst:Store(slot: pSlot, val: pVal, ty: pty));
								});
								pi++;
							});
						}
					], default: {});
				});
				:lowerArmBody(b: b, armExpr: v, resSlot: resSlot, resTy: resTy, hasResult: hasResult, endLbl: endLbl);
				b:popScope();

				local IrBlock is nextBlk: b:curFn:addBlock(label: nextLbl);
				b:switchBlock(blk: nextBlk);
			});
			ki++;
		});

		if({ hasElse }, {
			b:pushScope();
			:lowerArmBody(b: b, armExpr: elseExpr, resSlot: resSlot, resTy: resTy, hasResult: hasResult, endLbl: endLbl);
			b:popScope();
		}, {
			if({ !b:blkTerminated }, {
				b:terminate(inst: IrInst:Br(target: endLbl));
			});
		});

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
		if({ hasResult }, {
			local String is outVal: b:nextTmp();
			b:emit(inst: IrInst:Load(dst: outVal, slot: resSlot, ty: resTy));
			return outVal;
		});
		return '0';
	}
}
