#! SpecUnit sweep (from generic_function_test.spec): a Function-typed
#! parameter — a Function of String to Boolean value (held in an
#! unassigned local, so possibly null) flows through a named-argument
#! call into a Function-typed parameter and the call still returns.

Class of SpecUnitTest is TestGenericFunction{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	Function of Boolean is runPredicate(Function of String to Boolean is predicate, String is input){
		return true;
	}

	Function is testFunctionTypeParameter(){
		local Function of String to Boolean is myPred;
		local Boolean is result: self:runPredicate(predicate: myPred, input: 'test');
		Assert:isTrue(result);
	}
}
