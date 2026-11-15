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
		['base', 'sys', as Conditional()]
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
		if({ nm == 'if' && call:args:length() >= 2 }, { return true; });
		if({ nm == 'while' && call:args:length() >= 2 }, { return true; });
		return false;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		if({ nm == 'if' }, {
			return self:lowerIfCall(b: b, call: call);
		});
		if({ nm == 'while' }, {
			self:lowerWhileCall(b: b, call: call);
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
			condVal: b:lowerExpr(expr: condExpr);
		});
		return condVal;
	}

	local Function is lowerBlockExpr(IrBuilder is b, Expression is blkExpr){
		match(on: blkExpr, when: [
			Expression:AnonFn: local Function(Type is rt, Array of Parameter is ps, Array of Statement is bd){
				b:lowerStmts(stmts: bd);
			}
		], default: {
			local String is _unused: b:lowerExpr(expr: blkExpr);
		});
	}

	local Function of String is lowerIfCall(IrBuilder is b, CallData is call){
		local NamedArg is condNa: call:args:get(index: 0);
		local NamedArg is thenNa: call:args:get(index: 1);
		local Boolean is hasElse: call:args:length() >= 3;

		local String is condVal: self:lowerCondExpr(b: b, condExpr: condNa:value);
		local String is thenLbl: b:nextLabel(prefix: 'if_then');
		local String is elseLbl: b:nextLabel(prefix: 'if_else');
		local String is endLbl: b:nextLabel(prefix: 'if_end');
		if({ !hasElse }, { elseLbl: endLbl; });

		b:terminate(inst: IrInst:CondBr(cond: condVal, thenLabel: thenLbl, elseLabel: elseLbl));

		local IrBlock is thenBlk: b:curFn:addBlock(label: thenLbl);
		b:switchBlock(blk: thenBlk);
		self:lowerBlockExpr(b: b, blkExpr: thenNa:value);
		if({ !b:blkTerminated }, {
			b:terminate(inst: IrInst:Br(target: endLbl));
		});

		if({ hasElse }, {
			local NamedArg is elseNa: call:args:get(index: 2);
			local IrBlock is elseBlk: b:curFn:addBlock(label: elseLbl);
			b:switchBlock(blk: elseBlk);
			self:lowerBlockExpr(b: b, blkExpr: elseNa:value);
			if({ !b:blkTerminated }, {
				b:terminate(inst: IrInst:Br(target: endLbl));
			});
		});

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
		return '0';
	}

	local Function is lowerWhileCall(IrBuilder is b, CallData is call){
		local NamedArg is condNa: call:args:get(index: 0);
		local NamedArg is bodyNa: call:args:get(index: 1);

		local String is hdrLbl: b:nextLabel(prefix: 'while_hdr');
		local String is bodyLbl: b:nextLabel(prefix: 'while_body');
		local String is endLbl: b:nextLabel(prefix: 'while_end');

		b:terminate(inst: IrInst:Br(target: hdrLbl));

		local IrBlock is hdrBlk: b:curFn:addBlock(label: hdrLbl);
		b:switchBlock(blk: hdrBlk);
		local String is condVal: self:lowerCondExpr(b: b, condExpr: condNa:value);
		b:terminate(inst: IrInst:CondBr(cond: condVal, thenLabel: bodyLbl, elseLabel: endLbl));

		local IrBlock is bodyBlk: b:curFn:addBlock(label: bodyLbl);
		b:switchBlock(blk: bodyBlk);
		self:lowerBlockExpr(b: b, blkExpr: bodyNa:value);
		if({ !b:blkTerminated }, {
			b:terminate(inst: IrInst:Br(target: hdrLbl));
		});

		local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
		b:switchBlock(blk: endBlk);
	}
}
