#! Package n6cycle:b

Class is B{
	replace [String] is namespace: ['n6cycle', 'b'];
	replace [[String]] is using: [
		['n6cycle', 'a', as A()]
	];
	replace Function is init(Map of String to String is args) {}
}
