#! Package n6cycle:b

Class is B{
	namespace: ['n6cycle', 'b'];
	replace Array of Array of String is using: [
		['n6cycle', 'a', as A()]
	];
	replace Function is init(Map of String to String is args) {}
}
