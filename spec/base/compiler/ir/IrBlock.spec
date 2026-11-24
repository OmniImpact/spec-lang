#! Package base:compiler:ir
#! One basic block in an IR function.

Class is IrBlock{
	replace [String] is namespace: ['base', 'compiler', 'ir'];

	replace [[String]] is using: [
		['base', 'compiler', 'ir', IrInst],
		['base', 'struct', Array],
		['base', 'sys', as Loops()]
	];

	String is label: 'entry';
	[IrInst] is insts: [];
	[Int] is instLines: [];

	replace Function is init(){
	}

	replace Function is init(String is label){
		:label: label;
	}

	Function is append(IrInst is inst){
		:appendAt(inst: inst, line: 0);
	}

	Function is appendAt(IrInst is inst, Int is line){
		:insts:push(item: inst);
		:instLines:push(item: line);
	}

	Function is prependAt(IrInst is inst, Int is line){
		local Int is n: :insts:length();
		:insts:push(item: inst);
		:instLines:push(item: line);
		local Int is i: n;
		while({ i > 0 }, {
			:insts:set(index: i, item: :insts:get(index: i - 1));
			:instLines:set(index: i, item: :instLines:get(index: i - 1));
			i--;
		});
		:insts:set(index: 0, item: inst);
		:instLines:set(index: 0, item: line);
	}
}
