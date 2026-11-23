#! Package base:compiler:opt
#! Constant-folding pass over basic blocks for integer BinOp and Cmp.

Class of SpecOptimizer is ConstantFoldPass{
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
		return 'constant-fold';
	}

	replace Function of Int is order(){
		return 10;
	}

	replace Function is runOnFunction(IrFunction is fn){
		local Int is bi: 0;
		while({ bi < fn:blocks:length() }, {
			local IrBlock is blk: fn:blocks:get(index: bi);
			:foldBlock(blk: blk);
			bi++;
		});
	}

	local Function is foldBlock(IrBlock is blk){
		local Map of String to Int is intConsts: Map:init();
		local Map of String to Boolean is hasIntConst: Map:init();
		local Array of IrInst is out: Array();

		local Int is ii: 0;
		while({ ii < blk:insts:length() }, {
			local IrInst is inst: blk:insts:get(index: ii);
			local IrInst is nextInst: match(on: inst, when: [
				IrInst:ConstInt: local Function of IrInst(String is dst, Int is value){
					intConsts:set(key: dst, value: value);
					hasIntConst:set(key: dst, value: true);
					return inst;
				},
				IrInst:BinOp: local Function of IrInst(String is dst, String is op, String is lhs, String is rhs, IrType is ty){
					if({ hasIntConst:get(key: lhs, default: false) && hasIntConst:get(key: rhs, default: false) }, {
						local Int is a: intConsts:get(key: lhs, default: 0);
						local Int is b: intConsts:get(key: rhs, default: 0);
						local Boolean is folded: true;
						local Int is res: 0;
						if({ op == '+' }, { res: a + b; }, {
							if({ op == '-' }, { res: a - b; }, {
								if({ op == '*' }, { res: a * b; }, {
									if({ op == '/' && b != 0 }, { res: a / b; }, {
										if({ op == '%' && b != 0 }, { res: a % b; }, {
											if({ op == '&' }, { res: a & b; }, {
												if({ op == '|' }, { res: a | b; }, {
													if({ op == '^' }, { res: a ^ b; }, {
														folded: false;
													});
												});
											});
										});
									});
								});
							});
						});
						if({ folded }, {
							intConsts:set(key: dst, value: res);
							hasIntConst:set(key: dst, value: true);
							return IrInst:ConstInt(dst: dst, value: res);
						});
					});
					return inst;
				},
				IrInst:Cmp: local Function of IrInst(String is dst, String is op, String is lhs, String is rhs, IrType is ty){
					if({ hasIntConst:get(key: lhs, default: false) && hasIntConst:get(key: rhs, default: false) }, {
						local Int is a: intConsts:get(key: lhs, default: 0);
						local Int is b: intConsts:get(key: rhs, default: 0);
						local Boolean is folded: true;
						local Boolean is res: false;
						if({ op == '==' }, { res: a == b; }, {
							if({ op == '!=' }, { res: a != b; }, {
								if({ op == '<' }, { res: a < b; }, {
									if({ op == '<=' }, { res: a <= b; }, {
										if({ op == '>' }, { res: a > b; }, {
											if({ op == '>=' }, { res: a >= b; }, {
												folded: false;
											});
										});
									});
								});
							});
						});
						if({ folded }, {
							return IrInst:ConstBool(dst: dst, value: res);
						});
					});
					return inst;
				}
			], default: {
				return inst;
			});
			out:add(item: nextInst);
			ii++;
		});
		blk:insts: out;
	}
}
