class FunctionTypeTest{

	replace local Array of String is using: [
		base:io:*
	];

	replace local Function is executeCallback(Function is callback){
		output:line("Executing callback...");
	}

	replace local Function is init(Map of String to String is args){
		local Function is myFunc;
		self:executeCallback(callback: myFunc);
		output:line("Function type test passed!");
	}

}
