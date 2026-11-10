Class is ListGuardNegativeTest{

	replace Array of Array of String is using: [
		['base', 'sys', Output],
		['base', 'struct', List],
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		# Bare List without [T] element syntax is rejected
		local List is bare;

		# get without a mandatory default is rejected
		local [Byte] is buf;
		local Byte is b: buf:get(index: 0);

		Output:line('unreachable');
	}
}
