#! Package base:compiler:ir
#! One function in an IR module.

Class is IrFunction{
	namespace: ['base', 'compiler', 'ir'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrParam],
		['base', 'compiler', 'ir', IrBlock],
		['base', 'struct', Array]
	];

	String is name: '';
	IrType is retType: IrType:Void;
	Array of IrParam is params: [];
	Array of IrBlock is blocks: [];
	Boolean is isExternal: false;
	String is sourceFile: '';
	Int is line: 0;

	replace Function is init(){
	}

	Function is init(String is name, IrType is retType){
		self:name: name;
		self:retType: retType;
	}

	Function is addParam(String is name, IrType is ty){
		self:params:add(item: IrParam:init(name: name, ty: ty));
	}

	Function of IrBlock is addBlock(String is label){
		local IrBlock is blk: IrBlock:init(label: label);
		self:blocks:add(item: blk);
		return blk;
	}
}
