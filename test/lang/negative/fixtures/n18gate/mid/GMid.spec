#! Package n18:mid

Class is GMid{
	replace [String] is namespace: ['n18', 'mid'];
	replace [[String]] is using: [
		['n18', 'lib', GTarget]
	];
	replace Function is init(Map of String to String is args){}
}
