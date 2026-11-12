#! specunit: negative
#! expect: Instance import cycle: A -> B -> A

#! N6: instance-import cycle A -> B -> A must fail to compile (E4).

Class is CycleRoot{
	replace Array of Array of String is using: [
		['n6cycle', 'a', A]
	];
	replace Function is init(Map of String to String is args) {}
}
