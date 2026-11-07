Class is GenericFunctionTest{

	replace Array of Array of String is using: [
		['base', 'io'],
	];

	local Function of Boolean is testPredicate(Function of String to Boolean is predicate, String is input){
		output:line('Predicate checked with input: ' . input);
		return true;
	}

	replace Function is init(Map of String to String is args){
		local Function of String to Boolean is myPred;
		local Boolean is result: self:testPredicate(predicate: myPred, input: 'test');
		if (result) {
			output:line('Generic function type test passed!');
		}
	}

}
