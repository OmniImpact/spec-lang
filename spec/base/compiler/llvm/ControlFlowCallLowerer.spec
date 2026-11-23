#! Package base:compiler:llvm
#! Lowers control-flow calls (if, while) to Spec IR.

Class of CallLowerer is ControlFlowCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', CallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'compiler', 'ir', IrBlock],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'ControlFlowCallLowerer';
	}

	replace Function of Int is order(){
		return 10;
	}

	local Function of Boolean is isAnonArg(CallData is call, Int is idx){
		if({ idx >= call:args:length() }, { return false; });
		local NamedArg is na: call:args:get(index: idx);
		return match(on: na:value, when: [
			Expression:AnonFn: local Function of Boolean(Type is _rt, [Parameter] is _ps, [Statement] is _bd){ return true; },
			else: { false }
		]);
	}

	local Function of Boolean is isSysConditionalTarget(CallData is call){
		if({ call:bareProvider:endsWith(suffix: ':sysinternal:Conditional') }, { return true; });
		local Boolean is ok: false;
		match(on: call:target, when: [
			Expression:Path: local Function(Array of String is segs){
				local Int is n: segs:length();
				if({ n >= 2 && segs:get(index: n - 1, default: '') == 'Conditional' && segs:get(index: n - 2, default: '') == 'sysinternal' }, {
					ok: true;
				});
			}
		], default: {});
		return ok;
	}

	local Function of Boolean is isSysLoopsTarget(CallData is call){
		if({ call:bareProvider:endsWith(suffix: ':sysinternal:Loops') }, { return true; });
		local Boolean is ok: false;
		match(on: call:target, when: [
			Expression:Path: local Function(Array of String is segs){
				local Int is n: segs:length();
				if({ n >= 2 && segs:get(index: n - 1, default: '') == 'Loops' && segs:get(index: n - 2, default: '') == 'sysinternal' }, {
					ok: true;
				});
			}
		], default: {});
		return ok;
	}

	local Function of Boolean is isBareOrConditionalTarget(CallData is call){
		if({ :isSysConditionalTarget(call: call) }, { return true; });
		if({ call:bareProvider == 'Conditional' || call:bareProvider:endsWith(suffix: ':Conditional') }, { return true; });
		local Boolean is ok: false;
		match(on: call:target, when: [
			Expression:Unknown: local Function(){ ok: true; },
			Expression:Ident: local Function(String is tn){
				if({ tn == 'Conditional' || tn == '' || (tn == ':' && call:bareProvider == '') }, { ok: true; });
			},
			Expression:Path: local Function(Array of String is segs){
				if({ segs:length() > 0 && segs:get(index: segs:length() - 1, default: '') == 'Conditional' }, { ok: true; });
			}
		], default: {});
		return ok;
	}

	local Function of Boolean is isBareOrLoopsTarget(CallData is call){
		if({ :isSysLoopsTarget(call: call) }, { return true; });
		if({ call:bareProvider == 'Loops' || call:bareProvider:endsWith(suffix: ':Loops') }, { return true; });
		local Boolean is ok: false;
		match(on: call:target, when: [
			Expression:Unknown: local Function(){
				if({ call:bareProvider == '' }, { ok: true; });
			},
			Expression:Ident: local Function(String is tn){
				if({ tn == 'Loops' || tn == '' || (tn == ':' && call:bareProvider == '') }, { ok: true; });
			},
			Expression:Path: local Function(Array of String is segs){
				if({ segs:length() > 0 && segs:get(index: segs:length() - 1, default: '') == 'Loops' }, { ok: true; });
			},
			Expression:FieldAccess: local Function(Expression is obj, String is mem){
				if({ mem == 'Loops' }, { ok: true; });
			}
		], default: {});
		return ok;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		if({ b:inInlineLoopCallee && call:isBareCall && b:inlineFnParams:has(key: nm) }, {
			return true;
		});
		if({ nm == 'init' }, {
			local Boolean is isCf: false;
			match(on: call:target, when: [
				Expression:Path: local Function(Array of String is segs){
					local Int is n: segs:length();
					if({ n >= 2 && segs:get(index: n - 2, default: '') == 'sysinternal' && (segs:get(index: n - 1, default: '') == 'Conditional' || segs:get(index: n - 1, default: '') == 'Loops') }, {
						isCf: true;
					});
				}
			], default: {});
			return isCf;
		});
		if({ nm == 'branch' && call:args:length() >= 2 }, { return :isSysConditionalTarget(call: call); });
		if({ nm == 'if' && call:args:length() >= 2 }, {
			return :isBareOrConditionalTarget(call: call) && :isAnonArg(call: call, idx: 0) && :isAnonArg(call: call, idx: 1);
		});
		if({ nm == 'while' && call:args:length() >= 2 }, {
			if({ :isSysLoopsTarget(call: call) }, { return true; });
			return :isBareOrLoopsTarget(call: call) && :isAnonArg(call: call, idx: call:args:length() - 2) && :isAnonArg(call: call, idx: call:args:length() - 1);
		});
		if({ nm == 'repeat' && call:args:length() == 2 }, {
			return :isBareOrLoopsTarget(call: call) && :isAnonArg(call: call, idx: 1);
		});
		if({ nm == 'until' && call:args:length() == 2 }, {
			return :isBareOrLoopsTarget(call: call) && :isAnonArg(call: call, idx: 0) && :isAnonArg(call: call, idx: 1);
		});
		if({ nm == 'loop' && call:args:length() >= 2 }, {
			return :isBareOrLoopsTarget(call: call) && :isAnonArg(call: call, idx: call:args:length() - 2) && :isAnonArg(call: call, idx: call:args:length() - 1);
		});
		if({ nm == 'try' && call:args:length() == 2 }, {
			return :isBareOrConditionalTarget(call: call) && :isAnonArg(call: call, idx: 0) && :isAnonArg(call: call, idx: 1);
		});
		if({ b:resolveInlineLoopMember(call: call):name != '' }, {
			return true;
		});
		return false;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		if({ b:inInlineLoopCallee && call:isBareCall && b:inlineFnParams:has(key: nm) }, {
			return :lowerInlineFnParamCall(b: b, expr: expr, call: call);
		});
		if({ nm == 'init' }, {
			# The Conditional/Loops floor init binds the runtime branch
			# primitive; LoopControl constructions flow through the normal
			# generic-init path (the class is a real ARC class).
			return 'null';
		});
		if({ nm == 'if' || nm == 'branch' }, {
			return :lowerIfCall(b: b, expr: expr, call: call);
		});
		if({ nm == 'while' }, {
			:lowerWhileCall(b: b, call: call);
			return '0';
		});
		if({ nm == 'repeat' }, {
			:lowerRepeatCall(b: b, call: call);
			return '0';
		});
		if({ nm == 'until' }, {
			:lowerUntilCall(b: b, call: call);
			return '0';
		});
		if({ nm == 'loop' }, {
			:lowerLoopCall(b: b, call: call);
			return '0';
		});
		if({ nm == 'try' }, {
			return :lowerTryCall(b: b, expr: expr, call: call);
		});
		local Member is inlM: b:resolveInlineLoopMember(call: call);
		if({ inlM:name != '' }, {
			return :lowerStructuralLoopCall(b: b, expr: expr, call: call, m: inlM);
		});
		return '0';
	}

	local Function of String is lowerCondExpr(IrBuilder is b, Expression is condExpr){
		local String is condVal: '0';
		match(on: condExpr, when: [
			Expression:AnonFn: local Function(Type is rt, [Parameter] is ps, [Statement] is bd){
				b:pushScope();
				if({ bd:length() > 0 }, {
					local Int is ci: 0;
					while({ ci < (bd:length() - 1) && !b:blkTerminated }, {
						b:lowerStmt(stmt: bd:get(index: ci));
						ci++;
					});
					if({ !b:blkTerminated }, {
						local Statement is bs: bd:get(index: bd:length() - 1);
						match(on: bs, when: [
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
		], default: {
			local IrType is cty: b:irTypeFor(specType: condExpr:resolvedType);
			if({ cty == IrType:Ptr }, {
				local String is cObj: b:lowerExpr(expr: condExpr);
				local String is fnPtrAddr: b:nextTmp();
				b:emit(inst: IrInst:FieldPtr(dst: fnPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 0));
				local String is fnPtrVal: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: fnPtrVal, slot: fnPtrAddr, ty: IrType:Ptr));
				local String is envPtrAddr: b:nextTmp();
				b:emit(inst: IrInst:FieldPtr(dst: envPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 1));
				local String is envVal: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: envVal, slot: envPtrAddr, ty: IrType:Ptr));
				condVal: b:nextTmp();
				b:emit(inst: IrInst:IndirectCall(dst: condVal, hasDst: true, retType: IrType:I1, fnPtr: fnPtrVal, argTypes: [IrType:Ptr], args: [envVal]));
			}, {
				condVal: b:lowerExpr(expr: condExpr);
			});
		});
		return condVal;
	}

	local Function is lowerBlockExpr(IrBuilder is b, Expression is blkExpr){
		match(on: blkExpr, when: [
			Expression:AnonFn: local Function(Type is rt, [Parameter] is ps, [Statement] is bd){
				b:pushScope();
				b:lowerStmts(stmts: bd);
				b:popScope();
			}
		], default: {
			local IrType is bty: b:irTypeFor(specType: blkExpr:resolvedType);
			if({ bty == IrType:Ptr }, {
				local String is cObj: b:lowerExpr(expr: blkExpr);
				local String is fnPtrAddr: b:nextTmp();
				b:emit(inst: IrInst:FieldPtr(dst: fnPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 0));
				local String is fnPtrVal: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: fnPtrVal, slot: fnPtrAddr, ty: IrType:Ptr));
				local String is envPtrAddr: b:nextTmp();
				b:emit(inst: IrInst:FieldPtr(dst: envPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 1));
				local String is envVal: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: envVal, slot: envPtrAddr, ty: IrType:Ptr));
				b:emit(inst: IrInst:IndirectCall(dst: '', hasDst: false, retType: IrType:Void, fnPtr: fnPtrVal, argTypes: [IrType:Ptr], args: [envVal]));
			}, {
				local String is _unused: b:lowerExpr(expr: blkExpr);
			});
		});
	}

	local Function of String is lowerBlockExprVal(IrBuilder is b, Expression is blkExpr, IrType is expectedTy){
		local String is resVal: '';
		match(on: blkExpr, when: [
			Expression:AnonFn: local Function(Type is rt, [Parameter] is ps, [Statement] is bd){
				b:pushScope();
				if({ expectedTy != IrType:Void && bd:length() > 0 }, {
					local Int is lastIdx: bd:length() - 1;
					local Int is i: 0;
					while({ i < lastIdx }, {
						b:lowerStmt(stmt: bd:get(index: i));
						i++;
					});
					local Statement is lastStmt: bd:get(index: lastIdx);
					match(on: lastStmt, when: [
						Statement:Expr: local Function(Expression is es){
							local IrType is ety: b:irTypeFor(specType: es:resolvedType);
							local String is ev: b:lowerExpr(expr: es);
							resVal: b:castIfNeeded(val: ev, fromTy: ety, toTy: expectedTy);
						},
						Statement:Return: local Function(Expression is re, Boolean is hr){
							if({ hr }, {
								local IrType is rty: b:irTypeFor(specType: re:resolvedType);
								local String is rv: b:lowerExpr(expr: re);
								resVal: b:castIfNeeded(val: rv, fromTy: rty, toTy: expectedTy);
							}, {
								b:lowerStmt(stmt: lastStmt);
							});
						}
					], default: {
						b:lowerStmt(stmt: lastStmt);
					});
				}, {
					b:lowerStmts(stmts: bd);
				});
				b:popScope();
			}
		], default: {
			local IrType is bty: b:irTypeFor(specType: blkExpr:resolvedType);
			local String is bv: b:lowerExpr(expr: blkExpr);
			if({ expectedTy != IrType:Void }, {
				resVal: b:castIfNeeded(val: bv, fromTy: bty, toTy: expectedTy);
			});
		});
		return resVal;
	}

	local Function of String is lowerIfCall(IrBuilder is b, Expression is expr, CallData is call){
		local NamedArg is condNa: call:args:get(index: 0);
		local NamedArg is thenNa: call:args:get(index: 1);
		local Boolean is hasElse: false;
		local NamedArg is elseNa: thenNa;
		local Boolean is hasFinally: false;
		local NamedArg is finallyNa: thenNa;
		local Int is ai: 0;
		while({ ai < call:args:length() }, {
			local NamedArg is na: call:args:get(index: ai);
			if({ na:name == 'check' }, {
				condNa: na;
			}, {
				if({ na:name == 'then' }, {
					thenNa: na;
				}, {
					if({ na:name == 'finally' }, {
						hasFinally: true;
						finallyNa: na;
					}, {
						if({ na:name == 'else' || ai >= 2 }, {
							hasElse: true;
							elseNa: na;
						});
					});
				});
			});
			ai++;
		});
		local IrType is resTy: b:irTypeFor(specType: expr:resolvedType);
		local Boolean is yieldVal: resTy != IrType:Void && hasElse;
		local String is resSlot: '';
		if({ yieldVal }, {
			local String is _rtmp: b:nextTmp();
			resSlot: '%if_res_' . (b:tmpCounter as String);
			b:emit(inst: IrInst:Alloca(slot: resSlot, ty: resTy));
		});

		local String is condVal: :lowerCondExpr(b: b, condExpr: condNa:value);
		local String is thenLbl: b:nextLabel(prefix: 'if_then');
		local String is elseLbl: b:nextLabel(prefix: 'if_else');
		local String is endLbl: b:nextLabel(prefix: 'if_end');
		if({ !hasElse }, { elseLbl: endLbl; });

		b:terminate(inst: IrInst:CondBr(cond: condVal, thenLabel: thenLbl, elseLabel: elseLbl));

		local IrBlock is thenBlk: b:curFn:addBlock(label: thenLbl);
		b:switchBlock(blk: thenBlk);
		if({ yieldVal }, {
			local String is prevRetSlot: b:inlineReturnSlot;
			local String is prevRetEnd: b:inlineReturnEndLbl;
			local IrType is prevRetTy: b:inlineReturnTy;
			b:inlineReturnSlot: resSlot;
			b:inlineReturnEndLbl: endLbl;
			b:inlineReturnTy: resTy;
			local String is tv: :lowerBlockExprVal(b: b, blkExpr: thenNa:value, expectedTy: resTy);
			b:inlineReturnSlot: prevRetSlot;
			b:inlineReturnEndLbl: prevRetEnd;
			b:inlineReturnTy: prevRetTy;
			if({ !b:blkTerminated }, {
				if({ tv != '' }, {
					b:emit(inst: IrInst:Store(slot: resSlot, val: tv, ty: resTy));
				});
				b:terminate(inst: IrInst:Br(target: endLbl));
			});
		}, {
			:lowerBlockExpr(b: b, blkExpr: thenNa:value);
			if({ !b:blkTerminated }, {
				b:terminate(inst: IrInst:Br(target: endLbl));
			});
		});

		if({ hasElse }, {
			local IrBlock is elseBlk: b:curFn:addBlock(label: elseLbl);
			b:switchBlock(blk: elseBlk);
			if({ yieldVal }, {
				local String is prevRetSlot2: b:inlineReturnSlot;
				local String is prevRetEnd2: b:inlineReturnEndLbl;
				local IrType is prevRetTy2: b:inlineReturnTy;
				b:inlineReturnSlot: resSlot;
				b:inlineReturnEndLbl: endLbl;
				b:inlineReturnTy: resTy;
				local String is ev: :lowerBlockExprVal(b: b, blkExpr: elseNa:value, expectedTy: resTy);
				b:inlineReturnSlot: prevRetSlot2;
				b:inlineReturnEndLbl: prevRetEnd2;
				b:inlineReturnTy: prevRetTy2;
				if({ !b:blkTerminated }, {
					if({ ev != '' }, {
						b:emit(inst: IrInst:Store(slot: resSlot, val: ev, ty: resTy));
					});
					b:terminate(inst: IrInst:Br(target: endLbl));
				});
			}, {
				:lowerBlockExpr(b: b, blkExpr: elseNa:value);
				if({ !b:blkTerminated }, {
					b:terminate(inst: IrInst:Br(target: endLbl));
				});
			});
		});

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
		if({ hasFinally }, {
			:lowerBlockExpr(b: b, blkExpr: finallyNa:value);
		});
		if({ yieldVal }, {
			local String is outVal: b:nextTmp();
			b:emit(inst: IrInst:Load(dst: outVal, slot: resSlot, ty: resTy));
			return outVal;
		});
		return '0';
	}

	## `try(body, guard)` — runs the body region inline in the calling frame
	## with the frame's unwind checks retargeted to a local catch; on an
	## in-region unwind the guard runs with the consumed SpecError and its
	## value becomes the construct's value. The error reference is claimed
	## to the frame pool so every exit path (normal, guard re-raise, later
	## frame unwind) releases it exactly once.
	local Function of String is lowerTryCall(IrBuilder is b, Expression is expr, CallData is call){
		local NamedArg is bodyNa: call:args:get(index: 0);
		local NamedArg is guardNa: call:args:get(index: 1);
		local Int is nai: 0;
		while({ nai < call:args:length() }, {
			local NamedArg is na: call:args:get(index: nai);
			if({ na:name == 'body' }, {
				bodyNa: na;
			}, {
				if({ na:name == 'guard' }, {
					guardNa: na;
				});
			});
			nai++;
		});
		local IrType is resTy: b:irTypeFor(specType: expr:resolvedType);
		local Boolean is yieldVal: resTy != IrType:Void;
		local String is resSlot: '';
		if({ yieldVal }, {
			resSlot: b:nextTmp();
			b:emit(inst: IrInst:Alloca(slot: resSlot, ty: resTy));
		});

		local String is catchLbl: b:nextLabel(prefix: 'try_catch');
		local String is endLbl: b:nextLabel(prefix: 'try_end');

		# Body region — inline in this frame. Internal unwind checks and
		# raiseError statements branch to the local catch while the catch
		# context is set.
		local String is savedCatch: b:curInlineCatchLbl;
		local String is prevRetSlot: b:inlineReturnSlot;
		local String is prevRetEnd: b:inlineReturnEndLbl;
		local IrType is prevRetTy: b:inlineReturnTy;
		b:curInlineCatchLbl: catchLbl;
		if({ yieldVal }, {
			b:inlineReturnSlot: resSlot;
			b:inlineReturnEndLbl: endLbl;
			b:inlineReturnTy: resTy;
		});
		local String is bodyVal: :lowerBlockExprVal(b: b, blkExpr: bodyNa:value, expectedTy: resTy);
		b:curInlineCatchLbl: savedCatch;
		if({ yieldVal }, {
			b:inlineReturnSlot: prevRetSlot;
			b:inlineReturnEndLbl: prevRetEnd;
			b:inlineReturnTy: prevRetTy;
		});
		if({ !b:blkTerminated }, {
			if({ yieldVal && bodyVal != '' }, {
				b:emit(inst: IrInst:Store(slot: resSlot, val: bodyVal, ty: resTy));
			});
			local String is fifteenVal: b:nextTmp();
			b:emit(inst: IrInst:ConstInt(dst: fifteenVal, value: 15));
			local String is pendAddr: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: pendAddr, hasDst: true, retType: IrType:I64, callee: '__spec_mem_tls_get_i64', argTypes: [IrType:I64], args: [fifteenVal]));
			local String is zeroAddr: b:nextTmp();
			b:emit(inst: IrInst:ConstInt(dst: zeroAddr, value: 0));
			local String is noPend: b:nextTmp();
			b:emit(inst: IrInst:Cmp(dst: noPend, op: '==', lhs: pendAddr, rhs: zeroAddr, ty: IrType:I64));
			b:terminate(inst: IrInst:CondBr(cond: noPend, thenLabel: endLbl, elseLabel: catchLbl));
		});

		local IrBlock is catchBlk: b:curFn:addBlock(label: catchLbl);
		b:switchBlock(blk: catchBlk);
		local String is errAddr: b:nextTmp();
		b:emit(inst: IrInst:IrCall(dst: errAddr, hasDst: true, retType: IrType:I64, callee: 'Pool_takePendingError', argTypes: [IrType:Ptr], args: ['null']));
		local String is errPtr: b:nextTmp();
		b:emit(inst: IrInst:IrCast(dst: errPtr, val: errAddr, fromType: IrType:I64, toType: IrType:Ptr));
		b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Ptr, callee: 'spec_claim_pool', argTypes: [IrType:Ptr], args: [errPtr]));
		match(on: guardNa:value, when: [
			Expression:AnonFn: local Function(Type is rt, [Parameter] is ps, [Statement] is bd){
				if({ ps:length() > 0 }, {
					local Parameter is p: ps:get(index: 0);
					local String is slot: b:nextTmp();
					b:bindLocal(name: p:name, slot: slot, ty: IrType:Ptr, isArc: true, specType: 'SpecError', isBoxed: false);
					b:emit(inst: IrInst:Alloca(slot: slot, ty: IrType:Ptr));
					b:emit(inst: IrInst:Store(slot: slot, val: errPtr, ty: IrType:Ptr));
				});
			}
		], default: {});
		if({ yieldVal }, {
			b:inlineReturnSlot: resSlot;
			b:inlineReturnEndLbl: endLbl;
			b:inlineReturnTy: resTy;
		});
		local String is guardVal: :lowerBlockExprVal(b: b, blkExpr: guardNa:value, expectedTy: resTy);
		if({ yieldVal }, {
			b:inlineReturnSlot: prevRetSlot;
			b:inlineReturnEndLbl: prevRetEnd;
			b:inlineReturnTy: prevRetTy;
		});
		if({ !b:blkTerminated }, {
			if({ yieldVal && guardVal != '' }, {
				b:emit(inst: IrInst:Store(slot: resSlot, val: guardVal, ty: resTy));
			});
			b:terminate(inst: IrInst:Br(target: endLbl));
		});

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
		if({ yieldVal }, {
			local String is rv: b:nextTmp();
			b:emit(inst: IrInst:Load(dst: rv, slot: resSlot, ty: resTy));
			return rv;
		});
		return '0';
	}

	local Function is lowerLoopBody(IrBuilder is b, Expression is bodyExpr, String is contLbl, String is breakLbl){
		local Boolean is returnsBool: false;
		match(on: bodyExpr, when: [
			Expression:AnonFn: local Function(Type is rt, [Parameter] is ps, [Statement] is bd){
				if({ rt:name == 'Boolean' }, {
					returnsBool: true;
				});
			}
		], default: {});
		if({ returnsBool }, {
			local String is _lrtmp: b:nextTmp();
			local String is loopRetSlot: '%loop_ret_' . (b:tmpCounter as String);
			local String is loopRetEnd: b:nextLabel(prefix: 'loop_ret');
			b:emit(inst: IrInst:Alloca(slot: loopRetSlot, ty: IrType:I1));
			b:emit(inst: IrInst:Store(slot: loopRetSlot, val: '1', ty: IrType:I1));
			local String is prevRetSlot: b:inlineReturnSlot;
			local String is prevRetEnd: b:inlineReturnEndLbl;
			local IrType is prevRetTy: b:inlineReturnTy;
			b:inlineReturnSlot: loopRetSlot;
			b:inlineReturnEndLbl: loopRetEnd;
			b:inlineReturnTy: IrType:I1;
			local String is contVal: :lowerBlockExprVal(b: b, blkExpr: bodyExpr, expectedTy: IrType:I1);
			b:inlineReturnSlot: prevRetSlot;
			b:inlineReturnEndLbl: prevRetEnd;
			b:inlineReturnTy: prevRetTy;
			if({ !b:blkTerminated }, {
				if({ contVal != '' }, {
					b:emit(inst: IrInst:Store(slot: loopRetSlot, val: contVal, ty: IrType:I1));
				});
				b:terminate(inst: IrInst:Br(target: loopRetEnd));
			});
			local IrBlock is retBlk: b:curFn:addBlock(label: loopRetEnd);
			b:switchBlock(blk: retBlk);
			local String is finalCont: b:nextTmp();
			b:emit(inst: IrInst:Load(dst: finalCont, slot: loopRetSlot, ty: IrType:I1));
			b:terminate(inst: IrInst:CondBr(cond: finalCont, thenLabel: contLbl, elseLabel: breakLbl));
		}, {
			:lowerBlockExpr(b: b, blkExpr: bodyExpr);
			if({ !b:blkTerminated }, {
				b:terminate(inst: IrInst:Br(target: contLbl));
			});
		});
	}

	local Function is lowerWhileCall(IrBuilder is b, CallData is call){
		local Boolean is hasVars: false;
		local Boolean is hasEval: false;
		local Boolean is hasIter: false;
		local NamedArg is arg0: call:args:get(index: 0);
		local NamedArg is arg1: call:args:get(index: 1);
		local Expression is varsExpr: arg0:value;
		local Expression is evalExpr: arg0:value;
		local Expression is iterExpr: arg1:value;
		local Int is ai: 0;
		while({ ai < call:args:length() }, {
			local NamedArg is na: call:args:get(index: ai);
			if({ na:name == 'evaluate' }, { evalExpr: na:value; hasEval: true; });
			if({ na:name == 'iterate' || na:name == 'iteration' }, { iterExpr: na:value; hasIter: true; });
			if({ na:name == 'vars' || na:name == 'state' }, { varsExpr: na:value; hasVars: true; });
			ai++;
		});
		if({ !hasEval && call:args:length() >= 3 }, {
			evalExpr: arg1:value;
			hasEval: true;
		});
		if({ !hasIter && call:args:length() >= 3 }, {
			local NamedArg is arg2: call:args:get(index: 2);
			iterExpr: arg2:value;
			hasIter: true;
		});
		if({ !hasVars && call:args:length() >= 3 }, {
			varsExpr: arg0:value;
			hasVars: true;
		});
		b:pushScope();
		if({ hasVars }, {
			match(on: varsExpr, when: [
				Expression:AnonFn: local Function(Type is rt, [Parameter] is ps, [Statement] is bd){
					local Int is pi: 0;
					while({ pi < ps:length() }, {
						local Parameter is p: ps:get(index: pi);
						local IrType is pty: b:irTypeFor(specType: p:paramType:name);
						local Boolean is pArc: b:isArcTypeNode(t: p:paramType);
						local String is _wtmp: b:nextTmp();
						local String is slot: '%wvar_' . p:name . '_' . (b:tmpCounter as String);
						local Boolean is pBoxed: b:capturedNames:has(key: p:name);
						b:bindLocal(name: p:name, slot: slot, ty: pty, isArc: pArc, specType: p:paramType:name, isBoxed: pBoxed);
						local Boolean is pInEntry: b:curBlk:label == 'entry';
						if({ pBoxed }, {
							b:emit(inst: IrInst:Alloca(slot: slot, ty: IrType:Ptr));
						}, {
							b:emit(inst: IrInst:Alloca(slot: slot, ty: pty));
						});
						local String is val: b:emitDefaultVal(ty: pty);
						if({ p:hasDefault }, {
							val: b:lowerExpr(expr: p:defaultExpr);
							local IrType is vty: b:irTypeFor(specType: p:defaultExpr:resolvedType);
							val: b:castIfNeeded(val: val, fromTy: vty, toTy: pty);
							if({ val == '' }, { val: b:emitDefaultVal(ty: pty); });
						});
						if({ pBoxed }, {
							local String is boxPtr: b:emitNewBox(initVal: val, ty: pty, isArc: pArc);
							b:emit(inst: IrInst:Store(slot: slot, val: boxPtr, ty: IrType:Ptr));
						}, {
							b:emit(inst: IrInst:Store(slot: slot, val: val, ty: pty));
						});
						pi++;
					});
					if({ bd:length() > 0 }, {
						b:lowerStmts(stmts: bd);
					});
				}
			], default: {});
		});

		local String is hdrLbl: b:nextLabel(prefix: 'while_hdr');
		local String is bodyLbl: b:nextLabel(prefix: 'while_body');
		local String is endLbl: b:nextLabel(prefix: 'while_end');

		b:terminate(inst: IrInst:Br(target: hdrLbl));

		local IrBlock is hdrBlk: b:curFn:addBlock(label: hdrLbl);
		b:switchBlock(blk: hdrBlk);
		local String is condVal: :lowerCondExpr(b: b, condExpr: evalExpr);
		b:terminate(inst: IrInst:CondBr(cond: condVal, thenLabel: bodyLbl, elseLabel: endLbl));

		local IrBlock is bodyBlk: b:curFn:addBlock(label: bodyLbl);
		b:switchBlock(blk: bodyBlk);
		:lowerLoopBody(b: b, bodyExpr: iterExpr, contLbl: hdrLbl, breakLbl: endLbl);

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
		b:popScope();
	}

	local Function is lowerRepeatCall(IrBuilder is b, CallData is call){
		local NamedArg is na0: call:args:get(index: 0);
		local NamedArg is na1: call:args:get(index: 1);
		local Expression is countExpr: na0:value;
		local Expression is workerExpr: na1:value;
		local Int is ai: 0;
		while({ ai < call:args:length() }, {
			local NamedArg is na: call:args:get(index: ai);
			if({ na:name == 'count' }, { countExpr: na:value; });
			if({ na:name == 'worker' }, { workerExpr: na:value; });
			ai++;
		});

		local String is countVal: b:lowerExpr(expr: countExpr);
		local String is _dtmp: b:nextTmp();
		local String is doneSlot: '%rep_done_' . (b:tmpCounter as String);
		b:emit(inst: IrInst:Alloca(slot: doneSlot, ty: IrType:I64));
		b:emit(inst: IrInst:Store(slot: doneSlot, val: '0', ty: IrType:I64));

		local String is hdrLbl: b:nextLabel(prefix: 'rep_hdr');
		local String is bodyLbl: b:nextLabel(prefix: 'rep_body');
		local String is stepLbl: b:nextLabel(prefix: 'rep_step');
		local String is endLbl: b:nextLabel(prefix: 'rep_end');

		b:terminate(inst: IrInst:Br(target: hdrLbl));

		local IrBlock is hdrBlk: b:curFn:addBlock(label: hdrLbl);
		b:switchBlock(blk: hdrBlk);
		local String is curDone: b:nextTmp();
		b:emit(inst: IrInst:Load(dst: curDone, slot: doneSlot, ty: IrType:I64));
		local String is condVal: b:nextTmp();
		b:emit(inst: IrInst:Cmp(dst: condVal, op: '<', lhs: curDone, rhs: countVal, ty: IrType:I64));
		b:terminate(inst: IrInst:CondBr(cond: condVal, thenLabel: bodyLbl, elseLabel: endLbl));

		local IrBlock is bodyBlk: b:curFn:addBlock(label: bodyLbl);
		b:switchBlock(blk: bodyBlk);
		:lowerLoopBody(b: b, bodyExpr: workerExpr, contLbl: stepLbl, breakLbl: endLbl);

		local IrBlock is stepBlk: b:curFn:addBlock(label: stepLbl);
		b:switchBlock(blk: stepBlk);
		local String is dLoad: b:nextTmp();
		b:emit(inst: IrInst:Load(dst: dLoad, slot: doneSlot, ty: IrType:I64));
		local String is dNext: b:nextTmp();
		b:emit(inst: IrInst:BinOp(dst: dNext, op: '+', lhs: dLoad, rhs: '1', ty: IrType:I64));
		b:emit(inst: IrInst:Store(slot: doneSlot, val: dNext, ty: IrType:I64));
		b:terminate(inst: IrInst:Br(target: hdrLbl));

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
	}

	local Function is lowerUntilCall(IrBuilder is b, CallData is call){
		local NamedArg is na0: call:args:get(index: 0);
		local NamedArg is na1: call:args:get(index: 1);
		local Expression is evalExpr: na0:value;
		local Expression is iterExpr: na1:value;
		local Int is ai: 0;
		while({ ai < call:args:length() }, {
			local NamedArg is na: call:args:get(index: ai);
			if({ na:name == 'evaluate' }, { evalExpr: na:value; });
			if({ na:name == 'iteration' || na:name == 'iterate' }, { iterExpr: na:value; });
			ai++;
		});

		local String is bodyLbl: b:nextLabel(prefix: 'until_body');
		local String is evalLbl: b:nextLabel(prefix: 'until_eval');
		local String is endLbl: b:nextLabel(prefix: 'until_end');

		b:terminate(inst: IrInst:Br(target: bodyLbl));

		local IrBlock is bodyBlk: b:curFn:addBlock(label: bodyLbl);
		b:switchBlock(blk: bodyBlk);
		:lowerLoopBody(b: b, bodyExpr: iterExpr, contLbl: evalLbl, breakLbl: endLbl);

		local IrBlock is evalBlk: b:curFn:addBlock(label: evalLbl);
		b:switchBlock(blk: evalBlk);
		local String is condVal: :lowerCondExpr(b: b, condExpr: evalExpr);
		b:terminate(inst: IrInst:CondBr(cond: condVal, thenLabel: endLbl, elseLabel: bodyLbl));

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
	}

	local Function is lowerLoopCall(IrBuilder is b, CallData is call){
		local NamedArg is firstArg: call:args:get(index: 0);
		local Expression is varsExpr: firstArg:value;
		local Expression is evalExpr: firstArg:value;
		local Expression is iterExpr: firstArg:value;
		local Boolean is hasVars: false;
		local Boolean is hasEval: false;
		local Boolean is hasIter: false;
		local Int is ai: 0;
		while({ ai < call:args:length() }, {
			local NamedArg is na: call:args:get(index: ai);
			if({ na:name == 'vars' || na:name == 'state' }, {
				varsExpr: na:value;
				hasVars: true;
			});
			if({ na:name == 'evaluate' }, {
				evalExpr: na:value;
				hasEval: true;
			});
			if({ na:name == 'iterate' || na:name == 'iteration' }, {
				iterExpr: na:value;
				hasIter: true;
			});
			ai++;
		});
		if({ !hasVars && call:args:length() >= 3 }, {
			local NamedArg is na0: call:args:get(index: 0);
			varsExpr: na0:value;
			hasVars: true;
		});
		if({ !hasEval }, {
			if({ call:args:length() >= 3 }, {
				local NamedArg is na1: call:args:get(index: 1);
				evalExpr: na1:value;
			}, {
				local NamedArg is na0: call:args:get(index: 0);
				evalExpr: na0:value;
			});
		});
		if({ !hasIter }, {
			if({ call:args:length() >= 3 }, {
				local NamedArg is na2: call:args:get(index: 2);
				iterExpr: na2:value;
			}, {
				local NamedArg is na1: call:args:get(index: 1);
				iterExpr: na1:value;
			});
		});

		b:pushScope();
		if({ hasVars }, {
			match(on: varsExpr, when: [
				Expression:AnonFn: local Function(Type is rt, [Parameter] is params, [Statement] is bd){
					local Int is pi: 0;
					while({ pi < params:length() }, {
						local Parameter is p: params:get(index: pi);
						local IrType is vty: b:irTypeFor(specType: p:paramType:name);
						local String is _vtmp: b:nextTmp();
						local String is slot: '%lvar_' . p:name . '_' . (b:tmpCounter as String);
						local Boolean is vArc: b:isArcTypeNode(t: p:paramType);
						local Boolean is vBoxed: b:capturedNames:has(key: p:name);
						local Boolean is vInEntry: b:curBlk:label == 'entry';
						b:bindLocal(name: p:name, slot: slot, ty: vty, isArc: vArc, specType: p:paramType:name, isBoxed: vBoxed);
						if({ vBoxed }, {
							b:emit(inst: IrInst:Alloca(slot: slot, ty: IrType:Ptr));
						}, {
							b:emit(inst: IrInst:Alloca(slot: slot, ty: vty));
						});
						local String is ival: b:emitDefaultVal(ty: vty);
						if({ p:hasDefault }, {
							local IrType is ity: b:irTypeFor(specType: p:defaultExpr:resolvedType);
							ival: b:lowerExpr(expr: p:defaultExpr);
							ival: b:castIfNeeded(val: ival, fromTy: ity, toTy: vty);
						});
						if({ vBoxed }, {
							local String is boxPtr: b:emitNewBox(initVal: ival, ty: vty, isArc: vArc);
							b:emit(inst: IrInst:Store(slot: slot, val: boxPtr, ty: IrType:Ptr));
						}, {
							b:emit(inst: IrInst:Store(slot: slot, val: ival, ty: vty));
						});
						pi++;
					});
				}
			], default: {});
		});

		local String is hdrLbl: b:nextLabel(prefix: 'loop_hdr');
		local String is bodyLbl: b:nextLabel(prefix: 'loop_body');
		local String is endLbl: b:nextLabel(prefix: 'loop_end');

		b:terminate(inst: IrInst:Br(target: hdrLbl));

		local IrBlock is hdrBlk: b:curFn:addBlock(label: hdrLbl);
		b:switchBlock(blk: hdrBlk);
		local String is condVal: :lowerCondExpr(b: b, condExpr: evalExpr);
		b:terminate(inst: IrInst:CondBr(cond: condVal, thenLabel: bodyLbl, elseLabel: endLbl));

		local IrBlock is bodyBlk: b:curFn:addBlock(label: bodyLbl);
		b:switchBlock(blk: bodyBlk);
		:lowerLoopBody(b: b, bodyExpr: iterExpr, contLbl: hdrLbl, breakLbl: endLbl);

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
		b:popScope();
	}

	## Lowers a value-yielding inlined closure body in the caller's already-pushed
	## scope, evaluating the final statement as the yielded value when present.
	local Function of String is lowerInlineAnonBodyVal(IrBuilder is b, [Statement] is bd, IrType is expectedTy){
		local String is resVal: '';
		if({ expectedTy != IrType:Void && bd:length() > 0 }, {
			local Int is lastIdx: bd:length() - 1;
			while([Int is i: 0], { i < lastIdx && !b:blkTerminated }, {
				b:lowerStmt(stmt: bd:get(index: i));
				i++;
			});
			if({ !b:blkTerminated }, {
				local Statement is lastStmt: bd:get(index: lastIdx);
				match(on: lastStmt, when: [
					Statement:Expr: local Function(Expression is es){
						local IrType is ety: b:irTypeFor(specType: es:resolvedType);
						if({ ety == IrType:Void }, {
							b:lowerStmt(stmt: lastStmt);
						}, {
							local String is ev: b:lowerExpr(expr: es);
							resVal: b:castIfNeeded(val: ev, fromTy: ety, toTy: expectedTy);
						});
					},
					Statement:Return: local Function(Expression is re, Boolean is hr){
						if({ hr }, {
							local IrType is rty: b:irTypeFor(specType: re:resolvedType);
							local String is rv: b:lowerExpr(expr: re);
							resVal: b:castIfNeeded(val: rv, fromTy: rty, toTy: expectedTy);
						}, {
							b:lowerStmt(stmt: lastStmt);
						});
					}
				], default: {
					b:lowerStmt(stmt: lastStmt);
				});
			});
		}, {
			b:lowerStmts(stmts: bd);
		});
		return resVal;
	}

	## Structurally inlines any [Loops] method whose `Function`-typed parameters
	## are supplied as inline closure literals: evaluates non-closure arguments in
	## the caller's scope, lowers the callee's AST body in an isolated hygienic
	## scope, and expands invocations of its `Function` parameters inline in the
	## caller's lexical scope (zero closure allocation).
	local Function of String is lowerStructuralLoopCall(IrBuilder is b, Expression is expr, CallData is call, Member is m){
		local Int is wantIdx: if({ call:overloadIndex >= 0 }, { call:overloadIndex }, { 0 });
		local String is mKey: 'Loops:' . m:name . '#' . (wantIdx as String);

		local Boolean is allPos: true;
		while([Int is ai: 0], { allPos && ai < call:args:length() }, {
			if({ call:args:get(index: ai):name != '' }, { allPos: false; });
			ai++;
		});

		# 1. Evaluate non-Function arguments in the caller's scope and collect
		#    inline closure arguments by callee parameter name.
		local Map of String to Expression is fnParams: Map();
		local [String] is bindNames: [];
		local [String] is bindVals: [];
		local [IrType] is bindTys: [];
		local [Boolean] is bindArcs: [];
		local [String] is bindSpecs: [];

		while([Int is pi: 0], { pi < m:params:length() }, {
			local Parameter is p: m:params:get(index: pi);
			local Boolean is hasArg: false;
			local Expression is argExpr: Expression:Unknown;
			if({ allPos }, {
				if({ pi < call:args:length() }, {
					hasArg: true;
					argExpr: call:args:get(index: pi):value;
				});
			}, {
				while([Int is ai: 0], { !hasArg && ai < call:args:length() }, {
					local NamedArg is na: call:args:get(index: ai);
					if({ na:name == p:name }, {
						hasArg: true;
						argExpr: na:value;
					});
					ai++;
				});
			});
			if({ p:paramType:name == 'Function' }, {
				fnParams:set(key: p:name, value: argExpr);
			}, {
				local Expression is srcExpr: if({ hasArg }, { argExpr }, { p:defaultExpr });
				local String is val: b:lowerExpr(expr: srcExpr);
				local IrType is pty: b:irTypeForNode(t: p:paramType);
				local IrType is valTy: b:irTypeFor(specType: srcExpr:resolvedType);
				val: b:castIfNeeded(val: val, fromTy: valTy, toTy: pty);
				local String is pSpec: if({ p:paramType:name != '' && p:paramType:name != 'Any' }, { p:paramType:name }, { srcExpr:resolvedType });
				bindNames:push(item: p:name);
				bindVals:push(item: val);
				bindTys:push(item: pty);
				bindArcs:push(item: b:isArcTypeNode(t: p:paramType));
				bindSpecs:push(item: pSpec);
			});
			pi++;
		});

		# 2. Snapshot caller's lexical scope and any outer inline-loop state.
		local Boolean is prevInInline: b:inInlineLoopCallee;
		local Map of String to Expression is prevFnParams: b:inlineFnParams;
		local Boolean is prevCallerInInline: b:inlineCallerInInline;
		local Map of String to Expression is prevCallerFnParams: b:inlineCallerFnParams;
		local Map of String to String is prevCallerSlots: b:inlineCallerSlots;
		local Map of String to IrType is prevCallerTypes: b:inlineCallerTypes;
		local Map of String to Boolean is prevCallerIsArc: b:inlineCallerIsArc;
		local Map of String to String is prevCallerSpecTypes: b:inlineCallerSpecTypes;
		local Map of String to Boolean is prevCallerBoxed: b:inlineCallerBoxed;
		local Map of String to Boolean is prevCallerCaptured: b:inlineCallerCaptured;
		local Map of String to String is prevCallerLazyState: b:inlineCallerLazyStateSlots;
		local Map of String to Expression is prevCallerLazyExprs: b:inlineCallerLazyExprs;
		local Array of String is prevCallerScopeVars: b:inlineCallerScopeVars;
		local Array of String is prevCallerScopeOldSlots: b:inlineCallerScopeOldSlots;
		local [IrType] is prevCallerScopeOldTypes: b:inlineCallerScopeOldTypes;
		local [Boolean] is prevCallerScopeOldArcs: b:inlineCallerScopeOldArcs;
		local Array of String is prevCallerScopeOldSpecs: b:inlineCallerScopeOldSpecs;
		local [Boolean] is prevCallerScopeOldBoxed: b:inlineCallerScopeOldBoxed;
		local Array of String is prevCallerScopeOldLazyStates: b:inlineCallerScopeOldLazyStates;
		local [Expression] is prevCallerScopeOldLazyExprs: b:inlineCallerScopeOldLazyExprs;
		local [Int] is prevCallerScopeMarks: b:inlineCallerScopeMarks;

		local Map of String to String is callerSlots: b:localSlots;
		local Map of String to IrType is callerTypes: b:localTypes;
		local Map of String to Boolean is callerIsArc: b:localIsArc;
		local Map of String to String is callerSpecTypes: b:localSpecTypes;
		local Map of String to Boolean is callerBoxed: b:boxedLocals;
		local Map of String to Boolean is callerCaptured: b:capturedNames;
		local Map of String to String is callerLazyState: b:lazyLocalStateSlots;
		local Map of String to Expression is callerLazyExprs: b:lazyLocalExprs;
		local Array of String is callerScopeVars: b:scopeVarStack;
		local Array of String is callerScopeOldSlots: b:scopeOldSlotStack;
		local [IrType] is callerScopeOldTypes: b:scopeOldTypeStack;
		local [Boolean] is callerScopeOldArcs: b:scopeOldArcStack;
		local Array of String is callerScopeOldSpecs: b:scopeOldSpecTypeStack;
		local [Boolean] is callerScopeOldBoxed: b:scopeOldBoxedStack;
		local Array of String is callerScopeOldLazyStates: b:scopeOldLazyStateStack;
		local [Expression] is callerScopeOldLazyExprs: b:scopeOldLazyExprStack;
		local [Int] is callerScopeMarks: b:scopeMarkStack;

		# 3. Install caller snapshot and a clean lexical scope for the callee body.
		b:inlineCallerInInline: prevInInline;
		b:inlineCallerFnParams: prevFnParams;
		b:inlineCallerSlots: callerSlots;
		b:inlineCallerTypes: callerTypes;
		b:inlineCallerIsArc: callerIsArc;
		b:inlineCallerSpecTypes: callerSpecTypes;
		b:inlineCallerBoxed: callerBoxed;
		b:inlineCallerCaptured: callerCaptured;
		b:inlineCallerLazyStateSlots: callerLazyState;
		b:inlineCallerLazyExprs: callerLazyExprs;
		b:inlineCallerScopeVars: callerScopeVars;
		b:inlineCallerScopeOldSlots: callerScopeOldSlots;
		b:inlineCallerScopeOldTypes: callerScopeOldTypes;
		b:inlineCallerScopeOldArcs: callerScopeOldArcs;
		b:inlineCallerScopeOldSpecs: callerScopeOldSpecs;
		b:inlineCallerScopeOldBoxed: callerScopeOldBoxed;
		b:inlineCallerScopeOldLazyStates: callerScopeOldLazyStates;
		b:inlineCallerScopeOldLazyExprs: callerScopeOldLazyExprs;
		b:inlineCallerScopeMarks: callerScopeMarks;

		b:localSlots: Map();
		b:localTypes: Map();
		b:localIsArc: Map();
		b:localSpecTypes: Map();
		b:boxedLocals: Map();
		b:capturedNames: Map();
		b:lazyLocalStateSlots: Map();
		b:lazyLocalExprs: Map();
		b:scopeVarStack: Array();
		b:scopeOldSlotStack: Array();
		b:scopeOldTypeStack: [];
		b:scopeOldArcStack: [];
		b:scopeOldSpecTypeStack: Array();
		b:scopeOldBoxedStack: [];
		b:scopeOldLazyStateStack: Array();
		b:scopeOldLazyExprStack: [];
		b:scopeMarkStack: [];
		b:inlineFnParams: fnParams;
		b:inInlineLoopCallee: true;
		b:inlineActiveMethods:set(key: mKey, value: true);

		# 4. Bind non-Function parameters into the callee's clean scope.
		b:pushScope();
		while([Int is bi: 0], { bi < bindNames:length() }, {
			local String is bn: bindNames:get(index: bi);
			local String is bv: bindVals:get(index: bi);
			local IrType is bty: bindTys:get(index: bi);
			local Boolean is barc: bindArcs:get(index: bi);
			local String is bspec: bindSpecs:get(index: bi);
			local String is _btmp: b:nextTmp();
			local String is slot: '%ilp_' . bn . '_' . (b:tmpCounter as String);
			b:bindLocal(name: bn, slot: slot, ty: bty, isArc: barc, specType: bspec, isBoxed: false);
			b:emit(inst: IrInst:Alloca(slot: slot, ty: bty));
			b:emit(inst: IrInst:Store(slot: slot, val: bv, ty: bty));
			bi++;
		});

		# 5. Lower the callee's body with an inline return target so any `return`
		#    in the loop method exits the inlined loop rather than the caller.
		local IrType is retTy: b:irTypeFor(specType: expr:resolvedType);
		local String is endLbl: b:nextLabel(prefix: 'iloop_end');
		local String is resSlot: '';
		if({ retTy != IrType:Void }, {
			local String is _rtmp: b:nextTmp();
			resSlot: '%iloop_res_' . (b:tmpCounter as String);
			b:emit(inst: IrInst:Alloca(slot: resSlot, ty: retTy));
			b:emit(inst: IrInst:Store(slot: resSlot, val: b:emitDefaultVal(ty: retTy), ty: retTy));
		});
		local String is prevRetSlot: b:inlineReturnSlot;
		local String is prevRetEnd: b:inlineReturnEndLbl;
		local IrType is prevRetTy: b:inlineReturnTy;
		b:inlineReturnSlot: resSlot;
		b:inlineReturnEndLbl: endLbl;
		b:inlineReturnTy: retTy;

		b:lowerStmts(stmts: m:body);
		if({ !b:blkTerminated }, {
			b:terminate(inst: IrInst:Br(target: endLbl));
		});

		b:inlineReturnSlot: prevRetSlot;
		b:inlineReturnEndLbl: prevRetEnd;
		b:inlineReturnTy: prevRetTy;

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
		local String is outVal: '0';
		if({ retTy != IrType:Void }, {
			outVal: b:nextTmp();
			b:emit(inst: IrInst:Load(dst: outVal, slot: resSlot, ty: retTy));
		});

		b:popScope();

		# 6. Restore caller's lexical scope and outer inline-loop state.
		b:inlineActiveMethods:remove(key: mKey);
		b:localSlots: callerSlots;
		b:localTypes: callerTypes;
		b:localIsArc: callerIsArc;
		b:localSpecTypes: callerSpecTypes;
		b:boxedLocals: callerBoxed;
		b:capturedNames: callerCaptured;
		b:lazyLocalStateSlots: callerLazyState;
		b:lazyLocalExprs: callerLazyExprs;
		b:scopeVarStack: callerScopeVars;
		b:scopeOldSlotStack: callerScopeOldSlots;
		b:scopeOldTypeStack: callerScopeOldTypes;
		b:scopeOldArcStack: callerScopeOldArcs;
		b:scopeOldSpecTypeStack: callerScopeOldSpecs;
		b:scopeOldBoxedStack: callerScopeOldBoxed;
		b:scopeOldLazyStateStack: callerScopeOldLazyStates;
		b:scopeOldLazyExprStack: callerScopeOldLazyExprs;
		b:scopeMarkStack: callerScopeMarks;

		b:inInlineLoopCallee: prevInInline;
		b:inlineFnParams: prevFnParams;
		b:inlineCallerInInline: prevCallerInInline;
		b:inlineCallerFnParams: prevCallerFnParams;
		b:inlineCallerSlots: prevCallerSlots;
		b:inlineCallerTypes: prevCallerTypes;
		b:inlineCallerIsArc: prevCallerIsArc;
		b:inlineCallerSpecTypes: prevCallerSpecTypes;
		b:inlineCallerBoxed: prevCallerBoxed;
		b:inlineCallerCaptured: prevCallerCaptured;
		b:inlineCallerLazyStateSlots: prevCallerLazyState;
		b:inlineCallerLazyExprs: prevCallerLazyExprs;
		b:inlineCallerScopeVars: prevCallerScopeVars;
		b:inlineCallerScopeOldSlots: prevCallerScopeOldSlots;
		b:inlineCallerScopeOldTypes: prevCallerScopeOldTypes;
		b:inlineCallerScopeOldArcs: prevCallerScopeOldArcs;
		b:inlineCallerScopeOldSpecs: prevCallerScopeOldSpecs;
		b:inlineCallerScopeOldBoxed: prevCallerScopeOldBoxed;
		b:inlineCallerScopeOldLazyStates: prevCallerScopeOldLazyStates;
		b:inlineCallerScopeOldLazyExprs: prevCallerScopeOldLazyExprs;
		b:inlineCallerScopeMarks: prevCallerScopeMarks;

		return outVal;
	}

	## Expands an invocation of an inlined `Function` parameter (e.g. `worker(idx)`
	## or `action(list:get(index: idx))`) inside an inlined [Loops] body: evaluates
	## arguments in the callee's scope, then switches to the caller's lexical scope
	## to bind the closure's parameters and lower its body inline.
	local Function of String is lowerInlineFnParamCall(IrBuilder is b, Expression is expr, CallData is call){
		local Expression is fnExpr: b:inlineFnParams:get(key: call:name, default: Expression:Unknown);

		# 1. Evaluate call arguments in the callee's scope.
		local [String] is argNames: [];
		local [String] is argVals: [];
		local [IrType] is argTys: [];
		local [String] is argSpecs: [];
		while([Int is ai: 0], { ai < call:args:length() }, {
			local NamedArg is na: call:args:get(index: ai);
			local String is av: b:lowerExpr(expr: na:value);
			argNames:push(item: na:name);
			argVals:push(item: av);
			argTys:push(item: b:irTypeFor(specType: na:value:resolvedType));
			argSpecs:push(item: na:value:resolvedType);
			ai++;
		});

		# 2. Save callee scope and switch to caller's lexical scope.
		local Boolean is calleeInInline: b:inInlineLoopCallee;
		local Map of String to Expression is calleeFnParams: b:inlineFnParams;
		local Map of String to String is calleeSlots: b:localSlots;
		local Map of String to IrType is calleeTypes: b:localTypes;
		local Map of String to Boolean is calleeIsArc: b:localIsArc;
		local Map of String to String is calleeSpecTypes: b:localSpecTypes;
		local Map of String to Boolean is calleeBoxed: b:boxedLocals;
		local Map of String to Boolean is calleeCaptured: b:capturedNames;
		local Map of String to String is calleeLazyState: b:lazyLocalStateSlots;
		local Map of String to Expression is calleeLazyExprs: b:lazyLocalExprs;
		local Array of String is calleeScopeVars: b:scopeVarStack;
		local Array of String is calleeScopeOldSlots: b:scopeOldSlotStack;
		local [IrType] is calleeScopeOldTypes: b:scopeOldTypeStack;
		local [Boolean] is calleeScopeOldArcs: b:scopeOldArcStack;
		local Array of String is calleeScopeOldSpecs: b:scopeOldSpecTypeStack;
		local [Boolean] is calleeScopeOldBoxed: b:scopeOldBoxedStack;
		local Array of String is calleeScopeOldLazyStates: b:scopeOldLazyStateStack;
		local [Expression] is calleeScopeOldLazyExprs: b:scopeOldLazyExprStack;
		local [Int] is calleeScopeMarks: b:scopeMarkStack;

		b:inInlineLoopCallee: b:inlineCallerInInline;
		b:inlineFnParams: b:inlineCallerFnParams;
		b:localSlots: b:inlineCallerSlots;
		b:localTypes: b:inlineCallerTypes;
		b:localIsArc: b:inlineCallerIsArc;
		b:localSpecTypes: b:inlineCallerSpecTypes;
		b:boxedLocals: b:inlineCallerBoxed;
		b:capturedNames: b:inlineCallerCaptured;
		b:lazyLocalStateSlots: b:inlineCallerLazyStateSlots;
		b:lazyLocalExprs: b:inlineCallerLazyExprs;
		b:scopeVarStack: b:inlineCallerScopeVars;
		b:scopeOldSlotStack: b:inlineCallerScopeOldSlots;
		b:scopeOldTypeStack: b:inlineCallerScopeOldTypes;
		b:scopeOldArcStack: b:inlineCallerScopeOldArcs;
		b:scopeOldSpecTypeStack: b:inlineCallerScopeOldSpecs;
		b:scopeOldBoxedStack: b:inlineCallerScopeOldBoxed;
		b:scopeOldLazyStateStack: b:inlineCallerScopeOldLazyStates;
		b:scopeOldLazyExprStack: b:inlineCallerScopeOldLazyExprs;
		b:scopeMarkStack: b:inlineCallerScopeMarks;

		# 3. Bind the closure's parameters and lower its body in the caller's scope.
		local IrType is retTy: b:irTypeFor(specType: expr:resolvedType);
		local String is resVal: '0';
		match(on: fnExpr, when: [
			Expression:AnonFn: local Function(Type is rt, [Parameter] is ps, [Statement] is bd){
				b:pushScope();
				while([Int is pi: 0], { pi < ps:length() }, {
					local Parameter is p: ps:get(index: pi);
					local Int is matchIdx: -1;
					while([Int is aj: 0], { matchIdx < 0 && aj < argNames:length() }, {
						if({ argNames:get(index: aj) == p:name }, { matchIdx: aj; });
						aj++;
					});
					if({ matchIdx < 0 && pi < argVals:length() }, { matchIdx: pi; });
					if({ matchIdx >= 0 }, {
						local String is av: argVals:get(index: matchIdx);
						local IrType is aty: argTys:get(index: matchIdx);
						local String is aspec: argSpecs:get(index: matchIdx);
						local Boolean is hasDeclTy: p:paramType:name != '' && p:paramType:name != 'Any';
						local IrType is pty: if({ hasDeclTy }, { b:irTypeForNode(t: p:paramType) }, { aty });
						local String is pSpec: if({ hasDeclTy }, { p:paramType:name }, { aspec });
						local Boolean is pArc: if({ hasDeclTy }, { b:isArcTypeNode(t: p:paramType) }, { pty == IrType:Ptr });
						local Boolean is pBoxed: b:capturedNames:has(key: p:name);
						local String is boundVal: b:castIfNeeded(val: av, fromTy: aty, toTy: pty);
						local String is _ptmp: b:nextTmp();
						local String is slot: '%lidx_' . p:name . '_' . (b:tmpCounter as String);
						b:bindLocal(name: p:name, slot: slot, ty: pty, isArc: pArc, specType: pSpec, isBoxed: pBoxed);
						if({ pBoxed }, {
							b:emit(inst: IrInst:Alloca(slot: slot, ty: IrType:Ptr));
							local String is boxPtr: b:emitNewBox(initVal: boundVal, ty: pty, isArc: pArc);
							b:emit(inst: IrInst:Store(slot: slot, val: boxPtr, ty: IrType:Ptr));
						}, {
							b:emit(inst: IrInst:Alloca(slot: slot, ty: pty));
							b:emit(inst: IrInst:Store(slot: slot, val: boundVal, ty: pty));
						});
					});
					pi++;
				});

				local IrType is effRetTy: retTy;
				if({ expr:resolvedType == 'Any' && (rt:name == '' || rt:name == 'Void') }, {
					effRetTy: IrType:Void;
				});
				local String is fnEndLbl: b:nextLabel(prefix: 'inlfn_end');
				local String is prevRetSlot: b:inlineReturnSlot;
				local String is prevRetEnd: b:inlineReturnEndLbl;
				local IrType is prevRetTy: b:inlineReturnTy;
				if({ effRetTy != IrType:Void }, {
					local String is _ftmp: b:nextTmp();
					local String is fnResSlot: '%inlfn_res_' . (b:tmpCounter as String);
					b:emit(inst: IrInst:Alloca(slot: fnResSlot, ty: effRetTy));
					b:emit(inst: IrInst:Store(slot: fnResSlot, val: b:emitDefaultVal(ty: effRetTy), ty: effRetTy));
					b:inlineReturnSlot: fnResSlot;
					b:inlineReturnEndLbl: fnEndLbl;
					b:inlineReturnTy: effRetTy;
					local String is yielded: :lowerInlineAnonBodyVal(b: b, bd: bd, expectedTy: effRetTy);
					if({ !b:blkTerminated }, {
						if({ yielded != '' }, {
							b:emit(inst: IrInst:Store(slot: fnResSlot, val: yielded, ty: effRetTy));
						});
						b:terminate(inst: IrInst:Br(target: fnEndLbl));
					});
					b:inlineReturnSlot: prevRetSlot;
					b:inlineReturnEndLbl: prevRetEnd;
					b:inlineReturnTy: prevRetTy;
					local IrBlock is fnEndBlk: b:curFn:addBlock(label: fnEndLbl);
					b:switchBlock(blk: fnEndBlk);
					resVal: b:nextTmp();
					b:emit(inst: IrInst:Load(dst: resVal, slot: fnResSlot, ty: effRetTy));
				}, {
					b:inlineReturnSlot: '';
					b:inlineReturnEndLbl: fnEndLbl;
					b:inlineReturnTy: IrType:Void;
					b:lowerStmts(stmts: bd);
					if({ !b:blkTerminated }, {
						b:terminate(inst: IrInst:Br(target: fnEndLbl));
					});
					b:inlineReturnSlot: prevRetSlot;
					b:inlineReturnEndLbl: prevRetEnd;
					b:inlineReturnTy: prevRetTy;
					local IrBlock is fnEndBlk: b:curFn:addBlock(label: fnEndLbl);
					b:switchBlock(blk: fnEndBlk);
					if({ retTy == IrType:Ptr }, { resVal: 'null'; });
				});
				b:popScope();
			}
		], default: {});

		# 4. Restore callee scope.
		b:inInlineLoopCallee: calleeInInline;
		b:inlineFnParams: calleeFnParams;
		b:localSlots: calleeSlots;
		b:localTypes: calleeTypes;
		b:localIsArc: calleeIsArc;
		b:localSpecTypes: calleeSpecTypes;
		b:boxedLocals: calleeBoxed;
		b:capturedNames: calleeCaptured;
		b:lazyLocalStateSlots: calleeLazyState;
		b:lazyLocalExprs: calleeLazyExprs;
		b:scopeVarStack: calleeScopeVars;
		b:scopeOldSlotStack: calleeScopeOldSlots;
		b:scopeOldTypeStack: calleeScopeOldTypes;
		b:scopeOldArcStack: calleeScopeOldArcs;
		b:scopeOldSpecTypeStack: calleeScopeOldSpecs;
		b:scopeOldBoxedStack: calleeScopeOldBoxed;
		b:scopeOldLazyStateStack: calleeScopeOldLazyStates;
		b:scopeOldLazyExprStack: calleeScopeOldLazyExprs;
		b:scopeMarkStack: calleeScopeMarks;

		return resVal;
	}
}
