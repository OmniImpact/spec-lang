#! Package transitive:dep

Class is TransitiveLib{
	replace [String] is namespace: ['transitive', 'dep'];

	replace [[String]] is using: [
		['base', 'sys', as Output()]
	];

	Function of Int is triplify(Int is n){
		return n * 3;
	}
}
