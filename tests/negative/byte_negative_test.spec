Class is ByteNegativeTest{

	replace Array of Array of String is using: [
		['base', 'sys', Output],
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		# Int is not implicitly assignable to Byte: cast required
		local Byte is direct: 5;

		# Strings cannot cast to Byte
		local Byte is fromString: 'hello' as Byte;

		Output:line('unreachable');
	}
}
