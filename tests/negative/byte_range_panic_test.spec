#! specunit: run-fail
#! expect: [Spec Runtime Panic]
#! expect: Byte cast out of range: 300

Class is ByteRangePanicTest{

	replace Array of Array of String is using: [
		['base', 'sys', Output],
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		# Out-of-range Int-to-Byte casts panic at runtime (primitive-level fail-fast)
		local Byte is b: 300 as Byte;
		Output:line('unreachable');
	}
}
