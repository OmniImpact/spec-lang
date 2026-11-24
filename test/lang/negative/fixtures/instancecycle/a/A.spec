#! Package n6cycle:a

Class is A{
	replace [String] is namespace: ['n6cycle', 'a'];
	replace [[String]] is using: [
		['n6cycle', 'b', as B()]
	];
	replace Function is init(Map of String to String is args) {}
}
