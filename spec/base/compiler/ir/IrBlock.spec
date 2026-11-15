#! Package base:compiler:ir
#! One basic block in an IR function.

Class is IrBlock{
	namespace: ['base', 'compiler', 'ir'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ir', IrInst],
		['base', 'struct', Array]
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
}
