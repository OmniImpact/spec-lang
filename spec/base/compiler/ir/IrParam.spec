#! Package base:compiler:ir
#! One parameter in an IR function signature.

Class is IrParam{
	namespace: ['base', 'compiler', 'ir'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ir', IrType]
	];

	String is name: '';
	IrType is ty: IrType:I64;

	replace Function is init(){
	}

	Function is init(String is name, IrType is ty){
		:name: name;
		:ty: ty;
	}
}
