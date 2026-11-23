#! Package base:compiler:llvm
#! Lowers control-flow calls (if, while) to Spec IR.

Class of CallLowerer is ControlFlowCallLowerer{
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
		['base', 'struct', Array],
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
		return false;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
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
		if({ nm == 'times' }, {
			:lowerTimesCall(b: b, call: call);
			return '0';
		});
		if({ nm == 'range' }, {
			:lowerRangeCall(b: b, call: call);
			return '0';
		});
		if({ nm == 'rangeStep' }, {
			:lowerRangeStepCall(b: b, call: call);
			return '0';
		});
		if({ nm == 'forever' }, {
			:lowerForeverCall(b: b, call: call);
			return '0';
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

	local Function is bindWorkerParam(IrBuilder is b, Expression is workerExpr, String is val){
		match(on: workerExpr, when: [
			Expression:AnonFn: local Function(Type is rt, [Parameter] is ps, [Statement] is bd){
				if({ ps:length() > 0 }, {
					local Parameter is p: ps:get(index: 0);
					local String is _ptmp: b:nextTmp();
					local String is slot: '%lidx_' . p:name . '_' . (b:tmpCounter as String);
					b:bindLocal(name: p:name, slot: slot, ty: IrType:I64, isArc: false, specType: 'Int', isBoxed: false);
					b:emit(inst: IrInst:Alloca(slot: slot, ty: IrType:I64));
					b:emit(inst: IrInst:Store(slot: slot, val: val, ty: IrType:I64));
				});
			}
		], default: {});
	}

	local Function is lowerTimesCall(IrBuilder is b, CallData is call){
		local NamedArg is na0: call:args:get(index: 0);
		local NamedArg is na1: call:args:get(index: 1);
		local Expression is countExpr: na0:value;
		local Expression is workerExpr: na1:value;
		local String is endVal: b:lowerExpr(expr: countExpr);
		:lowerIntSteppedLoop(b: b, startVal: '0', endVal: endVal, stepVal: '1', workerExpr: workerExpr);
	}

	local Function is lowerRangeCall(IrBuilder is b, CallData is call){
		local NamedArg is na0: call:args:get(index: 0);
		local NamedArg is na1: call:args:get(index: 1);
		local NamedArg is na2: call:args:get(index: 2);
		local Expression is startExpr: na0:value;
		local Expression is endExpr: na1:value;
		local Expression is workerExpr: na2:value;
		local String is startVal: b:lowerExpr(expr: startExpr);
		local String is endVal: b:lowerExpr(expr: endExpr);
		:lowerIntSteppedLoop(b: b, startVal: startVal, endVal: endVal, stepVal: '1', workerExpr: workerExpr);
	}

	local Function is lowerRangeStepCall(IrBuilder is b, CallData is call){
		local NamedArg is na0: call:args:get(index: 0);
		local NamedArg is na1: call:args:get(index: 1);
		local NamedArg is na2: call:args:get(index: 2);
		local NamedArg is na3: call:args:get(index: 3);
		local Expression is startExpr: na0:value;
		local Expression is endExpr: na1:value;
		local Expression is stepExpr: na2:value;
		local Expression is workerExpr: na3:value;
		local String is startVal: b:lowerExpr(expr: startExpr);
		local String is endVal: b:lowerExpr(expr: endExpr);
		local String is stepVal: b:lowerExpr(expr: stepExpr);
		:lowerIntSteppedLoop(b: b, startVal: startVal, endVal: endVal, stepVal: stepVal, workerExpr: workerExpr);
	}

	local Function is lowerIntSteppedLoop(IrBuilder is b, String is startVal, String is endVal, String is stepVal, Expression is workerExpr){
		local String is _itmp: b:nextTmp();
		local String is idxSlot: '%rng_idx_' . (b:tmpCounter as String);
		b:emit(inst: IrInst:Alloca(slot: idxSlot, ty: IrType:I64));
		b:emit(inst: IrInst:Store(slot: idxSlot, val: startVal, ty: IrType:I64));

		local String is hdrLbl: b:nextLabel(prefix: 'rng_hdr');
		local String is bodyLbl: b:nextLabel(prefix: 'rng_body');
		local String is stepLbl: b:nextLabel(prefix: 'rng_step');
		local String is endLbl: b:nextLabel(prefix: 'rng_end');

		local String is nzCond: b:nextTmp();
		b:emit(inst: IrInst:Cmp(dst: nzCond, op: '!=', lhs: stepVal, rhs: '0', ty: IrType:I64));
		b:terminate(inst: IrInst:CondBr(cond: nzCond, thenLabel: hdrLbl, elseLabel: endLbl));

		local IrBlock is hdrBlk: b:curFn:addBlock(label: hdrLbl);
		b:switchBlock(blk: hdrBlk);
		local String is curIdx: b:nextTmp();
		b:emit(inst: IrInst:Load(dst: curIdx, slot: idxSlot, ty: IrType:I64));
		local String is isPos: b:nextTmp();
		b:emit(inst: IrInst:Cmp(dst: isPos, op: '>', lhs: stepVal, rhs: '0', ty: IrType:I64));
		local String is ltEnd: b:nextTmp();
		b:emit(inst: IrInst:Cmp(dst: ltEnd, op: '<', lhs: curIdx, rhs: endVal, ty: IrType:I64));
		local String is gtEnd: b:nextTmp();
		b:emit(inst: IrInst:Cmp(dst: gtEnd, op: '>', lhs: curIdx, rhs: endVal, ty: IrType:I64));
		local String is posOk: b:nextTmp();
		b:emit(inst: IrInst:BinOp(dst: posOk, op: '&', lhs: isPos, rhs: ltEnd, ty: IrType:I1));
		local String is isNeg: b:nextTmp();
		b:emit(inst: IrInst:Cmp(dst: isNeg, op: '<', lhs: stepVal, rhs: '0', ty: IrType:I64));
		local String is negOk: b:nextTmp();
		b:emit(inst: IrInst:BinOp(dst: negOk, op: '&', lhs: isNeg, rhs: gtEnd, ty: IrType:I1));
		local String is condVal: b:nextTmp();
		b:emit(inst: IrInst:BinOp(dst: condVal, op: '|', lhs: posOk, rhs: negOk, ty: IrType:I1));
		b:terminate(inst: IrInst:CondBr(cond: condVal, thenLabel: bodyLbl, elseLabel: endLbl));

		local IrBlock is bodyBlk: b:curFn:addBlock(label: bodyLbl);
		b:switchBlock(blk: bodyBlk);
		:bindWorkerParam(b: b, workerExpr: workerExpr, val: curIdx);
		:lowerLoopBody(b: b, bodyExpr: workerExpr, contLbl: stepLbl, breakLbl: endLbl);

		local IrBlock is stepBlk: b:curFn:addBlock(label: stepLbl);
		b:switchBlock(blk: stepBlk);
		local String is iLoad: b:nextTmp();
		b:emit(inst: IrInst:Load(dst: iLoad, slot: idxSlot, ty: IrType:I64));
		local String is iNext: b:nextTmp();
		b:emit(inst: IrInst:BinOp(dst: iNext, op: '+', lhs: iLoad, rhs: stepVal, ty: IrType:I64));
		b:emit(inst: IrInst:Store(slot: idxSlot, val: iNext, ty: IrType:I64));
		b:terminate(inst: IrInst:Br(target: hdrLbl));

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
	}

	local Function is lowerForeverCall(IrBuilder is b, CallData is call){
		local NamedArg is na0: call:args:get(index: 0);
		local Expression is workerExpr: na0:value;
		local String is bodyLbl: b:nextLabel(prefix: 'for_body');
		local String is endLbl: b:nextLabel(prefix: 'for_end');
		b:terminate(inst: IrInst:Br(target: bodyLbl));

		local IrBlock is bodyBlk: b:curFn:addBlock(label: bodyLbl);
		b:switchBlock(blk: bodyBlk);
		:lowerLoopBody(b: b, bodyExpr: workerExpr, contLbl: bodyLbl, breakLbl: endLbl);

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
	}
}
