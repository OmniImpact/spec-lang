#! Package n6cycle:a

Class is A{
	namespace: ['n6cycle', 'a'];
	replace Array of Array of String is using: [
		['n6cycle', 'b', as B()]
	];
	replace Function is init(Map of String to String is args) {}
}
