Class is FunctionTypeTest{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	local Function is executeCallback(Function is callback){
		Output:line('Executing callback...');
	}

	replace Function is init(Map of String to String is args){
		local Function is myFunc;
		self:executeCallback(callback: myFunc);
		Output:line('Function type test passed!');
	}

}
