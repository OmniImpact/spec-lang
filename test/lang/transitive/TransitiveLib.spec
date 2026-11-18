#! Package transitive:dep

Class is TransitiveLib{
	namespace: ['transitive', 'dep'];

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	Function of Int is triplify(Int is n){
		return n * 3;
	}
}
