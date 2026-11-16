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

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		if({ nm == 'init' }, {
			local Boolean is isCf: false;
			match(on: call:target, when: [
				Expression:Ident: local Function(String is tn){
					if({ tn == 'Conditional' || tn == 'Loops' || tn == 'LoopControl' }, { isCf: true; });
				}
			], default: {});
			return isCf;
		});
		if({ nm == 'stop' || nm == 'isStopped' || nm == 'complete' }, {
			if({ call:target:resolvedType == 'LoopControl' }, { return true; });
			local Boolean is isLc: false;
			match(on: call:target, when: [
				Expression:Ident: local Function(String is tn){
					if({ tn == 'LoopControl' }, { isLc: true; });
				}
			], default: {});
			if({ isLc }, { return true; });
		});
		if({ (nm == 'if' || nm == 'branch') && call:args:length() >= 2 }, { return true; });
		if({ nm == 'while' && call:args:length() >= 2 }, { return true; });
		if({ nm == 'repeat' && call:args:length() == 2 }, { return self:isBareOrLoopsTarget(call: call); });
		if({ nm == 'until' && call:args:length() == 2 }, { return self:isBareOrLoopsTarget(call: call); });
		if({ nm == 'loop' && call:args:length() >= 2 }, { return self:isBareOrLoopsTarget(call: call); });
		if({ nm == 'times' && call:args:length() == 2 }, { return self:isBareOrLoopsTarget(call: call); });
		if({ nm == 'range' && call:args:length() == 3 }, { return self:isBareOrLoopsTarget(call: call); });
		if({ nm == 'rangeStep' && call:args:length() == 4 }, { return self:isBareOrLoopsTarget(call: call); });
		if({ nm == 'forever' && call:args:length() == 1 }, { return self:isBareOrLoopsTarget(call: call); });
		return false;
	}

	local Function of Boolean is isBareOrLoopsTarget(CallData is call){
		local Boolean is ok: false;
		match(on: call:target, when: [
			Expression:Unknown: local Function(){ ok: true; },
			Expression:Ident: local Function(String is tn){
				if({ tn == 'Loops' || tn == 'self' || tn == '' }, { ok: true; });
			},
			Expression:FieldAccess: local Function(Expression is obj, String is mem){
				if({ mem == 'Loops' }, { ok: true; });
			}
		], default: {});
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		if({ nm == 'init' }, {
			local Boolean is isLcInit: false;
			match(on: call:target, when: [
				Expression:Ident: local Function(String is tn){
					if({ tn == 'LoopControl' }, { isLcInit: true; });
				}
			], default: {});
			if({ isLcInit }, {
				if({ call:args:length() == 0 }, {
					local String is dst0: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: dst0, hasDst: true, retType: IrType:Ptr, callee: 'LoopControl_new', argTypes: [], args: []));
					return dst0;
				});
				local NamedArg is cbArg: call:args:get(index: 0);
				local Expression is cbExpr: cbArg:value;
				local String is cbV: b:lowerExpr(expr: cbExpr);
				local String is cbClass: cbExpr:resolvedType:replaceAll(target: ':', replacement: '_');
				local String is fnRef: 'null';
				if({ cbClass != '' }, { fnRef: '@' . cbClass . '_onComplete'; });
				local String is dst1: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst1, hasDst: true, retType: IrType:Ptr, callee: 'spec_loop_control_with_callback', argTypes: [IrType:Ptr, IrType:Ptr], args: [cbV, fnRef]));
				return dst1;
			});
			return 'null';
		});
		if({ nm == 'stop' }, {
			local String is recv: b:lowerExpr(expr: call:target);
			b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'LoopControl_stop', argTypes: [IrType:Ptr], args: [recv]));
			return '0';
		});
		if({ nm == 'isStopped' }, {
			local String is recv: b:lowerExpr(expr: call:target);
			local String is dst2: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: dst2, hasDst: true, retType: IrType:I1, callee: 'spec_loop_control_is_stopped', argTypes: [IrType:Ptr], args: [recv]));
			return dst2;
		});
		if({ nm == 'complete' }, {
			local String is recv: b:lowerExpr(expr: call:target);
			b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_loop_control_complete', argTypes: [IrType:Ptr], args: [recv]));
			return '0';
		});
		if({ nm == 'if' || nm == 'branch' }, {
			return self:lowerIfCall(b: b, expr: expr, call: call);
		});
		if({ nm == 'while' }, {
			self:lowerWhileCall(b: b, call: call);
			return '0';
		});
		if({ nm == 'repeat' }, {
			self:lowerRepeatCall(b: b, call: call);
			return '0';
		});
		if({ nm == 'until' }, {
			self:lowerUntilCall(b: b, call: call);
			return '0';
		});
		if({ nm == 'loop' }, {
			self:lowerLoopCall(b: b, call: call);
			return '0';
		});
		if({ nm == 'times' }, {
			self:lowerTimesCall(b: b, call: call);
			return '0';
		});
		if({ nm == 'range' }, {
			self:lowerRangeCall(b: b, call: call);
			return '0';
		});
		if({ nm == 'rangeStep' }, {
			self:lowerRangeStepCall(b: b, call: call);
			return '0';
		});
		if({ nm == 'forever' }, {
			self:lowerForeverCall(b: b, call: call);
			return '0';
		});
		return '0';
	}

	local Function of String is lowerCondExpr(IrBuilder is b, Expression is condExpr){
		local String is condVal: '0';
		match(on: condExpr, when: [
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				if({ bd:length() > 0 }, {
					local Statement is bs: bd:get(index: 0);
					match(on: bs, when: [
						Statement:Return: local Function(Expression is re, Boolean is hr){
							if({ hr }, { condVal: b:lowerExpr(expr: re); });
						},
						Statement:Expr: local Function(Expression is es){
							condVal: b:lowerExpr(expr: es);
						}
					], default: {});
				});
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
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				b:lowerStmts(stmts: bd);
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
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
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
		local Int is ai: 2;
		while({ ai < call:args:length() }, {
			local NamedArg is na: call:args:get(index: ai);
			if({ na:name == 'finally' }, {
				hasFinally: true;
				finallyNa: na;
			}, {
				hasElse: true;
				elseNa: na;
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

		local String is condVal: self:lowerCondExpr(b: b, condExpr: condNa:value);
		local String is thenLbl: b:nextLabel(prefix: 'if_then');
		local String is elseLbl: b:nextLabel(prefix: 'if_else');
		local String is endLbl: b:nextLabel(prefix: 'if_end');
		if({ !hasElse }, { elseLbl: endLbl; });

		b:terminate(inst: IrInst:CondBr(cond: condVal, thenLabel: thenLbl, elseLabel: elseLbl));

		local IrBlock is thenBlk: b:curFn:addBlock(label: thenLbl);
		b:switchBlock(blk: thenBlk);
		if({ yieldVal }, {
			local String is tv: self:lowerBlockExprVal(b: b, blkExpr: thenNa:value, expectedTy: resTy);
			if({ !b:blkTerminated }, {
				if({ tv != '' }, {
					b:emit(inst: IrInst:Store(slot: resSlot, val: tv, ty: resTy));
				});
				b:terminate(inst: IrInst:Br(target: endLbl));
			});
		}, {
			self:lowerBlockExpr(b: b, blkExpr: thenNa:value);
			if({ !b:blkTerminated }, {
				b:terminate(inst: IrInst:Br(target: endLbl));
			});
		});

		if({ hasElse }, {
			local IrBlock is elseBlk: b:curFn:addBlock(label: elseLbl);
			b:switchBlock(blk: elseBlk);
			if({ yieldVal }, {
				local String is ev: self:lowerBlockExprVal(b: b, blkExpr: elseNa:value, expectedTy: resTy);
				if({ !b:blkTerminated }, {
					if({ ev != '' }, {
						b:emit(inst: IrInst:Store(slot: resSlot, val: ev, ty: resTy));
					});
					b:terminate(inst: IrInst:Br(target: endLbl));
				});
			}, {
				self:lowerBlockExpr(b: b, blkExpr: elseNa:value);
				if({ !b:blkTerminated }, {
					b:terminate(inst: IrInst:Br(target: endLbl));
				});
			});
		});

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
		if({ hasFinally }, {
			self:lowerBlockExpr(b: b, blkExpr: finallyNa:value);
		});
		if({ yieldVal }, {
			local String is outVal: b:nextTmp();
			b:emit(inst: IrInst:Load(dst: outVal, slot: resSlot, ty: resTy));
			return outVal;
		});
		return '0';
	}

	local Function is lowerLoopBody(IrBuilder is b, Expression is bodyExpr, String is contLbl, String is breakLbl){
		local Boolean is returnsBool: false;
		match(on: bodyExpr, when: [
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				if({ rt:name == 'Boolean' }, {
					returnsBool: true;
				});
			}
		], default: {});
		if({ returnsBool }, {
			local String is contVal: self:lowerBlockExprVal(b: b, blkExpr: bodyExpr, expectedTy: IrType:I1);
			if({ !b:blkTerminated }, {
				if({ contVal != '' }, {
					b:terminate(inst: IrInst:CondBr(cond: contVal, thenLabel: contLbl, elseLabel: breakLbl));
				}, {
					b:terminate(inst: IrInst:Br(target: contLbl));
				});
			});
		}, {
			self:lowerBlockExpr(b: b, blkExpr: bodyExpr);
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
		if({ hasVars }, {
			match(on: varsExpr, when: [
				Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
					local Int is pi: 0;
					while({ pi < ps:length() }, {
						local Parameter is p: ps:get(index: pi);
						local IrType is pty: b:irTypeFor(specType: p:paramType:name);
						local Boolean is pArc: b:isArcSpecType(specType: p:paramType:name);
						local String is _wtmp: b:nextTmp();
						local String is slot: '%wvar_' . p:name . '_' . (b:tmpCounter as String);
						b:localSlots:set(key: p:name, value: slot);
						b:localTypes:set(key: p:name, value: pty);
						b:localIsArc:set(key: p:name, value: pArc);
						b:localSpecTypes:set(key: p:name, value: p:paramType:name);
						b:localSpecTypes:set(key: p:name, value: p:paramType:name);
						b:emit(inst: IrInst:Alloca(slot: slot, ty: pty));
						if({ p:hasDefault }, {
							local String is val: b:lowerExpr(expr: p:defaultExpr);
							local IrType is vty: b:irTypeFor(specType: p:defaultExpr:resolvedType);
							val: b:castIfNeeded(val: val, fromTy: vty, toTy: pty);
							if({ val == '' }, { val: b:emitDefaultVal(ty: pty); });
							if({ pArc && val != '' && val != 'null' }, {
								b:emit(inst: IrInst:Retain(val: val));
							});
							b:emit(inst: IrInst:Store(slot: slot, val: val, ty: pty));
						}, {
							b:emit(inst: IrInst:Store(slot: slot, val: b:emitDefaultVal(ty: pty), ty: pty));
						});
						if({ pArc }, { b:ownedSlots:add(item: slot); });
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
		local String is condVal: self:lowerCondExpr(b: b, condExpr: evalExpr);
		b:terminate(inst: IrInst:CondBr(cond: condVal, thenLabel: bodyLbl, elseLabel: endLbl));

		local IrBlock is bodyBlk: b:curFn:addBlock(label: bodyLbl);
		b:switchBlock(blk: bodyBlk);
		self:lowerLoopBody(b: b, bodyExpr: iterExpr, contLbl: hdrLbl, breakLbl: endLbl);

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
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
		self:lowerLoopBody(b: b, bodyExpr: workerExpr, contLbl: stepLbl, breakLbl: endLbl);

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
		self:lowerLoopBody(b: b, bodyExpr: iterExpr, contLbl: evalLbl, breakLbl: endLbl);

		local IrBlock is evalBlk: b:curFn:addBlock(label: evalLbl);
		b:switchBlock(blk: evalBlk);
		local String is condVal: self:lowerCondExpr(b: b, condExpr: evalExpr);
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

		if({ hasVars }, {
			match(on: varsExpr, when: [
				Expression:AnonFn: local Function(Type is rt, Array of Parameter is params, Array of Statement is bd){
					local Int is pi: 0;
					while({ pi < params:length() }, {
						local Parameter is p: params:get(index: pi);
						local IrType is vty: b:irTypeFor(specType: p:paramType:name);
						local String is _vtmp: b:nextTmp();
						local String is slot: '%lvar_' . p:name . '_' . (b:tmpCounter as String);
						b:localSlots:set(key: p:name, value: slot);
						b:localTypes:set(key: p:name, value: vty);
						b:localIsArc:set(key: p:name, value: b:isArcSpecType(specType: p:paramType:name));
						b:localSpecTypes:set(key: p:name, value: p:paramType:name);
						b:localSpecTypes:set(key: p:name, value: p:paramType:name);
						b:emit(inst: IrInst:Alloca(slot: slot, ty: vty));
						if({ p:hasDefault }, {
							local IrType is ity: b:irTypeFor(specType: p:defaultExpr:resolvedType);
							local String is ival: b:lowerExpr(expr: p:defaultExpr);
							ival: b:castIfNeeded(val: ival, fromTy: ity, toTy: vty);
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
		local String is condVal: self:lowerCondExpr(b: b, condExpr: evalExpr);
		b:terminate(inst: IrInst:CondBr(cond: condVal, thenLabel: bodyLbl, elseLabel: endLbl));

		local IrBlock is bodyBlk: b:curFn:addBlock(label: bodyLbl);
		b:switchBlock(blk: bodyBlk);
		self:lowerLoopBody(b: b, bodyExpr: iterExpr, contLbl: hdrLbl, breakLbl: endLbl);

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
	}

	local Function is bindWorkerParam(IrBuilder is b, Expression is workerExpr, String is val){
		match(on: workerExpr, when: [
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				if({ ps:length() > 0 }, {
					local Parameter is p: ps:get(index: 0);
					local String is _ptmp: b:nextTmp();
					local String is slot: '%lidx_' . p:name . '_' . (b:tmpCounter as String);
					b:localSlots:set(key: p:name, value: slot);
					b:localTypes:set(key: p:name, value: IrType:I64);
					b:localIsArc:set(key: p:name, value: false);
					b:localSpecTypes:set(key: p:name, value: 'Int');
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
		self:lowerIntSteppedLoop(b: b, startVal: '0', endVal: endVal, stepVal: '1', workerExpr: workerExpr);
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
		self:lowerIntSteppedLoop(b: b, startVal: startVal, endVal: endVal, stepVal: '1', workerExpr: workerExpr);
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
		self:lowerIntSteppedLoop(b: b, startVal: startVal, endVal: endVal, stepVal: stepVal, workerExpr: workerExpr);
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
		self:bindWorkerParam(b: b, workerExpr: workerExpr, val: curIdx);
		self:lowerLoopBody(b: b, bodyExpr: workerExpr, contLbl: stepLbl, breakLbl: endLbl);

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
		self:lowerLoopBody(b: b, bodyExpr: workerExpr, contLbl: bodyLbl, breakLbl: endLbl);

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
	}
}
