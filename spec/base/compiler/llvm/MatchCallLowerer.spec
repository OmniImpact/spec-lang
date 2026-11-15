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
		return call:name == 'match';
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
		local Boolean is handledAnon: false;
		match(on: armExpr, when: [
			Expression:AnonFn: local Function(Type is _rt, Array of Parameter is _ps, Array of Statement is bd){
				handledAnon: true;
				local Int is i: 0;
				while({ i < bd:length() && !b:blkTerminated }, {
					local Statement is st: bd:get(index: i);
					local Boolean is isLast: i == (bd:length() - 1);
					if({ hasResult && isLast }, {
						if({ !self:storeLastStmt(b: b, st: st, resSlot: resSlot, resTy: resTy) }, {
							b:lowerStmts(stmts: [st]);
						});
					}, {
						b:lowerStmts(stmts: [st]);
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
		if({ !b:blkTerminated }, {
			b:terminate(inst: IrInst:Br(target: endLbl));
		});
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

		local IrType is resTy: b:irTypeFor(specType: expr:resolvedType);
		local Boolean is hasResult: resTy != IrType:Void;
		local String is resSlot: '';
		if({ hasResult }, {
			resSlot: '%match_res_' . (b:nextTmp());
			resSlot: '%match_res_' . (b:tmpCounter as String);
			b:emit(inst: IrInst:Alloca(slot: resSlot, ty: resTy));
		});

		local String is subjVal: '0';
		local IrType is subjTy: IrType:I64;
		if({ hasOn }, {
			subjVal: b:lowerExpr(expr: onExpr);
			subjTy: b:irTypeFor(specType: onExpr:resolvedType);
			if({ subjTy == IrType:Void }, { subjTy: IrType:I64; });
		});

		local String is endLbl: b:nextLabel(prefix: 'match_end');
		local Array of Expression is keys: [];
		local Array of Expression is vals: [];
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
			if({ self:isElseKey(key: k) }, {
				hasElse: true;
				elseExpr: v;
			}, {
				local String is condVal: '0';
				if({ hasOn }, {
					local String is kVal: b:lowerExpr(expr: k);
					condVal: b:nextTmp();
					if({ subjTy == IrType:Ptr }, {
						b:emit(inst: IrInst:IrCall(dst: condVal, hasDst: true, retType: IrType:I1, callee: 'spec_string_equals', argTypes: [IrType:Ptr, IrType:Ptr], args: [subjVal, kVal]));
					}, {
						b:emit(inst: IrInst:Cmp(dst: condVal, op: '==', lhs: subjVal, rhs: kVal, ty: subjTy));
					});
				}, {
					local Boolean is unwrapped: false;
					match(on: k, when: [
						Expression:AnonFn: local Function(Type is _rt, Array of Parameter is _ps, Array of Statement is kbd){
							unwrapped: true;
							if({ kbd:length() > 0 }, {
								local Statement is ks: kbd:get(index: 0);
								match(on: ks, when: [
									Statement:Return: local Function(Expression is re, Boolean is hr){
										if({ hr }, { condVal: b:lowerExpr(expr: re); });
									},
									Statement:Expr: local Function(Expression is es){
										condVal: b:lowerExpr(expr: es);
									}
								], default: {});
							});
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
				self:lowerArmBody(b: b, armExpr: v, resSlot: resSlot, resTy: resTy, hasResult: hasResult, endLbl: endLbl);

				local IrBlock is nextBlk: b:curFn:addBlock(label: nextLbl);
				b:switchBlock(blk: nextBlk);
			});
			ki++;
		});

		if({ hasElse }, {
			self:lowerArmBody(b: b, armExpr: elseExpr, resSlot: resSlot, resTy: resTy, hasResult: hasResult, endLbl: endLbl);
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
