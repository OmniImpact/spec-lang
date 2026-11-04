Class is FunctionTypeTest{

	replace Array of String is using: [
		base:io:*
	];

	local Function is executeCallback(Function is callback){
		output:line('Executing callback...');
	}

	replace Function is init(Map of String to String is args){
		local Function is myFunc;
		self:executeCallback(callback: myFunc);
		output:line('Function type test passed!');
	}

}
