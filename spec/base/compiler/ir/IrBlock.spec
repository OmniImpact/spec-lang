#! Package base:compiler:ir
#! One basic block in an IR function.

Class is IrBlock{
	namespace: ['base', 'compiler', 'ir'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ir', IrInst],
		['base', 'struct', Array],
		['base', 'sys', as Loops()]
	];

	String is label: 'entry';
	Array of IrInst is insts: [];
	Array of Int is instLines: [];

	replace Function is init(){
	}

	Function is init(String is label){
		self:label: label;
	}

	Function is append(IrInst is inst){
		self:appendAt(inst: inst, line: 0);
	}

	Function is appendAt(IrInst is inst, Int is line){
		self:insts:add(item: inst);
		self:instLines:add(item: line);
	}

	Function is prependAt(IrInst is inst, Int is line){
		local Int is n: self:insts:length();
		self:insts:add(item: inst);
		self:instLines:add(item: line);
		local Int is i: n;
		while({ i > 0 }, {
			self:insts:set(index: i, item: self:insts:get(index: i - 1));
			self:instLines:set(index: i, item: self:instLines:get(index: i - 1));
			i--;
		});
		self:insts:set(index: 0, item: inst);
		self:instLines:set(index: 0, item: line);
	}
}
